--[[
	Attendance (server authoritative)

	Every second, during a Class period of the school clock, each player is checked
	against the zone of that period's room (a box test on the server, not Touched events).
	When the period ends, one record is saved per player:

		Present    arrived within GraceMinutes and stayed
		Tardy      arrived late (before TardyCutoffFraction of the period) and stayed
		LeftEarly  arrived but spent less than StayFraction of the remaining time in the room
		Absent     never arrived, or arrived after the cutoff
		Excused    joined the game too late in the period to attend

	Exploit / edge handling:
		- The period in progress is saved in player data (Attendance.InProgress), so leaving
		  and rejoining (any server: the clock is global) continues the same record. A record
		  left unfinished when a player leaves is finalized the next time they are seen.
		- LastRecordedKey stops the same period from being recorded or paid twice.
		- Presence only accrues for real elapsed time (clock jumps don't count).

	(1.47) Substitute days (Services.School.Substitutes): a student on a substitute's errand has a hall pass for the room
	(Player attribute NHHallPass = room id) and counts as in class. A Strict substitute books a late arrival again (+1
	Tardy) and pays OnTimeExp for arriving on time; a Lenient one counts late as Present.

	API:
		Attendance.Recorded(Player, Record)   -- signal, for discipline / quests later
		Attendance.GetCurrentClass(Player?)   -- { Period, Subject, Room } or nil (Player: their elective in an elective slot)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local Classes = require(ReplicatedStorage.Config.Classes)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local Rules = Classes.Attendance
local TICK = 1

local STATUS_TEXT = {
	Present = { Text = `Present`, Kind = `Good` };
	Tardy = { Text = `Tardy`, Kind = `Warning` };
	LeftEarly = { Text = `Left early`, Kind = `Bad` };
	Absent = { Text = `Absent`, Kind = `Bad` };
	Excused = { Text = `Excused`, Kind = `Info` };
}

local Zones = {} :: { [string]: BasePart }
local FirstSeen = {} :: { [Player]: number } -- absolute in-game minute the player was first seen this session
local Deferred = {} :: { [Player]: number } -- (audit) ticks a finalize has waited for a running lesson's grade

local Local = {}
local Shared = {}

Shared.Recorded = SignalPlus()

---| Helpers |---

function Local.RefreshZones()
	table.clear(Zones)
	local School = workspace:FindFirstChild(`School`)
	if not School then return end

	for _, Part in School:GetDescendants() do
		if Part:IsA(`BasePart`) and Part.Name == `Zone` and Part:GetAttribute(`RoomId`) then
			Zones[Part:GetAttribute(`RoomId`)] = Part
		end
	end
end

function Local.IsInRoom(Player: Player, RoomId: string): boolean
	local Zone = Zones[RoomId]
	local Character = Player.Character
	local Root = Character and Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Zone or not Root or not Humanoid or Humanoid.Health <= 0 then return false end

	local Offset = Zone.CFrame:PointToObjectSpace(Root.Position)
	local Half = Zone.Size / 2
	return math.abs(Offset.X) <= Half.X and math.abs(Offset.Y) <= Half.Y and math.abs(Offset.Z) <= Half.Z
end

-- (1.47) in the room, or out on a substitute's errand with a hall pass for it
function Local.InClass(Player: Player, RoomId: string): boolean
	return Local.IsInRoom(Player, RoomId) or Player:GetAttribute(`NHHallPass`) == RoomId
end

-- (1.47) the substitute covering this record's class, if any
function Local.SubFor(Progress)
	local Ok, Subs = pcall(require, ServerScriptService.Services.School.Substitutes)
	local E = Ok and Subs and Subs.Today()
	return if E and E.Subject == Progress.Subject and E.Day == Progress.Day then E else nil
end

-- (Electives) the player's own class in this slot: their term elective on Tue/Thu periods 3-4, else the base period
function Local.ClassFor(Segment, Day: number?, Player: Player?): any
	if Segment.Kind ~= `Class` then return nil end
	return Classes.For(Segment.Name, Day or SchoolClock.GetState().Day, Player)
end

function Shared.GetCurrentClass(Player: Player?)
	local State = SchoolClock.GetState()
	local Class = Local.ClassFor(State.Segment, State.Day, Player)
	if not Class then return nil end
	return { Period = State.Segment.Name, Subject = Class.Subject, Room = Class.Room }
end

function Local.EnsureData(Profile): any
	if typeof(Profile.Attendance) ~= `table` then
		Profile.Attendance = {
			Totals = { Present = 0; Tardy = 0; LeftEarly = 0; Absent = 0; Excused = 0 };
			Streak = 0; BestStreak = 0; LastRecordedKey = ``; Recent = {}; InProgress = false;
		}
	end
	return Profile.Attendance
end

---| Rules |---

function Shared.ComputeStatus(Progress): string
	local Duration = Progress.End - Progress.Start
	local EffectiveStart = Progress.JoinedAt
	local LateJoin = EffectiveStart > Progress.Start

	if not Progress.ArrivedAt then
		if LateJoin and (Progress.End - Progress.JoinedAt) < Rules.LateJoinMinMinutes then
			return `Excused`
		end
		return `Absent`
	end

	local Late = Progress.ArrivedAt - EffectiveStart
	if Late > Duration * Rules.TardyCutoffFraction then
		return `Absent`
	end

	local Window = Progress.End - Progress.ArrivedAt
	if Window > 0 and Progress.PresentMinutes < Window * Rules.StayFraction then
		return `LeftEarly`
	end

	if Late <= Rules.GraceMinutes then
		return `Present`
	end
	return `Tardy`
end

---| Records |---

-- A period counts as recorded if it is the last record or any kept recent record
-- (Recent holds more than a day's worth of periods).
function Local.AlreadyRecorded(Attendance, Key: string): boolean
	if Attendance.LastRecordedKey == Key then return true end
	for _, Record in Attendance.Recent do
		if Record.Key == Key then return true end
	end
	return false
end

function Local.Finalize(Player: Player, Profile)
	local Attendance = Local.EnsureData(Profile)
	local Progress = Attendance.InProgress
	if not Progress then return end

	Attendance.InProgress = false
	if Local.AlreadyRecorded(Attendance, Progress.Key) then return end

	local Status = Shared.ComputeStatus(Progress)
	-- (1.47) a substitute's late rule
	local Sub = Local.SubFor(Progress)
	local SubNote = nil
	if Sub and Sub.Rule then
		if Sub.Rule.Late == `Lenient` and Status == `Tardy` then
			Status = `Present`
			SubNote = `{Sub.Sub.Name} didn't notice you were late.`
		elseif Sub.Rule.Late == `Strict` and Status == `Tardy` then
			pcall(function() require(ServerScriptService.Services.School.Discipline).AddViolation(Player, `Tardy`, { By = Sub.Sub.Name }) end)
			SubNote = `{Sub.Sub.Name} marked you late. Twice.`
		elseif Sub.Rule.Late == `Strict` and Status == `Present` and Sub.Rule.OnTimeExp then
			pcall(function() require(ServerScriptService.Services.Player.Progression).Award(Player, Sub.Rule.OnTimeExp, `Class`, `On time for {Sub.Sub.Name}`) end)
			SubNote = `On time: {Sub.Sub.Name} approves (+{Sub.Rule.OnTimeExp} EXP).`
		end
	end
	Attendance.LastRecordedKey = Progress.Key
	Attendance.Totals[Status] = (Attendance.Totals[Status] or 0) + 1

	if Status == `Present` then
		Attendance.Streak += 1
		Attendance.BestStreak = math.max(Attendance.BestStreak, Attendance.Streak)
	elseif Status == `Absent` or Status == `LeftEarly` then
		Attendance.Streak = 0
	end

	local Record = {
		Key = Progress.Key;
		Day = Progress.Day;
		Period = Progress.Period;
		Subject = Progress.Subject;
		Room = Progress.Room;
		Status = Status;
		ArrivedAt = Progress.ArrivedAt and SchoolTime.FormatClock(Progress.ArrivedAt) or nil;
		MinutesInRoom = math.floor(Progress.PresentMinutes + 0.5);
		ActivityGrade = Progress.ActivityGrade; -- lesson minigame grade, if played
	}
	table.insert(Attendance.Recent, 1, Record)
	-- (1.39) Teacher's Pet: in class, with a B or better (Services.Social.Superlatives)
	if Status == `Present` and (Record.ActivityGrade == `B` or Record.ActivityGrade == `A` or Record.ActivityGrade == `A+`) then
		pcall(function() require(game:GetService(`ServerScriptService`).Services.Social.Superlatives).Count(Player, `Classes`) end)
	end
	while #Attendance.Recent > Rules.RecentLimit do
		table.remove(Attendance.Recent)
	end
	-- (1.40) the week's report card (Services.School.ReportCards)
	pcall(function() require(game:GetService(`ServerScriptService`).Services.School.ReportCards).Class(Player, Record.Subject, Status, Record.ActivityGrade) end)

	Data.UpdateState(Player, { type = `SetAttendance`; attendance = Attendance })

	local Reward = Rules.Rewards[Status]
	if Reward and Reward > 0 then
		Data.UpdateState(Player, { type = `UpdateYen`; amount = Reward })
	end

	local Info = STATUS_TEXT[Status]
	Notifications.Notify(Player, {
		Title = `{Progress.Period}: {Progress.Subject}`;
		Text = (if Reward and Reward > 0 then `{Info.Text}  (+{Reward} Yen)` else Info.Text)
			.. (if Progress.ActivityGrade then `  ·  Lesson grade {Progress.ActivityGrade}` else ``)
			.. (if SubNote then `  ·  {SubNote}` else ``);
		Kind = Info.Kind;
		Duration = 5;
	})

	Shared.Recorded:Fire(Player, Record)
end

-- (audit) a lesson still running (Activities grades a bell-ended one on its next 0.25 s tick)
function Local.LessonRunning(Player: Player): boolean
	local Ok, Activities = pcall(require, ServerScriptService.Services.School.Activities)
	return Ok and Activities ~= nil and Activities.IsInActivity(Player) == true
end

function Local.UpdatePlayer(Player: Player, State, AbsoluteMinute: number)
	local Profile = Data.GetProfile(Player)
	if not Profile then return end

	-- (2.7.3) still in the main menu (the creator or wardrobe after picking a slot): not at school yet. Nothing is
	-- tracked or finalized, and the first sighting waits for Enter, so entering mid-class counts like a late join
	-- (Excused near the end). An unfinished record from an earlier visit is finalized right after Enter.
	if Player:GetAttribute(`InMainMenu`) == true then
		Player:SetAttribute(`ClassRoom`, nil)
		Player:SetAttribute(`ClassInRoom`, nil)
		return
	end

	local Attendance = Local.EnsureData(Profile)
	FirstSeen[Player] = FirstSeen[Player] or AbsoluteMinute

	local Class = Local.ClassFor(State.Segment, State.Day, Player)
	local Key = `D{State.Day}-S{State.SegmentIndex}`

	-- Suspended: classes aren't expected, so an unfinished record is dropped, not counted.
	if Player:GetAttribute(`Suspended`) == true then
		Attendance.InProgress = false
	end

	-- Close a record from an earlier period (ended while online, or while away).
	if Attendance.InProgress and (not Class or Attendance.InProgress.Key ~= Key) then
		-- (audit) the bell can get here before Activities grades the lesson that was running (~1 in 8): wait up to 3 ticks
		-- so the grade lands on the record and the report card
		if (Deferred[Player] or 0) < 3 and Local.LessonRunning(Player) then
			Deferred[Player] = (Deferred[Player] or 0) + 1
			return
		end
		Deferred[Player] = nil
		Local.Finalize(Player, Profile)
	end

	-- Suspended students aren't expected in class (Discipline sets this attribute).
	if not Class or Player:GetAttribute(`Suspended`) == true then
		Player:SetAttribute(`ClassRoom`, nil)
		Player:SetAttribute(`ClassInRoom`, nil)
		return
	end

	if Local.AlreadyRecorded(Attendance, Key) then
		Player:SetAttribute(`ClassRoom`, Class.Room)
		Player:SetAttribute(`ClassInRoom`, Local.InClass(Player, Class.Room))
		return -- this period is already recorded (e.g. the clock was moved back)
	end

	local Segment = State.Segment
	local Progress = Attendance.InProgress
	if not Progress then
		-- Players online since before the bell started on time; later joiners start when seen.
		local PeriodStartAbsolute = State.Day * 1440 + Segment.Start
		local JoinedAt = if FirstSeen[Player] <= PeriodStartAbsolute then Segment.Start else math.max(Segment.Start, State.MinuteOfDay)

		Progress = {
			Key = Key;
			Day = State.Day;
			Period = Segment.Name;
			Subject = Class.Subject;
			Room = Class.Room;
			Start = Segment.Start;
			End = Segment.End;
			JoinedAt = JoinedAt;
			ArrivedAt = nil;
			PresentMinutes = 0;
			LastMinute = State.MinuteOfDay;
		}
		Attendance.InProgress = Progress
	end

	-- Only real elapsed time counts (a clock jump can't fill the presence meter).
	local Step = State.MinuteOfDay - (Progress.LastMinute or State.MinuteOfDay)
	local MaxStep = (TICK / SchoolTime.SecondsPerGameMinute()) * 2
	Step = math.clamp(Step, 0, MaxStep)
	Progress.LastMinute = State.MinuteOfDay

	local InRoom = Local.InClass(Player, Class.Room)
	if InRoom then
		Progress.ArrivedAt = Progress.ArrivedAt or State.MinuteOfDay
		Progress.PresentMinutes += Step
	end

	Player:SetAttribute(`ClassRoom`, Class.Room)
	Player:SetAttribute(`ClassInRoom`, InRoom)
end

function Local.Tick()
	local State = SchoolClock.GetState()
	local AbsoluteMinute = State.Day * 1440 + State.MinuteOfDay

	for _, Player in Players:GetPlayers() do
		local Ok, Err = pcall(Local.UpdatePlayer, Player, State, AbsoluteMinute)
		if not Ok then
			warn(`[Attendance] {Player.Name}: {Err}`)
		end
	end
end

-- Called by Activities: remembers the best lesson grade for the class in progress.
local GRADE_ORDER = { `F`, `D`, `C`, `B`, `A`, `A+` }
function Shared.SetActivityResult(Player: Player, Key: string, Grade: string)
	local Profile = Data.GetProfile(Player)
	local Progress = Profile and Local.EnsureData(Profile).InProgress
	if not Progress or Progress.Key ~= Key then return end

	local Old = Progress.ActivityGrade
	if not Old or (table.find(GRADE_ORDER, Grade) or 0) > (table.find(GRADE_ORDER, Old) or 0) then
		Progress.ActivityGrade = Grade
	end
end

-- Testing only (TestBridge): forget when the player was first seen this session,
-- so after a clock jump they count as online since before the bell.
function Shared.ResetSessionForTests(Player: Player)
	FirstSeen[Player] = nil
end

function Shared.OnStart()
	Local.RefreshZones()

	local School = workspace:FindFirstChild(`School`)
	if School then
		School.DescendantAdded:Connect(function(Part)
			if Part.Name == `Zone` then Local.RefreshZones() end
		end)
	end

	Players.PlayerRemoving:Connect(function(Player)
		FirstSeen[Player] = nil
		Deferred[Player] = nil -- (audit)
	end)

	task.spawn(function()
		while true do
			task.wait(TICK)
			Local.Tick()
		end
	end)
end

return Shared
