--[[
	Discipline (server authoritative)

	Points ladder: Clear -> Warning -> Detention -> Probation -> Suspension (Config.Discipline).
	- Violations add points (attendance results, hall-monitor catches, fights, walking out of detention).
	- Good behaviour removes points: Present classes, daily decay (offline days count too),
	  and serving detention.
	- Reaching Detention level (from below) owes one detention.
	- Probation / Suspension last a set number of in-game days once reached. When a suspension
	  ends, points drop to PointsAfterSuspension and probation starts.

	Witnesses: other systems call ReportIncident(). Only recognised suspects are punished;
	an unrecognised incident is logged but can't be pinned on anyone later.

	API:
		Discipline.AddViolation(Player, Type, Details?)
		Discipline.Reduce(Player, Amount, Reason)
		Discipline.ServeDetention(Player)
		Discipline.ReportIncident({ Type, Suspect: Player, Witness, Position?, Recognized }) -> punished?
		(2.37) Notoriety hears every report (OnReport); a caught report carries the Bonus
		Discipline.GetData(Player), Discipline.IsSuspended(Player)
		Signals: ViolationAdded(Player, Record), LevelChanged(Player, New, Old), DetentionServed(Player)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local Config = require(ReplicatedStorage.Config.Discipline)

local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Attendance = require(ServerScriptService.Services.School.Attendance)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local TICK = 2
local LEVEL_RANK = {} :: { [string]: number }
for Index, Level in Config.Levels do
	LEVEL_RANK[Level.Name] = Index
end

local Incidents = {} :: { any } -- recent incidents (server memory, for debugging / future systems)
local MAX_INCIDENTS = 50

local Local = {}
local Shared = {}

Shared.ViolationAdded = SignalPlus()
Shared.LevelChanged = SignalPlus()
Shared.DetentionServed = SignalPlus()

---| Data |---

function Shared.GetData(Player: Player): any?
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end

	if typeof(Profile.Discipline) ~= `table` then
		Profile.Discipline = {
			Points = 0; Level = `Clear`; DetentionsOwed = 0; DetentionsServed = 0;
			ProbationUntilDay = -1; SuspendedUntilDay = -1; LastDecayDay = -1; Recent = {};
		}
	end
	return Profile.Discipline
end

function Shared.IsSuspended(Player: Player): boolean
	local Discipline = Shared.GetData(Player)
	return Discipline ~= nil and Discipline.Level == `Suspension`
end

function Local.LevelForPoints(Points: number): string
	local Result = Config.Levels[1].Name
	for _, Level in Config.Levels do
		if Points >= Level.MinPoints then Result = Level.Name end
	end
	return Result
end

function Local.Sync(Player: Player, Discipline)
	Player:SetAttribute(`DisciplineLevel`, Discipline.Level)
	Player:SetAttribute(`DisciplinePoints`, Discipline.Points)
	Player:SetAttribute(`DetentionsOwed`, Discipline.DetentionsOwed)
	Player:SetAttribute(`Suspended`, Discipline.Level == `Suspension`)
	Data.UpdateState(Player, { type = `SetDiscipline`; discipline = Discipline })
end

-- Applies timed levels and the point ladder, then reports any change.
function Local.Recompute(Player: Player, Discipline, Quiet: boolean?)
	local Day = SchoolClock.GetState().Day
	local Old = Discipline.Level

	if Discipline.SuspendedUntilDay >= 0 and Day >= Discipline.SuspendedUntilDay then
		Discipline.SuspendedUntilDay = -1
		-- (2.7.3) points from violations during the suspension come back on top: a suspension isn't a free pass
		local Held = Discipline.HeldPoints or 0
		Discipline.HeldPoints = nil
		Discipline.Points = math.min(Discipline.Points, Config.PointsAfterSuspension) + Held
		Discipline.ProbationUntilDay = Day + Config.ProbationDays
		if Held > 0 then
			Notifications.Notify(Player, {
				Title = `Discipline`;
				Text = `What you did while suspended still counts (+{Held} points)`;
				Kind = `Bad`;
				Duration = 6;
			})
		end
	end
	if Discipline.SuspendedUntilDay < 0 then Discipline.HeldPoints = nil end -- (2.7.3) e.g. an admin lifted it
	if Discipline.ProbationUntilDay >= 0 and Day >= Discipline.ProbationUntilDay then
		Discipline.ProbationUntilDay = -1
	end

	local Level = Local.LevelForPoints(Discipline.Points)
	if Level == `Suspension` and Discipline.SuspendedUntilDay < 0 then
		Discipline.SuspendedUntilDay = Day + Config.SuspensionDays
	end
	if Level == `Probation` and Discipline.ProbationUntilDay < 0 then
		Discipline.ProbationUntilDay = Day + Config.ProbationDays
	end

	if Discipline.SuspendedUntilDay >= 0 then
		Level = `Suspension`
	elseif Discipline.ProbationUntilDay >= 0 and LEVEL_RANK[Level] < LEVEL_RANK.Probation then
		Level = `Probation`
	end

	-- Reaching Detention (or worse) from below owes one detention.
	if LEVEL_RANK[Level] >= LEVEL_RANK.Detention and (LEVEL_RANK[Old] or 1) < LEVEL_RANK.Detention then
		-- (2.8.1) capped (Config.Discipline.Record.MaxDetentionsOwed): owing used to pile up with every climb back
		Discipline.DetentionsOwed = math.max(Discipline.DetentionsOwed, math.min(Discipline.DetentionsOwed + 1, Config.Record.MaxDetentionsOwed))
		-- (1.39) Most Likely to Be Expelled (Services.Social.Superlatives); (1.40) and the report card
		pcall(function() require(game:GetService(`ServerScriptService`).Services.Social.Superlatives).Count(Player, `Detentions`) end)
		pcall(function() require(game:GetService(`ServerScriptService`).Services.School.ReportCards).Detention(Player) end)
	end

	Discipline.Level = Level
	Local.Sync(Player, Discipline)

	if Level ~= Old then
		Shared.LevelChanged:Fire(Player, Level, Old)
		if not Quiet then
			local Worse = (LEVEL_RANK[Level] or 1) > (LEVEL_RANK[Old] or 1)
			local Text = `Your record is now: {Level}`
			if Level == `Detention` then Text ..= ` (report to Room 106 outside class)` end
			if Level == `Suspension` then Text ..= ` (stay off campus during class today; Bruno has work at the Back Lot)` end
			if Level == `Probation` then Text ..= ` (the hall monitor knows your face; hall passes are void)` end
			Notifications.Notify(Player, {
				Title = if Worse then `Discipline` else `Record improved`;
				Text = Text;
				Kind = if Worse then `Bad` else `Good`;
				Duration = 6;
			})
		end
	end
end

---| Changes |---

function Shared.AddViolation(Player: Player, Type: string, Details: any?): any?
	local Rule = Config.Violations[Type]
	local Discipline = Shared.GetData(Player)
	if not Rule or not Discipline then return nil end
	local Bonus = math.max(0, math.floor(tonumber(Details and Details.Bonus) or 0)) -- (2.37) Notoriety: caught while hunted
	local Points = Rule.Points + Bonus

	local State = SchoolClock.GetState()
	local Record = {
		Type = Type;
		Text = Rule.Text;
		Points = Points;
		Bonus = if Bonus > 0 then Bonus else nil;
		Day = State.Day;
		Time = State.ClockText;
		Witness = Details and Details.Witness or nil;
	}

	Discipline.Points += Points
	-- (2.7.3) kept aside while suspended: the suspension's end resets points to PointsAfterSuspension, then adds these
	if Discipline.SuspendedUntilDay >= 0 and State.Day < Discipline.SuspendedUntilDay then
		Discipline.HeldPoints = (Discipline.HeldPoints or 0) + Points
	end
	table.insert(Discipline.Recent, 1, Record)
	while #Discipline.Recent > Config.RecentLimit do
		table.remove(Discipline.Recent)
	end

	Notifications.Notify(Player, {
		Title = `Violation: {Rule.Text}`;
		Text = `+{Points} discipline points ({Discipline.Points} total)` .. (if Bonus > 0 then ` · +{Bonus} for running` else ``);
		Kind = `Warning`;
		Duration = 5;
	})

	-- (1.40) the week's report card: conduct (Services.School.ReportCards)
	pcall(function() require(game:GetService(`ServerScriptService`).Services.School.ReportCards).Violation(Player) end)
	Local.Recompute(Player, Discipline)
	Shared.ViolationAdded:Fire(Player, Record)
	return Record
end

function Shared.Reduce(Player: Player, Amount: number, Reason: string?)
	local Discipline = Shared.GetData(Player)
	if not Discipline or Amount <= 0 or Discipline.Points <= 0 then return end

	Discipline.Points = math.max(0, Discipline.Points - Amount)
	Local.Recompute(Player, Discipline)
end

function Shared.ServeDetention(Player: Player)
	local Discipline = Shared.GetData(Player)
	if not Discipline or Discipline.DetentionsOwed <= 0 then return false end

	Discipline.DetentionsOwed -= 1
	Discipline.DetentionsServed += 1
	Discipline.Points = math.max(0, Discipline.Points - Config.Recovery.ServedDetention)

	Notifications.Notify(Player, {
		Title = `Detention served`;
		Text = `-{Config.Recovery.ServedDetention} discipline points`;
		Kind = `Good`;
		Duration = 5;
	})

	Local.Recompute(Player, Discipline)
	Shared.DetentionServed:Fire(Player)
	return true
end

-- (2.37) Notoriety (Services.School.Notoriety) hears every report; required lazily (it requires this module)
function Local.Notoriety(): any?
	local Ok, M = pcall(function() return require(ServerScriptService.Services.School.Notoriety) end)
	return if Ok then M else nil
end

-- Witness framework entry point. Returns true if the suspect was punished.
function Shared.ReportIncident(Incident): boolean
	local State = SchoolClock.GetState()
	Incident.Day = State.Day
	Incident.Time = State.ClockText

	table.insert(Incidents, 1, Incident)
	while #Incidents > MAX_INCIDENTS do table.remove(Incidents) end

	local Bonus = 0
	local N = Local.Notoriety()
	if N and N.OnReport then
		local Ok, B = pcall(N.OnReport, Incident)
		if Ok and type(B) == `number` then Bonus = B end
	end

	local Suspect = Incident.Suspect
	if Incident.Recognized and typeof(Suspect) == `Instance` and Suspect:IsA(`Player`) then
		Shared.AddViolation(Suspect, Incident.Type, { Witness = Incident.Witness; Bonus = Bonus })
		return true
	end
	return false
end

function Shared.GetIncidents(): { any }
	return table.clone(Incidents)
end

---| Daily upkeep |---

function Local.Tick()
	local Day = SchoolClock.GetState().Day

	for _, Player in Players:GetPlayers() do
		local Discipline = Shared.GetData(Player)
		if not Discipline then continue end

		local Changed = Player:GetAttribute(`DisciplineLevel`) == nil -- first time seen
		if Discipline.LastDecayDay < 0 then
			Discipline.LastDecayDay = Day
		elseif Day > Discipline.LastDecayDay then
			local Days = Day - Discipline.LastDecayDay
			Discipline.LastDecayDay = Day
			Discipline.Points = math.max(0, Discipline.Points - Days * Config.Recovery.DailyDecay)
			Changed = true
		end

		-- Re-check timed levels (probation / suspension end) once per tick.
		if Changed
			or (Discipline.SuspendedUntilDay >= 0 and Day >= Discipline.SuspendedUntilDay)
			or (Discipline.ProbationUntilDay >= 0 and Day >= Discipline.ProbationUntilDay) then
			Local.Recompute(Player, Discipline, Player:GetAttribute(`DisciplineLevel`) == nil)
		end
	end
end

function Shared.OnStart()
	-- Teachers take attendance: results feed the ladder directly.
	Attendance.Recorded:Connect(function(Player: Player, Record)
		if Record.Status == `Present` then
			Shared.Reduce(Player, Config.Recovery.PresentClass, `Attended class`)
		elseif Config.Violations[Record.Status] then
			local Witness = `Teacher`
			pcall(function() -- (2.28) the room's teacher, if they're at the desk (Services.School.Teachers)
				Witness = require(game:GetService(`ServerScriptService`).Services.School.Teachers).NameFor(Record.Room, Record.Period)
			end)
			Shared.AddViolation(Player, Record.Status, { Witness = Witness })
		end
	end)

	task.spawn(function()
		while true do
			local Ok, Err = pcall(Local.Tick)
			if not Ok then warn(`[Discipline] {Err}`) end
			task.wait(TICK)
		end
	end)
end

return Shared
