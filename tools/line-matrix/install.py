"""Install one repo file into Roblox Studio (NH line matrix).

Usage: python tools/line-matrix/install.py <source.luau> <Instance.Path> [ModuleScript|Script|LocalScript]
Prints a Luau snippet. Run it with the Roblox Studio execute_luau tool, datamodel "Edit". It creates or replaces the
script, then checks its Source against the file's checksum (h = (h*31 + byte) % 1000000007, CRLF -> LF).
The source travels inside the snippet, so no shared install buffer is used.
"""
import pathlib
import sys

src = pathlib.Path(sys.argv[1]).read_bytes().replace(b"\r\n", b"\n")
path = sys.argv[2]
cls = sys.argv[3] if len(sys.argv) > 3 else "ModuleScript"
h = 0
for b in src:
    h = (h * 31 + b) % 1000000007
text = src.decode("utf-8")
eq = "="
while "]" + eq + "]" in text:
    eq += "="
parts = path.split(".")
if parts[0] == "game":
    parts = parts[1:]
parts_lua = ", ".join('"' + p + '"' for p in parts)
print("assert(not game:GetService('RunService'):IsRunning(), 'Studio is in Play mode: install in Edit only')")
print("local Src = [" + eq + "[")
print(text + "]" + eq + "]")
print("local Parts = { " + parts_lua + " }")
print("local CLS, SUM = '" + cls + "', " + str(h))
print("""local Node = game:GetService(Parts[1])
for I = 2, #Parts - 1 do
	Node = Node:FindFirstChild(Parts[I]) or error(`missing {Parts[I]} under {Node:GetFullName()}`)
end
local Name = Parts[#Parts]
local S = Node:FindFirstChild(Name)
if S and not S:IsA(CLS) then error(`{S:GetFullName()} is a {S.ClassName}, not a {CLS}`) end
if not S then S = Instance.new(CLS) S.Name = Name S.Parent = Node end
S.Source = Src
local H = 0
local Got = S.Source
for I = 1, #Got do H = (H * 31 + string.byte(Got, I)) % 1000000007 end
assert(H == SUM, `checksum {H} ~= {SUM}`)
return `installed {S:GetFullName()}: {#Got} b, checksum {H}`""")
