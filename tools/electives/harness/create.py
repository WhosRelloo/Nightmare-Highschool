"""Create new scripts in NH Combat Test (Edit) from live/<Dotted.Path>.luau. Refuses if the path already exists.
usage: python -X utf8 -I create.py <ModuleScript|Script|LocalScript> <Dotted.Path> [...]"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = os.path.join(os.path.dirname(HERE), "live")
cls = sys.argv[1]
bad = 0
for p in sys.argv[2:]:
    src = open(os.path.join(LIVE, p + ".luau"), encoding="utf-8", newline="").read()
    n = 2
    while ("]" + "=" * n + "]") in src: n += 1
    o, c = "[" + "=" * n + "[", "]" + "=" * n + "]"
    segs = p.split(".")
    lua = ('local N = game for _, S in {%s} do N = N and N:FindFirstChild(S) end\n'
           'if not N then return "NOPARENT" end\n'
           'if N:FindFirstChild("%s") then return "EXISTS" end\n'
           'local Src = %s\n%s%s\n'
           'local Ok, Err = loadstring(Src) if not Ok then return "PARSE " .. tostring(Err) end\n'
           'local M = Instance.new("%s") M.Name = "%s" M.Source = Src M.Parent = N return "CREATED " .. M:GetFullName()'
           % (", ".join('"%s"' % s for s in segs[:-1]), segs[-1], o, src, c, cls, segs[-1]))
    f = os.path.join(HERE, "_create.lua")
    open(f, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + f], capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or r.stderr).strip()
    print(p, out[:300])
    if "CREATED" not in out: bad += 1
sys.exit(1 if bad else 0)
