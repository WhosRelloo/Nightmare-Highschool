-- Server, Play, slot 2: every migrated command through Admin.Dispatch once, plus the level and argument refusals.
-- Run with run_live.py (not run_check.py): the MCP's Server execute_luau gets a fresh module graph where Admin's
-- OnStart never ran and no profile is loaded, so this runs inside a Script under ServerScriptService, in the game's
-- own VM, and hands its result back through an attribute.
-- (Task 8) restore.py only puts back Quests, Yen, Discipline and the social standings. Everything else this run
-- changes on slot 2 (look and build, identity and gear, race, progress, places found, club, titles, attendance,
-- classes) is copied from the profile before the run and put back just before the last command (Kill), so the
-- respawn rebuilds the character from it; the clock (day, time, speed) goes back too.
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
local Undo = {}
local function putBack()
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
			if json(Prof[K]) ~= json(Saved[K]) then Prof[K] = deep(Saved[K]) end
			table.insert(Undo, K)
		end
	end
	pcall(function() require(SSS.Social.Reputation).Sync(P) end)
	pcall(function() local I = require(SSS.Player.Identity) if I.Mirror then I.Mirror(P, I.Get(P)) end end)
	pcall(function() require(SSS.Sports.Clubs).Notify(P) end)
	pcall(function() local Pg = require(SSS.Player.Progression) Pg.Apply(P) Pg.Notify(P) end)
	P:SetAttribute("Level", Attr0.Level)
	pcall(function() Clock.SetSpeed(Before.ClockSpeed) Clock.SetTime("12:30", Before.Day) end)
end

-- levels (NHTestLevel, Studio only)
P:SetAttribute("NHTestLevel", 1)
task.wait(0.3)
want(false, "Heal", {}, Me, "Needs an admin")
want(false, "Shutdown", {}, nil, "Needs the owner")
want(true, "Warn", { Reason = "console test" }, Me)
P:SetAttribute("NHTestLevel", 2)
task.wait(0.3)
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

-- commands that may fairly be refused in this state: each needs this exact refusal message, never just "not true"
local StateOk = {
	StartLesson = "Couldn't start it", -- 12:30 is After School: no class in R101 (Activities.TryStart: "No ... class right now")
}
local StateSeen = {}

-- every safe command once (Kick, Ban, Unban and Shutdown are left out: they would end the Play session)
local L = Admin.Lists()
local function first(K) local I = L[K] and L[K][1] return I and (if typeof(I) == "table" then I.Id else I) end
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
	{ "RegionsAll" }, { "RegionsReset" }, { "SetClub", { Club = first("Clubs") } },
	{ "MatchStart", { Venue = first("Venues") } }, { "MatchEnd", { Venue = first("Venues") }, true },
	{ "SetTime", { Time = "12:30" }, true }, { "ClockSpeed", { Value = 60 }, true }, { "SkipToPeriod", { Segment = first("Segments") }, true }, { "RingBell", nil, true },
	{ "StartLesson", { Room = "R101" } }, { "SetDisciplinePoints", { Value = 0 } }, { "ClearDiscipline" }, { "LiftSuspension" }, { "ExcuseToday" },
	{ "OweDetention" }, { "ClearDetention" },
	{ "QuestStart", { Id = first("Quests") } }, { "QuestAbandon", { Id = first("Quests") } }, { "QuestReset" },
	{ "FullMoon", nil, true }, { "GotoRegion", { Id = first("Regions") }, true },
	{ "SpawnDelinquents", nil, true }, { "SpawnDelinquent", { Role = "Brute" }, true }, { "SpawnWolves", nil, true },
	{ "SpawnBeast", { Beast = first("Beasts") }, true }, { "SpawnSparring", { Tier = "Easy" }, true }, { "ClearEnemies", nil, true },
	{ "Invisible", nil, true }, { "Invisible", nil, true },
	{ "TeleportTo", { Position = (P.Character and P.Character:GetPivot().Position or Vector3.zero) + Vector3.new(0, 0, 4) }, true },
	{ "Kill" }, -- last: the respawn
}
for _, R in Runs do
	local Cmd, Args, NoTarget = R[1], R[2], R[3]
	Seen[Cmd] = true
	if Cmd == "Kill" then putBack() end
	local A, B = go(Cmd, Args, if NoTarget then nil else Me)
	Ran += 1
	if A ~= true then
		local Msg = StateOk[Cmd]
		if Msg and typeof(B) == "string" and string.find(B, Msg, 1, true) then table.insert(StateSeen, `{Cmd}: {B}`)
		else table.insert(Fails, `{Cmd} refused: {tostring(B)}`) end
	end
	-- the clock goes straight back to 12:30 today after a jump, so no class gets booked while the run goes on
	if Cmd == "SkipToPeriod" or Cmd == "FullMoon" then Clock.SetTime("12:30", Before.Day) end
	-- a lesson that did start is walked out of at once
	if Cmd == "StartLesson" and A == true then pcall(require(SSS.School.Activities).ActionForTests, P, "Quit") end
end
for _, Id in { "Kick", "Ban", "Unban", "Shutdown" } do Seen[Id] = true end
for _, D in Admin.Registry(3) do if not Seen[D.Id] then table.insert(Fails, D.Id .. " not run") end end
P:SetAttribute("NHTestLevel", nil)

-- after the respawn: everything outside the snapshot is as it was
local t0 = os.clock()
repeat task.wait(0.5)
	local H = P.Character and P.Character:FindFirstChildWhichIsA("Humanoid")
until (H and H.Health > 0) or os.clock() - t0 > 20
task.wait(2)
local Prof = Data.GetProfile(P)
for _, K in KEYS do if json(Prof[K]) ~= json(Saved[K]) then table.insert(Fails, `profile {K} not put back`) end end
for _, K in { "Level", "SubRace", "RaceTier", "Race", "Title", "HeightText", "Slot", "Enrolled" } do
	if P:GetAttribute(K) ~= Attr0[K] then table.insert(Fails, `attribute {K}: {tostring(P:GetAttribute(K))}, was {tostring(Attr0[K])}`) end
end
local Drift = {}
for K, V in P:GetAttributes() do if Attr0[K] ~= V then table.insert(Drift, `{K}={tostring(V)} (was {tostring(Attr0[K])})`) end end
if Clock.GetState().Day ~= Before.Day then table.insert(Fails, "clock day not put back") end
if Admin.Locked() then table.insert(Fails, "ServerLock left on") end
local Tail = `\nstate-refused ({#StateSeen}): {table.concat(StateSeen, " | ")}\nput back: {table.concat(Undo, ", ")}\nattribute drift: {table.concat(Drift, ", ")}`
if #Fails > 0 then return "FAIL " .. #Fails .. " of " .. Ran .. "\n" .. table.concat(Fails, "\n") .. Tail end
return "PASS console_play_run (" .. Ran .. " calls)" .. Tail
