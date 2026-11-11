"""Drop the hair tucks acc_tuckcheck.py found unsafe, so the hair stays refused for that item instead.

python acc_tuckprune.py <tuckcheck.json> [--root E:/NH-Work/acc]

For each failure:
  SINGLE  hair x item: that item refuses the hair
  PAIR    two items worn together: if only one of them is tucked for this hair, that one refuses it; if both are,
          the one with the larger turn does
  SWAY    hair x item: that item refuses the hair
Adds to <root>/tuck/drop.json ({ "<Model>.<Lead>": [hair, ...] }), which acc_tuckmerge.py reads. Then restore the
layouts' hair_fit (layout backups from before the merge), run acc_tuckmerge.py and acc_tuckcheck.py again, and repeat
until the check finds nothing.
"""
import json, os, re, sys

args = sys.argv[1:]
ROOT = args[args.index("--root") + 1] if "--root" in args else "E:/NH-Work/acc"
fails = json.load(open(args[0]))["fails"]
dp = os.path.join(ROOT, "tuck", "drop.json")
drop = json.load(open(dp)) if os.path.exists(dp) else {}


def tuck(key, hair):
    p = os.path.join(ROOT, "tuck", f"{key}.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p))["hairs"].get(hair)
    return r["bones"] if r and r.get("bones") else None


def size(bones):
    return max((sum(x * x for x in v) ** 0.5 for v in bones.values()), default=0)


n = 0
for f in fails:
    m = re.match(r"(SINGLE|SWAY) (\S+) (\S+?)(?::| \()", f)
    if m:
        _, h, key = m.groups()
        targets = [key]
    else:
        m = re.match(r"PAIR (\S+) (\S+) \+ (\S+):", f)
        if not m:
            print("TUCKPRUNE ? ", f)
            continue
        h, a, b = m.groups()
        ta, tb = tuck(a, h), tuck(b, h)
        if ta and tb:
            targets = [a if size(ta) >= size(tb) else b]
        else:
            targets = [k for k, t in ((a, ta), (b, tb)) if t]
    for k in targets:
        if h not in drop.setdefault(k, []):
            drop[k].append(h)
            n += 1
json.dump(drop, open(dp, "w"), indent=1, sort_keys=True)
print(f"TUCKPRUNE {n} new drops ({sum(len(v) for v in drop.values())} in all)")
