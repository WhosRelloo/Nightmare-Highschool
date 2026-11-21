-- leavedisc (2.35.0, task 9 fix round 1, I1): Tutorial.Leave's two ends of a running cut, on the REAL server modules.
-- Run on the Server (rbxc luau ... Server @leavedisc.lua) in Play with a client in the game; it makes a temporary Script
-- (so the game's modules are required in the game VM, not a rogue copy), and takes ~30 s:
--   A  Leave(P, "Left")  (the disconnect path)   -> cut ends, OnFinish How "Left", NOT marked Seen (state stays "Started")
--   A2 Leave(P, "Left") again / Cine.EndFor      -> no-op (order independent with Cine's own PlayerRemoving)
--   B  Leave(P)          (a deliberate leave)    -> cut ends, OnFinish How "Aborted", NOT marked Seen
-- The cut starts "unseen" (CineMark nil). Afterwards the cut's state is put back to nil and NHTutorial is cleared.
local S = Instance.new("Script")
S.Source = [[
local P = game.Players:GetPlayers()[1]
local H = game:GetService("HttpService")
local SSS = game.ServerScriptService.Services
local Cine = require(SSS.World.Cine)
local Tut = require(SSS.World.Tutorial)
local Quests = require(SSS.Quests.Quests)
local CUT = "__BeatHoldTest"
local Out, Pass = {}, true
local function check(Ok, Text) Pass = Pass and Ok table.insert(Out, (Ok and "ok   " or "FAIL ") .. Text) end
local function state() local C = Quests.CineState(P) return C and C[CUT] end
local function run(Label, Why, ExpectHow)
	Quests.CineState(P)[CUT] = nil
	Tut.Enter(P)
	local How, Calls = nil, 0
	local Id = Cine.Play({ P }, CUT, { OnFinish = function(_, H) How = H Calls += 1 end })
	check(Id ~= nil and Cine.IsWatching(P, CUT), Label .. " cut started")
	task.wait(6) -- into the beat
	Tut.Leave(P, Why)
	task.wait(0.5)
	check(not Cine.IsWatching(P, CUT), Label .. " session ended")
	check(How == ExpectHow and Calls == 1, Label .. " OnFinish How=" .. tostring(How) .. " x" .. Calls .. " (want " .. ExpectHow .. " x1)")
	check(not Cine.Seen(P, CUT) and state() == "Started", Label .. " not marked Seen (state " .. tostring(state()) .. ")")
	check(P:GetAttribute("NHTutorial") == nil, Label .. " NHTutorial cleared")
	Tut.Leave(P, Why); Cine.EndFor(P, "Left") -- no session left: no-ops, no second OnFinish
	check(Calls == 1 and not Cine.Seen(P, CUT), Label .. " second leave / EndFor is a no-op")
end
local Ok, Err = pcall(function()
	run("A", "Left", "Left")
	task.wait(16) -- the client plays the rest of the cut out on its own clock (Left tells it nothing)
	run("B", nil, "Aborted")
	task.wait(3)
	Quests.CineState(P)[CUT] = nil
end)
if not Ok then Pass = false table.insert(Out, "ERROR " .. tostring(Err)) end
script:SetAttribute("R", (Pass and "PASS" or "FAIL") .. "\n" .. table.concat(Out, "\n"))
]]
S.Parent = game.ServerScriptService
local T0 = os.clock()
repeat task.wait(0.5) until S:GetAttribute("R") or os.clock() - T0 > 60
local R = S:GetAttribute("R")
S:Destroy()
return R or "TIMEOUT"
