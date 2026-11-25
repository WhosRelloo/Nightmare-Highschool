-- soccer_match_end (soccer-2.0, Server, Play): ends the Pitch match and waits until the player is out of it.
local M = require(game.ServerScriptService.Services.Sports.Matches)
local P = game.Players:GetPlayers()[1]
local m = M.Get("Pitch")
if m and m.Phase ~= "Waiting" and m.Phase ~= "Ended" then m:End(nil, "Soccer 2.0 check") end
local T0 = os.clock()
while P:GetAttribute("InSport") and os.clock() - T0 < 20 do task.wait(0.25) end
return if P:GetAttribute("InSport") then "FAIL still InSport" else "PASS ended"
