"""Pieces worn together share one hair fit (a hat and its veil must scale and lift together, or they'd part).

python acc_hairgroup.py [--root E:/NH-Work/acc]

For every item of several pieces (`Pieces = { ... }` in Config.Accessories or a pending fragment), each hair's fit
becomes the larger scale and the larger lift of its pieces' fits, and "no fit" (null) if any piece has none. Run after
acc_hairfit.py. First it applies <root>/hair_overrides.json (hairs measured to cross a piece the
game's way). acc_hairfit searches the smallest scale and lift with no strand through a piece; a larger scale about
the headband and a higher lift only take the piece further from the hair, so the merged fit stays clear for both.
"""
import json, os, re, sys

args = sys.argv[1:]
ROOT = args[args.index("--root") + 1] if "--root" in args else "E:/NH-Work/acc"
texts = []
p = "E:/NH-Work/acc/src/Accessories.luau"
if os.path.exists(p):
    texts.append(open(p, encoding="utf-8").read())
pend = "E:/NH-Work/acc/src/pending"
for f in sorted(os.listdir(pend)) if os.path.isdir(pend) else []:
    if f.endswith(".luau"):
        texts.append(open(os.path.join(pend, f), encoding="utf-8").read())
# hairs ruled out by a measurement acc_hairfit doesn't make (the game's way of wearing it, an orbit's spin)
op = os.path.join(ROOT, "hair_overrides.json")
for key, hairs in (json.load(open(op)) if os.path.exists(op) else {}).items():
    if key == "note":
        continue
    it, pn = key.split("/")
    lp = os.path.join(ROOT, "layout", f"{it}.json")
    if not os.path.exists(lp):
        continue
    lay = json.load(open(lp))
    f = lay["pieces"].get(pn, {}).get("hair_fit")
    if f is None:
        continue
    for h in hairs:
        f[h] = None
    json.dump(lay, open(lp, "w"), indent=1)
    print(f"HAIRGROUP override {key}: not with {len(hairs)} hairs")
groups = []
for t in texts:
    for m in re.finditer(r"Model = `(\w+)`; Pieces = \{([^}]*)\}", t):
        groups.append((m.group(1), re.findall(r"`(\w+)`", m.group(2))))
for model, names in groups:
    lp = os.path.join(ROOT, "layout", f"{model}.json")
    if not os.path.exists(lp):
        continue
    lay = json.load(open(lp))
    fits = [lay["pieces"][n].get("hair_fit") for n in names if n in lay["pieces"]]
    if len(fits) < 2 or any(f is None for f in fits):
        print("HAIRGROUP skip", model, names, "(a piece has no hair fit yet)")
        continue
    merged = {}
    for h in set().union(*[f.keys() for f in fits]):
        vals = [f.get(h) for f in fits]
        if any(v is None for v in vals):
            merged[h] = None
        else:
            merged[h] = [round(max(v[0] for v in vals), 3), round(max(v[1] for v in vals), 3)]
    for n in names:
        lay["pieces"][n]["hair_fit"] = merged
    json.dump(lay, open(lp, "w"), indent=1)
    ok = sum(1 for v in merged.values() if v is not None)
    print(f"HAIRGROUP {model} {'+'.join(names)}: {ok}/{len(merged)} hairs")
