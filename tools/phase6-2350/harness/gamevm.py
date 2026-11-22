"""Run Luau inside the running game (Play mode) rather than the MCP sandbox, whose requires are separate fresh copies.
usage: python -X utf8 -I gamevm.py <file.lua>
The file is a function body: it may use P (the first player) and must `return` a string (or anything tostring-able).
It runs as a temporary Script in ServerScriptService, so `require` returns the game's live modules."""
import os, subprocess, sys
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
HERE = os.path.dirname(os.path.abspath(__file__))
body = open(sys.argv[1], encoding="utf-8").read()
n = 2
while ("]" + "=" * n + "]") in body: n += 1
o, c = "[" + "=" * n + "[", "]" + "=" * n + "]"
src = """local S = Instance.new("Script")
S.Source = %s
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
%s
end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
%s
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)""" % (o, body, c)
tmp = os.path.join(HERE, "_gamevm.lua")
open(tmp, "w", encoding="utf-8").write(src)
r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Server", "@" + tmp],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.replace("\r", "").strip())
