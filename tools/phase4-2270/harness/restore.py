"""usage: python -X utf8 -I restore.py   (reads _slot2.json next to this file)"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
j = json.dumps(json.load(open(os.path.join(HERE, "_slot2.json"), encoding="utf-8")))
assert "]==]" not in j
lua = '''local J = [==[%s]==]
local S = Instance.new("Script")
S:SetAttribute("Json", J)
S.Source = [[
local H = game:GetService("HttpService")
local P = game.Players:GetPlayers()[1]
local ok, err = pcall(function()
	local SSS = game.ServerScriptService.Services
	local Data = require(SSS.Player.Data)
	local Disc = require(SSS.School.Discipline)
	local Snap = H:JSONDecode(script:GetAttribute("Json"))
	local Prof = Data.GetProfile(P)
	Prof.Quests = Snap.Quests
	Prof.Social = Prof.Social or {}
	Prof.Social.Relationships = Snap.Relationships or {} -- (2.27)
	require(SSS.Social.Reputation).Sync(P)
	require(SSS.Quests.Quests).SyncForCine(P)
	Data.UpdateState(P, { type = "UpdateYen"; amount = Snap.Yen - Prof.Yen })
	local ls = P:FindFirstChild("leaderstats") if ls and ls:FindFirstChild("Yen") then ls.Yen.Value = Prof.Yen end
	local D = Disc.GetData(P) for K, V in Snap.Discipline do D[K] = V end
	P:SetAttribute("DisciplineLevel", D.Level) P:SetAttribute("DisciplinePoints", D.Points) P:SetAttribute("DetentionsOwed", D.DetentionsOwed)
end)
script:SetAttribute("Out", ok and "restored" or ("ERR " .. tostring(err)))
]]
S.Parent = game.ServerScriptService
task.wait(1.5)
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)''' % j
tmp = os.path.join(HERE, "_restore.lua")
open(tmp, "w", encoding="utf-8").write(lua)
print(subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", "placeId: 98950102230473", "Server", "@" + tmp], capture_output=True, text=True, encoding="utf-8").stdout)
