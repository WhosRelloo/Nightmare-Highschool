"""Hair tuck: bend the game's rigged hairs so they lie over, under or round a worn accessory instead of passing through it.

E:/Blender/blender.exe -b --factory-startup -P acc_hairtuck.py -- [--items A,B] [--hairs H1,H2] [--root E:/NH-Work/acc]
                                                                [--rig E:/NH-Work/hair_rigged_v2] [--all]

For every item (a model and its pieces, as worn on the standard body at rest) and every hair the item refuses
today (hair_fit "x" on any of its pieces; --all: every hair), it looks for the gentlest bend of each lock of the hair
(the v2 rigs, tools/hair-rig/nh_hair_autorig.py: the locks carry their strands) such that:
  * no hair triangle crosses a piece triangle (the same test as acc_check --hair)
  * no strand sinks into the head or the torso further than it already does at rest
  * hair that lies on the head at rest stays close to it (no bald patch where a lock lifts away)
  * bends near the scalp cost more than bends further down a lock
Head pieces are worn at the hair's fit (scale k about the headband, lift dz); a hair the piece refused gets the
piece's generous fit (the "*" fit acc_assemble writes for unlisted hairs).
Writes <root>/tuck/<Item>.json: { hair: { "fit": [k, dz], "bones": { bone: [x, y, z] } } | null }, each bone's turn
as a rotation vector (radians) in the hair Handle's own frame, applied at the bone's head in its rest frame (what
Controllers.Character.HairSway composes under its sway). null = no bend clears it (the hair stays refused).
"""
import bpy, sys, os, json, math, time
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ROOT = argv[argv.index("--root") + 1] if "--root" in argv else "E:/NH-Work/acc"
RIG = argv[argv.index("--rig") + 1] if "--rig" in argv else "E:/NH-Work/hair_rigged_v2"
RENDER = argv[argv.index("--render") + 1] if "--render" in argv else None   # a folder: before / after shots
RVIEWS = ("back34", "side")
ONLY = argv[argv.index("--items") + 1].split(",") if "--items" in argv else None
HAIRS = argv[argv.index("--hairs") + 1].split(",") if "--hairs" in argv else None
ALL = "--all" in argv
OUT = os.path.join(ROOT, "tuck")
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import nh_acc as A
import acc_check as C

M1 = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)   # Blender (as imported) <-> the Roblox handle frame
SEAT = np.array([0, 0, 1.93])
HEAD_LO, HEAD_HI = np.array([-0.6, -0.6, 0.9]), np.array([0.6, 0.6, 2.1])
MAXBEND = 40.0   # degrees per bone axis
STRAIN_OK = 0.15  # the worst 0.5% of the hair's edges may stretch or shrink by at most 15%: no crumpled cards
TWIST_OK = 30.0   # degrees: the worst 0.5% of neighbouring triangles may turn against each other by at most this
EXPOSE_OK = 0.03  # at most 3% of the head the hair covered at rest may show
TORSO_LO, TORSO_HI = np.array([-1.0, -0.5, -1.0]), np.array([1.0, 0.5, 1.0])


# ------------------------------------------------------------------------------------------------ a hair
class Hair:
    def __init__(self, name):
        self.name = name
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=f"{RIG}/{name}.fbx")
        arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
        mesh = next(o for o in bpy.data.objects if o.type == "MESH")
        Pw = np.array([mesh.matrix_world @ v.co for v in mesh.data.vertices])
        c = (Pw.min(0) + Pw.max(0)) / 2
        pos, ori, _ = A._hair_attach()[name]
        k = 0.88 / 0.9
        Ra = np.array(A._rbx_rot(*ori))
        a = np.array(pos) * k
        self.Rimp = M1 @ Ra.T @ M1                       # import space -> character space (rotation part)
        self.Amat = k * self.Rimp
        self.bvec = M1 @ (np.array([0, 0.6, 0]) + Ra.T @ (-k * (M1 @ c) - a)) + np.array([0, 0, 1.5])
        self.P = Pw @ self.Amat.T + self.bvec            # rest vertices, character space
        mesh.data.calc_loop_triangles()
        self.tris = np.array([tuple(t.vertices) for t in mesh.data.loop_triangles])
        # bones: char-space heads and directions, parents, depth along the lock
        self.bones = [b.name for b in arm.data.bones]
        self.bi = {n: i for i, n in enumerate(self.bones)}
        self.parent = [self.bi[b.parent.name] if b.parent else -1 for b in arm.data.bones]
        H = np.array([arm.matrix_world @ b.head_local for b in arm.data.bones])
        T = np.array([arm.matrix_world @ b.tail_local for b in arm.data.bones])
        self.head = H @ self.Amat.T + self.bvec
        d = (T - H) @ self.Rimp.T
        self.dir = d / np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
        # weights: up to 4 per vertex
        gi = {g.index: g.name for g in mesh.vertex_groups}
        n = len(self.P)
        self.wi = np.zeros((n, 4), int)
        self.ww = np.zeros((n, 4))
        root = self.bi["HairRoot"]
        for vi, v in enumerate(mesh.data.vertices):
            gs = sorted(((g.weight, gi[g.group]) for g in v.groups if g.weight > 0 and gi[g.group] in self.bi), reverse=True)[:4]
            if not gs:
                gs = [(1.0, "HairRoot")]
            tot = sum(g[0] for g in gs)
            for s, (w, bn) in enumerate(gs):
                self.wi[vi, s] = self.bi[bn]
                self.ww[vi, s] = w / tot
            for s in range(len(gs), 4):
                self.wi[vi, s] = root
        # locks: chains of bones, their vertices (any weight) and triangles
        self.locks = {}
        for bn in self.bones:
            if bn.startswith("Lock"):
                self.locks.setdefault(bn.split("_")[0], []).append(self.bi[bn])
        for ln in self.locks:
            self.locks[ln].sort(key=lambda i: int(self.bones[i].split("_")[1]))
        self.lockverts = {}
        for ln, ids in self.locks.items():
            m = np.isin(self.wi, ids) & (self.ww > 1e-4)
            self.lockverts[ln] = np.where(m.any(1))[0]
        # rest measures
        self.head_rest = box_depth(self.P, HEAD_LO, HEAD_HI)
        self.torso_rest = box_depth(self.P, TORSO_LO, TORSO_HI)
        self.on_head = box_dist(self.P, HEAD_LO, HEAD_HI) < 0.12
        e = set()
        for t in self.tris:
            e.update({(min(t[0], t[1]), max(t[0], t[1])), (min(t[1], t[2]), max(t[1], t[2])), (min(t[0], t[2]), max(t[0], t[2]))})
        self.edges = np.array(sorted(e))
        self.elen = np.linalg.norm(self.P[self.edges[:, 0]] - self.P[self.edges[:, 1]], axis=1)
        keep = self.elen > 2e-3             # welded / zero-length edges carry no shape
        self.edges, self.elen = self.edges[keep], self.elen[keep]
        # neighbouring triangles (sharing an edge) and their rest angle: a strand card must not twist against its neighbour
        owner = {}
        pairs = []
        for ti, t in enumerate(self.tris):
            for a_, b_ in ((t[0], t[1]), (t[1], t[2]), (t[0], t[2])):
                key = (min(a_, b_), max(a_, b_))
                if key in owner:
                    pairs.append((owner[key], ti))
                else:
                    owner[key] = ti
        self.tpairs = np.array(pairs, int).reshape(-1, 2)
        n0 = tri_normals(self.P, self.tris)
        self.tang0 = np.arccos(np.clip((n0[self.tpairs[:, 0]] * n0[self.tpairs[:, 1]]).sum(1), -1, 1))
        # the head's surface the hair covers at rest (lower back and sides): it must stay covered
        self.cover0 = covered(self.P, self.tris)

    def axes(self, b):
        d = self.dir[b]
        u = np.cross(d, [0, 0, 1.0])
        if np.linalg.norm(u) < 0.2:
            u = np.cross(d, [1.0, 0, 0])
        u /= np.linalg.norm(u)
        return u, np.cross(d, u)

    def transforms(self, rv):
        """rv: {bone index: rotation vector (char space)} -> per-bone (R, t) for every bone (parents first)"""
        nb = len(self.bones)
        R = np.tile(np.eye(3), (nb, 1, 1))
        t = np.zeros((nb, 3))
        for b in range(nb):           # FBX import keeps parents before children
            q = rv.get(b)
            if q is not None and np.linalg.norm(q) > 1e-9:
                Rl = rotvec(q)
                tl = self.head[b] - Rl @ self.head[b]
            else:
                Rl, tl = np.eye(3), np.zeros(3)
            p = self.parent[b]
            if p >= 0:
                R[b] = R[p] @ Rl
                t[b] = R[p] @ tl + t[p]
            else:
                R[b], t[b] = Rl, tl
        return R, t

    def deform(self, rv, vids=None):
        R, t = self.transforms(rv)
        idx = slice(None) if vids is None else vids
        P = self.P[idx]
        wi, ww = self.wi[idx], self.ww[idx]
        out = np.zeros_like(P)
        for s in range(4):
            Rb, tb = R[wi[:, s]], t[wi[:, s]]
            out += ww[:, s, None] * (np.einsum("vij,vj->vi", Rb, P) + tb)
        return out

    def handle_frame(self, q):
        """a char-space rotation vector -> the hair Handle's frame (what the game reads)"""
        return M1 @ (self.Rimp.T @ q)


def tri_normals(P, T):
    n = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]])
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)


def head_samples():
    pts = []
    for z in np.linspace(0.95, 1.6, 12):
        for x in np.linspace(-0.55, 0.55, 12):
            pts.append(((x, 0.6, z), (0, 1, 0)))                    # the back of the head (+Y is behind)
        for y in np.linspace(-0.1, 0.55, 7):
            pts.append(((0.6, y, z), (1, 0, 0)))
            pts.append(((-0.6, y, z), (-1, 0, 0)))
    return pts


HEAD_SAMPLES = head_samples()


def covered(P, T):
    """which head sample points have hair over them (a ray outward from the skin hits the hair)"""
    bvh = BVHTree.FromPolygons([Vector(p) for p in P], [tuple(t) for t in T], epsilon=0.0)
    out = np.zeros(len(HEAD_SAMPLES), bool)
    for i, (p, d) in enumerate(HEAD_SAMPLES):
        out[i] = bvh.ray_cast(Vector(p), Vector(d), 0.5)[0] is not None
    return out


def rotvec(q):
    th = np.linalg.norm(q)
    if th < 1e-12:
        return np.eye(3)
    k = q / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def box_depth(P, lo, hi):
    """how far inside the box each point is (0 outside)"""
    inside = np.all((P > lo) & (P < hi), axis=1)
    d = np.minimum(P - lo, hi - P).min(1)
    return np.where(inside, d, 0.0)


def box_dist(P, lo, hi):
    q = np.minimum(np.maximum(P, lo), hi)
    return np.linalg.norm(P - q, axis=1)


# ------------------------------------------------------------------------------------------------ the pieces
def game_items():
    """the game's items (Config.Accessories): (model, [pieces worn together]); the lead piece names the item here"""
    import re
    out = []
    for f in [f"{ROOT}/src/Accessories.luau"]:
        t = open(f, encoding="utf-8").read()
        for m in re.finditer(r"\{ Id = `([^`]+)`;([^\n]*)\};", t):
            line = m.group(2)
            mm = re.search(r"Model = `(\w+)`", line)
            if not mm:
                continue
            model = mm.group(1)
            ps = re.search(r"Pieces = \{([^}]*)\}", line)
            p1 = re.search(r"Piece = `(\w+)`", line)
            if ps:
                pieces = re.findall(r"`(\w+)`", ps.group(1))
            elif p1:
                pieces = [p1.group(1)]
            else:
                lp = f"{ROOT}/layout/{model}.json"
                pieces = list(json.load(open(lp))["pieces"]) if os.path.exists(lp) else []
            if pieces and (model, tuple(pieces)) not in [(a, tuple(b)) for a, b in out]:
                out.append((model, pieces))
    return out


def load_item(it, only=None):
    lay = json.load(open(f"{ROOT}/layout/{it}.json"))
    pieces = {}
    with bpy.data.libraries.load(f"{ROOT}/blend/{it}.blend", link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n in lay["pieces"] and (only is None or n in only)]
    for ob in dst.objects:
        bpy.context.scene.collection.objects.link(ob)
        for md in list(ob.modifiers):
            if md.type == "ARMATURE":
                ob.modifiers.remove(md)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        V = np.array([ob.matrix_world @ v.co for v in me.vertices])
        me.calc_loop_triangles()
        Tr = [tuple(t.vertices) for t in me.loop_triangles]
        ev.to_mesh_clear()
        e = lay["pieces"][ob.name]
        pieces[ob.name] = dict(V=V, T=Tr, mount=e["mount"], fit=e.get("hair_fit") or {}, body=e.get("fit_body") or {})
        bpy.data.objects.remove(ob)
    return pieces


def generous(fits):
    ks = sorted(v[0] for v in fits.values() if v); zs = sorted(v[1] for v in fits.values() if v)
    if not ks:
        return [1.0, 0.0]
    q = max(0, int(len(ks) * 0.9) - 1)
    return [ks[q], zs[q]]


def item_bvh(pieces, hair):
    """the item's pieces as worn with this hair: one BVH (head pieces at the hair's fit)"""
    V, T, fit = [], [], None
    for pn, P in pieces.items():
        Vp = P["V"]
        variants = [Vp]
        if P["mount"] == "Head":
            f = P["fit"].get(hair)
            f = f if f else generous(P["fit"])
            fit = f
            if pn in C.MASKS:   # (1.99.0) a mask scales out round the head's axis only (acc_check.at_hair_fit)
                variants = [Vp * np.array([f[0], f[0], 1.0]) + np.array([0, 0, f[1]])]
            else:
                variants = [SEAT + (Vp - SEAT) * f[0] + np.array([0, 0, f[1]])]
        elif P["body"]:
            # every body type wears it deeper or shallower (the depth fit scales front-to-back about the part's centre):
            # the hair must clear the shallowest and the deepest fit as well as the standard one
            for k in (min(P["body"].values()), max(P["body"].values())):
                if abs(k - 1) > 1e-3:
                    variants.append(Vp * np.array([1.0, k, 1.0]))
        for Vv in variants:
            off = len(V)
            V += [Vector(p) for p in Vv]
            T += [tuple(i + off for i in t) for t in P["T"]]
    return BVHTree.FromPolygons(V, T, epsilon=0.0), fit or [1.0, 0.0]


# ------------------------------------------------------------------------------------------------ the solve
def crossings(bvh, Pv, tris, want_tree=False):
    if len(tris) == 0:
        return (0, None) if want_tree else 0
    hb = BVHTree.FromPolygons([Vector(p) for p in Pv], [tuple(t) for t in tris], epsilon=0.0)
    n = len(bvh.overlap(hb))
    return (n, hb) if want_tree else n


def covered_by(tree):
    out = np.zeros(len(HEAD_SAMPLES), bool)
    if tree is None:
        return out
    for i, (p, d) in enumerate(HEAD_SAMPLES):
        out[i] = tree.ray_cast(Vector(p), Vector(d), 0.5)[0] is not None
    return out


def visible_samples(bvh):
    """head sample points the worn piece does not hide (a ray outward from the skin misses the piece)"""
    return np.array([bvh.ray_cast(Vector(p), Vector(d), 0.6)[0] is None for p, d in HEAD_SAMPLES])


def solve(hair, bvh, others=()):
    """others: the BVHs of the other items this hair can wear with this one: a tuck may not push hair into them"""
    rv = {}
    seen = visible_samples(bvh)
    cover0 = hair.cover0 & seen
    full = hair.P
    total0 = crossings(bvh, full, hair.tris)
    if total0 == 0:
        hair.last_strain, hair.last_twist, hair.last_exposed = (0.0, 0.0), 0.0, 0.0
        return {}, 0, 0
    for ln, ids in hair.locks.items():
        own = hair.lockverts[ln]
        if len(own) == 0:
            continue
        tmask = np.isin(hair.tris, own).any(1)      # every triangle the lock moves, shared ones too
        vids = np.unique(np.concatenate([own, hair.tris[tmask].ravel()]))
        local = {v: i for i, v in enumerate(vids)}
        ltris = np.vectorize(local.get)(hair.tris[tmask]) if tmask.any() else np.zeros((0, 3), int)
        if crossings(bvh, hair.P[vids], ltris) == 0:
            continue
        hb0 = BVHTree.FromPolygons([Vector(p) for p in hair.P[vids]], [tuple(t) for t in ltris], epsilon=0.0)
        base_o = [len(o.overlap(hb0)) for o in others]
        ax = [hair.axes(b) for b in ids]
        emask = np.isin(hair.edges, vids).all(1)
        ledges = np.vectorize(local.get)(hair.edges[emask]) if emask.any() else np.zeros((0, 2), int)
        lelen = np.maximum(hair.elen[emask], 1e-4)
        P0 = hair.P[vids]
        tidx = np.where(tmask)[0]
        tloc = {t: i for i, t in enumerate(tidx)}
        pm = np.isin(hair.tpairs, tidx).all(1)
        lpairs = np.vectorize(tloc.get)(hair.tpairs[pm]) if pm.any() else np.zeros((0, 2), int)
        lang0 = hair.tang0[pm]
        # the head the rest of the hair (as posed so far) already covers
        Pcur = hair.deform(rv) if rv else hair.P
        rest_tris = hair.tris[~tmask]
        static = covered(Pcur, rest_tris) if len(rest_tris) else np.zeros(len(HEAD_SAMPLES), bool)
        need = cover0 & ~static
        hr, tr, oh = hair.head_rest[vids], hair.torso_rest[vids], hair.on_head[vids]
        # where hair may sink a little into the head: the lower back and sides of it (the nape, tucked into a collar),
        # never the crown or the face
        nape_ok = (P0[:, 2] < 1.25) & (P0[:, 1] > -0.2)

        def pose_of(x):
            q = dict(rv)
            for j, b in enumerate(ids):
                u, w = ax[j]
                q[b] = np.radians(x[2 * j]) * u + np.radians(x[2 * j + 1]) * w
            return q

        def cost(x):
            Pv = hair.deform(pose_of(x), vids)
            ov, tree = crossings(bvh, Pv, ltris, True)
            if others and tree is not None:
                ov += sum(max(0, len(o.overlap(tree)) - b) for o, b in zip(others, base_o))
            bare = int((need & ~covered_by(tree)).sum()) if need.any() else 0
            hd = np.maximum(0, box_depth(Pv, HEAD_LO, HEAD_HI) - hr - 0.005)
            ph = hd[~nape_ok].sum() + np.maximum(0, hd[nape_ok] - 0.08).sum()
            pt = np.maximum(0, box_depth(Pv, TORSO_LO, TORSO_HI) - tr - 0.005).sum()
            cov = np.maximum(0, np.linalg.norm(Pv - P0, axis=1) - 0.04)[oh].sum()
            strain = np.abs(np.linalg.norm(Pv[ledges[:, 0]] - Pv[ledges[:, 1]], axis=1) / lelen - 1)
            st = np.maximum(0, strain - 0.04).sum()
            nn = tri_normals(Pv, ltris)
            ang = np.arccos(np.clip((nn[lpairs[:, 0]] * nn[lpairs[:, 1]]).sum(1), -1, 1))
            tw = np.maximum(0, np.abs(ang - lang0) - 0.3).sum()
            bend = sum((x[2 * j] ** 2 + x[2 * j + 1] ** 2) * (6.0 if j == 0 else 1.0) for j in range(len(ids)))
            return 4 * ov + 20 * ph + 20 * pt + 3.0 * cov + 6.0 * st + 1.5 * tw + 0.6 * bare + 0.0016 * bend, ov

        def descend(x):
            best, bov = cost(x)
            step = 16.0
            while step >= 2.0:
                improved = False
                for i in range(len(x)):
                    for s in (step, -step):
                        y = list(x)
                        y[i] = max(-MAXBEND, min(MAXBEND, y[i] + s))
                        c, ov = cost(y)
                        if c < best - 1e-6:
                            best, bov, x, improved = c, ov, y, True
                if not improved:
                    step /= 2
            return best, bov, x

        rng = np.random.default_rng(len(vids))
        best = descend([0.0] * (2 * len(ids)))
        tries = 0
        while 0 < best[1] <= 25 and tries < 8:   # a lock still crossing a lot after a full descent won't clear
            tries += 1
            st = list(rng.uniform(-25, 25, 2 * len(ids)))
            cand = descend(st)
            if (cand[1], cand[0]) < (best[1], best[0]):
                best = cand
        for b, q in pose_of(best[2]).items():
            rv[b] = q
    Pf = hair.deform(rv)
    total1, tf = crossings(bvh, Pf, hair.tris, True)
    if others and rv:
        hr0 = BVHTree.FromPolygons([Vector(p) for p in hair.P], [tuple(t) for t in hair.tris], epsilon=0.0)
        total1 += sum(max(0, len(o.overlap(tf)) - len(o.overlap(hr0))) for o in others)
    strain = np.abs(np.linalg.norm(Pf[hair.edges[:, 0]] - Pf[hair.edges[:, 1]], axis=1) / np.maximum(hair.elen, 1e-4) - 1)
    nn = tri_normals(Pf, hair.tris)
    ang = np.arccos(np.clip((nn[hair.tpairs[:, 0]] * nn[hair.tpairs[:, 1]]).sum(1), -1, 1))
    twist = np.abs(ang - hair.tang0)
    cov = covered(Pf, hair.tris)
    lost = int((cover0 & ~cov).sum())
    hair.last_strain = (float(np.percentile(strain, 99.5)), float(strain.max()))
    hair.last_twist = float(np.degrees(np.percentile(twist, 99.5)))
    hair.last_exposed = lost / max(1, int(cover0.sum()))
    return rv, total0, total1


def main():
    t0 = time.time()
    hairs = HAIRS or sorted(f[:-4] for f in os.listdir(RIG) if f.endswith(".fbx"))
    C.load_slots()
    C.load_conflicts()
    all_items = [(m, ps) for m, ps in game_items() if os.path.exists(f"{ROOT}/blend/{m}.blend")]
    items = [(m, ps) for m, ps in all_items if ONLY is None or m in ONLY or ps[0] in ONLY]

    def moves(m, ps):   # an orbit, a bob or an idle (AccessoryFx): only ever cleared at rest, so not tucked
        xp = f"{ROOT}/layout/{m}.extra.json"
        x = json.load(open(xp)) if os.path.exists(xp) else {}
        return any(k in x.get(p, {}) for p in ps for k in ("orbit", "bob", "idle"))
    items = [(m, ps) for m, ps in items if not moves(m, ps)]
    # which hairs each item refuses (any of its pieces "x")
    want = {}
    for m, ps in items:
        lay = json.load(open(f"{ROOT}/layout/{m}.json"))
        refused = set()
        for pn in ps:
            for h, v in (lay["pieces"].get(pn, {}).get("hair_fit") or {}).items():
                if v is None:
                    refused.add(h)
        todo = [h for h in hairs if ALL or h in refused]
        if todo:
            want[(m, tuple(ps))] = todo
    print(f"TUCK {sum(len(v) for v in want.values())} hair x item pairs over {len(want)} items")
    for h in hairs:
        its = [k for k, hs in want.items() if h in hs]
        if not its:
            continue
        hair = Hair(h)
        # every item this hair can wear today (by the layouts), as worn with it: the obstacles a tuck must keep clear of
        worn = {}
        for (m2, ps2) in all_items:
            lay2 = json.load(open(f"{ROOT}/layout/{m2}.json"))
            if any((lay2["pieces"].get(p, {}).get("hair_fit") or {}).get(h, "absent") is None for p in ps2):
                continue
            worn[(m2, ps2[0])] = (ps2, item_bvh(load_item(m2, ps2), h)[0])
        for (m, ps) in its:
            it = f"{m}.{ps[0]}"
            pieces = load_item(m, ps)
            bvh, fit = item_bvh(pieces, h)
            others = [b for (m2, p0), (ps2, b) in worn.items()
                      if (m2, p0) != (m, ps[0]) and C.slot_of(m2, p0) != C.slot_of(m, ps[0])
                      and not C.exclusive((m2, p0), (m, ps[0]))]
            rv, c0, c1 = solve(hair, bvh, others)
            ok = c1 == 0 and hair.last_strain[0] <= STRAIN_OK and hair.last_twist <= TWIST_OK and hair.last_exposed <= EXPOSE_OK
            part = {"model": m, "pieces": list(ps), "fit": fit, "ok": bool(ok), "crossings": [int(c0), int(c1)], "strain": round(hair.last_strain[0], 3),
                    "twist": round(hair.last_twist, 1), "bare": round(hair.last_exposed, 3),
                    "bones": {hair.bones[b]: [round(float(x), 4) for x in hair.handle_frame(q)]
                              for b, q in rv.items() if np.linalg.norm(q) > 1e-6}}
            os.makedirs(f"{OUT}/parts", exist_ok=True)
            json.dump(part, open(f"{OUT}/parts/{it}__{h}.json", "w"), indent=1)
            mx = max([np.degrees(np.linalg.norm(q)) for q in rv.values()] or [0])
            print(f"TUCK {it:16s} {h:36s} crossings {c0:5d} -> {c1:4d}  max bend {mx:4.0f} deg  strain {hair.last_strain[0]:.2f}  twist {hair.last_twist:3.0f}  bare {100 * hair.last_exposed:3.0f}%  {'OK' if ok else 'refused'}  [{time.time() - t0:.0f}s]", flush=True)
    print("TUCK done", f"{time.time() - t0:.0f}s")
    if RENDER:
        render(want)


def render(want):
    """before / after (back, three-quarter back, side) for every solved pair, on the standard mannequin"""
    os.makedirs(RENDER, exist_ok=True)
    A.HAIR_DIR = RIG
    A.RES = 420
    for (m, ps), hs in want.items():
        it = f"{m}.{ps[0]}"
        for h in hs:
            pp = f"{OUT}/parts/{it}__{h}.json"
            if not os.path.exists(pp):
                continue
            res = {h: json.load(open(pp))}
            hair = Hair(h)
            rv = {}
            for bn, q in res[h]["bones"].items():
                rv[hair.bi[bn]] = hair.Rimp @ (M1.T @ np.array(q))     # handle frame -> char space
            after = hair.deform(rv)
            pieces = load_item(m, ps)
            bpy.ops.wm.read_factory_settings(use_empty=True)
            cam = A.stage()
            bpy.context.scene.cycles.samples = 20
            for ob in A.mannequin("standard"):
                if ob.name.startswith("Hair"):
                    bpy.data.objects.remove(ob)
            lay = json.load(open(f"{ROOT}/layout/{m}.json"))
            with bpy.data.libraries.load(f"{ROOT}/blend/{m}.blend", link=False) as (src, dst):
                dst.objects = [n for n in src.objects if n in ps]
            f = res[h]["fit"]
            for ob in dst.objects:
                bpy.context.scene.collection.objects.link(ob)
                for md in list(ob.modifiers):
                    if md.type == "ARMATURE":
                        ob.modifiers.remove(md)
                if lay["pieces"][ob.name]["mount"] == "Head":
                    ob.data.transform(ob.matrix_world); ob.matrix_world = ob.matrix_world.Identity(4)
                    worn = C.at_hair_fit(ob.name, [v.co.copy() for v in ob.data.vertices], f[0], f[1])
                    for v, w in zip(ob.data.vertices, worn):
                        v.co = w
            hm = A.real_hair(h)
            head_piece = any(p["mount"] == "Head" for p in pieces.values())
            tgt = (0, 0, 1.3) if head_piece else (0, 0, 0.8)
            shots = []
            for tag, P in (("before", hair.P), ("after", after)):
                hm.data.vertices.foreach_set("co", P.ravel())
                hm.data.update()
                for view in RVIEWS:
                    p = os.path.abspath(f"{RENDER}/{it}__{h}__{tag}_{view}.png")
                    A.shoot(cam, p, view, target=tgt, lens=110 if head_piece else 95, aspect=1.0)
                    shots.append(p)
            try:
                raise ImportError
                from PIL import Image
                ims = [Image.open(p).convert("RGB") for p in shots]
                w, hh = ims[0].size
                S = Image.new("RGB", (w * 3, hh * 2))
                for i, im in enumerate(ims):
                    S.paste(im, ((i % 3) * w, (i // 3) * hh))
                S.save(f"{RENDER}/{it}__{h}.jpg", quality=86)
                for p in shots:
                    os.remove(p)
            except ImportError:
                pass


if __name__ == "__main__":
    main()
