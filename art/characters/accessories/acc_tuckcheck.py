"""Check the hair tucks as the game wears them: every hair against every item it can wear, alone and in pairs, with
the tucks merged the way UI.AccessoryWear merges them (per bone, the larger turn), and with HairSway's sway on top.

E:/Blender/blender.exe -b --factory-startup -P acc_tuckcheck.py -- [--hairs H1,H2] [--json out.json]

For each hair:
  single  each item it can wear (hair_fit not null), with that item's tuck (if any): no hair triangle crosses it
  pairs   every two items of different slots that can be worn together (Config.Accessories.Conflicts), at least one
          of them tucked for this hair: the merged tuck clears both
  sway    with the merged tuck, each tucked lock swung at full drag (back, left, right, up) at HairSway's TUCK_SWAY
          share of MAX_BEND (capped at MAX_JOINT per joint): still clear of the worn items. TUCK_SWAY is 0 (a tucked
          lock rests on the piece and holds still; at 0.35, 73% of the tucks swung back into their piece)
Items are worn on the standard body (and torso / arm pieces at their shallowest and deepest body fits too), head
pieces at the hair's fit. Prints every failure and "TUCKCHECK done <n> fails".
"""
import bpy, sys, os, json, itertools, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HAIRS = argv[argv.index("--hairs") + 1].split(",") if "--hairs" in argv else None
OUTJ = argv[argv.index("--json") + 1] if "--json" in argv else None
import acc_check as C
import acc_hairtuck as T

MAX_BEND, MAX_JOINT, TUCK_SWAY = math.radians(50), math.radians(15), 0.0   # Controllers.Character.HairSway (a tucked lock holds still)


def tuck_of(model, lead, hair):
    p = f"{T.ROOT}/tuck/{model}.{lead}.json"
    if not os.path.exists(p):
        return None
    return json.load(open(p))["hairs"].get(hair)


def rot_from_handle(hair, bones):
    return {hair.bi[b]: hair.Rimp @ (T.M1.T @ np.array(v)) for b, v in bones.items()}


def merged(hair, tucks):
    out = {}
    for t in tucks:
        for b, q in t.items():
            if b not in out or np.linalg.norm(q) > np.linalg.norm(out[b]):
                out[b] = q
    return out


def shares(hair):
    """HairSway's share of the bend per bone: (depth - 1) / (1 + 2 + ... + (N - 1)), N the deepest bone under HairRoot"""
    depth = {}
    for b in range(len(hair.bones)):
        d, p = 1, hair.parent[b]
        while p >= 0:
            d += 1
            p = hair.parent[p]
        depth[b] = d
    N = max(depth.values())
    S = (N - 1) * N / 2
    return {b: ((d - 1) / S if d > 1 and S > 0 else 0) for b, d in depth.items()}


def with_sway(hair, rv, pull, share):
    """the tuck plus HairSway's bend toward pull (char space) on the tucked locks"""
    tucked = set()
    for ln, ids in hair.locks.items():
        if any(b in rv for b in ids):
            tucked.update(ids)
    out = dict(rv)
    for b in tucked:
        d = hair.dir[b]
        ax = np.cross(d, pull)
        n = np.linalg.norm(ax)
        if n < 1e-4:
            continue
        ang = min(min(n, 1) * MAX_BEND * share[b], MAX_JOINT) * TUCK_SWAY
        if ang < 1e-9:
            continue     # a tucked lock that holds still
        Rs = T.rotvec(ax / n * ang)
        Rt = T.rotvec(rv[b]) if b in rv and np.linalg.norm(rv[b]) > 1e-9 else np.eye(3)
        R = Rs @ Rt
        # back to a rotation vector
        th = math.acos(max(-1, min(1, (np.trace(R) - 1) / 2)))
        if th < 1e-9:
            out[b] = np.zeros(3)
        else:
            w = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]]) / (2 * math.sin(th))
            out[b] = w * th
    return out


def main():
    C.load_slots()
    C.load_conflicts()
    items = [(m, ps) for m, ps in T.game_items() if os.path.exists(f"{T.ROOT}/blend/{m}.blend")]
    hairs = HAIRS or sorted(f[:-4] for f in os.listdir(T.RIG) if f.endswith(".fbx"))
    fails, report = [], {}
    pulls = {"back": np.array([0, 1.0, 0]), "left": np.array([1.0, 0, 0]), "right": np.array([-1.0, 0, 0]), "up": np.array([0, 0, 1.0])}
    for h in hairs:
        hair = T.Hair(h)
        share = shares(hair)
        wearable = []
        for m, ps in items:
            lay = json.load(open(f"{T.ROOT}/layout/{m}.json"))
            if any((lay["pieces"].get(p, {}).get("hair_fit") or {}).get(h, "absent") is None for p in ps):
                continue   # the hair can't wear it (refused)
            r = tuck_of(m, ps[0], h)
            wearable.append((m, ps, rot_from_handle(hair, r["bones"]) if r else {}))
        bvhs = {}
        for m, ps, _ in wearable:
            pieces = T.load_item(m, ps)
            bvhs[(m, ps[0])] = T.item_bvh(pieces, h)[0]
        n_single = n_pair = n_sway = 0
        for m, ps, tk in wearable:
            P = hair.deform(tk) if tk else hair.P
            c = T.crossings(bvhs[(m, ps[0])], P, hair.tris)
            n_single += 1
            if c:
                fails.append(f"SINGLE {h} {m}.{ps[0]}: {c} crossings")
        for (ma, pa, ta), (mb, pb, tb) in itertools.combinations(wearable, 2):
            if not (ta or tb):
                continue
            sa, sb = C.slot_of(ma, pa[0]), C.slot_of(mb, pb[0])
            if sa == sb or C.exclusive((ma, pa[0]), (mb, pb[0])):
                continue
            rv = merged(hair, [ta, tb])
            P = hair.deform(rv)
            n_pair += 1
            for (m, p0) in ((ma, pa[0]), (mb, pb[0])):
                c = T.crossings(bvhs[(m, p0)], P, hair.tris)
                if c:
                    fails.append(f"PAIR {h} {ma}.{pa[0]} + {mb}.{pb[0]}: {c} crossings with {m}.{p0}")
        for m, ps, tk in wearable:
            if not tk:
                continue
            for name, pull in pulls.items():
                n_sway += 1
                P = hair.deform(with_sway(hair, tk, pull, share))
                c = T.crossings(bvhs[(m, ps[0])], P, hair.tris)
                if c:
                    fails.append(f"SWAY {h} {m}.{ps[0]} ({name}): {c} crossings")
        report[h] = dict(single=n_single, pairs=n_pair, sway=n_sway)
        print(f"TUCKCHECK {h:36s} items {n_single:3d}  pairs {n_pair:4d}  sway {n_sway:3d}  fails so far {len(fails)}", flush=True)
    for f in fails:
        print("TUCKCHECK FAIL", f)
    print("TUCKCHECK done", len(fails), "fails")
    if OUTJ:
        json.dump({"report": report, "fails": fails}, open(OUTJ, "w"), indent=1)


main()
