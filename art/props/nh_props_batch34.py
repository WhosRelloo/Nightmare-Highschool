"""Props batch 34 (2026-11-05): the beasts kit's models for nh_props.py (design: docs/superpowers/specs/2026-11-05-beasts-design.md).
Each beast is a creature skeleton skinned into one muscular mesh (the dead oak's method, batch 33), baked like every prop,
rigged with named bones for the published clips, glowing parts as Glow pieces skinned to the same rig.

  Hellhound   a hound bigger than the wolves (about 5.5 wide, 6.5 tall, 13 long): a deep keel of a chest, a narrow waist,
              heavy haunches, a long skull with brow ridges and swept-back horns, a hinged jaw full of fangs, bony spikes
              down its back, black claws; charred black hide split by ember-orange cracks; glowing eyes and throat (Glow)

Front faces -Y, Z is up, the origin is at the bottom centre (the paws on the ground). Registered into nh_props.BUILD on import.
"""
import math
import random

import bpy
from mathutils import Vector

import nh_props as P
from nh_props import set_group, _finish, material
from nh_props_batch3 import sphere, cone
from nh_props_batch4 import _dims, flat
from nh_props_batch33 import Skel, _perp


# ------------------------------------------------------------------ materials

def charred_hide():
    """Charred black hide: a fine leathery grain, a network of cracks that burn ember orange (they read as glowing in the
    baked colour), the plates between them dull and rough, the cracks smoother; relief through a bump."""
    m = bpy.data.materials.get("CharredHide")
    if m:
        return m
    m = bpy.data.materials.new("CharredHide")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links.new
    bs = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    L(tc.outputs["Object"], mp.inputs["Vector"])
    warp = N.new("ShaderNodeTexNoise")
    warp.inputs["Scale"].default_value = 1.2
    warp.inputs["Detail"].default_value = 2.0
    L(mp.outputs["Vector"], warp.inputs["Vector"])
    wmix = N.new("ShaderNodeMix")
    wmix.data_type = "VECTOR"
    wmix.inputs[0].default_value = 0.25
    L(mp.outputs["Vector"], wmix.inputs[4])
    L(warp.outputs["Color"], wmix.inputs[5])
    vor = N.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 6.0
    L(wmix.outputs[1], vor.inputs["Vector"])
    crack = N.new("ShaderNodeMapRange")            # 1 in a crack, 0 on the plates
    crack.inputs["From Min"].default_value = 0.022
    crack.inputs["From Max"].default_value = 0.0
    L(vor.outputs["Distance"], crack.inputs["Value"])
    heat = N.new("ShaderNodeTexNoise")              # some cracks burn hotter than others
    heat.inputs["Scale"].default_value = 0.8
    L(tc.outputs["Object"], heat.inputs["Vector"])
    hm = N.new("ShaderNodeMapRange")
    hm.inputs["From Min"].default_value = 0.5
    hm.inputs["From Max"].default_value = 0.68
    hm.inputs["To Min"].default_value = 0.0
    L(heat.outputs["Fac"], hm.inputs["Value"])
    glow = N.new("ShaderNodeMath")
    glow.operation = "MULTIPLY"
    L(crack.outputs["Result"], glow.inputs[0])
    L(hm.outputs["Result"], glow.inputs[1])
    grain = N.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 22.0
    grain.inputs["Detail"].default_value = 6.0
    L(tc.outputs["Object"], grain.inputs["Vector"])
    hide = N.new("ShaderNodeMix")
    hide.data_type = "RGBA"
    hide.inputs[6].default_value = (0.01, 0.008, 0.007, 1)
    hide.inputs[7].default_value = (0.05, 0.043, 0.04, 1)            # ash on the raised grain
    L(grain.outputs["Fac"], hide.inputs[0])
    col = N.new("ShaderNodeMix")
    col.data_type = "RGBA"
    L(glow.outputs[0], col.inputs[0])
    L(hide.outputs[2], col.inputs[6])
    col.inputs[7].default_value = (1.0, 0.32, 0.04, 1)
    L(col.outputs[2], bs.inputs["Base Color"])
    rough = N.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.72
    rough.inputs["To Max"].default_value = 0.35
    L(crack.outputs["Result"], rough.inputs["Value"])
    L(rough.outputs["Result"], bs.inputs["Roughness"])
    bs.inputs["Metallic"].default_value = 0.0
    h = N.new("ShaderNodeMath")
    h.operation = "MULTIPLY_ADD"
    L(grain.outputs["Fac"], h.inputs[0])
    h.inputs[1].default_value = 0.3
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    L(crack.outputs["Result"], inv.inputs[1])
    L(inv.outputs[0], h.inputs[2])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.04
    L(h.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], bs.inputs["Normal"])
    return m


def bone_white():
    return flat("FangBone", (0.55, 0.5, 0.42), 0.45, dirt=0.6)


def claw_black():
    return flat("ClawBlack", (0.01, 0.009, 0.009), 0.3, dirt=0.3)


# ------------------------------------------------------------------ the hound

JOINTS = {}   # bone name -> (head, tail, parent): filled by the builder, read by the rig


def chain(S, pts, radii, parent):
    ids = [parent]
    for p, r in zip(pts, radii):
        ids.append(S.add(p, r, ids[-1]))
    return ids[1:]


def hellhound(M):
    rnd = random.Random(3401)
    JOINTS.clear()
    hide = charred_hide()
    S = Skel()
    set_group("Main")
    K = 1.18                                                   # the whole hound, bigger than a wolf
    V = lambda x, y, z: Vector((x * K, y * K, z * K))
    # the spine from the pelvis forward to the nose: a deep chest, a narrow waist, a heavy arched neck, a long skull
    pelvis = V(0, 3.5, 4.2)
    spine_pts = [V(0, 2.35, 4.4), V(0, 1.0, 4.35), V(0, -0.5, 4.55), V(0, -1.85, 4.85), V(0, -2.85, 5.3)]
    spine_r = [0.92 * K, 0.78 * K, 1.08 * K, 1.3 * K, 1.18 * K]
    neck_pts = [V(0, -3.6, 5.95), V(0, -4.2, 6.45)]
    neck_r = [1.02 * K, 0.88 * K]
    head_pts = [V(0, -4.8, 6.6), V(0, -5.55, 6.42), V(0, -6.3, 6.18), V(0, -6.9, 5.98)]
    head_r = [0.82 * K, 0.6 * K, 0.46 * K, 0.33 * K]
    root = S.add(pelvis, 1.0 * K)
    sp = chain(S, spine_pts, spine_r, root)
    nk = chain(S, neck_pts, neck_r, sp[-1])
    hd = chain(S, head_pts, head_r, nk[-1])
    # the keel of the chest, hanging low between the forelegs; the belly tucked up behind it
    chain(S, [V(0, -1.25, 3.45), V(0, -0.85, 2.95)], [1.12 * K, 0.8 * K], sp[2])
    chain(S, [V(0, 1.05, 3.7)], [0.6 * K], sp[1])
    # the crest of the neck, the skull's back and jaw muscles, brow ridges, cheekbones, shoulder blades, haunches
    chain(S, [V(0, -3.3, 6.45)], [0.72 * K], nk[0])
    for sx in (-1, 1):
        chain(S, [V(sx * 0.42, -5.05, 6.92)], [0.3 * K], hd[0])                 # brow
        chain(S, [V(sx * 0.55, -5.0, 6.3)], [0.42 * K], hd[0])                  # jaw muscle
        chain(S, [V(sx * 0.38, -5.85, 6.05)], [0.3 * K], hd[1])                 # cheekbone
        chain(S, [V(sx * 0.62, -1.75, 5.25), V(sx * 0.82, -1.5, 4.55)], [0.78 * K, 0.7 * K], sp[3])   # shoulder blade and its muscle
        chain(S, [V(sx * 0.7, 3.15, 4.35), V(sx * 0.95, 2.9, 3.55)], [0.85 * K, 0.8 * K], root)      # the haunch
    # the legs, properly angled: L = +X (the hound faces -Y)
    legs = {}
    for side, sx in (("L", 1), ("R", -1)):
        # forelegs: the elbow tucked back, a straight forearm, the pastern angled forward, a broad paw
        f = [V(sx * 1.02, -1.7, 4.05), V(sx * 1.1, -1.25, 2.55), V(sx * 1.02, -1.55, 1.05), V(sx * 1.02, -1.95, 0.36), V(sx * 1.02, -2.5, 0.22)]
        fr = [0.74 * K, 0.5 * K, 0.3 * K, 0.4 * K, 0.36 * K]
        legs[f"F{side}"] = (f, chain(S, f, fr, sp[3]))
        chain(S, [V(sx * 1.12, -1.45, 2.05)], [0.42 * K], legs[f"F{side}"][1][1])      # the forearm's muscle
        # hind legs: a heavy thigh, the stifle forward, the hock high behind, the cannon near vertical
        h = [V(sx * 1.05, 3.3, 3.75), V(sx * 1.15, 2.35, 2.45), V(sx * 1.05, 3.5, 1.3), V(sx * 1.05, 3.2, 0.36), V(sx * 1.05, 2.7, 0.22)]
        hr = [1.0 * K, 0.62 * K, 0.32 * K, 0.4 * K, 0.36 * K]
        legs[f"H{side}"] = (h, chain(S, h, hr, root))
        chain(S, [V(sx * 1.12, 3.05, 2.1)], [0.46 * K], legs[f"H{side}"][1][1])        # the gaskin
    # the tail: up from the pelvis, then sweeping down and back
    tail = [V(0, 4.45, 4.45), V(0, 5.5, 4.3), V(0, 6.5, 3.8), V(0, 7.35, 3.15), V(0, 8.0, 2.65)]
    chain(S, tail, [0.42 * K, 0.34 * K, 0.26 * K, 0.18 * K, 0.1 * K], root)
    S.build("Body", hide, subdiv=2, knobs=0.06)
    # the jaw, its own piece (it opens on its bone)
    set_group("Jaw")
    J = Skel()
    j0 = J.add(V(0, -4.75, 6.05), 0.52 * K)
    chain(J, [V(0, -5.6, 5.82), V(0, -6.35, 5.62), V(0, -6.85, 5.52)], [0.4 * K, 0.3 * K, 0.2 * K], j0)
    J.build("Jaw", hide, subdiv=2, knobs=0.02)
    # fangs and teeth along both jaws
    bw = bone_white()
    for k in range(6):
        t = k / 5
        y = (-5.3 - 1.55 * t) * K
        for sx in (-1, 1):
            x = sx * (0.36 - 0.15 * t) * K
            L_ = (0.24 if k != 4 else 0.46) * K
            set_group("Main")
            cone(f"ToothU{k}{sx}", 0.065 * K, 0.0, L_, (x, y, (6.05 - 0.2 * t) * K - L_ / 2), bw, verts=6, rot=(math.pi, 0, 0))
            set_group("Jaw")
            cone(f"ToothL{k}{sx}", 0.06 * K, 0.0, L_ * 0.8, (x * 0.9, y + 0.05, (5.9 - 0.25 * t) * K + L_ * 0.4), bw, verts=6)
    set_group("Main")
    # horns swept back off the brow
    for sx in (-1, 1):
        base = V(sx * 0.42, -4.9, 7.1)
        H = Skel()
        h0 = H.add(base, 0.17)
        d = Vector((sx * 0.35, 1.0, 0.55)).normalized()
        pts, p = [], base.copy()
        for i in range(6):
            d = (d + Vector((sx * 0.02, 0.05, -0.12))).normalized()
            p = p + d * 0.42
            pts.append(p.copy())
        chain(H, pts, [0.17, 0.15, 0.12, 0.09, 0.06, 0.03], h0)
        H.build(f"Horn{sx}", claw_black(), subdiv=1, knobs=0.0)
    # spikes down the spine, leaning back
    path = [pelvis] + spine_pts + neck_pts
    for k in range(9):
        t = 0.1 + 0.8 * k / 8
        i = t * (len(path) - 1)
        a, b = path[int(i)], path[min(len(path) - 1, int(i) + 1)]
        p = a.lerp(b, i - int(i))
        r = (0.9 + 0.38 * math.sin(math.pi * t)) * K
        h = (0.35 + 0.4 * math.sin(math.pi * t)) * K
        cone(f"Spike{k}", 0.13, 0.0, h, (p.x, p.y + 0.12, p.z + r * 0.9 + h * 0.4), claw_black(), verts=6, rot=(-0.55, 0, 0))
    # claws on every paw
    for key, (pts, ids) in legs.items():
        toe = pts[-1]
        for c in (-1, 0, 1):
            cone(f"Claw{key}{c}", 0.08, 0.0, 0.36, (toe.x + c * 0.2, toe.y - 0.32, 0.13), claw_black(), verts=5, rot=(math.pi / 2 + 0.35, 0, 0))
    # the glowing eyes and the furnace of the throat
    set_group("Glow")
    for sx in (-1, 1):
        sphere(f"Eye{sx}", 0.13, tuple(V(sx * 0.4, -5.38, 6.82)), hide, seg=10, rings=6, scale=(1.0, 0.7, 0.5))
    sphere("Throat", 0.32, tuple(V(0, -5.35, 5.96)), hide, seg=10, rings=6, scale=(0.75, 1.8, 0.45))
    set_group("Main")
    for name, pts in (("Pelvis", None),):
        pass
    # the joints for the rig
    JOINTS["Root"] = (V(0, 1.0, 0.0), V(0, 1.0, 1.0), None)
    JOINTS["Pelvis"] = (pelvis, spine_pts[0], "Root")
    JOINTS["Spine"] = (spine_pts[0], spine_pts[2], "Pelvis")
    JOINTS["Chest"] = (spine_pts[2], spine_pts[4], "Spine")
    JOINTS["Neck"] = (spine_pts[4], neck_pts[1], "Chest")
    JOINTS["Head"] = (neck_pts[1], head_pts[2], "Neck")
    JOINTS["Jaw"] = (V(0, -4.75, 6.05), V(0, -6.85, 5.52), "Head")
    for side in ("L", "R"):
        f, _ = legs[f"F{side}"]
        JOINTS[f"F{side}_Upper"] = (f[0], f[1], "Chest")
        JOINTS[f"F{side}_Lower"] = (f[1], f[2], f"F{side}_Upper")
        JOINTS[f"F{side}_Foot"] = (f[2], f[4], f"F{side}_Lower")
        h, _ = legs[f"H{side}"]
        JOINTS[f"H{side}_Upper"] = (h[0], h[1], "Pelvis")
        JOINTS[f"H{side}_Lower"] = (h[1], h[2], f"H{side}_Upper")
        JOINTS[f"H{side}_Foot"] = (h[2], h[4], f"H{side}_Lower")
    for k in range(4):
        JOINTS[f"Tail{k + 1}"] = (tail[k], tail[k + 1], "Pelvis" if k == 0 else f"Tail{k}")
    return _dims()


def rig_from_joints(name, joints, objs, pin=None):
    """An armature from `joints` (bone -> head, tail, parent); each vertex weighted to its two nearest bones (inverse
    square of the distance to the bone's segment); pieces whose name ends in one of `pin`'s keys go wholly to that bone."""
    arm_data = bpy.data.armatures.new(f"{name}Rig")
    arm = bpy.data.objects.new(f"{name}Rig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    for bn, (h, t, _) in joints.items():
        b = eb.new(bn)
        b.head, b.tail = tuple(h), tuple(t)
    for bn, (_, _, par) in joints.items():
        if par:
            eb[bn].parent = eb[par]
    bpy.ops.object.mode_set(mode="OBJECT")
    segs = [(bn, Vector(h), Vector(t)) for bn, (h, t, _) in joints.items() if bn != "Root"]

    def dist(p, a, b):
        ab = b - a
        u = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab))))
        return (p - (a + ab * u)).length

    for ob in objs:
        if ob.type != "MESH":
            continue
        groups = {bn: ob.vertex_groups.new(name=bn) for bn in joints}
        mw = ob.matrix_world
        fixed = next((bn for suffix, bn in (pin or {}).items() if ob.name.endswith(suffix)), None)
        for v in ob.data.vertices:
            if fixed:
                groups[fixed].add([v.index], 1.0, "REPLACE")
                continue
            p = mw @ v.co
            ds = sorted(((dist(p, a, b), bn) for bn, a, b in segs), key=lambda x: x[0])[:2]
            ws = [(bn, 1.0 / (d * d + 0.01)) for d, bn in ds]
            tot = sum(w for _, w in ws)
            for bn, w in ws:
                groups[bn].add([v.index], w / tot, "REPLACE")
        md = ob.modifiers.new("Rig", "ARMATURE")
        md.object = arm
        ob.parent = arm
    print(f"[rig] {name} bones", len(joints))
    return arm


BUILDERS = {
    "Hellhound": hellhound,
}
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"Hellhound": 1.05})
P.RIGS["Hellhound"] = lambda objs: rig_from_joints("Hellhound", JOINTS, objs, pin={"_Jaw": "Jaw"})
