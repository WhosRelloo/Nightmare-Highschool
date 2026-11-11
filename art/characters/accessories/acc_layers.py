"""Keep the torso layers in order on every body: python acc_layers.py [--root E:/NH-Work/acc]

Each piece's depth fit (layout fit_body: a scale of its depth about the torso's centre plane, per body type) is measured
on its own, so on a bust or a belly an inner piece (a tie) could be pushed further out than an outer one (a bag strap)
and pass through it. This makes every outer layer scale at least as much as the inner layers on each body, the way an
outer strap drapes over what's under it. Layers, inner to outer:
  shirt  the school tie, the bow tie, the clique pins, the choir collar, the falling ruff, the gorget
  sash   the Prefect and Head Student sashes, the hunter's bandolier
  strap  the satchel's, the messenger bag's and the crossbow's straps (and the bags)
  wrap   the knitted scarves (their tails lie over the straps)
"""
import json, os, sys

args = sys.argv[1:]
ROOT = args[args.index("--root") + 1] if "--root" in args else "E:/NH-Work/acc"
LAYERS = [
    ("shirt", [("SchoolTie", "SchoolTie"), ("BowTie", "BowTie"), ("ChoirCollar", "ChoirCollar"), ("Ruff", "Ruff"),
               ("Gorget", "Gorget")] +
     [("CliquePins", f"Pin{k}") for k in ("Vigil", "Court", "Athletes", "Delinquents", "Pack", "Ordinary", "Choir", "Ink")]),
    ("sash", [("Sashes", "PrefectSash"), ("Sashes", "HeadSash"), ("Bandolier", "Bandolier")]),
    ("strap", [("Satchel", "Satchel"), ("MessengerBag", "MessengerStrap"), ("Crossbow", "CrossbowStrap")]),
    ("wrap", [("Scarves", "ScarfStripe"), ("Scarves", "ScarfViolet")]),
]
if __name__ != "__main__":
    raise SystemExit   # imported for LAYERS only (acc_check.py --fixlayers does the measured version)
lays = {}
for _, members in LAYERS:
    for it, _p in members:
        p = os.path.join(ROOT, "layout", f"{it}.json")
        if os.path.exists(p) and it not in lays:
            lays[it] = json.load(open(p))
floor = {}   # body -> the largest scale of the layers so far
changed = []
for name, members in LAYERS:
    here = {}
    for it, pn in members:
        e = lays.get(it, {}).get("pieces", {}).get(pn)
        if not e:
            continue
        fb = e.setdefault("fit_body", {})
        for bid in set(fb) | set(floor):
            s0 = fb.get(bid, 1.0)
            s = max(s0, floor.get(bid, 0.0))
            if s != s0:
                changed.append(f"{it}/{pn} {bid}: {s0} -> {s}")
                fb[bid] = s
            here[bid] = max(here.get(bid, 0.0), s)
    for bid, s in here.items():
        floor[bid] = max(floor.get(bid, 0.0), s)
for it, lay in lays.items():
    json.dump(lay, open(os.path.join(ROOT, "layout", f"{it}.json"), "w"), indent=1)
print("LAYERS", len(changed), "raised")
for c in changed:
    print("LAYERS ", c)
