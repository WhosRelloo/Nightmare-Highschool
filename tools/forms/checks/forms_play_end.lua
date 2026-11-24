-- forms Play check, end of round (server, game VM via harness/server.py): stop the form through the real service and
-- put the Player's race attributes back to the slot's own (Human, tier 1, no looks); the profile was never touched.
local P = game.Players:GetPlayers()[1]
local T = require(game.ServerScriptService.Services.Features.Transformation)
local C = P.Character
if T.IsActive(C) then T.Stop(C) end
task.wait(1)
P:SetAttribute("Race", "Human")
P:SetAttribute("RaceTier", 1)
P:SetAttribute("RaceLooks", "")
P:SetAttribute("TransformReadyAt", nil)
task.wait(1)
local a = {}
for _, k in { "Race", "RaceTier", "RaceLooks", "TransformReadyAt", "CineState", "Seen", "Origin" } do
	table.insert(a, k .. "=" .. tostring(P:GetAttribute(k)))
end
return "Transformation=" .. tostring(C:GetAttribute("Transformation")) .. " | " .. table.concat(a, " ")
