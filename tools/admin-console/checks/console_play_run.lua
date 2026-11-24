-- Server, Play, slot 2: every migrated command through Admin.Dispatch once, plus the level and argument refusals.
-- Run with run_live.py (not run_check.py): the MCP's Server execute_luau gets a fresh module graph where Admin's
-- OnStart never ran and no profile is loaded, so this runs inside a Script under ServerScriptService, in the game's
-- own VM, and hands its result back through an attribute.
-- (Task 8) restore.py only puts back Quests, Yen, Discipline and the social standings. Everything else this run
-- changes on slot 2 (look and build, identity and gear, race, progress, places found, club, titles, attendance,
-- classes) is copied from the profile before the run and put back just before the last command (Kill), so the
-- respawn rebuilds the character from it; the clock (day, time, speed) goes back too.
-- (fix round 1) The run is one xpcall: whatever stops it (an error, or run_live.py's "Stop" attribute on a timeout),
-- the put-back still runs and NHTestLevel is cleared. Put-back writes go into the profile's own tables (services
-- keep references to them). Attribute drift fails unless it is on the allow-list below, with its reason.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")
local SSS = game.ServerScriptService.Services
local Admin = require(SSS.Features.Admin)
local P = Players:GetPlayers()[1]
if not P then return "FAIL no player" end
local Fails, Ran, Seen = {}, 0, {}
local function go(Cmd, Args, Target)
	task.wait(0.2) -- Dispatch's 0.15 s rate limit
	if script:GetAttribute("Stop") then error("stopped by run_live.py (timeout)", 0) end
	return Admin.Dispatch(P, Cmd, Target, Args or {})
end
local function want(Ok, Cmd, Args, Target, Expect)
	local A, B = go(Cmd, Args, Target)
	Ran += 1
	if (A == true) ~= Ok then table.insert(Fails, `{Cmd}: got {tostring(A)} {tostring(B)}`) return end
	if A == true then Seen[Cmd] = true end -- (Warn runs here, at level 1)
	if Expect and not string.find(tostring(B), Expect, 1, true) then table.insert(Fails, `{Cmd}: message "{tostring(B)}", want "{Expect}"`) end
end
local Me = P.UserId

-- record what this run changes outside slot 2's snapshot, to put back at the end
local Data = require(SSS.Player.Data)
local Clock = require(SSS.School.SchoolClock)
local ClockPart = workspace:FindFirstChild("Clock", true) or RS:FindFirstChild("Clock", true)
local function deep(T) if typeof(T) ~= "table" then return T end local O = {} for K, V in T do O[K] = deep(V) end return O end
-- a canonical dump (sorted keys): JSONEncode follows table order, which differs between a table and its copy
local function json(V)
	if typeof(V) ~= "table" then return typeof(V) .. ":" .. tostring(V) end
	local Ks = {}
	for K in V do table.insert(Ks, K) end
	table.sort(Ks, function(a, b) return tostring(a) < tostring(b) end)
	local Out = {}
	for _, K in Ks do table.insert(Out, tostring(K) .. "=" .. json(V[K])) end
	return "{" .. table.concat(Out, ",") .. "}"
end
local KEYS = { "Appearance", "Identity", "Lineage", "Progress", "Regions", "Sports", "Social", "Attendance", "Classes", "Inventory", "Armory", "Training" }
local Prof0 = Data.GetProfile(P)
if not Prof0 then return "FAIL no profile loaded (run this with run_live.py)" end
local Saved = {}
for _, K in KEYS do Saved[K] = deep(Prof0[K]) end
local Attr0 = P:GetAttributes()
local St0 = Clock.GetState()
local Before = {
	Sub = P:GetAttribute("SubRace") or P:GetAttribute("Race"); Tier = P:GetAttribute("RaceTier");
	Day = St0.Day;
	ClockSpeed = (ClockPart and ClockPart:GetAttribute("RealSecondsPerGameHour")) or require(RS.Config.SchoolSchedule).RealSecondsPerGameHour;
}
local Undo, Direct = {}, {}
-- put a saved value back into the profile's existing table, so no service is left holding an orphan
local function into(Prof, K, V)
	local T = Prof[K]
	if typeof(T) == "table" and typeof(V) == "table" then
		for X in T do T[X] = nil end
		for X, Y in deep(V) do T[X] = Y end
	else
		Prof[K] = deep(V)
	end
end
local PutBackDone = false
local function putBack()
	if PutBackDone then return end
	PutBackDone = true
	local Prof = Data.GetProfile(P)
	local UPDATE = { Appearance = { "SetAppearance", "appearance" }; Identity = { "SetIdentity", "identity" }; Progress = { "SetProgress", "progress" };
		Regions = { "SetRegions", "regions" }; Sports = { "SetSports", "sports" }; Attendance = { "SetAttendance", "attendance" } }
	pcall(function() local Lin = require(RS.Lineage) Lin.AdminSetRace(P, Before.Sub) Lin.AdminSetTier(P, Before.Tier or 1) end)
	-- the club: leaving clears the Club / ClubRank mirrors that a put-back profile alone would leave
	pcall(function() if not (Saved.Sports and Saved.Sports.Club) then require(SSS.Sports.Clubs).Leave(P) end end)
	for _, K in KEYS do
		if json(Prof[K]) ~= json(Saved[K]) then
			local U = UPDATE[K]
			if U then pcall(Data.UpdateState, P, { type = U[1]; [U[2]] = deep(Saved[K]) }) end
			if json(Prof[K]) ~= json(Saved[K]) then into(Prof, K, Saved[K]) table.insert(Direct, K) end
			table.insert(Undo, K)
		end
	end
	pcall(function() require(SSS.Social.Reputation).Sync(P) end)
	pcall(function() local I = require(SSS.Player.Identity) if I.Mirror then I.Mirror(P, I.Get(P)) end end)
	pcall(function() require(SSS.Sports.Clubs).Notify(P) end)
	pcall(function() require(SSS.Player.Height).Apply(P) end) -- height mirrors and body (a stopped run has no respawn)
	pcall(function() local Pg = require(SSS.Player.Progression) Pg.Apply(P) Pg.Notify(P) end)
	P:SetAttribute("Level", Attr0.Level)
	pcall(function() Clock.SetSpeed(Before.ClockSpeed) Clock.SetTime("12:30", Before.Day) end)
end

local Activities = require(SSS.School.Activities)
local Lesson = { Ran = false }
local StateSeen = {}
local function body()
local function first0(K) local L0 = Admin.Lists() local I = L0[K] and L0[K][1] return I and (if typeof(I) == "table" then I.Id else I) end
-- levels (NHTestLevel, Studio only)
P:SetAttribute("NHTestLevel", 1)
task.wait(0.3)
want(false, "Heal", {}, Me, "Needs an admin")
want(false, "Shutdown", {}, nil, "Needs the owner")
want(true, "Warn", { Reason = "console test" }, Me)
-- (final review fix 3) the Inspect remote is level 2, as the console offers it
if Admin.InspectFor(P, Me) ~= nil then table.insert(Fails, "Inspect answered a moderator") end
Ran += 1
P:SetAttribute("NHTestLevel", 2)
task.wait(0.3)
if typeof(Admin.InspectFor(P, Me)) ~= "table" then table.insert(Fails, "Inspect refused an admin") end
Ran += 1
want(false, "Ban", { Days = 0; Reason = "test" }, Me, "Permanent bans are owner-only")
want(false, "GiveYen", { Amount = 200000 }, Me, "needs an owner")
P:SetAttribute("NHTestLevel", 0)
task.wait(0.3)
want(false, "Warn", {}, Me, "Not staff")
P:SetAttribute("NHTestLevel", nil)
task.wait(0.3)

-- arguments
want(false, "Speed", { Value = 500 }, Me, "Speed must be 0 to 120")
want(false, "SetHeight", { Pick = "Huge" }, Me, "Unknown Height")
want(false, "SpawnSparring", { Tier = "Godlike" }, nil, "Unknown Difficulty")
want(false, "Announce", { Text = "" }, nil, "Message is needed")
want(false, "Heal", {}, nil, "Pick a player first")
-- (final review fix 1) "Send them" needs the selected student, now Dispatch's target (Target = "optional")
want(false, "GotoRegion", { Id = first0("Regions"); Send = true }, nil, "Pick a student first")
-- (final review fix 2) CheckArgs stays strict: an empty club is refused, "None" is the way out
want(false, "SetClub", { Club = "" }, Me, "Club is needed")

-- commands that may fairly be refused in this state: each needs this exact refusal message, never just "not true"
local StateOk = {
}

-- every safe command once (Kick, Ban, Unban and Shutdown are left out: they would end the Play session)
local L = Admin.Lists()
local function first(K) local I = L[K] and L[K][1] return I and (if typeof(I) == "table" then I.Id else I) end
-- (fix round 1) the quest: the first in the list that can start now. A dare is open only on its own day (Quests.DareFor),
-- so first("Quests") alone is refused on most days ("not open to them yet").
-- (final review fix 2) Lists.Clubs starts with "None" (take them out): the join uses the first real club
local RealClub = L.Clubs[2] and L.Clubs[2].Id
if first("Clubs") ~= "None" then table.insert(Fails, "Lists.Clubs doesn't start with None") end
local QuestId = first("Quests")
pcall(function()
	local Q = require(SSS.Quests.Quests)
	for _, It in L.Quests do if Q.CanStart(P, It.Id) == true then QuestId = It.Id break end end
end)
local Runs = {
	{ "Mute" }, { "Unmute" }, { "Freeze" }, { "Freeze" }, { "Jail" }, { "Spectate" }, { "Bring" }, { "Goto" },
	{ "Note", { Text = "console test" } }, { "Note", { Text = "" } },
	{ "Announce", { Text = "Console test, please ignore" } }, { "ServerLock" }, { "ServerLock" }, { "BringAll" },
	{ "FreezeAll", { On = true } }, { "FreezeAll", { On = false } },
	{ "Heal" }, { "Revive" }, { "God" }, { "God" }, { "Speed", { Value = 16 } },
	{ "SetRace", { Sub = Before.Sub } }, { "SetTier", { Tier = Before.Tier or 1 } }, { "SetHeight", { Pick = "Average" } },
	{ "SpinHeight" }, { "SetBuild", { Build = "Average"; Step = 0 } }, { "Transform" }, { "Transform" },
	{ "GiveYen", { Amount = 10 } }, { "GiveYen", { Amount = -10 } }, { "GiveExp", { Amount = 10; Category = "Combat" } },
	{ "GiveGear", { Id = first("Gear") } }, { "GiveSpins", { Amount = 1 } }, { "GiveNameChange" },
	{ "SetLevel", { Value = 5 } }, { "SetStatPoints", { Value = 3 } }, { "GrantTitle", { Title = "Tester" } }, { "RemoveTitle", { Title = "Tester" } },
	{ "RegionsAll" }, { "RegionsReset" }, { "SetClub", { Club = RealClub } }, { "SetClub", { Club = "None" } },
	{ "MatchStart", { Venue = first("Venues") } }, { "MatchEnd", { Venue = first("Venues") }, true },
	{ "SetTime", { Time = "12:30" }, true }, { "ClockSpeed", { Value = 60 }, true }, { "SkipToPeriod", { Segment = first("Segments") }, true }, { "RingBell", nil, true },
	{ "SetDisciplinePoints", { Value = 0 } }, { "ClearDiscipline" }, { "LiftSuspension" }, { "ExcuseToday" },
	{ "OweDetention" }, { "ClearDetention" },
	{ "QuestStart", { Id = QuestId } }, { "QuestAbandon", { Id = QuestId } }, { "QuestReset" },
	{ "FullMoon", nil, true }, { "GotoRegion", { Id = first("Regions") }, true }, { "GotoRegion", { Id = first("Regions"); Send = true } },
	{ "SpawnDelinquents", nil, true }, { "SpawnDelinquent", { Role = "Brute" }, true }, { "SpawnWolves", nil, true },
	{ "SpawnBeast", { Beast = first("Beasts") }, true }, { "SpawnSparring", { Tier = "Easy" }, true }, { "ClearEnemies", nil, true },
	{ "Invisible", nil, true }, { "Invisible", nil, true },
	{ "TeleportTo", { Position = (P.Character and P.Character:GetPivot().Position or Vector3.zero) + Vector3.new(0, 0, 4) }, true },
	-- (fix round 1) after the quest rows: the lesson needs the clock in a class period (tomorrow), and a dare that sees
	-- school hours on another day is no longer open, so QuestStart would be refused if this ran first
	{ "StartLesson", { Room = "R102" } },
	{ "Kill" }, -- last: the respawn
}
for _, R in Runs do
	local Cmd, Args, NoTarget = R[1], R[2], R[3]
	Seen[Cmd] = true
	if Cmd == "Kill" then putBack() end
	-- StartLesson's success path: skip to Period 1 (Mathematics in R102), be in the room (a hall pass counts as in
	-- class: Attendance.InClass), then it must start; it is quit at once and the clock goes back to 12:30 today.
	-- (Not R101: that is Homeroom, which has no lesson in Config.Activities.Subjects, so it can never start.)
	if Cmd == "StartLesson" then
		local A0, B0 = go("SkipToPeriod", { Segment = "Period 1" }, nil)
		Ran += 1
		if A0 ~= true then table.insert(Fails, `SkipToPeriod Period 1 refused: {tostring(B0)}`) end
		Lesson.Ran = true
		P:SetAttribute("NHHallPass", "R102")
		local t1 = os.clock()
		while P:GetAttribute("ClassInRoom") ~= true and os.clock() - t1 < 10 do task.wait(0.25) end
		if P:GetAttribute("ClassInRoom") ~= true then table.insert(Fails, "StartLesson setup: ClassInRoom never true in Period 1") end
	end
	local A, B = go(Cmd, Args, if NoTarget then nil else Me)
	Ran += 1
	if A ~= true then
		local Msg = StateOk[Cmd]
		if Msg and typeof(B) == "string" and string.find(B, Msg, 1, true) then table.insert(StateSeen, `{Cmd}: {B}`)
		else table.insert(Fails, `{Cmd} refused: {tostring(B)}`) end
	end
	if Cmd == "SetClub" and A == true then
		local Want = if Args.Club == "None" then nil else Args.Club
		if P:GetAttribute("Club") ~= Want then table.insert(Fails, `SetClub {Args.Club}: Club attribute is {tostring(P:GetAttribute("Club"))}`) end
		if Args.Club == "None" and not string.find(tostring(B), "left their club", 1, true) then table.insert(Fails, `SetClub None: "{tostring(B)}"`) end
	end
	-- (one player in Play: the selected student is you, so Run reports "You went"; without a target it is refused above)
	if Cmd == "GotoRegion" and Args.Send == true and A == true and not string.find(tostring(B), "went to", 1, true) then
		table.insert(Fails, `GotoRegion Send: "{tostring(B)}", want "... went to ..."`)
	end
	-- the clock goes straight back to 12:30 today after a jump, so no class gets booked while the run goes on
	if Cmd == "SkipToPeriod" or Cmd == "FullMoon" then Clock.SetTime("12:30", Before.Day) end
	-- the lesson is walked out of at once, and the clock goes back
	if Cmd == "StartLesson" then
		if A == true then
			Activities.ActionForTests(P, "Quit")
			if Activities.GetSessionForTests(P) ~= nil then table.insert(Fails, "StartLesson: the lesson didn't end on Quit") end
		end
		P:SetAttribute("NHHallPass", nil)
		Clock.SetTime("12:30", Before.Day)
	end
end
for _, Id in { "Kick", "Ban", "Unban", "Shutdown" } do Seen[Id] = true end
for _, D in Admin.Registry(3) do if not Seen[D.Id] then table.insert(Fails, D.Id .. " not run") end end
end

-- the run, then always: NHTestLevel and the hall pass cleared, any lesson quit, everything put back
local OkRun, Err = xpcall(body, debug.traceback)
if not OkRun then table.insert(Fails, "run stopped: " .. tostring(Err):sub(1, 300)) end
P:SetAttribute("NHTestLevel", nil)
if Lesson.Ran then
	P:SetAttribute("NHHallPass", nil)
	if Activities.GetSessionForTests(P) then pcall(Activities.ActionForTests, P, "Quit") end
end
putBack()

-- after the respawn: everything outside the snapshot is as it was
local t0 = os.clock()
repeat task.wait(0.5)
	local H = P.Character and P.Character:FindFirstChildWhichIsA("Humanoid")
until (H and H.Health > 0) or os.clock() - t0 > 20
task.wait(2)
local Prof = Data.GetProfile(P)
for _, K in KEYS do if json(Prof[K]) ~= json(Saved[K]) then table.insert(Fails, `profile {K} not put back`) end end
for _, K in { "Level", "SubRace", "RaceTier", "Race", "Title", "HeightText", "Slot", "Enrolled", "Club", "ClubRank", "NHTestLevel", "NHHallPass" } do
	if P:GetAttribute(K) ~= Attr0[K] then table.insert(Fails, `attribute {K}: {tostring(P:GetAttribute(K))}, was {tostring(Attr0[K])}`) end
end
-- attributes allowed to differ after the run, each with its reason; any other drift fails
local DRIFT_OK = {
	DetentionsOwed = "Discipline: Owe/ClearDetention set it; restore.py puts the discipline record back after the run";
	DetentionActive = "Detention: whether a detention session runs; Jail / Owe / ClearDetention start or end one, restore.py puts the owed count back";
	DetentionCollected = "Detention: a running session's progress; it goes when ClearDetention ends the session";
	DetentionTotal = "Detention: a running session's goal; it goes when ClearDetention ends the session";
	DisciplinePoints = "Discipline: SetDisciplinePoints / ClearDiscipline change it; restore.py puts the discipline record back";
	DisciplineLevel = "Discipline: follows DisciplinePoints; restore.py puts the discipline record back";
}
local Drift = {}
local Now = P:GetAttributes()
for K, V in Now do if Attr0[K] ~= V then
	if DRIFT_OK[K] then table.insert(Drift, `{K}={tostring(V)} (was {tostring(Attr0[K])}; allowed: {DRIFT_OK[K]})`)
	else table.insert(Fails, `attribute drift {K}={tostring(V)} (was {tostring(Attr0[K])})`) end
end end
for K, V in Attr0 do if Now[K] == nil then
	if DRIFT_OK[K] then table.insert(Drift, `{K}=nil (was {tostring(V)}; allowed)`) else table.insert(Fails, `attribute drift {K}=nil (was {tostring(V)})`) end
end end
if Clock.GetState().Day ~= Before.Day then table.insert(Fails, "clock day not put back") end
if Admin.Locked() then table.insert(Fails, "ServerLock left on") end
local Tail = `\nstate-refused ({#StateSeen}): {table.concat(StateSeen, " | ")}\nput back: {table.concat(Undo, ", ")} (direct write, in place: {if #Direct > 0 then table.concat(Direct, ", ") else "none"})\nattribute drift: {table.concat(Drift, ", ")}`
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") .. Tail end
return "PASS console_play_run (" .. Ran .. " calls)" .. Tail
