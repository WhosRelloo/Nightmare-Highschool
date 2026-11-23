"""R8: copy the bake manifest's lengths and carry curves into live/ReplicatedStorage.Config.Gestures.luau (in place).
usage: python -X utf8 anim/sync_config.py"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(HERE, "..", "live", "ReplicatedStorage.Config.Gestures.luau")
man = json.load(open(os.path.join(HERE, "out", "manifest.json"), encoding="utf-8"))
s = open(CFG, encoding="utf-8").read()
bases = {}
for name, e in man.items():
    bases.setdefault(e.get("base", name), e)
n = 0
for base, e in bases.items():
    pat = re.compile(r"(\n\t" + re.escape(base) + r" = \{[^\n]*?Len = )([0-9.]+)")
    s, k = pat.subn(lambda m: m.group(1) + ("%g" % e["Len"]), s)
    n += k
    if "Carry" in e:
        curve = "{ " + ", ".join("{ %g, %g, %g, %g }" % tuple(r) for r in e["Carry"]) + " }"
        s = re.sub(r"(\n\t" + re.escape(base) + r" = \{[^\n]*?Carry = )(nil|\{[^\n]*?\} \})", lambda m: m.group(1) + curve, s)
open(CFG, "w", encoding="utf-8", newline="\n").write(s)
print("lengths set:", n, "of", len(bases))
