"""Set .Source in place on existing scripts (keeps class, children, attributes), Edit mode.
usage: python -X utf8 -I install_inplace.py <orig_dir> <new_dir> <backup_name> <Dotted.Path> [...]
Refuses everything if any live Source differs from <orig_dir>'s copy, or any new source fails to parse.
Pristine copies go to ServerStorage.NH_Backup.<backup_name> (the project's backup convention)."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
orig, new, bk = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_inplace.lua")


def bracket(*srcs):
    n = 2
    while any(("]" + "=" * n + "]") in s for s in srcs): n += 1
    return "[" + "=" * n + "[", "]" + "=" * n + "]"


def rd(d, p):
    return open(os.path.join(d, p + ".luau"), encoding="utf-8", newline="").read()


parts = ["local Items = {}"]
for p in sys.argv[4:]:
    a, b = rd(orig, p), rd(new, p)
    o, c = bracket(a, b)
    segs = ", ".join('"%s"' % s for s in p.split("."))
    # a long bracket drops one newline right after the opener: add one so the text is exact
    parts.append("table.insert(Items, { Name = \"%s\"; Path = {%s}; Old = %s\n%s%s; New = %s\n%s%s })" % (p, segs, o, a, c, o, b, c))
parts.append(r'''
local BK = "%s"
local Report = {}
local function find(Path)
	local Node = game:GetService(Path[1])
	for I = 2, #Path do
		Node = Node and Node:FindFirstChild(Path[I])
	end
	return Node
end
local function norm(S) return (string.gsub(S, "\r\n", "\n")) end
for _, It in Items do
	local Node = find(It.Path)
	if not (Node and Node:IsA("LuaSourceContainer")) then return "MISSING " .. It.Name end
	if norm(Node.Source) ~= norm(It.Old) then return "CHANGED SINCE FETCH " .. It.Name .. " (" .. #Node.Source .. " vs " .. #It.Old .. ")" end
	local Fn, Err = loadstring(It.New)
	if not Fn then return "PARSE FAIL " .. It.Name .. ": " .. tostring(Err) end
	It.Node = Node
end
local Root = game:GetService("ServerStorage"):FindFirstChild("NH_Backup")
if not Root then Root = Instance.new("Folder") Root.Name = "NH_Backup" Root.Parent = game:GetService("ServerStorage") end
local Folder = Root:FindFirstChild(BK)
if not Folder then Folder = Instance.new("Folder") Folder.Name = BK Folder.Parent = Root end
for _, It in Items do
	if not Folder:FindFirstChild(It.Name) then
		local B = Instance.new("ModuleScript")
		B.Name = It.Name
		B.Source = It.Old
		B.Parent = Folder
	end
	It.Node.Source = It.New
	table.insert(Report, It.Node:GetFullName() .. " " .. It.Node.ClassName .. " " .. #It.Node.Source)
end
return table.concat(Report, "\n")''' % bk)
open(OUT, "w", encoding="utf-8").write("\n".join(parts))
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + OUT], capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", ""), r.stderr[-2000:] if r.returncode else "")
bad = any(k in r.stdout for k in ("PARSE FAIL", "MISSING", "CHANGED SINCE"))
sys.exit(1 if bad or r.returncode else 0)
