"""Run a pure check in a VM with no HTTP: inlines every live/*.luau the check names in load("...") as __SRC.
usage: python -X utf8 -I pure.py <check.lua> [Edit|Server|Client]   (writes nothing in the place; the check only computes)"""
import os, re, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(os.path.dirname(HERE), "live")
check = open(sys.argv[1], encoding="utf-8").read()
vm = sys.argv[2] if len(sys.argv) > 2 else "Edit"
names = sorted(set(re.findall(r'load\("([^"]+\.luau)"\)', check)))
def bracket(src):
    n = 2
    while ("]" + "=" * n + "]") in src: n += 1
    return "[" + "=" * n + "[", "]" + "=" * n + "]"
pre = ["local __SRC = {}"]
for n in names:
    src = open(os.path.join(LIVE, n), encoding="utf-8").read()
    o, c = bracket(src)
    pre.append('__SRC["%s"] = %s\n%s%s' % (n, o, src, c))
out = os.path.join(HERE, "_pure.lua")
open(out, "w", encoding="utf-8").write("\n".join(pre) + "\n" + check)
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, vm, "@" + out], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", "") or r.stderr)
