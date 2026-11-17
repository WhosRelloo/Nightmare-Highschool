local RS = game:GetService("ReplicatedStorage")
local Prompt = require(game.Players.LocalPlayer.PlayerScripts.Controllers.CinePrompt)
local Judge = require(RS.Functions.CineJudge)
local B = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
B.Name = "NHCineTestInput"
B.Parent = RS
local Results = {}
local function run(P, Feed)
	local Got = nil
	Prompt.Open(P, { Reduced = false; Touch = false }, function(Input) Got = Input end)
	Feed()
	local T0 = os.clock()
	while not Got and os.clock() - T0 < 6 do task.wait(0.03) end
	return Got and table.pack(Judge.Evaluate(P, Got)) or { "no close" }
end
local r1 = run({ kind = "Press"; at = 0; beat = 0.6; on = {} }, function() task.wait(0.6) B:Fire({ Kind = "Down" }) end)
local r2 = run({ kind = "Direction"; at = 0; dur = 0.9; options = { "Left", "Right" }; answer = "Right"; on = {} }, function() task.wait(0.3) B:Fire({ Kind = "Pick"; Id = "Right" }) end)
local r3 = run({ kind = "Mash"; at = 0; dur = 1.0; rate = 7; on = {} }, function() for i = 1, 9 do task.wait(0.1) B:Fire({ Kind = "Down" }) end end)
local r4 = run({ kind = "Hold"; at = 0; zoneAt = 0.8; zone = 0.15; on = {} }, function() task.wait(0.1) B:Fire({ Kind = "Down" }) task.wait(0.7) B:Fire({ Kind = "Up" }) end)
local r5 = run({ kind = "Press"; at = 0; beat = 0.6; on = {} }, function() end)
B:Destroy()
return string.format("press %s | dir %s | mash %s | hold %s | press-none %s", tostring(r1[1]), tostring(r2[1]), tostring(r3[1]), tostring(r4[1]), tostring(r5[1]))
