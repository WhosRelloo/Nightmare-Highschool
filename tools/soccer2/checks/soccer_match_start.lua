-- soccer_match_start (soccer-2.0, Server, Play): a solo test match at the Pitch for the first player (the staff
-- console's MatchStart path), then waits for Live.
local M = require(game.ServerScriptService.Services.Sports.Matches)
local P = game.Players:GetPlayers()[1]
local ok, err = M.ForceStart("Pitch", { P }, {}, true)
if ok == false and err ~= nil then return "FAIL ForceStart: " .. tostring(err) end
local m = M.Get("Pitch")
local T0 = os.clock()
while m and m.Phase ~= "Live" and os.clock() - T0 < 25 do task.wait(0.25) end
if not (m and m.Phase == "Live") then return "FAIL phase " .. tostring(m and m.Phase) end
return "PASS live, InSport=" .. tostring(P:GetAttribute("InSport"))
