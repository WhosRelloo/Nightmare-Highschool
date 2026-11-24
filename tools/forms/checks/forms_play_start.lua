-- forms Play check (server, game VM via harness/server.py): set the Player's Race ATTRIBUTE only (the profile is not
-- touched), then transform through the real service. Usage: edit RACE / LOOKS, run, then read the client.
local RACE, LOOKS = "Wraith", "FormDirection=2"
local P = game.Players:GetPlayers()[1]
local T = require(game.ServerScriptService.Services.Features.Transformation)
local C = P.Character
if T.IsActive and T.IsActive(C) then T.Stop(C) task.wait(0.5) end
P:SetAttribute("TransformReadyAt", nil)
P:SetAttribute("Race", RACE)
P:SetAttribute("RaceTier", 1)
P:SetAttribute("RaceLooks", LOOKS)
task.wait(0.5)
local ok, msg = T.Start(C)
task.wait(1.5)
return "start " .. tostring(ok) .. " " .. tostring(msg) .. " | Transformation=" .. tostring(C:GetAttribute("Transformation"))
