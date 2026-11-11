"""Nightmare Highschool: the QOL items kit (12 everyday-carry items), held on the R6 body.

Headless:
  E:/Blender/blender.exe -b --factory-startup -P nh_qol.py -- <Item>[,<Item>...]|all [--out E:/NH-Work/qol]
        [--bake] [--size 2048] [--samples 64] [--gpu] [--norender] [--res 900] [--fast]

Reuses the accessory kit's materials, helpers, bake and R6 mannequin (art/characters/accessories/nh_acc.py, imported
as A, never edited). Every item is built in ITEM SPACE: studs, its grip point at the origin, Blender -Y = the side
that faces away from the holder, +Z up as it is held. A HOLD then poses the R6 mannequin (shoulder pitch / yaw, like
the phone's Right Shoulder C0 pose) and places the item at the hand.

Per item (OUT = E:/NH-Work/qol):
  fbx/NHQol_<Item>.fbx     item-space pieces, global_scale 0.01
  maps/NHAcc_<Item>_*.png  the 2048 atlas (with --bake)
  layout/<Item>.json       pieces (kind, tris, size, bbox centre in item space, Roblox axes), the hold (shoulder
                           angles, the item's CFrame in the arm's frame), the clearance report
  renders/<Item>_{hero,close,pov,solo}.png
Piece kinds: Main (baked atlas), Glow (Neon, colour), Glass (Roblox Glass, see-through), and moving Main pieces with
their own MeshPart (the compass needle, the tin lid).
"""
import bpy, bmesh, json, math, os, sys
from mathutils import Vector, Matrix, Euler
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--out" not in argv:
    sys.argv += ["--out", "E:/NH-Work/qol"]
if "--bake" not in argv and "--nobake" not in sys.argv:
    sys.argv += ["--nobake"]
sys.path.insert(0, os.path.join(HERE, "..", "accessories"))
import nh_acc as A   # noqa: E402

OUT = A.OUT
PRINTS = os.path.join(OUT, "prints")
FAST = "--fast" in argv
for d in ("fbx", "maps", "layout", "renders", "blend"):
    os.makedirs(os.path.join(OUT, d), exist_ok=True)
lerp, V = A.lerp, Vector

# ================================================================== extra materials
_print_cache = {}


def mat_print(name, png, rough=0.7, metal=0.0, bump=0.02, coat=0.0):
    """printed paper / label: the image read through the nh_print corner attribute (survives the bake UV pass)"""
    key = (name, png)
    if key in _print_cache:
        return _print_cache[key]
    m, T, bs = A._base(name)
    at = T.node("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name="nh_print")
    tx = T.node("ShaderNodeTexImage", interpolation="Cubic", extension="EXTEND")
    tx.image = bpy.data.images.load(os.path.join(PRINTS, png), check_existing=True)
    T.L(at.outputs["Vector"], tx.inputs["Vector"])
    nz = T.node("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    T.L(T.coord(90.0), nz.inputs["Vector"])
    bp = T.node("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.004
    T.L(nz.outputs["Fac"], bp.inputs["Height"])
    if coat:
        bs.inputs["Coat Weight"].default_value = coat
    A._weather(T, bs, tx.outputs["Color"], A._val(T, rough), A._val(T, metal), bp.outputs["Normal"], 0.12, False, 0.35, 0.004)
    _print_cache[key] = m
    return m


def mat_glass(name, tint=(0.92, 0.88, 0.80)):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*tint, 1)
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["IOR"].default_value = 1.45
    m["nh_glass"] = True
    return m


def set_print(ob, fn):
    """write the nh_print corner attribute: fn(co, normal) -> (u, v) per loop (object = world space here)"""
    me = ob.data
    at = me.attributes.get("nh_print") or me.attributes.new("nh_print", "FLOAT_VECTOR", "CORNER")
    mw = ob.matrix_world
    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()
        for li in poly.loop_indices:
            co = mw @ me.vertices[me.loops[li].vertex_index].co
            u, v = fn(co, n)
            at.data[li].vector = (u, v, 0.0)
    return ob


def planar(o, ux, vy, w, h):
    """uv on a plane: origin o (the image's bottom-left), axis vectors ux (right), vy (up), size w x h"""
    o, ux, vy = V(o), V(ux).normalized(), V(vy).normalized()
    return lambda co, n: ((co - o).dot(ux) / w, (co - o).dot(vy) / h)


def grid_panel(name, corner, ux, vy, w, h, thick, mat, nu=1, nv=1, bend=None):
    """a thin printable panel (paper, card): a grid nu x nv on the plane, given thickness along -(ux x vy).
    bend(u, v) -> offset along the panel normal (a gentle curl)."""
    c, ux, vy = V(corner), V(ux).normalized(), V(vy).normalized()
    nrm = ux.cross(vy).normalized()
    G = []
    for i in range(nu + 1):
        col = []
        for j in range(nv + 1):
            u, v = i / nu, j / nv
            p = c + ux * (u * w) + vy * (v * h)
            if bend:
                p += nrm * bend(u, v)
            col.append(p)
        G.append(col)
    ob = A.surface(name, G, thick, mat, smooth_all=True)
    return ob


# ================================================================== items and holds
ITEMS = {}


def item(key, name, hold, views=("hero", "close", "solo"), notes=""):
    """hold = dict(r=(pitch, yaw), l=(pitch, yaw) or None, at=(x, y, z) world offset from the right hand point,
    rot=(rx, ry, rz) degrees, the item's world rotation; or worn='LeftLeg' for a worn piece (no hold)"""
    def deco(fn):
        ITEMS[key] = dict(name=name, build=fn, hold=hold, views=views, notes=notes)
        return fn
    return deco


R_PIVOT, L_PIVOT = V((-1.0, 0, 0.5)), V((1.0, 0, 0.5))
R_HAND_REST, L_HAND_REST = V((-1.5, 0, -1.0)), V((1.5, 0, -1.0))


def arm_matrix(side, pitch, yaw):
    """the arm's rotation about its shoulder joint: raise forward by pitch, then swing inward by yaw (degrees)"""
    pv = R_PIVOT if side == "R" else L_PIVOT
    sgn = 1 if side == "R" else -1
    Rm = Matrix.Rotation(math.radians(sgn * yaw), 4, "Z") @ Matrix.Rotation(math.radians(-pitch), 4, "X")
    return Matrix.Translation(pv) @ Rm @ Matrix.Translation(-pv)


def place_matrix(hold):
    Mr = arm_matrix("R", *hold["r"])
    hand = Mr @ R_HAND_REST
    rot = Euler([math.radians(a) for a in hold.get("rot", (0, 0, 0))], "XYZ").to_matrix().to_4x4()
    pos = hand + V(hold.get("at", (0, 0, 0)))
    if hold.get("mid"):   # two-handed: centred between the hands
        pos.x = 0.0
    return Matrix.Translation(pos) @ rot, Mr


C_RB = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))   # Blender (x, y, z) -> Roblox (-x, z, y)


def to_rbx_cf(M):
    """a Blender transform -> Roblox CFrame components (x, y, z, R00..R22)"""
    p = C_RB @ M.to_translation()
    R = C_RB @ M.to_3x3() @ C_RB.inverted()
    return [round(v, 5) for v in (p.x, p.y, p.z, R[0][0], R[0][1], R[0][2], R[1][0], R[1][1], R[1][2], R[2][0], R[2][1], R[2][2])]


# ================================================================== the body for holds
def posed_mannequin(hold, body="standard"):
    man = A.mannequin(body)
    parts = {}
    for o in man:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        c = sum(vs, V()) / max(1, len(vs))
        if o.get("nh_mannequin") and abs(c.z) < 0.2 and c.x < -1.2:
            parts["RightArm"] = o
        elif o.get("nh_mannequin") and abs(c.z) < 0.2 and c.x > 1.2:
            parts["LeftArm"] = o
        elif abs(c.z) < 0.2 and abs(c.x) < 0.2:
            parts["Torso"] = o
        elif c.z < -1.5:
            parts["RightLeg" if c.x < 0 else "LeftLeg"] = o
        elif c.z > 1.2:
            parts["Head"] = o
    if hold.get("r"):
        parts["RightArm"].matrix_world = arm_matrix("R", *hold["r"]) @ parts["RightArm"].matrix_world
    if hold.get("l"):
        parts["LeftArm"].matrix_world = arm_matrix("L", *hold["l"]) @ parts["LeftArm"].matrix_world
    bpy.context.view_layer.update()
    return man, parts


def _world_bvh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new(); bm.from_mesh(me); bm.transform(ob.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    t = BVHTree.FromBMesh(bm)
    verts = [v.co.copy() for v in bm.verts]
    bm.free(); ev.to_mesh_clear()
    return t, verts


def clearance(objs, parts, grip_part="RightArm", also=()):
    """per body part: intersecting triangle pairs and the deepest item vertex inside it; the gap from the item to
    the holding hand (a held item must touch it: gap <= 0.04)"""
    rep = {}
    items = [_world_bvh(o) for o in objs.values() if o.type == "MESH"]
    for pn, po in parts.items():
        pb, pverts = _world_bvh(po)
        inter, deep, gap = 0, 0.0, 99.0
        for ib, iverts in items:
            inter += len(pb.overlap(ib))
            for v in iverts[::max(1, len(iverts) // 4000)]:
                loc, nrm, idx, dist = pb.find_nearest(v)
                if loc is None:
                    continue
                inside = (v - loc).dot(nrm) < 0
                if inside:
                    deep = max(deep, dist)
                else:
                    gap = min(gap, dist)
        rep[pn] = dict(intersections=inter, deepest=round(deep, 4), gap=round(gap, 4))
    fails = [f"{pn} clip {r['deepest']} ({r['intersections']} tri pairs)" for pn, r in rep.items()
             if (r["deepest"] > 0.003 or r["intersections"] > 0) and pn not in also]
    if grip_part in rep and rep[grip_part]["gap"] > 0.04 and rep[grip_part]["deepest"] == 0:
        fails.append(f"hovers {rep[grip_part]['gap']} from the {grip_part}")
    return rep, fails


def _signed(objs, part):
    """deepest item vertex inside the part and the smallest outside gap"""
    pb, _ = _world_bvh(part)
    deep, gap = 0.0, 99.0
    for o in objs.values():
        if o.type != "MESH":
            continue
        _, iverts = _world_bvh(o)
        for v in iverts:
            loc, nrm, idx, dist = pb.find_nearest(v)
            if loc is None:
                continue
            if (v - loc).dot(nrm) < 0:
                deep = max(deep, dist)
            else:
                gap = min(gap, dist)
    return deep, gap


def rest_on(objs, parts, names, n, touch=0.012):
    """slide the item along n (out of the hand) until nothing is inside the parts and it touches (gap <= touch)"""
    n = V(n).normalized()
    moved = V()
    def overlaps():
        tot = 0
        items = [_world_bvh(o)[0] for o in objs.values() if o.type == "MESH"]
        for nm in names:
            pb, _ = _world_bvh(parts[nm])
            tot += sum(len(pb.overlap(ib)) for ib in items)
        return tot
    def move(step):
        nonlocal moved
        for o in objs.values():
            o.matrix_world = Matrix.Translation(step) @ o.matrix_world
        moved += step
        bpy.context.view_layer.update()

    def state():
        res = [_signed(objs, parts[nm]) for nm in names]
        return max(r[0] for r in res), min(r[1] for r in res)
    # 1. out: until nothing is inside the hand and no triangle crosses it
    for _ in range(40):
        deep, gap = state()
        if deep > 0.0004:
            move(n * (deep + 0.002))
        elif overlaps():
            move(n * 0.004)
        else:
            break
    # 2. back in toward the hand (rest on it), never into it: halve the step whenever it would clip
    step = None
    for _ in range(12):
        deep, gap = state()
        if gap <= touch:
            break
        step = (gap - touch * 0.4) if step is None else step
        move(-n * step)
        d2, _ = state()
        if d2 > 0.0004 or overlaps():
            move(n * step)
            step *= 0.5
            if step < 0.001:
                break
    return moved


# ================================================================== run
def piece_kind(n):
    return A.PIECES[n]["kind"]


def run(key, render=True):
    spec = ITEMS[key]
    A.reset()
    sc = bpy.context.scene
    M = A.palette()
    extra = spec["build"](M) or {}
    objs = A.join_pieces()
    if extra.get("scale"):   # scale the whole item about its grip point
        for o in objs.values():
            o.data.transform(Matrix.Scale(extra["scale"], 4))
    for n, o in objs.items():
        k = piece_kind(n)
        if k == "Glow":
            o.data.materials.clear(); o.data.materials.append(A.mat_glow("G_" + n, A.PIECES[n]["glow"], 3.2))
    baked = [o for n, o in objs.items() if piece_kind(n) == "Main"]
    if baked and A.BAKE:
        A.bake_uv(baked)
        imgs = A.bake_all(baked, f"Qol{key}")
        A.final_material(baked, f"Qol{key}", imgs)
    layout = dict(key=key, name=spec["name"], atlas=A.SIZE, pieces={}, notes=extra.get("notes", spec["notes"]))
    for n, o in objs.items():
        me = o.data
        pts = [o.matrix_world @ v.co for v in me.vertices]
        lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        ent = dict(kind=piece_kind(n), tris=sum(len(f.vertices) - 2 for f in me.polygons),
                   size=[round(hi.x - lo.x, 4), round(hi.z - lo.z, 4), round(hi.y - lo.y, 4)],
                   centre=[round(c, 4) for c in A.to_rbx((lo + hi) / 2)])
        if piece_kind(n) == "Glow":
            ent["glow"] = [round(x, 3) for x in A.PIECES[n]["glow"]]
        if max(ent["size"]) > 20.4:
            print(f"[qol] WARNING {n} over the import cap {ent['size']}")
        layout["pieces"][n] = ent
    layout["tris"] = sum(e["tris"] for e in layout["pieces"].values())
    # export in item space
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs.values():
        o.select_set(True)
    bpy.context.view_layer.objects.active = list(objs.values())[0]
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", f"NHQol_{key}.fbx"), use_selection=True,
                             object_types={"MESH"}, apply_unit_scale=True, global_scale=0.01, axis_forward="-Z",
                             axis_up="Y", mesh_smooth_type="FACE", path_mode="STRIP", embed_textures=False,
                             add_leaf_bones=False, bake_anim=False)
    hold = spec["hold"]
    # place at the hand and check the clearance on the standard body
    stage_cam = A.stage()
    sc.cycles.samples = 24 if FAST else 48
    if "worn" in hold:
        man, parts = posed_mannequin({})
        Pm = Matrix()
        layout["hold"] = dict(worn=hold["worn"])
    else:
        Pm, Mr = place_matrix(hold)
        man, parts = posed_mannequin(hold)
        armM = Mr @ Matrix.Translation((-1.5, 0, 0))
        layout["hold"] = dict(r=hold["r"], l=hold.get("l"), grip_in_arm=to_rbx_cf(armM.inverted() @ Pm),
                              item_in_torso=to_rbx_cf(Pm))
    for o in objs.values():
        o.matrix_world = Pm @ o.matrix_world
    bpy.context.view_layer.update()
    # rest it on the hand (or the worn part): out along the hand's face normal until it touches without clipping
    if "worn" in hold:
        if hold.get("rest"):
            mv = rest_on(objs, parts, [hold["worn"]], hold["rest"])
            Pm = Matrix.Translation(mv) @ Pm
            layout["hold"]["rested"] = [round(x, 4) for x in A.to_rbx(mv)]
    else:
        hands = ["RightArm"] + (["LeftArm"] if hold.get("l") else [])
        nr = Mr.to_3x3() @ V((0, 0, -1))
        if hold.get("l"):
            Ml = arm_matrix("L", *hold["l"])
            nr = (nr + Ml.to_3x3() @ V((0, 0, -1))).normalized()
        mv = rest_on(objs, parts, hands, hold.get("push", nr))
        Pm = Matrix.Translation(mv) @ Pm
        layout["hold"].update(grip_in_arm=to_rbx_cf(armM.inverted() @ Pm), item_in_torso=to_rbx_cf(Pm),
                              rested=[round(x, 4) for x in A.to_rbx(mv)])
    rep, fails = clearance(objs, parts, grip_part=hold.get("grip", "RightArm") if "worn" not in hold else "none",
                           also=hold.get("touch", ()))
    layout["clearance"] = dict(standard=rep, fails=fails)
    print(f"[qol] {key}: {layout['tris']} tris; clearance fails: {fails or 'none'}")
    with open(os.path.join(OUT, "layout", f"{key}.json"), "w") as fh:
        json.dump(layout, fh, indent=1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "blend", f"{key}.blend"))
    if render and A.RENDER:
        shots(key, spec, objs, man, stage_cam, extra)


def look(cam, loc, tgt, lens, path, res=None, aspect=1.15):
    sc = bpy.context.scene
    r = res or (560 if FAST else A.RES)
    sc.render.resolution_x = r; sc.render.resolution_y = int(r * aspect)
    cam.data.lens = lens
    cam.location = V(loc)
    cam.rotation_euler = (V(tgt) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def item_centre(objs):
    pts = []
    for o in objs.values():
        pts += [o.matrix_world @ v.co for v in list(o.data.vertices)[::7]]
    lo = V((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = V((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return (lo + hi) / 2, (hi - lo).length


def shots(key, spec, objs, man, cam, extra):
    R = os.path.join(OUT, "renders")
    c, size = item_centre(objs)
    cams = extra.get("cams", {})
    if "hero" in spec["views"]:
        loc, tgt, lens = cams.get("hero", ((-5.4, -8.8, 1.9), (-0.5, -0.4, -0.35), 50))
        look(cam, loc, tgt, lens, os.path.join(R, f"{key}_hero.png"))
    if "close" in spec["views"]:
        d = max(2.2, size * 1.6)
        out = V((c.x, c.y - 0.6, 0.0)).normalized()
        cd = V(extra["close_dir"]).normalized() if extra.get("close_dir") else (out + V((0, 0, 0.45))).normalized()
        loc, tgt, lens = cams.get("close", (tuple(c + cd * d * 2.2), tuple(c), 70))
        look(cam, loc, tgt, lens, os.path.join(R, f"{key}_close.png"))
    if "pov" in spec["views"]:
        loc, tgt, lens = cams.get("pov", ((-3.3, 1.1, 2.5), tuple(c), 42))
        tgt = tgt or tuple(c)
        look(cam, loc, tgt, lens, os.path.join(R, f"{key}_pov.png"))
    if "solo" in spec["views"]:
        for o in man:
            o.hide_render = True
        for o in bpy.data.objects:
            if o.get("nh_stage"):
                o.hide_render = False
        d = max(1.6, size * 1.25)
        sd = V(extra.get("solo_dir", (-0.6, -1.0, 0.45))).normalized()
        loc, tgt, lens = cams.get("solo", (tuple(c + sd * d * 2.4), tuple(c), 65))
        look(cam, loc, tgt, lens, os.path.join(R, f"{key}_solo.png"), aspect=0.85)
        for o in man:
            o.hide_render = False


# ================================================================== shared bits
def ring_band(name, r, z, h, mat, thick=0.012, seg=40):
    """a raised band round a cylinder: a short lathe ring"""
    return A.lathe(name, [(r - 0.002, z), (r + thick, z + 0.002), (r + thick, z + h - 0.002), (r - 0.002, z + h)], (0, 0, 0), mat, seg=seg)


def bez(p0, p1, p2, p3, n=12):
    out = []
    for i in range(n + 1):
        t = i / n
        a = [(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3]
        out.append(tuple(sum(a[k] * (p0, p1, p2, p3)[k][j] for k in range(4)) for j in range(len(p0))))
    return out


# ================================================================== 1. the hand lantern
@item("Lantern", "Hand lantern", hold=dict(r=(28, 4), at=(0, 0, 0), rot=(0, 0, 0)), views=("hero", "close", "solo"))
def build_lantern(M):
    brass, brassold, iron = M["brassold"], A.mat_metal("BrassDark", (0.50, 0.34, 0.15), rough=0.5, tarnish=(0.10, 0.08, 0.05)), M["iron"]
    crimson = M["crimson_enamel"]
    A.piece("Lantern", "RightArm")
    top = -0.035                       # the grip roll's top touches the hand
    zb = -1.42                         # the foot
    # the oil font: a squat brass drum with a rolled foot and a stepped shoulder
    A.lathe("LanFont", [(0.0, zb), (0.285, zb), (0.305, zb + 0.015), (0.305, zb + 0.04), (0.285, zb + 0.055),
                        (0.29, zb + 0.07), (0.30, zb + 0.15), (0.29, zb + 0.18), (0.255, zb + 0.21), (0.19, zb + 0.235),
                        (0.13, zb + 0.245), (0.0, zb + 0.245)], (0, 0, 0), brass, seg=48)
    ring_band("LanFontBand", 0.30, zb + 0.085, 0.03, crimson, thick=0.008, seg=48)
    # filler cap and the wick-raiser knob (the signature: a fluted knob you turn to light it)
    A.cyl("LanFiller", 0.045, 0.05, (0.16, 0.08, zb + 0.255), brassold, verts=16)
    A.cyl("LanFillerCap", 0.052, 0.022, (0.16, 0.08, zb + 0.288), brass, verts=20)
    A.cyl("LanWickStem", 0.012, 0.16, (-0.205, -0.0, zb + 0.30), brassold, rot=(0, math.radians(90), 0), verts=10)
    for k in range(10):
        a = 2 * math.pi * k / 10
        A.box(f"LanKnobFlute{k}", (0.012, 0.012, 0.075), (-0.30, 0.042 * math.cos(a), zb + 0.30 + 0.042 * math.sin(a)), brass,
              bevel=0.003, rot=(a, 0, 0))
    A.cyl("LanKnob", 0.042, 0.03, (-0.30, 0, zb + 0.30), brass, rot=(0, math.radians(90), 0), verts=20)
    # burner collar and the globe gallery
    A.lathe("LanBurner", [(0.0, zb + 0.24), (0.15, zb + 0.24), (0.165, zb + 0.27), (0.15, zb + 0.30), (0.17, zb + 0.32),
                          (0.17, zb + 0.34), (0.0, zb + 0.34)], (0, 0, 0), brassold, seg=40)
    # the globe (Glass) and the flame (Glow)
    A.piece("Lantern_Glass", "RightArm", kind="Glass")
    gz0 = zb + 0.335
    prof = [(0.150, gz0), (0.19, gz0 + 0.06), (0.228, gz0 + 0.16), (0.236, gz0 + 0.26), (0.22, gz0 + 0.36),
            (0.17, gz0 + 0.45), (0.135, gz0 + 0.50), (0.13, gz0 + 0.54)]
    inner = [(r - 0.012, z) for r, z in reversed(prof)]
    A.lathe("LanGlobe", prof + inner + [prof[0]], (0, 0, 0), mat_glass("LanGlass", (0.95, 0.90, 0.80)), seg=40)
    A.piece("Lantern_Glow", "RightArm", kind="Glow", glow=(1.0, 0.62, 0.26))
    A.lathe("LanFlame", [(0.0, gz0 + 0.04), (0.035, gz0 + 0.07), (0.045, gz0 + 0.11), (0.03, gz0 + 0.16), (0.0, gz0 + 0.21)],
            (0, 0, 0), None, seg=16)
    A.PARTS[-1].data.materials.append(A.mat_glow("LanFlameM", (1.0, 0.62, 0.26)))
    A.piece("Lantern", "RightArm")
    A.cyl("LanWick", 0.02, 0.05, (0, 0, gz0 + 0.02), M["leather_black"], verts=10)
    # the crown: a pierced crimson-enamel chimney with a brass smoke bell
    cz = gz0 + 0.53
    A.lathe("LanCrownRing", [(0.0, cz), (0.165, cz), (0.175, cz + 0.02), (0.165, cz + 0.04), (0.0, cz + 0.04)], (0, 0, 0), brass, seg=40)
    A.lathe("LanChimney", [(0.0, cz + 0.04), (0.135, cz + 0.04), (0.12, cz + 0.17), (0.10, cz + 0.19), (0.0, cz + 0.19)],
            (0, 0, 0), crimson, seg=40)
    for k in range(8):   # brass vent slots round the chimney
        a = 2 * math.pi * k / 8 + 0.2
        A.box(f"LanVent{k}", (0.03, 0.012, 0.075), (0.13 * math.cos(a), 0.13 * math.sin(a), cz + 0.105), M["steel"],
              bevel=0.003, rot=(0, 0, a + math.pi / 2))
    A.lathe("LanBell", [(0.0, cz + 0.19), (0.17, cz + 0.19), (0.185, cz + 0.205), (0.12, cz + 0.24), (0.05, cz + 0.27),
                        (0.035, cz + 0.30), (0.0, cz + 0.30)], (0, 0, 0), brass, seg=40)
    A.sphere("LanFinial", 0.035, (0, 0, cz + 0.32), brassold, seg=14, rings=8)
    # the black iron guard: four bowed wires from the font to the crown ring
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        pts = []
        for i in range(9):
            t = i / 8
            z = lerp(zb + 0.235, cz + 0.02, t)
            r = 0.205 + 0.065 * math.sin(math.pi * t) + 0.02 * (1 - t)
            pts.append((r * math.cos(a), r * math.sin(a), z))
        A.tube(f"LanGuard{k}", pts, 0.0115, iron, res=8)
    for k, z in enumerate((gz0 + 0.17, gz0 + 0.34)):
        rr = 0.205 + 0.065 * math.sin(math.pi * (z - zb - 0.235) / (cz + 0.02 - zb - 0.235)) + 0.008
        A.torus(f"LanHoop{k}", rr, 0.011, (0, 0, z), iron, major=40, minor=8)
    # the bail: an iron hoop from two lugs on the bell up to a bone grip roll
    for s in (-1, 1):
        A.cyl(f"LanLug{s}", 0.03, 0.03, (s * 0.165, 0, cz + 0.205), brassold, rot=(0, math.radians(90), 0), verts=12)
    pts = [(-0.18, 0, cz + 0.205), (-0.20, 0, cz + 0.35), (-0.16, 0, top - 0.09), (-0.1, 0, top - 0.045),
           (0.1, 0, top - 0.045), (0.16, 0, top - 0.09), (0.20, 0, cz + 0.35), (0.18, 0, cz + 0.205)]
    A.tube("LanBail", pts, 0.012, iron, res=10)
    A.cyl("LanGrip", 0.033, 0.19, (0, 0, top - 0.035), M["bone"], rot=(0, math.radians(90), 0), verts=20)
    for s in (-1, 1):
        A.cyl(f"LanGripCap{s}", 0.037, 0.018, (s * 0.1, 0, top - 0.035), brass, rot=(0, math.radians(90), 0), verts=20)
    return dict(scale=1.2, notes="brass oil lantern: fluted wick knob, glass globe (Glass), flame (Glow), pierced crimson chimney, "
                      "iron guard and bail with a bone grip roll; hangs from the hand")


# ================================================================== 2. the folding campus map
MAP_W, MAP_H = 2.7, 1.8


@item("CampusMap", "Folding campus map", hold=dict(r=(62, 8), l=(62, 8), at=(0, -0.03, 0.25), rot=(-28, 0, 0), mid=True), views=("hero", "close", "solo"))
def build_map(M):
    """three panels folded like an accordion (the folds stand a little proud), held open by both hands"""
    A.piece("CampusMap", "RightArm")
    inside = mat_print("MapInside", "map_print.png", rough=0.78)
    outside = mat_print("MapOutside", "map_cover.png", rough=0.8)
    w = MAP_W / 3
    ang = math.radians(9)
    xs = [-MAP_W / 2]
    ys = [0.0]
    for k in range(3):   # zig-zag: panels 0 and 2 tilt toward the reader, 1 lies flat
        a = (ang if k == 0 else -ang if k == 2 else 0.0)
        xs.append(xs[-1] + w * math.cos(a))
        ys.append(ys[-1] + (w * math.sin(ang) if k == 0 else -w * math.sin(ang) if k == 2 else 0.0))
    ys = [y - max(ys) for y in ys]
    xs = [x - (xs[0] + xs[-1]) / 2 for x in xs]
    for k in range(3):
        a0, a1 = V((xs[k], ys[k], -MAP_H / 2)), V((xs[k + 1], ys[k + 1], -MAP_H / 2))
        ux = a1 - a0
        L = ux.length
        def curl(u, v, k=k):
            return 0.012 * math.sin(math.pi * v) + 0.006 * math.sin(math.pi * u)
        p = grid_panel(f"MapPanel{k}", a0, ux, (0, 0, 1), L, MAP_H, 0.008, inside, nu=8, nv=10, bend=curl)
        # the face toward the holder (+Y) shows the plan, the back shows the cover on the right-hand panel
        def uvf(co, n, k=k, a0=a0, ux=ux.normalized(), L=L):
            t = (co - a0).dot(ux) / L
            v = (co.z + MAP_H / 2) / MAP_H
            if n.y < -0.3:     # the outside (away from the reader): the cover on panel 0, plain paper on the others
                return (t if k == 0 else 0.02, v if k == 0 else 0.5)
            return (1 - (k + t) / 3, v)   # the reader looks toward -Y: the sheet's left is +X
        set_print(p, uvf)
        p.data.materials.append(outside)
        for poly in p.data.polygons:
            if (p.matrix_world.to_3x3() @ poly.normal).y < -0.3 and k == 0:
                poly.material_index = 1
    return dict(notes="a three-panel campus map, the inked plan of the grounds on the inside (map_print.png); "
                      "held open in both hands at chest height, tilted to the reader",
                cams=dict(hero=((-5.2, -8.6, 1.9), (0, -0.9, -0.1), 48),
                          pov=((-2.6, 1.9, 3.4), (0, -1.6, 0.1), 38)), solo_dir=(-0.25, 1.0, 0.3))


# ================================================================== 3. the pocket compass
@item("Compass", "Pocket compass", hold=dict(r=(66, 22), at=(0, -0.02, 0.16), rot=(-38, 0, 0)), views=("hero", "close", "pov", "solo"))
def build_compass(M):
    brass, brassold, gold = M["brass"], M["brassold"], M["gold"]
    A.piece("Compass", "RightArm")
    R0, H = 0.27, 0.11
    # the case: its back rim rests against the hand, it lies flat, the lid stands open at the far side
    cy = -R0 - 0.004
    A.lathe("CmpCase", [(0.0, -H / 2), (R0 - 0.03, -H / 2), (R0 - 0.004, -H / 2 + 0.012), (R0, -H / 2 + 0.03), (R0, H / 2 - 0.02),
                        (R0 - 0.012, H / 2), (R0 - 0.035, H / 2), (R0 - 0.035, H / 2 - 0.03), (0.0, H / 2 - 0.03)],
            (0, cy, 0), brass, seg=56)
    A.torus("CmpBezel", R0 - 0.022, 0.014, (0, cy, H / 2 - 0.004), gold, major=56, minor=8)
    # the dial (printed bone) and the needle on its jewel
    dial = A.cyl("CmpDial", R0 - 0.04, 0.006, (0, cy, H / 2 - 0.03), mat_print("CmpDialM", "compass_dial.png", rough=0.5), verts=48)
    set_print(dial, lambda co, n: (0.5 - co.x / (2 * (R0 - 0.04)), 0.5 - (co.y - cy) / (2 * (R0 - 0.04))))
    A.piece("Compass_Needle", "RightArm")
    nz = H / 2 - 0.02
    nfr = Matrix.Translation((0, cy, nz + 0.009)) @ Matrix.Rotation(math.radians(90), 4, "X")   # north tip toward -Y
    A.extrude_poly("CmpNeedleN", [(-0.022, 0.0), (0.0, 0.175), (0.022, 0.0)], 0.006, M["crimson_enamel"], frame=nfr, bevel=0.0)
    A.extrude_poly("CmpNeedleS", [(-0.022, 0.0), (0.022, 0.0), (0.0, -0.175)], 0.006, M["steel"], frame=nfr, bevel=0.0)
    A.cyl("CmpJewel", 0.016, 0.014, (0, cy, nz + 0.006), gold, verts=16)
    A.piece("Compass_Glass", "RightArm", kind="Glass")
    A.cyl("CmpCrystal", R0 - 0.03, 0.006, (0, cy, H / 2 - 0.012), mat_glass("CmpGlassM", (0.96, 0.95, 0.92)), verts=48)
    A.piece("Compass", "RightArm")
    # the hinge at the far side (-Y) and the open lid standing up, its inside engraved with the crest ring
    hy = cy - R0 + 0.01
    A.cyl("CmpHinge", 0.016, 0.12, (0, hy, H / 2 - 0.005), brassold, rot=(0, math.radians(90), 0), verts=14)
    lid_ang = math.radians(100)
    Fl = Matrix.Translation((0, hy, H / 2 - 0.005)) @ Matrix.Rotation(lid_ang, 4, "X") @ Matrix.Translation((0, R0 - 0.01, 0))
    lid = A.lathe("CmpLid", [(0.0, 0.0), (R0 - 0.01, 0.0), (R0, 0.012), (R0 - 0.01, 0.032), (R0 - 0.08, 0.045), (0.0, 0.05)],
                  (0, 0, 0), brass, seg=56)
    lid.matrix_world = Fl; bpy.context.view_layer.update()
    ins = A.cyl("CmpLidInside", R0 - 0.03, 0.004, (0, 0, -0.001), M["gold"], verts=48)
    ins.matrix_world = Fl; bpy.context.view_layer.update()
    for k in range(12):   # the engraved sun-ray guilloche on the lid's outside: raised ribs
        a = 2 * math.pi * k / 12
        rib = A.box(f"CmpRay{k}", (0.012, R0 * 0.62, 0.006), (0.5 * R0 * 0.62 * math.cos(a) * 0 + 0, 0, 0.049), brassold,
                    bevel=0.002)
        rib.matrix_world = Fl @ Matrix.Rotation(a, 4, "Z") @ Matrix.Translation((0, R0 * 0.34, 0.046)); bpy.context.view_layer.update()
    em = A.cyl("CmpLidBoss", 0.06, 0.012, (0, 0, 0.052), M["crimson_enamel"], verts=24)
    em.matrix_world = Fl @ Matrix.Translation((0, 0, 0.052)); bpy.context.view_layer.update()
    # the crown and bow at the near side, and a short fob chain to the hand
    # crown and bow at the outer side (-X, away from the body), clear of the hand
    A.cyl("CmpStem", 0.022, 0.05, (-R0 - 0.02, cy, 0.0), brassold, rot=(0, math.radians(90), 0), verts=14)
    A.cyl("CmpCrown", 0.032, 0.032, (-R0 - 0.055, cy, 0.0), brass, rot=(0, math.radians(90), 0), verts=18)
    A.torus("CmpBow", 0.05, 0.01, (-R0 - 0.035, cy, 0.0), brass, rot=(math.radians(90), 0, 0), major=24, minor=8)
    return dict(scale=1.25, solo_dir=(-0.3, 0.8, 0.9), notes="hunter-case brass compass: printed bone dial, crimson needle (its own piece, turned by the client to "
                      "the target), glass crystal, the lid open with a guilloche sunburst and an enamel boss; lies flat "
                      "on the hand, its crown against the palm",
                cams=dict(pov=((-2.2, 0.4, 2.4), None, 55)))


# ================================================================== 4. the umbrella
UMB_R, UMB_L = 2.25, 3.05


@item("Umbrella", "Umbrella", hold=dict(r=(88, 10), at=(0, 0.0, 0.0), rot=(30, 0, -14)), views=("hero", "close", "solo"))
def build_umbrella(M):
    """eight black waxed-canvas gores with a crimson silk lining, iron ribs, a carved bone crook"""
    canvas = A.mat_cloth("UmbCanvas", (0.012, 0.011, 0.014), weave=520, rough=0.62, sheen=0.08, bump=0.06, twill=False)
    lining = M["crimson_silk"]
    iron, brass = M["iron"], M["brass"]
    A.piece("Umbrella", "RightArm")
    # the shaft runs up (+Z) from the grip point; the hand holds it just above the crook
    top = UMB_L
    A.cyl("UmbShaft", 0.03, top - 0.05, (0, 0, (top - 0.05) / 2 + 0.02), M["steel"], verts=14)
    A.lathe("UmbFerrule", [(0.0, top - 0.02), (0.04, top - 0.02), (0.035, top + 0.05), (0.012, top + 0.22), (0.0, top + 0.24)],
            (0, 0, 0), brass, seg=18)
    # the canopy: 8 gores, sagging between ribs, scalloped at the edge
    N, nr = 8, 10
    zc = top - 0.06
    def canopy_pt(phi, t, off=0.0):
        k = (phi / (2 * math.pi / N)) % 1.0
        sag = math.sin(math.pi * k)
        r = UMB_R * t * (1 - 0.05 * sag * t)
        z = zc - 0.95 * t ** 1.7 - 0.06 * sag * t + off
        return V((r * math.cos(phi), r * math.sin(phi), z))
    for g in range(N):
        a0 = 2 * math.pi * g / N
        G = []
        for i in range(7):
            phi = a0 + (2 * math.pi / N) * i / 6
            G.append([canopy_pt(phi, max(0.045, j / nr)) for j in range(nr + 1)])
        A.surface(f"UmbGore{g}", G, 0.018, canvas)
        Gl = [[p + V((0, 0, -0.016)) for p in col] for col in G]
        A.surface(f"UmbLining{g}", Gl, 0.006, lining)
    # ribs and stretchers (iron) with brass tips
    run_z = top - 1.05
    A.cyl("UmbRunner", 0.05, 0.12, (0, 0, run_z), brass, verts=16)
    A.cyl("UmbNotch", 0.045, 0.08, (0, 0, zc - 0.02), brass, verts=16)
    for g in range(N):
        a = 2 * math.pi * g / N
        pts = [tuple(canopy_pt(a, t, -0.03)) for t in (0.03, 0.2, 0.4, 0.6, 0.8, 1.0)]
        A.tube(f"UmbRib{g}", pts, 0.011, iron, res=8)
        A.lathe(f"UmbTip{g}", [(0.0, 0.0), (0.018, 0.0), (0.014, 0.06), (0.0, 0.08)], (0, 0, 0), brass, seg=10)
        tip = A.PARTS[-1]
        end = canopy_pt(a, 1.0, -0.03)
        dirv = (end - canopy_pt(a, 0.92, -0.03)).normalized()
        tip.matrix_world = Matrix.Translation(end) @ dirv.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bpy.context.view_layer.update()
        mid = canopy_pt(a, 0.5, -0.035)
        A.tube(f"UmbStretch{g}", [(0.05 * math.cos(a), 0.05 * math.sin(a), run_z + 0.04), tuple(mid)], 0.009, iron, res=6)
    # the crook handle below the grip point: carved bone with brass collars
    A.cyl("UmbCollar", 0.042, 0.06, (0, 0, -0.03), brass, verts=18)
    pts = [(0, 0, -0.06), (0, 0, -0.30), (0, -0.02, -0.42), (0, -0.09, -0.50), (0, -0.18, -0.51), (0, -0.25, -0.46),
           (0, -0.27, -0.38), (0, -0.24, -0.32)]
    A.tube("UmbCrook", pts, 0.04, M["bone"], res=12, taper=lambda t: 1.0 - 0.25 * t)
    for k, z in enumerate((-0.12, -0.2)):
        A.torus(f"UmbCarve{k}", 0.041, 0.008, (0, 0, z), M["brassold"], major=20, minor=6)
    A.sphere("UmbCrookEnd", 0.034, (0, -0.24, -0.32), brass, seg=12, rings=8)
    return dict(notes="black waxed-canvas umbrella, 4.5 across: 8 gores with a crimson silk lining, iron ribs and "
                      "stretchers, brass tips and ferrule, a carved bone crook; held up over the head",
                solo_dir=(-0.55, -0.8, 0.12),
                cams=dict(hero=((-7.0, -11.0, 1.2), (-0.6, -0.6, 0.9), 40),
                          close=((-4.6, -3.4, -0.2), (-1.2, -1.6, 0.6), 50)))


# ================================================================== 5. the timetable card
@item("Timetable", "Class timetable card", hold=dict(r=(70, 24), at=(0.36, -0.03, 0.30), rot=(-12, 0, 0), grip="RightArm"), views=("hero", "solo"))
def build_timetable(M):
    A.piece("Timetable", "RightArm")
    W, H = 1.0, 0.643
    face = mat_print("TTFace", "timetable_print.png", rough=0.62, coat=0.15)
    card = grid_panel("TTCard", (-W / 2, 0.0, -H / 2), (1, 0, 0), (0, 0, 1), W, H, 0.012, face, nu=6, nv=4,
                      bend=lambda u, v: 0.008 * math.sin(math.pi * u))
    set_print(card, lambda co, n: ((W / 2 - co.x) / W, (co.z + H / 2) / H) if n.y > -0.5 else (0.015, 0.3))
    # brass corner guards and a crimson ribbon through a brass eyelet
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = [(0, 0), (0.09, 0), (0, 0.09)]
            fr = Matrix.Translation((sx * (W / 2 - 0.005), 0.012, sz * (H / 2 - 0.005))) @ Matrix.Scale(-sx, 4, (1, 0, 0)) @ Matrix.Scale(-sz, 4, (0, 0, 1))
            A.extrude_poly(f"TTCorner{sx}{sz}", p, 0.036, M["brass"], frame=fr, bevel=0.003)
    A.torus("TTEyelet", 0.022, 0.007, (W / 2 - 0.07, 0.0, H / 2 - 0.07), M["brass"], rot=(math.radians(90), 0, 0), major=16, minor=6)
    pts = [(W / 2 - 0.07, 0.0, H / 2 - 0.07), (W / 2 + 0.02, -0.01, H / 2 + 0.02), (W / 2 + 0.08, -0.02, H / 2 - 0.10),
           (W / 2 + 0.09, -0.02, H / 2 - 0.26)]
    A.tube("TTRibbon", pts, 0.012, M["crimson_silk"], res=8, taper=lambda t: 1.0)
    return dict(solo_dir=(-0.3, 1.0, 0.35), close_dir=(-1.0, 0.55, 0.75), notes="the timetable card (the real bell times, timetable_print.png), brass corner guards, a crimson ribbon; "
                      "held up to read",
                cams=dict(pov=((-3.2, 0.9, 2.4), None, 42)))


# ================================================================== 6. the dorm key ring (worn on the hip)
def key_shape(name, length, bow_r, mat, bow_mat, frame, wards=2, quatre=True):
    """a skeleton key along -Z from its bow: a quatrefoil bow, a round shank with collars, a toothed bit"""
    obs = []
    if quatre:
        pts = []
        for i in range(64):
            a = 2 * math.pi * i / 64
            r = bow_r * (0.82 + 0.18 * abs(math.cos(2 * a)))
            pts.append((r * math.cos(a), r * math.sin(a)))
        hole = [(bow_r * 0.45 * math.cos(2 * math.pi * i / 24), bow_r * 0.45 * math.sin(2 * math.pi * i / 24)) for i in range(24)]
        obs.append(A.extrude_poly(name + "Bow", pts, 0.028, bow_mat, frame=frame @ Matrix.Translation((0, 0.014, 0)), bevel=0.004,
                                  holes=[hole[::-1]]))
    else:
        o = A.torus(name + "Bow", bow_r * 0.75, bow_r * 0.22, (0, 0, 0), bow_mat, rot=(math.radians(90), 0, 0), major=24, minor=8)
        o.matrix_world = frame @ o.matrix_world
    sh = A.cyl(name + "Shank", 0.017, length, (0, 0, -bow_r - length / 2), mat, verts=12)
    sh.matrix_world = frame @ sh.matrix_world
    for k, z in enumerate((-bow_r - 0.02, -bow_r - 0.06)):
        c = A.cyl(name + f"Collar{k}", 0.026, 0.016, (0, 0, z), mat, verts=14)
        c.matrix_world = frame @ c.matrix_world
    bit = A.extrude_poly(name + "Bit", [(0.0, 0.0), (0.12, 0.0), (0.12, -0.03), (0.08, -0.03), (0.08, -0.06), (0.12, -0.06),
                                        (0.12, -0.10), (0.0, -0.10)], 0.018,
                         mat, frame=frame @ Matrix.Translation((0.0, 0.009, -bow_r - length + 0.10)), bevel=0.003)
    bpy.context.view_layer.update()


@item("KeyRing", "Dorm key ring", hold=dict(worn="LeftLeg", rest=(0, -1, 0)), views=("hero", "close", "solo"))
def build_keys(M):
    """worn: a leather tab buttoned on the left trouser pocket, the ring and three keys hanging beside the thigh
    (the leg's front-outer corner, clear of the arm's sweep and the torso)"""
    A.piece("KeyRing", "LeftLeg")
    brass, iron = M["brass"], M["iron"]
    leg_front, leg_out = -0.5, 1.0
    # the tab: leather strap over the pocket edge, a brass press-stud
    hx, hz = 0.80, -1.32
    G = [[V((hx + du, leg_front - 0.006 - 0.0 * dv, hz + 0.06 - dv * 0.26)) for dv in (0.0, 0.25, 0.5, 0.75, 1.0)] for du in (-0.055, 0.055)]
    A.surface("KeyTab", G, 0.012, M["leather_brown"])
    A.cyl("KeyStud", 0.026, 0.012, (hx, leg_front - 0.02, hz + 0.02), brass, rot=(math.radians(90), 0, 0), verts=16)
    A.torus("KeyDee", 0.045, 0.009, (hx, leg_front - 0.03, hz - 0.21), brass, rot=(0, math.radians(90), 0), major=18, minor=6)
    # the ring hangs from the D, lying against the leg
    rz = hz - 0.38
    A.torus("KeyRingHoop", 0.13, 0.014, (hx, leg_front - 0.035, rz), iron, rot=(math.radians(90), 0, 0), major=40, minor=8)
    # three keys hanging from the bottom of the ring, fanned, flat to the leg
    for k, (dx, ang, L, br, mat, bm, q) in enumerate((
            (-0.07, 16, 0.30, 0.075, brass, M["crimson_enamel"], True),
            (0.0, 0, 0.38, 0.085, iron, iron, True),
            (0.08, -18, 0.24, 0.06, M["brassold"], M["brassold"], False))):
        a = math.radians(ang)
        hang = V((hx + 0.13 * math.sin(a), leg_front - 0.05 - 0.012 * k, rz - 0.13 * math.cos(a)))
        fr = Matrix.Translation(hang) @ Matrix.Rotation(-a, 4, "Y") @ Matrix.Translation((0, 0, -0.0))
        key_shape(f"Key{k}", L, br, mat, bm, fr @ Matrix.Translation((0, 0, -br)), quatre=q)
    # the bone tag with the room number (printed)
    tz = rz - 0.13 - 0.12
    tag = grid_panel("KeyTag", (hx - 0.22 - 0.07, leg_front - 0.03, tz - 0.27), (1, 0, 0), (0, 0, 1), 0.18, 0.27, 0.014,
                     mat_print("KeyTagM", "key_tag.png", rough=0.55), nu=2, nv=2)
    set_print(tag, lambda co, n: ((co.x - (hx - 0.29)) / 0.18, (co.z - (tz - 0.27)) / 0.27))
    A.torus("KeyTagRing", 0.03, 0.006, (hx - 0.2, leg_front - 0.035, tz + 0.02), brass, rot=(math.radians(90), 0, 0), major=16, minor=6)
    return dict(notes="three keys (a crimson-enamel quatrefoil brass key, the iron room key, a small trunk key) and a printed "
                      "bone tag on an iron ring, buttoned to the left trouser pocket; sways (Pendulum) and jingles",
                cams=dict(close=((2.6, -3.2, -0.9), (0.8, -0.5, -1.75), 55),
                          hero=((6.5, -10.0, 1.6), (0.3, 0, -0.6), 45)))


# ================================================================== 7. the hall pass
@item("HallPass", "Hall pass", hold=dict(r=(84, 20), at=(0.0, -0.0, 0.0), rot=(0, 0, 0)), views=("hero", "close", "solo"))
def build_pass(M):
    """a brass paddle with a pointed gothic arch, crimson enamel field, raised PASS, three punch holes; leather grip"""
    A.piece("HallPass", "RightArm")
    brass, gold = M["brass"], M["gold"]
    Wd, Hh = 0.56, 0.74
    gz = 0.36                     # the plaque's bottom above the grip point
    arch = [(-Wd / 2, 0.0), (Wd / 2, 0.0), (Wd / 2, Hh * 0.62)]
    arch += [(Wd / 2 * math.cos(t) - 0, Hh * 0.62 + (Hh * 0.38) * math.sin(t) ** 0.9) for t in [i / 14 * math.pi / 2 for i in range(1, 14)]]
    arch = arch[:3] + [(Wd / 2 * (1 - i / 14) ** 0.9, Hh * 0.62 + Hh * 0.38 * math.sin(math.pi / 2 * i / 14)) for i in range(1, 15)]
    arch += [(-x, z) for x, z in reversed(arch[3:-1])] + [(-Wd / 2, Hh * 0.62)]
    def sc(p, s, dz=0.0):
        return [(x * s, z * s + dz) for x, z in p]
    fr = Matrix.Translation((0, 0.02, gz))
    A.extrude_poly("PassPlate", arch, 0.04, brass, frame=fr, bevel=0.006, segments=3)
    inner = sc(arch, 0.82, Hh * 0.06)
    A.extrude_poly("PassField", inner, 0.012, M["crimson_enamel"], frame=fr @ Matrix.Translation((0, -0.04, 0)), bevel=0.002)
    A.extrude_poly("PassFillet", sc(arch, 0.86, Hh * 0.045), 0.008, gold, frame=fr @ Matrix.Translation((0, -0.036, 0)), bevel=0.0,
                   holes=[sc(arch, 0.82, Hh * 0.06)[::-1]])
    tf = Matrix.Translation((0, 0.02 - 0.052, gz + Hh * 0.47))
    A.text_mesh("PassWord", "PASS", 0.16, gold, tf, font="timesbd.ttf", depth=0.012, spacing=1.1)
    A.text_mesh("PassHall", "HALL", 0.085, gold, Matrix.Translation((0, 0.02 - 0.052, gz + Hh * 0.66)), font="timesbd.ttf",
                depth=0.01, spacing=1.25)
    A.text_mesh("PassSub", "NIGHTMARE HIGH", 0.042, gold, Matrix.Translation((0, 0.02 - 0.052, gz + Hh * 0.3)), font="georgiab.ttf",
                depth=0.008, spacing=1.1)
    for k in range(3):   # punch tally: three brass-rimmed holes (the game fills them as you use the pass)
        x = (k - 1) * 0.12
        A.torus(f"PassPunch{k}", 0.03, 0.009, (x, 0.02 - 0.046, gz + Hh * 0.17), gold, rot=(math.radians(90), 0, 0), major=16, minor=6)
        A.cyl(f"PassPunchHole{k}", 0.026, 0.006, (x, 0.02 - 0.043, gz + Hh * 0.17), M["steel"], rot=(math.radians(90), 0, 0), verts=16)
    # the neck and a leather-wrapped grip down to the hand
    A.box("PassNeck", (0.12, 0.04, 0.08), (0, 0.0, gz - 0.03), brass, bevel=0.01)
    A.cyl("PassGrip", 0.055, 0.30, (0, 0.0, gz - 0.21), M["leather_oxblood"], verts=20)
    for k, z in enumerate((gz - 0.075, gz - 0.21, gz - 0.345)):
        A.torus(f"PassRing{k}", 0.057, 0.008, (0, 0.0, z), M["brassold"], major=24, minor=6)
    A.cyl("PassPommel", 0.062, 0.03, (0, 0.0, 0.015), brass, verts=20)
    # a crimson tassel on a cord from the pommel
    A.tube("PassCord", [(0, 0.0, 0.0), (0.05, -0.02, -0.05), (0.09, -0.03, -0.12)], 0.008, M["crimson_silk"], res=6)
    A.lathe("PassTassel", [(0.0, -0.12), (0.025, -0.13), (0.045, -0.22), (0.05, -0.27), (0.0, -0.27)], (0.09, -0.03, 0), M["crimson_silk"], seg=14)
    return dict(notes="a brass gothic-arch paddle on a leather-wrapped grip: crimson enamel, raised HALL PASS, three "
                      "punch holes (one per use), a crimson tassel; held up to show a prefect",
                solo_dir=(-0.35, -1.0, 0.2))


# ================================================================== 8. the library book and card
@item("LibraryBook", "Library book and card", hold=dict(r=(14, 6), at=(0, 0, 0), rot=(0, 0, -90)), views=("hero", "close", "solo"))
def build_book(M):
    """an Archive hardback: blue cloth boards, an oxblood leather spine with raised bands, brass corners, the printed
    cover plate, the borrowing card and a crimson ribbon standing out of the top; carried by its top edge"""
    A.piece("LibraryBook", "RightArm")
    Wb, Hb, T = 0.74, 1.0, 0.22     # width (x), height (z), thickness (y)
    top = -0.006
    zc = top - Hb / 2
    cloth = A.mat_cloth("BookCloth", (0.03, 0.045, 0.085), weave=380, rough=0.8, sheen=0.3, bump=0.07, twill=False)
    pages = A.mat_set("BookPages", "NH_Paper", tint=(0.86, 0.80, 0.66), scale=6.0, wear=0.2, dirt=0.8)
    spine_l = A.mat_leather("BookSpine", (0.26, 0.05, 0.05), scale=3.0)
    bt = 0.022
    for s in (-1, 1):
        A.box(f"BookBoard{s}", (Wb, bt, Hb), (0.0, s * (T / 2 - bt / 2), zc), cloth, bevel=0.006)
    A.box("BookBlock", (Wb - 0.04, T - 2 * bt, Hb - 0.04), (0.02, 0, zc), pages, bevel=0.004)
    # the spine at -X: a rounded leather back with four raised bands
    sp = A.cyl("BookSpineRound", T / 2 + 0.006, Hb, (-Wb / 2, 0, zc), spine_l, verts=28)
    for k in range(4):
        A.cyl(f"BookBand{k}", T / 2 + 0.016, 0.03, (-Wb / 2, 0, zc - Hb / 2 + 0.2 + k * 0.2), spine_l, verts=28)
    # leather wraps a little onto each board (quarter binding)
    for s in (-1, 1):
        A.box(f"BookQuarter{s}", (0.13, 0.006, Hb), (-Wb / 2 + 0.06, s * (T / 2 + 0.002), zc), spine_l, bevel=0.002)
    # brass corners on the fore-edge
    for s in (-1, 1):
        for sz in (-1, 1):
            p = [(0, 0), (0.11, 0), (0, 0.11)]
            fr = Matrix.Translation((Wb / 2 + 0.003, s * (T / 2 + 0.004) + (0.0 if s > 0 else 0.0), zc + sz * (Hb / 2 + 0.003))) @ \
                Matrix.Scale(-1, 4, (1, 0, 0)) @ Matrix.Scale(-sz, 4, (0, 0, 1)) @ Matrix.Translation((0, 0.004 if s < 0 else 0.0, 0))
            A.extrude_poly(f"BookCorner{s}{sz}", p, 0.008, M["brassold"], frame=fr @ Matrix.Translation((0, (0.0 if s < 0 else 0.008), 0)), bevel=0.002)
    # the printed cover plate on the outward board (-Y) and the spine label
    cov = grid_panel("BookCover", (-Wb / 2 + 0.135, -T / 2 - 0.0035, zc - Hb / 2 + 0.03), (1, 0, 0), (0, 0, 1), Wb - 0.165, Hb - 0.06,
                     0.002, mat_print("BookCoverM", "book_cover.png", rough=0.7), nu=1, nv=1)
    set_print(cov, planar((-Wb / 2 + 0.135, 0, zc - Hb / 2 + 0.03), (1, 0, 0), (0, 0, 1), Wb - 0.165, Hb - 0.06))
    # the card in its pocket, standing out of the top, and the ribbon marker
    card = grid_panel("BookCard", (-0.05, 0.03, zc + Hb / 2 - 0.25), (1, 0, 0), (0, 0, 1), 0.30, 0.45, 0.006,
                      mat_print("BookCardM", "library_card.png", rough=0.65), nu=1, nv=2)
    set_print(card, planar((-0.05, 0, zc + Hb / 2 - 0.25), (1, 0, 0), (0, 0, 1), 0.30, 0.45))
    A.tube("BookRibbon", [(0.22, -0.02, zc + Hb / 2 - 0.1), (0.24, -0.03, zc + Hb / 2 + 0.06), (0.30, -0.06, zc + Hb / 2 + 0.03),
                          (0.33, -0.08, zc + Hb / 2 - 0.12)], 0.016, M["crimson_silk"], res=6, square=True)
    return dict(notes="a quarter-bound Archive hardback (cloth boards, oxblood leather spine with raised bands, brass corners), "
                      "the printed cover plate, the borrowing card and a ribbon standing out of the top; carried by the top edge",
                solo_dir=(-1.0, -0.5, 0.3))


# ================================================================== 9. the thermos
@item("Thermos", "Thermos flask", hold=dict(r=(32, 6), at=(0.0, 0.0, 0.0), rot=(0, 0, 0)), views=("hero", "close", "solo"))
def build_thermos(M):
    A.piece("Thermos", "RightArm")
    R0, Hf = 0.21, 0.92
    zt = -0.17                  # the flask's shoulder sits just under the hand
    zb = zt - Hf
    black = M["black_enamel"]
    A.lathe("FlaskBody", [(0.0, zb), (R0 - 0.02, zb), (R0, zb + 0.02), (R0, zt - 0.06), (R0 - 0.03, zt - 0.01), (0.12, zt + 0.02),
                          (0.0, zt + 0.02)], (0, 0, 0), black, seg=48)
    lab = A.lathe("FlaskLabel", [(R0 + 0.003, zb + 0.22), (R0 + 0.003, zb + 0.62)], (0, 0, 0), mat_print("FlaskLabelM", "thermos_label.png", rough=0.4, coat=0.3), seg=64)
    def uvl(co, n):
        a = math.atan2(co.y, co.x)
        u = ((a + math.pi / 2) / (2 * math.pi) + 0.25) % 1.0   # u = 0.25 faces -Y; u grows to the viewer's right
        return (u, (co.z - zb - 0.22) / 0.40)
    set_print(lab, uvl)
    for k, z in enumerate((zb + 0.03, zb + 0.2, zb + 0.64, zt - 0.08)):
        ring_band(f"FlaskBand{k}", R0, z, 0.035, M["brass"], thick=0.01, seg=48)
    # the neck, the screw stopper and the cup-lid (brass, knurled)
    A.lathe("FlaskNeck", [(0.0, zt + 0.0), (0.11, zt + 0.0), (0.11, zt + 0.06), (0.0, zt + 0.06)], (0, 0, 0), M["steel"], seg=32)
    A.lathe("FlaskCup", [(0.0, zt + 0.05), (0.165, zt + 0.05), (0.175, zt + 0.07), (0.168, zt + 0.20), (0.155, zt + 0.22),
                         (0.0, zt + 0.22)], (0, 0, 0), M["brass"], seg=48)
    for k in range(24):
        a = 2 * math.pi * k / 24
        A.box(f"FlaskKnurl{k}", (0.012, 0.01, 0.1), (0.172 * math.cos(a), 0.172 * math.sin(a), zt + 0.135), M["brassold"], bevel=0.002,
              rot=(0, 0, a))
    # the carry strap: leather from the bottom band up the back to the shoulder band, a brass buckle
    G = []
    for du in (-0.04, 0.04):
        col = []
        for t in [i / 10 for i in range(11)]:
            z = lerp(zb + 0.05, zt - 0.06, t)
            off = 0.045 * math.sin(math.pi * t)
            col.append(V((du, R0 + 0.012 + off, z)))
        G.append(col)
    A.surface("FlaskStrap", G, 0.014, M["leather_oxblood"])
    A.box("FlaskBuckle", (0.1, 0.02, 0.07), (0, R0 + 0.06, zb + 0.46), M["brass"], bevel=0.008)
    # the hand holds the flask by the cup (its top touches the hand)
    return dict(notes="black-enamel vacuum flask with brass bands, the printed WICK & KETTLE label, a knurled brass cup-lid "
                      "and an oxblood carry strap; held by the cup, upright",
                )


# ================================================================== 10. the snack tin
@item("SnackTin", "Snack tin", hold=dict(r=(56, 26), at=(0.0, 0.0, 0.0), rot=(10, 0, 0)), views=("hero", "close", "solo"))
def build_tin(M):
    """a round crimson biscuit tin with a gilt-printed band, held flat, lid hinged open at the back, biscuits inside"""
    A.piece("SnackTin", "RightArm")
    R0, Ht = 0.36, 0.24
    cy = -R0 - 0.01             # the tin's near rim touches the hand
    zb = -Ht - 0.02
    zt = zb + Ht
    band = mat_print("TinBandM", "tin_band.png", rough=0.25, metal=0.6, coat=0.4)
    tin = A.lathe("TinBody", [(0.0, zb), (R0 - 0.015, zb), (R0, zb + 0.015), (R0, zt - 0.02), (R0 + 0.008, zt - 0.01), (R0 + 0.008, zt),
                              (R0 - 0.012, zt), (R0 - 0.012, zb + 0.02), (0.0, zb + 0.02)], (0, cy, 0), band, seg=64)
    def uvb(co, n):
        a = math.atan2(co.y - cy, co.x)
        return ((a / (2 * math.pi)) % 1.0 * 4 % 1.0, (co.z - zb) / Ht)
    set_print(tin, uvb)
    for k, z in enumerate((zb + 0.004, zt - 0.03)):
        A.torus(f"TinBead{k}", R0 + 0.004, 0.008, (0, cy, z), M["gold"], major=64, minor=6)
    # biscuits: round, docked, stacked on their edges and a few flat on top
    bisc = A.mat_flat("Biscuit", (0.62, 0.40, 0.17), rough=0.75, noise=120, bump=0.25, vary=0.18, wear=0.0, dirt=0.3)
    for k in range(9):
        a = 2 * math.pi * k / 9
        x, y = 0.2 * math.cos(a), cy + 0.2 * math.sin(a)
        b = A.cyl(f"TinBisc{k}", 0.105, 0.03, (0, 0, 0), bisc, verts=24, bevel=0.008)
        b.matrix_world = Matrix.Translation((x, y, zb + 0.13)) @ Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(78), 4, "Y")
        bpy.context.view_layer.update()
    for k in range(3):
        b = A.cyl(f"TinBiscTop{k}", 0.105, 0.03, (0.07 * (k - 1), cy + 0.04 * (k % 2), zb + 0.14 + k * 0.032), bisc, verts=24, bevel=0.008)
    # the lid, hinged at the far side (-Y), open past upright
    A.piece("SnackTin_Lid", "RightArm")
    hy = cy - R0
    lid_print = mat_print("TinLidM", "tin_lid.png", rough=0.22, metal=0.5, coat=0.5)
    Fl = Matrix.Translation((0, hy, zt)) @ Matrix.Rotation(math.radians(105), 4, "X") @ Matrix.Translation((0, R0, 0))
    lid = A.lathe("TinLid", [(0.0, 0.03), (R0 - 0.04, 0.03), (R0 + 0.01, 0.022), (R0 + 0.018, 0.008), (R0 + 0.018, -0.04),
                             (R0 + 0.006, -0.04), (R0 + 0.006, 0.0), (0.0, 0.0)], (0, 0, 0), lid_print, seg=64)
    lid.matrix_world = Fl; bpy.context.view_layer.update()
    set_print(lid, lambda co, n: (0.04, 0.5))
    top = A.cyl("TinLidTop", R0 - 0.04, 0.004, (0, 0, 0.032), lid_print, verts=64)
    top.matrix_world = Fl @ Matrix.Translation((0, 0, 0.032)); bpy.context.view_layer.update()
    Fi = Fl.inverted()
    def uvt(co, n):
        q = Fi @ co
        return (0.5 + q.x / (2 * (R0 - 0.04)), 0.5 + q.y / (2 * (R0 - 0.04)))
    set_print(top, uvt)
    A.piece("SnackTin", "RightArm")
    A.cyl("TinHinge", 0.012, 0.16, (0, hy - 0.005, zt), M["brassold"], rot=(0, math.radians(90), 0), verts=12)
    return dict(notes="a round crimson-and-gilt MORROW & VANE biscuit tin (printed band and lid), its lid (own piece) hinged "
                      "open; biscuits stand on edge round the inside; held flat on the hand",
                )


# ================================================================== 11. the first-aid pouch
@item("FirstAid", "First-aid pouch", hold=dict(r=(12, 4), at=(-0.14, 0.0, 0.0), rot=(0, 0, 0)), views=("hero", "close", "solo"))
def build_firstaid(M):
    """a black leather field pouch: a flap with a stitched bone cross and a brass turn-lock, a linen bandage roll in a
    side loop, a small amber bottle, carried by its top handle"""
    A.piece("FirstAid", "RightArm")
    lb = A.mat_leather("AidLeather", (0.035, 0.03, 0.034), scale=2.4)
    Wp, Hp, Dp = 0.66, 0.5, 0.26
    zt = -0.24
    zc = zt - Hp / 2
    A.box("AidBody", (Wp, Dp, Hp), (0, 0, zc), lb, bevel=0.04, segments=4)
    # the flap over the front (-Y), slightly domed, its edge stitched
    G = []
    for i in range(9):
        u = i / 8
        col = []
        for j in range(7):
            v = j / 6
            x = lerp(-Wp / 2 - 0.01, Wp / 2 + 0.01, u)
            # over the top then down the front
            if v < 0.35:
                t = v / 0.35
                p = V((x, lerp(Dp / 2 - 0.02, -Dp / 2, t), zt + 0.012 + 0.01 * math.sin(math.pi * t)))
            else:
                t = (v - 0.35) / 0.65
                p = V((x, -Dp / 2 - 0.014 - 0.012 * math.sin(math.pi * u), zt - t * Hp * 0.62))
            col.append(p)
        G.append(col)
    A.surface("AidFlap", G, 0.016, A.mat_leather("AidFlapL", (0.05, 0.042, 0.046), scale=2.6))
    # the stitched cross: bone-coloured linen tape (not the red cross: bone on black, with a stitched outline)
    cf = Matrix.Translation((0, -Dp / 2 - 0.03, zt - Hp * 0.28))
    arm = 0.055
    cross = [(-arm, 0.15), (arm, 0.15), (arm, arm), (0.15, arm), (0.15, -arm), (arm, -arm), (arm, -0.15), (-arm, -0.15),
             (-arm, -arm), (-0.15, -arm), (-0.15, arm), (-arm, arm)]
    A.extrude_poly("AidCross", [(x * 0.8, z * 0.8) for x, z in cross], 0.006, M["bone"], frame=cf, bevel=0.0015)
    # the turn-lock clasp below it
    A.box("AidLockPlate", (0.12, 0.012, 0.07), (0, -Dp / 2 - 0.028, zt - Hp * 0.6), M["brass"], bevel=0.006)
    A.cyl("AidLockTurn", 0.022, 0.03, (0, -Dp / 2 - 0.04, zt - Hp * 0.6), M["brassold"], rot=(math.radians(90), 0, 0), verts=14)
    # the side loop with the bandage roll (+X) and a small amber bottle (-X)
    A.box("AidLoop", (0.03, Dp * 0.8, 0.07), (Wp / 2 + 0.012, 0, zc), A.mat_leather("AidLoopL", (0.12, 0.08, 0.06)), bevel=0.01)
    roll = A.cyl("AidRoll", 0.085, 0.2, (Wp / 2 + 0.095, 0, zc), M["white_linen"], verts=28, bevel=0.01)
    A.lathe("AidRollEnd", [(0.0, 0.0), (0.06, 0.0), (0.07, 0.01), (0.0, 0.012)], (Wp / 2 + 0.095, 0, zc + 0.1), M["white_linen"], seg=20)
    A.tube("AidRollTail", [(Wp / 2 + 0.17, -0.03, zc + 0.05), (Wp / 2 + 0.185, -0.04, zc - 0.05), (Wp / 2 + 0.17, -0.06, zc - 0.17)],
           0.008, M["white_linen"], res=6, square=True)
    A.box("AidLoopL2", (0.03, Dp * 0.8, 0.07), (-Wp / 2 - 0.012, 0, zc - 0.04), A.mat_leather("AidLoopL3", (0.12, 0.08, 0.06)), bevel=0.01)
    amber = A.mat_flat("Amber", (0.24, 0.10, 0.02), rough=0.08, coat=0.8, noise=20, bump=0.0, vary=0.02, wear=0.0)
    A.lathe("AidBottle", [(0.0, -0.13), (0.055, -0.13), (0.06, -0.12), (0.06, 0.03), (0.03, 0.07), (0.022, 0.09), (0.0, 0.09)],
            (-Wp / 2 - 0.085, 0, zc - 0.02), amber, seg=24)
    A.cyl("AidBottleCap", 0.028, 0.05, (-Wp / 2 - 0.085, 0, zc + 0.095), M["black_enamel"], verts=16)
    # the top handle (the hand holds it)
    pts = [(-0.14, 0, zt + 0.0), (-0.13, 0, zt + 0.12), (-0.07, 0, zt + 0.2), (0.07, 0, zt + 0.2), (0.13, 0, zt + 0.12), (0.14, 0, zt + 0.0)]
    A.tube("AidHandle", pts, 0.026, A.mat_leather("AidHandleL", (0.22, 0.12, 0.06)), res=10)
    for s in (-1, 1):
        A.box(f"AidHandleTab{s}", (0.07, 0.07, 0.05), (s * 0.14, 0, zt + 0.0), M["leather_brown"], bevel=0.01)
        A.cyl(f"AidRivet{s}", 0.014, 0.08, (s * 0.14, 0, zt + 0.0), M["brass"], rot=(math.radians(90), 0, 0), verts=10)
    return dict(notes="black leather pouch with a stitched bone cross (not the Red Cross emblem), brass turn-lock, a linen "
                      "bandage roll and an amber bottle in side loops; carried by its top handle",
                )


# ================================================================== 12. the hand warmer
@item("HandWarmer", "Hand warmer", hold=dict(r=(60, 24), at=(0.0, 0.0, 0.0), rot=(-30, 0, 0)), views=("hero", "close", "solo"))
def build_warmer(M):
    """a pierced brass ember case (crescent moon and star vents glowing from the coals inside) on a fob chain"""
    A.piece("HandWarmer", "RightArm")
    a_, b_, Hc = 0.25, 0.17, 0.12        # oval half-axes, height
    cy = -b_ - 0.005
    # the case: two shells and a rolled seam
    A.lathe("WarmBase", [(0.0, -Hc / 2), (0.92, -Hc / 2), (1.0, -Hc / 2 + 0.25 * Hc), (1.0, 0.0), (0.0, 0.0)], (0, cy, 0), M["brassold"],
            seg=48, scale=(a_, b_, 1.0))
    A.torus("WarmSeam", 1.0, 0.04, (0, cy, 0.0), M["brass"], major=48, minor=8, scale=(a_ + 0.003, b_ + 0.003, 0.25))
    # the lid: an oval dome plate with the vents cut through
    pts = [(a_ * 0.96 * math.cos(2 * math.pi * i / 64), b_ * 0.96 * math.sin(2 * math.pi * i / 64)) for i in range(64)]
    moon = [(0.05 + 0.06 * math.cos(t), 0.06 * math.sin(t)) for t in [math.pi * 0.25 + i / 20 * math.pi * 1.5 for i in range(21)]]
    moon += [(0.075 + 0.045 * math.cos(t), 0.045 * math.sin(t)) for t in [math.pi * 1.75 - i / 20 * math.pi * 1.5 for i in range(1, 20)]]
    moon = [(x - 0.12, y) for x, y in moon]
    def star(cx, cz, r):
        return [(cx + (r if i % 2 == 0 else r * 0.42) * math.cos(math.pi / 2 + i * math.pi / 5),
                 cz + (r if i % 2 == 0 else r * 0.42) * math.sin(math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    holes = [moon[::-1], star(0.07, 0.04, 0.035)[::-1], star(0.13, -0.05, 0.022)[::-1], star(0.02, -0.075, 0.02)[::-1]]
    lf = Matrix.Translation((0, cy, Hc / 2 - 0.005)) @ Matrix.Rotation(math.radians(90), 4, "X")
    A.extrude_poly("WarmLid", pts, 0.025, M["brass"], frame=lf, bevel=0.004, holes=holes)
    A.lathe("WarmLidSkirt", [(0.97, 0.0), (1.0, 0.004), (1.0, Hc / 2 - 0.01), (0.96, Hc / 2 - 0.005)], (0, cy, 0), M["brass"], seg=48,
            scale=(a_, b_, 1.0))
    # engraved scroll border on the lid: a raised fine ring
    A.torus("WarmScroll", 1.0, 0.03, (0, cy, Hc / 2 + 0.018), M["gold"], major=64, minor=6, scale=(a_ * 0.88, b_ * 0.86, 0.2))
    # the coals under the vents (Glow)
    A.piece("HandWarmer_Glow", "RightArm", kind="Glow", glow=(1.0, 0.36, 0.10))
    A.cyl("WarmEmbers", 1.0, 0.01, (0, cy, Hc / 2 - 0.045), None, verts=40)
    A.PARTS[-1].scale = (a_ * 0.9, b_ * 0.9, 1.0)
    A.PARTS[-1].data.materials.append(A.mat_glow("WarmEmberM", (1.0, 0.36, 0.10)))
    A.piece("HandWarmer", "RightArm")
    A.lathe("WarmFloor", [(0.0, Hc / 2 - 0.052), (0.9, Hc / 2 - 0.052), (0.9, Hc / 2 - 0.058), (0.0, Hc / 2 - 0.058)], (0, cy, 0),
            M["steel"], seg=40, scale=(a_, b_, 1.0))
    # the hinge at the far side and the fob ring and chain at the near side (toward the hand)
    A.cyl("WarmHinge", 0.014, 0.12, (0, cy - b_ - 0.008, Hc / 2 - 0.01), M["brassold"], rot=(0, math.radians(90), 0), verts=12)
    A.torus("WarmBow", 0.04, 0.009, (0, cy + b_ + 0.03, 0.0), M["brass"], rot=(math.radians(0), math.radians(90), 0), major=18, minor=6)
    return dict(scale=1.45, solo_dir=(-0.3, -0.5, 1.0), close_dir=(-0.7, -0.5, 1.0), notes="an oval pierced-brass ember case: crescent and star vents with glowing coals (Glow) under them, a gilt "
                      "scroll border, a hinge and a fob bow; held flat on the hand",
                )


# ================================================================== main
if __name__ == "__main__":
    targets = [a for a in argv if not a.startswith("--") and (argv.index(a) == 0 or not argv[argv.index(a) - 1].startswith("--"))]
    want = targets[0].split(",") if targets else ["all"]
    keys = list(ITEMS) if want == ["all"] else want
    for k in keys:
        run(k)
