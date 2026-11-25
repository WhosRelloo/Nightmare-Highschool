-- Server, Play, slot 2: every phase 2 card through Admin.Dispatch, then everything put back.
-- Run with run_live.py (the game's own VM). Slot 2's Quests (cine state and the Investigation cases, Quests.Cases),
-- Discipline, Lineage (Looks.FormDirection) and Progress are copied first and put back at the end, inside an xpcall,
-- so a failure still restores them.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local Data = require(SSS.Player.Data)
local Nt = require(SSS.School.Notoriety)
local HM = require(SSS.School.HallMonitor)
local Q = require(SSS.Quests.Quests)
local Tu = require(SSS.World.Tutorial)
local Cine = require(SSS.World.Cine)
local Clock = require(SSS.School.SchoolClock)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local Prof = Data.GetProfile(P)
if not Prof then return "FAIL no profile loaded (run this with run_live.py)" end
local Fails, Ran = {}, 0
local function go(Cmd, Args, Target)
	task.wait(0.2) -- Dispatch's rate limit
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return B end
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: "{tostring(B)}", want "{Expect}"`) end
	return B
end
local function deep(T) if typeof(T) ~= "table" then return T end local O = {} for K, V in T do O[K] = deep(V) end return O end
local function json(V)
	if typeof(V) ~= "table" then return typeof(V) .. ":" .. tostring(V) end
	local Ks = {} for K in V do table.insert(Ks, K) end
	table.sort(Ks, function(a, b) return tostring(a) < tostring(b) end)
	local Out = {} for _, K in Ks do table.insert(Out, tostring(K) .. "=" .. json(V[K])) end
	return "{" .. table.concat(Out, ",") .. "}"
end
local KEYS = { "Quests", "Discipline", "Lineage", "Progress" }
local Saved = {} for _, K in KEYS do Saved[K] = deep(Prof[K]) end
local WA = { "NHSeason", "NHSky", "NHMoonOverride", "NHMoonOverrideNight", "NHMonitorsOff" }
local W0 = {} for _, K in WA do W0[K] = workspace:GetAttribute(K) end
local PA = { "RaceLooks", "NHTutorial", "RaceHunger", "NHSummons", "NHBells", "NHBellState" }
local P0 = {} for _, K in PA do P0[K] = P:GetAttribute(K) end
local St0 = Clock.GetState()
local Me = P.UserId
local Race0 = P:GetAttribute("Race")
local function lookNow() return Prof.Lineage and Prof.Lineage.Looks and Prof.Lineage.Looks.FormDirection end
local Look0 = lookNow()
local LookAfterSet = nil
local Sub0, Tier0 = P:GetAttribute("SubRace") or P:GetAttribute("Race"), P:GetAttribute("RaceTier")

local function putBack()
	Admin.TestLiveMode = false
	P:SetAttribute("NHTestLevel", nil)
	pcall(Nt.Clear, P)
	if not HM.IsEnabled() then HM.SetEnabled(true) end
	if P:GetAttribute("NHTutorial") == true then pcall(Tu.Leave, P) end
	pcall(Cine.EndFor, P, "Aborted")
	pcall(function() local Lin = require(RS.Lineage) Lin.AdminSetRace(P, Sub0) Lin.AdminSetTier(P, Tier0 or 1) end)
	for _, K in KEYS do
		local Cur, Old = Prof[K], Saved[K]
		if typeof(Cur) == "table" and typeof(Old) == "table" then
			for Key in Cur do Cur[Key] = nil end
			for Key, V in Old do Cur[Key] = deep(V) end
		else
			Prof[K] = deep(Old)
		end
	end
	pcall(Q.SyncForCine, P)
	for _, K in PA do if P:GetAttribute(K) ~= P0[K] then P:SetAttribute(K, P0[K]) end end
	for _, K in WA do workspace:SetAttribute(K, W0[K]) end
	-- Lineage mirrors RaceHunger from the profile (math.floor(l.Hunger or 0)); the profile is what was restored
	P:SetAttribute("RaceHunger", math.floor((Prof.Lineage and Prof.Lineage.Hunger) or 0))
	-- SchoolClock.GetState().MinuteOfDay is 0..1440 and fractional
	pcall(Clock.SetTime, string.format("%02d:%02d", math.floor(St0.MinuteOfDay // 60), math.floor(St0.MinuteOfDay % 60)), St0.Day)
end

local Ok, Err = xpcall(function()
	-- World
	want(true, "TimePreset", { Preset = "Dusk" }, nil, "18:30")
	want(true, "SetSeason", { Season = "Winter" }, nil, "to Winter")
	if workspace:GetAttribute("NHSeason") ~= "Winter" then table.insert(Fails, "NHSeason not Winter") end
	want(true, "SetSeason", { Season = "Autumn" }, nil, "to Autumn")
	if workspace:GetAttribute("NHSeason") ~= nil then table.insert(Fails, "Autumn should clear NHSeason") end
	want(true, "SetMoon", { Moon = "Crimson" }, nil, "to Crimson")
	task.wait(1.5)
	if workspace:GetAttribute("NHMoonEventTonight") ~= "Crimson" then table.insert(Fails, "MoonPhases didn't pick up Crimson (NHMoonEventTonight=" .. tostring(workspace:GetAttribute("NHMoonEventTonight")) .. ")") end
	want(true, "SetMoon", { Moon = "Auto" }, nil, "to Auto")
	want(true, "SetSky", { Sky = "Storm" }, nil, "to Storm")
	want(true, "SetSky", { Sky = "Auto" }, nil, "to Auto")
	-- the live rule: level 2 refused, level 3 allowed
	Admin.TestLiveMode = true
	P:SetAttribute("NHTestLevel", 2) task.wait(0.3)
	for _, C in { { "SetSeason", { Season = "Winter" } }, { "SetMoon", { Moon = "New" } }, { "SetSky", { Sky = "Storm" } } } do
		want(false, C[1], C[2], nil, "Owner only in live servers")
	end
	want(true, "TimePreset", { Preset = "Noon" })
	P:SetAttribute("NHTestLevel", 3) task.wait(0.3)
	want(true, "SetSky", { Sky = "Storm" }) want(true, "SetSky", { Sky = "Auto" })
	P:SetAttribute("NHTestLevel", nil) Admin.TestLiveMode = false task.wait(0.3)

	-- Bell Tower (on yourself: no targeting up in Studio)
	want(true, "SetHeat", { Heat = 30 }, Me, "Bell 2")
	if P:GetAttribute("NHBells") ~= 2 then table.insert(Fails, "NHBells not 2 after Heat 30 (" .. tostring(P:GetAttribute("NHBells")) .. ")") end
	want(true, "SetBells", { Bells = 4 }, Me, "to 4")
	if P:GetAttribute("NHBells") ~= 4 then table.insert(Fails, "NHBells not 4 (" .. tostring(P:GetAttribute("NHBells")) .. ")") end
	want(true, "WhosWanted", {}, nil, P.Name)
	want(true, "GiveSummons", { Type = (Admin.Lists().Misdeeds[1] or {}).Id }, Me, "Summons for")
	if (P:GetAttribute("NHSummons") or 0) < 1 then table.insert(Fails, "no summons owed") end
	want(true, "ClearNotoriety", {}, Me, "Cleared")
	if P:GetAttribute("NHBells") ~= nil or P:GetAttribute("NHSummons") ~= nil then table.insert(Fails, "Clear left bells or summons") end
	want(true, "SetBells", { Bells = 0 }, Me, "to 0")
	want(true, "HallMonitors", { On = false }, nil, "off")
	if workspace:GetAttribute("NHMonitorsOff") ~= true or #HM.GetMonitors() ~= 0 then table.insert(Fails, "monitors still about") end
	want(false, "HallMonitors", { On = false }, nil, "already off")
	want(true, "HallMonitors", { On = true }, nil, "on")
	task.wait(3)
	if #HM.GetMonitors() == 0 then table.insert(Fails, "no monitors after On") end
	want(false, "SetHeat", { Heat = 101 }, Me, "0 to 100")

	-- Story
	local Cuts = Admin.Lists().Cutscenes
	local Cut = Cuts[1] and Cuts[1].Id
	if not Cut then table.insert(Fails, "no cutscenes listed") else
		local Before = json(Q.CineState(P))
		want(true, "PlayCutscene", { Id = Cut; Replay = true }, nil, "(replay)")
		task.wait(1) Cine.EndFor(P, "Aborted") task.wait(1)
		if json(Q.CineState(P)) ~= Before then table.insert(Fails, "a replay changed the cine state") end
		want(true, "CutsceneSeen", { Id = Cut; Mark = "Seen" }, Me, "seen for")
		if Q.CineState(P)[Cut] ~= "Seen" then table.insert(Fails, "Seen not written") end
		want(true, "CutsceneSeen", { Id = Cut; Mark = "Clear" }, Me, "cleared for")
		if Q.CineState(P)[Cut] ~= nil then table.insert(Fails, "Clear left a mark") end
		want(false, "PlayCutscene", { Id = "NoSuchCut" }, nil, "Unknown")
	end
	want(true, "TutorialEnter", {}, Me, " is in the tutorial (")
	for _, Cp in { "Garden", "Fence", "Bus" } do want(true, "TutorialJump", { Checkpoint = Cp }, Me, "tutorial at the " .. string.lower(Cp) .. " (mark ") end
	want(true, "TutorialLeave", {}, Me, " left the tutorial")
	want(false, "TutorialLeave", {}, Me, "is not in the tutorial")
	local Clue = Admin.Lists().Clues[1]
	if not Clue then table.insert(Fails, "no clues listed") else
		local Case = Clue.Id:match("^([%w_]+)/")
		want(true, "ResetCase", { Case = Case }, Me, "Reset")
		want(true, "GiveClue", { Clue = Clue.Id }, Me, "Gave")
		want(false, "GiveClue", { Clue = Clue.Id }, Me, "already")
		want(true, "ResetCase", { Case = Case }, Me, "Reset")
	end
	want(false, "GiveClue", { Clue = "Nope/Nope" }, Me, "Unknown")

	-- Form direction (a race without a form is refused). The first real run of Lineage.SetLook from the console.
	-- a race without a form is refused; then (temporarily) a Vampire, so SetLook really runs (put back by putBack)
	local Forms = require(RS.Config.Forms)
	if Forms.Races[P:GetAttribute("Race") or ""] == nil then
		want(false, "FormDirection", { Direction = "1" }, Me, "has no form")
		local Lin = require(RS.Lineage)
		Lin.AdminSetRace(P, "Vampire") Lin.AdminSetTier(P, 1) task.wait(1)
	end
	if Forms.Races[P:GetAttribute("Race") or ""] == nil then table.insert(Fails, "couldn't give slot 2 a race with a form")
	else
		want(true, "FormDirection", { Direction = "2" }, Me, "direction 2")
		LookAfterSet = lookNow()
		if LookAfterSet ~= "2" then table.insert(Fails, "Looks.FormDirection after direction 2 is " .. tostring(LookAfterSet)) end
		want(true, "FormDirection", { Direction = "1" }, Me, "direction 1")
		if lookNow() ~= "1" then table.insert(Fails, "Looks.FormDirection after direction 1 is " .. tostring(lookNow())) end
	end
end, debug.traceback)
putBack()
-- slot 2 must be exactly as it was
for _, K in KEYS do if json(Prof[K]) ~= json(Saved[K]) then table.insert(Fails, "slot 2 " .. K .. " not put back") end end
for _, K in WA do if workspace:GetAttribute(K) ~= W0[K] then table.insert(Fails, "workspace " .. K .. " not put back") end end
if P:GetAttribute("Race") ~= Race0 or P:GetAttribute("RaceTier") ~= Tier0 then table.insert(Fails, "race not put back: " .. tostring(P:GetAttribute("Race")) .. " tier " .. tostring(P:GetAttribute("RaceTier"))) end
for _, K in PA do
	local Cur, Old = P:GetAttribute(K), P0[K]
	local Same = Cur == Old or (K == "RaceHunger" and typeof(Cur) == "number" and typeof(Old) == "number" and math.abs(Cur - Old) <= 2)
	if not Same then table.insert(Fails, "player attribute " .. K .. " not put back") end
end
if Clock.GetState().Day ~= St0.Day then table.insert(Fails, "clock day not put back: " .. tostring(Clock.GetState().Day) .. " vs " .. tostring(St0.Day)) end
if lookNow() ~= Look0 then table.insert(Fails, "FormDirection look not put back: " .. tostring(lookNow()) .. " vs " .. tostring(Look0)) end
local Note = `\n(race {tostring(Race0)}; FormDirection look before {tostring(Look0)}, after direction 2 {tostring(LookAfterSet)}, after put-back {tostring(lookNow())})`
if not Ok then return "FAIL error: " .. tostring(Err) .. Note end
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") .. Note end
return "PASS console2_play_run (" .. Ran .. " calls)" .. Note
