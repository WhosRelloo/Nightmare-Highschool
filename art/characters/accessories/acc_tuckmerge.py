"""Gather the hair tucks (acc_hairtuck.py's tuck/parts/<Item>__<Hair>.json) into tuck/<Item>.json and open the hairs
they clear: a hair an item refused (hair_fit null on any of its pieces) is fitted again, at the fit the tuck was solved
for, when its tuck passed every check (no crossing, no crumpled or twisted cards, the head stays covered).

python acc_tuckmerge.py [--root E:/NH-Work/acc] [--dry]
tuck/<Model>.<LeadPiece>.json is one game item's tucks (acc_assemble puts it on that lead piece as NHHairTuck).

Run after acc_hairfit.py, acc_hairgroup.py and acc_hoodfit.py (they write hair_fit from scratch), then acc_assemble.py
writes each item's tuck onto its lead piece (NHHairTuck).
"""
import json, os, sys

args = sys.argv[1:]
ROOT = args[args.index("--root") + 1] if "--root" in args else "E:/NH-Work/acc"
DRY = "--dry" in args
parts = os.path.join(ROOT, "tuck", "parts")
by_item = {}
for f in sorted(os.listdir(parts)) if os.path.isdir(parts) else []:
    if f.endswith(".json") and "__" in f:
        it, h = f[:-5].split("__", 1)
        by_item.setdefault(it, {})[h] = json.load(open(os.path.join(parts, f)))
opened = closed = 0
# tucks acc_tuckcheck.py found unsafe with another item worn with them: { "<Model>.<Lead>": [hair, ...] }
dp = os.path.join(ROOT, "tuck", "drop.json")
DROP = json.load(open(dp)) if os.path.exists(dp) else {}
for it, res in sorted(by_item.items()):
    # it = "<Model>.<lead piece>": one game item (the pieces worn together)
    any_r = next(iter(res.values()))
    model = any_r.get("model") or it.split(".")[0]
    names = any_r.get("pieces") or [it.split(".", 1)[1]]
    out = {h: ({"fit": r["fit"], "bones": r["bones"]} if r.get("ok") and h not in DROP.get(it, ()) else None)
           for h, r in sorted(res.items())}
    # a piece that moves on its own (an orbit, a bob, an idle: AccessoryFx) was only cleared at rest: keep its refusals
    xp = os.path.join(ROOT, "layout", f"{model}.extra.json")
    extra = json.load(open(xp)) if os.path.exists(xp) else {}
    moving = [pn for pn in names if any(k in extra.get(pn, {}) for k in ("orbit", "bob", "idle"))]
    if moving:
        print(f"TUCKMERGE {it:16s} skipped: {', '.join(moving)} moves on its own (cleared at rest only)")
        continue
    lp = os.path.join(ROOT, "layout", f"{model}.json")
    lay = json.load(open(lp))
    n = 0
    for pn, e in lay["pieces"].items():
        if pn not in names:
            continue
        hf = e.get("hair_fit")
        if hf is None:
            continue
        for h, r in out.items():
            if r and hf.get(h, "absent") is None:
                hf[h] = [1.0, 0.0] if e["mount"] != "Head" else [round(r["fit"][0], 3), round(r["fit"][1], 3)]
                n += 1
            elif r is None and hf.get(h) is not None and h in hf:
                hf[h] = None     # it crossed this hair on some body and no tuck clears it: refused now
                closed += 1
        # a hair the check found crossing this item, with or without a tuck: refused (a hair the fit passed untucked
        # has no tuck to drop)
        for h in DROP.get(it, ()):
            if h in hf:
                hf[h] = None
    ok = sum(1 for r in out.values() if r)
    print(f"TUCKMERGE {it:16s} {ok}/{len(out)} hairs cleared ({n} piece fits opened)")
    opened += ok
    if not DRY:
        json.dump({"pieces": names, "hairs": out}, open(os.path.join(ROOT, "tuck", f"{it}.json"), "w"), indent=1, sort_keys=True)
        json.dump(lay, open(lp, "w"), indent=1)
print("TUCKMERGE done", opened, "hair x item pairs cleared,", closed, "refused (they crossed on some body)")
