-- soccer_play_pack_respawn (soccer-2.0 Task 5, Server, Play, during a solo match): the player dies and respawns.
local P = game.Players:GetPlayers()[1]
local Old = P.Character
local Hum = Old and Old:FindFirstChildOfClass("Humanoid")
if not Hum then return "FAIL no character to kill" end
Hum.Health = 0
local T0 = os.clock()
while os.clock() - T0 < 15 do
	local C = P.Character
	if C and C ~= Old and C:FindFirstChildOfClass("Humanoid") and C:FindFirstChild("HumanoidRootPart") then return "PASS respawned" end
	task.wait(0.25)
end
return "FAIL no new character within 15s"
