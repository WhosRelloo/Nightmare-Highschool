-- soccer_clips_resolve (soccer-2.0 Task 3, Edit): every Config.Sports.SoccerAnims slot resolves as spec §2 says.
-- usage: python -X utf8 -I tools/admin-console/run_check.py Edit tools/soccer2/checks/soccer_clips_resolve.lua
local RS = game:GetService("ReplicatedStorage")
local Mod = game:GetService("StarterPlayer").StarterPlayerScripts.Controllers.Gui.Soccer:FindFirstChild("Clips")
if not Mod then return "FAIL no Controllers.Gui.Soccer.Clips" end
local Clips = require(Mod)
local Cfg = require(RS.Config.Sports).SoccerAnims
local Fails = {}
local FIER = { "KickRun", "Kick", "Pass", "Volley", "Dribble", "Feint", "Tackle", "Tackled", "Tackled2", "Trip", "Fallen",
	"KeeperDiveLeft", "KeeperDiveRight", "KeeperCatch", "KeeperCatchIdle", "Idle", "IdleBall", "KeeperIdle", "Jog", "JogBack",
	"KeeperStepLeft", "KeeperStepRight", "Chip", "Stall", "Penalty" }
for _, S in FIER do
	local Id, Fier = Clips.Id(S)
	if not (Id and Fier) then table.insert(Fails, S .. " doesn't resolve to its FIER clip (" .. tostring(Id) .. ")") end
	if not Clips.Clip(S) then table.insert(Fails, S .. " has no clip data") end
end
local Id, Fier = Clips.Id("KeeperThrow")
if Id ~= "rbxassetid://126461164655749" or Fier then table.insert(Fails, "KeeperThrow resolves to " .. tostring(Id)) end
if (Clips.Id("Celebrate")) ~= "rbxassetid://73569467689521" then table.insert(Fails, "Celebrate resolves to " .. tostring((Clips.Id("Celebrate")))) end
if Clips.Id("Header") ~= nil then table.insert(Fails, "Header should have no clip") end
if not (Cfg.Tackle and Cfg.Tackle.Was == 98978935956373) then table.insert(Fails, "Tackle lost its 1.1 clip (Was)") end
local K = Clips.Clip("Kick")
if not (K and math.abs((K.ContactAt or 0) - 0.23) < 1e-3) then table.insert(Fails, "Kick ContactAt") end
local Sp = Clips.Clip("Dribble")
if not (Sp and Sp.Path) then table.insert(Fails, "Dribble has no Path") end
for S, E in Cfg do if type(E) ~= "table" then table.insert(Fails, S .. " is still a bare " .. type(E)) end end
if #Fails > 0 then return "FAIL soccer_clips_resolve\n" .. table.concat(Fails, "\n") end
return "PASS soccer_clips_resolve"
