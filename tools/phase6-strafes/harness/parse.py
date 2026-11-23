"""Parse-check every live/*.luau (and build/*.luau) with loadstring in a VM. Compiles only; runs nothing, writes nothing.
usage: python -X utf8 -I parse.py [files...]"""
import glob, os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "live", "*.luau")) + glob.glob(os.path.join(ROOT, "build", "*.luau")))
def bracket(src):
    n = 2
    while ("]" + "=" * n + "]") in src: n += 1
    return "[" + "=" * n + "[", "]" + "=" * n + "]"
fails, ok = [], 0
for i in range(0, len(files), 6):
    parts = ["local R = {}"]
    for f in files[i:i + 6]:
        src = open(f, encoding="utf-8").read()
        o, c = bracket(src)
        parts.append('do local Fn, Err = loadstring(%s\n%s%s) if not Fn then table.insert(R, "%s: " .. tostring(Err)) end end' % (o, src, c, os.path.basename(f)))
    parts.append('return #R == 0 and "OK" or table.concat(R, string.char(10))')
    tmp = os.path.join(HERE, "_parse.lua")
    open(tmp, "w", encoding="utf-8").write("\n".join(parts))
    out = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Edit", "@" + tmp], capture_output=True, text=True, encoding="utf-8").stdout.strip()
    if out == "OK": ok += len(files[i:i + 6])
    else: fails.append(out)
print("PASS parse %d" % ok if not fails else "FAIL parse\n" + "\n".join(fails))
