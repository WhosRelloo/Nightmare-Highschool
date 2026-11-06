"""Props batch 33 (2026-11-05): a dead tree for the grounds. Owner: "make a few ON THEMED plants and tree models", "make
them match the spooky, gothic theme", "make the trees wayy better quality than that", "only make the dead one".

  DeadOak   a great dead oak: a flared, root-gripped base, a twisting trunk splitting low into four contorted limbs that
            reach out and up, clawing side branches and crooked twigs, one limb snapped off short, a dark hollow in the
            trunk; ridged, cracked, soot-dark bark with moss on its upper faces

How it is made: a branching skeleton (every limb a smooth, low-frequency wobble rather than a random walk, so it bends like
wood) is skinned into one continuous mesh (Blender's Skin modifier, so limbs grow out of the trunk without seams),
smoothed once, given a broad knobbly displacement, then baked like every prop: the bark is a procedural material (Voronoi
plates and cracks, fine grain, moss where the surface faces up), its relief baked into the normal map. The fine twigs are
three pieces of their own (Twigs, Twigs2, Twigs3) so each mesh stays under 20k triangles.

Front faces -Y, Z is up, the origin is at the bottom centre. Registered into nh_props.BUILD on import.
"""
import math
import random

import bpy
from mathutils import Vector

import nh_props as P
from nh_props import set_group, _finish
from nh_props_batch4 import _dims
from nh_props_batch8 import hollow


# ------------------------------------------------------------------ the bark

def bark_dead():
    """Soot-dark weathered bark: plates and deep cracks (Voronoi), a fine grain (noise) running along the wood, pale grey
    on the plate faces, moss on the upward faces; its relief goes to the normal map through a bump."""
    m = bpy.data.materials.get("DeadBark")
    if m:
        return m
    m = bpy.data.materials.new("DeadBark")
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links.new
    bs = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (7.5, 7.5, 1.1)            # ridges long and narrow along the (mostly upright) wood
    L(tc.outputs["Object"], mp.inputs["Vector"])
    vor = N.new("ShaderNodeTexVoronoi")
    vor.feature = "DISTANCE_TO_EDGE"
    vor.inputs["Scale"].default_value = 1.6
    vor.inputs["Randomness"].default_value = 0.9
    L(mp.outputs["Vector"], vor.inputs["Vector"])
    crack = N.new("ShaderNodeMapRange")
    crack.inputs["From Min"].default_value = 0.0
    crack.inputs["From Max"].default_value = 0.16
    L(vor.outputs["Distance"], crack.inputs["Value"])          # 0 in the cracks, 1 on the plates
    grain = N.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 14.0
    grain.inputs["Detail"].default_value = 8.0
    grain.inputs["Roughness"].default_value = 0.6
    gm = N.new("ShaderNodeMapping")
    gm.inputs["Scale"].default_value = (5.0, 5.0, 0.6)
    L(tc.outputs["Object"], gm.inputs["Vector"])
    L(gm.outputs["Vector"], grain.inputs["Vector"])
    blot = N.new("ShaderNodeTexNoise")
    blot.inputs["Scale"].default_value = 1.6
    blot.inputs["Detail"].default_value = 3.0
    L(tc.outputs["Object"], blot.inputs["Vector"])
    # colour: cracks near black, plates soot-brown to weathered grey, moss on the upward faces
    c1 = N.new("ShaderNodeMix")
    c1.data_type = "RGBA"
    c1.inputs[6].default_value = (0.012, 0.011, 0.01, 1)       # crack
    c1.inputs[7].default_value = (0.06, 0.052, 0.046, 1)       # plate
    L(crack.outputs["Result"], c1.inputs[0])
    c2 = N.new("ShaderNodeMix")
    c2.data_type = "RGBA"
    c2.inputs[7].default_value = (0.13, 0.125, 0.118, 1)       # bleached grey on the weathered plate faces
    L(c1.outputs[2], c2.inputs[6])
    w = N.new("ShaderNodeMath")
    w.operation = "MULTIPLY"
    L(crack.outputs["Result"], w.inputs[0])
    L(blot.outputs["Fac"], w.inputs[1])
    w2 = N.new("ShaderNodeMapRange")
    w2.inputs["From Min"].default_value = 0.35
    w2.inputs["From Max"].default_value = 0.75
    L(w.outputs[0], w2.inputs["Value"])
    L(w2.outputs["Result"], c2.inputs[0])
    gr = N.new("ShaderNodeMix")
    gr.data_type = "RGBA"
    gr.blend_type = "MULTIPLY"
    gr.inputs[0].default_value = 0.45
    L(c2.outputs[2], gr.inputs[6])
    L(grain.outputs["Color"], gr.inputs[7])
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    L(geo.outputs["Normal"], sep.inputs["Vector"])
    up = N.new("ShaderNodeMapRange")
    up.inputs["From Min"].default_value = 0.45
    up.inputs["From Max"].default_value = 0.85
    L(sep.outputs["Z"], up.inputs["Value"])
    mn = N.new("ShaderNodeTexNoise")
    mn.inputs["Scale"].default_value = 3.5
    mn.inputs["Detail"].default_value = 5.0
    L(tc.outputs["Object"], mn.inputs["Vector"])
    mm = N.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    L(up.outputs["Result"], mm.inputs[0])
    mm2 = N.new("ShaderNodeMapRange")
    mm2.inputs["From Min"].default_value = 0.45
    mm2.inputs["From Max"].default_value = 0.6
    L(mn.outputs["Fac"], mm2.inputs["Value"])
    L(mm2.outputs["Result"], mm.inputs[1])
    moss = N.new("ShaderNodeMix")
    moss.data_type = "RGBA"
    L(mm.outputs[0], moss.inputs[0])
    L(gr.outputs[2], moss.inputs[6])
    moss.inputs[7].default_value = (0.016, 0.03, 0.01, 1)
    L(moss.outputs[2], bs.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.78
    rr.inputs["To Max"].default_value = 0.95
    L(grain.outputs["Fac"], rr.inputs["Value"])
    L(rr.outputs["Result"], bs.inputs["Roughness"])
    bs.inputs["Metallic"].default_value = 0.0
    hsum = N.new("ShaderNodeMath")
    hsum.operation = "MULTIPLY_ADD"
    L(grain.outputs["Fac"], hsum.inputs[0])
    hsum.inputs[1].default_value = 0.35
    L(crack.outputs["Result"], hsum.inputs[2])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.75
    bump.inputs["Distance"].default_value = 0.06
    L(hsum.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], bs.inputs["Normal"])
    return m


# ------------------------------------------------------------------ the skeleton

class Skel:
    """A branching skeleton: vertices with radii and edges, skinned into one mesh."""

    def __init__(self):
        self.co, self.r, self.edges = [], [], []

    def add(self, p, r, parent=None):
        self.co.append(Vector(p))
        self.r.append(r)
        i = len(self.co) - 1
        if parent is not None:
            self.edges.append((parent, i))
        return i

    def build(self, name, mat, subdiv=1, knobs=0.05):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(c) for c in self.co], self.edges, [])
        ob = bpy.data.objects.new(name, me)
        bpy.context.collection.objects.link(ob)
        sk = ob.modifiers.new("Skin", "SKIN")
        sk.branch_smoothing = 0.6
        sk.use_smooth_shade = True
        roots = set()
        for a, b in self.edges:
            pass
        # a root per connected piece (the first vertex of each)
        seen = set()
        adj = {}
        for a, b in self.edges:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        for i in range(len(self.co)):
            if i in seen:
                continue
            roots.add(i)
            stack = [i]
            while stack:
                j = stack.pop()
                if j in seen:
                    continue
                seen.add(j)
                stack.extend(adj.get(j, []))
        for i, v in enumerate(me.skin_vertices[0].data):
            v.radius = (self.r[i], self.r[i])
            v.use_root = i in roots
        if subdiv:
            sd = ob.modifiers.new("Sub", "SUBSURF")
            sd.levels = subdiv
            sd.render_levels = subdiv
        if knobs:
            tex = bpy.data.textures.new(f"{name}Knobs", "CLOUDS")
            tex.noise_scale = 0.9
            tex.noise_depth = 2
            dp = ob.modifiers.new("Knobs", "DISPLACE")
            dp.texture = tex
            dp.texture_coords = "OBJECT"
            dp.strength = knobs
            dp.mid_level = 0.5
        _finish(ob, mat, 0)
        return ob


def _wobble(rnd, amp, n=3):
    """A smooth, low-frequency wobble: a sum of sines with random phases, as two perpendicular offsets over t 0..1."""
    terms = [(rnd.uniform(0.6, 1.6) * (k + 1), rnd.uniform(0, 6.28), rnd.uniform(0, 6.28), amp / (k + 1)) for k in range(n)]

    def f(t):
        a = sum(A * math.sin(2 * math.pi * fr * t + p1) for fr, p1, _, A in terms)
        b = sum(A * math.sin(2 * math.pi * fr * t + p2) for fr, _, p2, A in terms)
        return a, b
    return f


def _perp(d):
    a = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(a).normalized()
    return u, d.cross(u).normalized()


def limb(S, rnd, start, parent, d, length, r0, r1, seg, amp, curl=Vector((0, 0, 0)), gravity=0.0):
    """One limb from vertex `parent` at `start`, heading d, `seg` segments, radius r0 -> r1, a smooth wobble of `amp`, a
    steady curl added to the heading as it goes and a droop by gravity. Returns (points, vertex ids, headings)."""
    w = _wobble(rnd, amp)
    u, v = _perp(Vector(d).normalized())
    pts, ids, heads = [Vector(start)], [parent], []
    p, h = Vector(start), Vector(d).normalized()
    prev = (0.0, 0.0)
    for i in range(1, seg + 1):
        t = i / seg
        h = (h + curl * (1.0 / seg) + Vector((0, 0, -gravity * t / seg))).normalized()
        a, b = w(t)
        p = p + h * (length / seg) + (u * (a - prev[0]) + v * (b - prev[1])) * length * 0.25
        prev = (a, b)
        r = r0 + (r1 - r0) * (t ** 0.85)
        ids.append(S.add(p, r, ids[-1]))
        pts.append(p.copy())
        heads.append(h.copy())
    return pts, ids, heads


CHAINS = []   # (chain name, points, bones, parent chain, index on the parent where it leaves): the rig follows these


def dead_oak(M):
    CHAINS.clear()
    rnd = random.Random(3301)
    bark = bark_dead()
    S = Skel()
    TW = [Skel(), Skel(), Skel()]
    turn = [0]

    def T_next():
        turn[0] += 1
        return TW[turn[0] % 3]
    set_group("Main")
    # the trunk: a flared foot, a slow twist, splitting at about 3
    root = S.add((0, 0, -0.35), 1.05)
    tw = _wobble(rnd, 0.12)
    trunk, tids = [Vector((0, 0, -0.35))], [root]
    for i in range(1, 9):
        t = i / 8
        a, b = tw(t)
        p = Vector((a * 0.8 * t + 0.25 * t, b * 0.8 * t - 0.1 * t, -0.35 + 4.6 * t))
        r = 0.98 - 0.3 * t
        tids.append(S.add(p, r, tids[-1]))
        trunk.append(p)
    CHAINS.append(("Trunk", trunk, 3, None, 0))
    # the roots gripping the ground: out from the foot, arching, diving in
    for k in range(7):
        a = k / 7 * 2 * math.pi + rnd.uniform(-0.25, 0.25)
        d = Vector((math.cos(a), math.sin(a), 0.12)).normalized()
        i0 = 1
        # slim, long roots: they leave the foot nearly level, arch over the ground and dive in
        limb(S, rnd, trunk[i0], tids[i0], d, rnd.uniform(2.8, 4.2), 0.46, 0.07, 9, 0.1, curl=Vector((0, 0, -0.85)))
    # the four great limbs, each with clawing side branches and crooked twigs
    majors = []
    for k in range(4):
        a = k / 4 * 2 * math.pi + rnd.uniform(-0.35, 0.35) + 0.4
        elev = rnd.uniform(0.35, 0.85)
        d = Vector((math.cos(a) * math.cos(elev), math.sin(a) * math.cos(elev), math.sin(elev)))
        i0 = (5, 6, 7, 8)[k]
        snapped = (k == 2)
        L = rnd.uniform(2.0, 2.4) if snapped else rnd.uniform(6.0, 7.6)
        pts, ids, heads = limb(S, rnd, trunk[i0], tids[i0], d, L, S.r[tids[i0]] * 0.74, 0.3 if snapped else 0.1, 6 if snapped else 12, 0.28,
                               curl=Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.2, 0.6))), gravity=0.25)
        majors.append((pts, ids, heads, snapped))
        CHAINS.append((f"Limb{k + 1}", pts, 2 if snapped else 3, "Trunk", i0))
    for mk, (pts, ids, heads, snapped) in enumerate(majors):
        n_side = 2 if snapped else 4
        for s in range(n_side):
            i = rnd.randint(3, len(pts) - 2) if not snapped else rnd.randint(2, len(pts) - 2)
            h = heads[i - 1]
            u, v = _perp(h)
            ang = rnd.uniform(0, 6.28)
            side = (u * math.cos(ang) + v * math.sin(ang))
            d = (h * 0.55 + side * 0.85 + Vector((0, 0, rnd.uniform(0.0, 0.5)))).normalized()
            r_here = S.r[ids[i]]
            sp, sids, sh = limb(S, rnd, pts[i], ids[i], d, rnd.uniform(2.0, 3.6), r_here * 0.62, 0.05, 8, 0.32,
                                curl=Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.4))), gravity=0.35)
            CHAINS.append((f"Limb{mk + 1}S{s + 1}", sp, 2, f"Limb{mk + 1}", i))
            # crooked twigs off the side branch: their own skeleton, rooted just inside the branch
            for tw_i in range(rnd.randint(3, 5)):
                j = rnd.randint(3, len(sp) - 1)
                hh = sh[j - 1]
                uu, vv = _perp(hh)
                aa = rnd.uniform(0, 6.28)
                dd = (hh * 0.4 + (uu * math.cos(aa) + vv * math.sin(aa)) + Vector((0, 0, rnd.uniform(-0.2, 0.6)))).normalized()
                T = T_next()
                b0 = T.add(sp[j], S.r[sids[j]] * 0.85)
                limb(T, rnd, sp[j], b0, dd, rnd.uniform(0.7, 1.5), S.r[sids[j]] * 0.7, 0.018, 5, 0.5,
                     curl=Vector((rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-1.5, 1.5))))
        if not snapped:
            for c in range(4):
                hh = heads[-1]
                uu, vv = _perp(hh)
                aa = c / 4 * 6.28 + rnd.uniform(-0.4, 0.4)
                dd = (hh + (uu * math.cos(aa) + vv * math.sin(aa)) * 0.9).normalized()
                T = T_next()
                b0 = T.add(pts[-1], S.r[ids[-1]] * 0.9)
                limb(T, rnd, pts[-1], b0, dd, rnd.uniform(0.8, 1.7), S.r[ids[-1]] * 0.75, 0.016, 5, 0.55,
                     curl=Vector((rnd.uniform(-2, 2), rnd.uniform(-2, 2), rnd.uniform(-1.5, 1.0))))
    # the snapped limb's end: jagged splinters standing up from the break
    for pts, ids, heads, snapped in majors:
        if not snapped:
            continue
        tip, hh = pts[-1], heads[-1]
        uu, vv = _perp(hh)
        rr = S.r[ids[-1]]
        for k in range(6):
            aa = k / 6 * 6.28 + rnd.uniform(-0.3, 0.3)
            off = (uu * math.cos(aa) + vv * math.sin(aa)) * rr * rnd.uniform(0.3, 0.7)
            dd = (hh + off * 0.6 + Vector((rnd.gauss(0, 0.15), rnd.gauss(0, 0.15), rnd.gauss(0, 0.15)))).normalized()
            T = T_next()
            q = tip - hh * 0.06 + off
            b0 = T.add(q, rr * 0.32)
            limb(T, rnd, q, b0, dd, rnd.uniform(0.2, 0.55), rr * 0.26, 0.01, 3, 0.25)
    # a few small dead sprouts low on the trunk
    for k in range(3):
        i = rnd.randint(2, 5)
        a = rnd.uniform(0, 6.28)
        d = Vector((math.cos(a), math.sin(a), 0.4)).normalized()
        q = trunk[i] + d * S.r[tids[i]] * 0.7
        T = T_next()
        b0 = T.add(q, 0.08)
        limb(T, rnd, q, b0, d, rnd.uniform(0.6, 1.1), 0.07, 0.015, 4, 0.5)
    S.build("Tree", bark, subdiv=1, knobs=0.09)
    for k, T in enumerate(TW):
        set_group("Twigs" if k == 0 else f"Twigs{k + 1}")
        T.build(f"Twigs{k + 1}", bark, subdiv=1, knobs=0.0)
    set_group("Main")
    # the hollow: a dark mouth in the trunk's front, its lip swollen
    c = trunk[3]
    r = S.r[tids[3]]
    front = Vector((c.x, c.y - r * 0.82, c.z + 0.2))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=14, ring_count=8, radius=1.0, location=front)
    h = bpy.context.active_object
    h.name = "Hollow"
    h.scale = (r * 0.36, r * 0.3, r * 0.7)
    _finish(h, hollow(), 0)
    return _dims()


def rig_dead_oak(objs):
    """The tree's armature, from its skeleton chains: Root (the foot and the roots, which never move), Trunk1-3, every
    great limb Limb<k>_1-3 (the snapped one _1-2) and every side branch Limb<k>S<s>_1-2, each chain's first bone parented
    to the bone it grows from. Every vertex is weighted to its two nearest bones (inverse square of the distance to the
    bone's segment); the foot and the roots (below 1 stud) go wholly to Root, blending up to the trunk by 1.8 studs."""
    arm_data = bpy.data.armatures.new("DeadOakRig")
    arm = bpy.data.objects.new("DeadOakRig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones
    segs = {}                                  # chain -> [(bone name, head index, tail index)]
    bones = []                                 # (name, head, tail)
    root = eb.new("Root")
    root.head, root.tail = (0, 0, -0.35), (0, 0, 0.9)
    bones.append(("Root", Vector((0, 0, -0.35)), Vector((0, 0, 0.9))))
    for cname, pts, nb, parent, at in CHAINS:
        n = len(pts) - 1
        cuts = [round(n * j / nb) for j in range(nb + 1)]
        segs[cname] = []
        prev = None
        for j in range(nb):
            bn = f"{cname}{j + 1}" if cname == "Trunk" else f"{cname}_{j + 1}"
            b = eb.new(bn)
            b.head, b.tail = tuple(pts[cuts[j]]), tuple(pts[cuts[j + 1]])
            if prev is not None:
                b.parent = prev
                b.use_connect = True
            else:
                if parent is None:
                    b.parent = root
                else:
                    pb = next(name for name, h0, h1 in segs[parent] if h0 <= at <= h1)
                    b.parent = eb[pb]
            segs[cname].append((bn, cuts[j], cuts[j + 1]))
            bones.append((bn, Vector(pts[cuts[j]]), Vector(pts[cuts[j + 1]])))
            prev = b
    bpy.ops.object.mode_set(mode="OBJECT")

    def seg_dist(p, a, b):
        ab = b - a
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-9, ab.dot(ab))))
        return (p - (a + ab * t)).length

    for ob in objs:
        if ob.type != "MESH":
            continue
        groups = {name: ob.vertex_groups.new(name=name) for name, _, _ in bones}
        mw = ob.matrix_world
        for v in ob.data.vertices:
            p = mw @ v.co
            ds = sorted(((seg_dist(p, a, b), name) for name, a, b in bones if name != "Root"), key=lambda x: x[0])[:2]
            ws = [(name, 1.0 / (d * d + 0.02)) for d, name in ds]
            tot = sum(w for _, w in ws)
            ground = max(0.0, min(1.0, (1.8 - p.z) / 0.8))      # 1 below 1 stud, 0 above 1.8
            for name, w in ws:
                groups[name].add([v.index], (w / tot) * (1 - ground), "REPLACE")
            if ground > 0:
                groups["Root"].add([v.index], ground, "REPLACE")
        md = ob.modifiers.new("Rig", "ARMATURE")
        md.object = arm
        ob.parent = arm
    print("[rig] DeadOak bones", len(bones))
    return arm


BUILDERS = {
    "DeadOak": dead_oak,
}
P.RIGS["DeadOak"] = rig_dead_oak
P.BUILD.update(BUILDERS)
P.PREVIEW_PAD.update({"DeadOak": 1.05})
