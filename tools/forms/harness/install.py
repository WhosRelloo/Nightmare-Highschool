"""Install mirror files into NH Combat Test (Edit mode) as fresh ModuleScripts.
usage: python -X utf8 -I install.py <file.luau> [...]   (paths to tools/quietcorners/live/<dotted path>.luau)"""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_install.lua")

def bracket(src):
    n = 2
    while ("]" + "=" * n + "]") in src: n += 1
    return "[" + "=" * n + "[", "]" + "=" * n + "]"

parts = ["local Report = {}", "local Items = {}"]
for f in sys.argv[1:]:
    segs = os.path.basename(f)[:-len(".luau")].split(".")
    src = open(f, encoding="utf-8").read()
    o, c = bracket(src)
    parts.append("table.insert(Items, { Path = {%s}; Source = %s\n%s%s })" % (", ".join('"%s"' % s for s in segs), o, src, c))
parts.append(r'''
for _, It in Items do
	local Fn, Err = loadstring(It.Source)
	if not Fn then return "PARSE FAIL " .. table.concat(It.Path, ".") .. ": " .. tostring(Err) end
end
for _, It in Items do
	local Node = game:GetService(It.Path[1])
	for I = 2, #It.Path - 1 do
		local Next = Node:FindFirstChild(It.Path[I])
		if not Next then Next = Instance.new("Folder") Next.Name = It.Path[I] Next.Parent = Node end
		Node = Next
	end
	local Name = It.Path[#It.Path]
	local Old = Node:FindFirstChild(Name)
	local New = Instance.new("ModuleScript")
	New.Name = Name
	New.Source = It.Source
	New.Parent = Node
	if Old then for _, K in Old:GetChildren() do K.Parent = New end Old:Destroy() end
	table.insert(Report, New:GetFullName() .. " " .. #New.Source)
end
return table.concat(Report, "\n")''')
open(OUT, "w", encoding="utf-8").write("\n".join(parts))
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + OUT], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""), r.stderr[-2000:] if r.returncode else "")
sys.exit(1 if "PARSE FAIL" in r.stdout or r.returncode else 0)
