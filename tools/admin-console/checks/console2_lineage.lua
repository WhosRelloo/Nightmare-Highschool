local L = require(game.ReplicatedStorage.Lineage:Clone())
local Fails = {}
local function Eq(Got, Want, What) if Got ~= Want then table.insert(Fails, What .. ": got " .. tostring(Got) .. ", want " .. tostring(Want)) end end
local W = workspace
local Old = { W:GetAttribute("NHMoonOverride"), W:GetAttribute("NHMoonOverrideNight") }
local ok, err = pcall(function()
	W:SetAttribute("NHMoonOverride", nil) W:SetAttribute("NHMoonOverrideNight", nil)
	-- no override: the cycle as before (night 1 Waning, night 2 New, night 4 Full; night 16 is the Blue event, night 32 Crimson)
	Eq(L.MoonPhase(1, 22), "Waning", "plain phase") Eq(L.MoonPhase(2, 22), "New", "plain night 2")
	Eq(L.IsFullMoon(4, 22), true, "plain full") Eq(L.MoonEvent(16, 22), "Blue", "plain event 16") Eq(L.MoonEvent(32, 22), "Crimson", "plain event 32")
	Eq(L.MoonOverride(1, 22), nil, "no override")
	-- tonight (night 1) is Full
	W:SetAttribute("NHMoonOverride", "Full") W:SetAttribute("NHMoonOverrideNight", 1)
	Eq(L.MoonPhase(1, 22), "Full", "override at 22:00") Eq(L.MoonPhase(2, 3), "Full", "still night 1 at 03:00 next day")
	Eq(L.MoonPhase(1, 12), "Full", "by day the coming night") Eq(L.IsFullMoon(1, 22), true, "override full")
	Eq(L.NightsUntilFull(1, 22), 0, "full tonight")
	Eq(L.MoonPhase(2, 22), "New", "the next night is back on the cycle")
	-- New is not full
	W:SetAttribute("NHMoonOverride", "New")
	Eq(L.MoonPhase(1, 22), "New", "override new") Eq(L.IsFullMoon(1, 22), false, "New is not full")
	-- Crimson: a full moon with the crimson event
	W:SetAttribute("NHMoonOverride", "Crimson")
	Eq(L.MoonPhase(1, 22), "Full", "crimson is a full phase") Eq(L.MoonEvent(1, 22), "Crimson", "crimson event")
	Eq(L.IsFullMoon(1, 22), true, "crimson is full")
	-- an ordinary moon on an event night: the event goes
	W:SetAttribute("NHMoonOverride", "Waxing") W:SetAttribute("NHMoonOverrideNight", 16)
	Eq(L.MoonEvent(16, 22), nil, "an ordinary moon has no event") Eq(L.MoonPhase(16, 22), "Waxing", "waxing on night 16")
	-- junk is ignored
	W:SetAttribute("NHMoonOverride", "Purple") Eq(L.MoonPhase(16, 22), "Full", "unknown override ignored")
end)
W:SetAttribute("NHMoonOverride", Old[1]) W:SetAttribute("NHMoonOverrideNight", Old[2])
if not ok then return "FAIL error: " .. tostring(err) end
if #Fails > 0 then return "FAIL " .. #Fails .. "\n" .. table.concat(Fails, "\n") end
return "PASS console2_lineage"
