--[[
	Class activities (server authoritative)

	Start: the "Start lesson" prompt on the teacher's desk of the current class's room
	(only during that class, only while you're in the room).
	Play: the client sends actions; the game module (ServerStorage.Activities.<Type>) judges them.
	End: finished, out of time, or the bell rings -> graded A+..F. Leaving the room, quitting,
	or disconnecting cancels it (no grade).
	Rewards (C or better, once per class period): Yen by grade, +1 class level (max 5).
	Replaying a period you already passed is practice (no rewards).
	The grade is also written to that period's attendance record.
	(1.47) Substitute days (Services.School.Substitutes, Config.Substitutes): a covered class runs at the substitute's
	level / time / pay rule, may run another minigame (Swap, Game), or sends the student on an errand (GrantErrand pays it
	as an A).

	Game module interface:
		Start(Session, Level, StartAt) -> client payload
		Handle(Session, Action, Data, Now) -> (reply?, finished)
		Tick?(Session, Now) -> (finished, update?)
		Score(Session) -> (earned, max)
		TimeLimit(Level) -> seconds
]]

---| Services |---

local Players = game:GetService(`Players`)
local HttpService = game:GetService(`HttpService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Config = require(ReplicatedStorage.Config.Activities)
local Classes = require(ReplicatedStorage.Config.Classes)
local Interaction = require(ReplicatedStorage.Config.Interaction)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local SchoolClock = require(ServerScriptService.Services.School.SchoolClock)
local Attendance = require(ServerScriptService.Services.School.Attendance)
local Data = require(ServerScriptService.Services.Player.Data)
local Notifications = require(ServerScriptService.Services.Features.Notifications)

local TICK = 0.25

-- (1.47) Substitutes requires this module, so it's loaded on use
local function Subs()
	local Ok, M = pcall(require, ServerScriptService.Services.School.Substitutes)
	return Ok and M or nil
end
local MAX_ACTIONS_PER_SECOND = 20

local Sessions = {} :: { [Player]: any }

local Local = {}
local Shared = {}

Shared.Finished = SignalPlus() -- (Player, Subject, Result)   class lessons only
-- Optional: function(Player, Subject, Result) -> extra line for the grade sheet. Set by Factions
-- for Night Study sessions (which pay faction standing instead of class rewards).
Shared.StudyHandler = nil :: ((Player, string, any) -> string?)?

---| Helpers |---

function Local.GradeFor(Percent: number): string
	for _, Grade in Config.Grades do
		if Percent >= Grade.Min then return Grade.Letter end
	end
	return `F`
end

function Local.GradeRank(Letter: string?): number
	for Index, Grade in Config.Grades do
		if Grade.Letter == Letter then return #Config.Grades - Index + 1 end
	end
	return 0
end

function Local.Pick(List: { string }): string
	return List[math.random(1, #List)]
end

function Local.SubjectForRoom(RoomId: string): (string?, string?)
	for PeriodName, Class in Classes.Periods do
		if Class.Room == RoomId and Config.Subjects[Class.Subject] then
			return Class.Subject, PeriodName
		end
	end
	return nil, nil
end

function Local.GetClassData(Player: Player, Subject: string)
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil, nil end
	if typeof(Profile.Classes) ~= `table` then Profile.Classes = {} end

	local ClassData = Profile.Classes[Subject]
	if typeof(ClassData) ~= `table` then
		ClassData = { Level = 1; Passes = 0; BestGrade = ``; LastRewardKey = `` }
		Profile.Classes[Subject] = ClassData
	end
	return ClassData, Profile
end

function Local.Send(Player: Player, Message)
	if Player.Parent then Packets.ActivityEvent:FireClient(Player, Message) end
end

---| Sessions |---

function Local.TryStart(Player: Player, RoomId: string)
	if Sessions[Player] then return end
	if Player:GetAttribute(`Enrolled`) == false then -- Services.School.Enrollment
		Notifications.Notify(Player, { Title = `You're not enrolled yet`; Text = `Sign up at the Enrollment desk outside the Records Office.`; Kind = `Info`; Duration = 4 })
		return
	end

	local Subject = Local.SubjectForRoom(RoomId)
	if not Subject then return end

	local State = SchoolClock.GetState()
	local Current = State.Segment.Kind == `Class` and Classes.Periods[State.Segment.Name]
	if not Current or Current.Room ~= RoomId then
		Notifications.Notify(Player, { Title = `No {Subject} class right now`; Text = `Check the timetable.`; Kind = `Info`; Duration = 3 })
		return
	end
	if Player:GetAttribute(`ClassInRoom`) ~= true then
		Notifications.Notify(Player, { Title = `Take your seat first`; Kind = `Info`; Duration = 3 })
		return
	end

	local ClassData = Local.GetClassData(Player, Subject)
	if not ClassData then return end

	local Key = `D{State.Day}-S{State.SegmentIndex}`
	local Practice = ClassData.LastRewardKey == Key
	-- (1.47) a substitute covering this class today
	local M = Subs()
	local Sub = M and M.For(Subject)
	if Sub and Sub.Twist == `Errand` then
		if Practice then
			Notifications.Notify(Player, { Title = Sub.Sub.Name; Text = `You've already done my errand. Sit. Quietly.`; Kind = `Info`; Duration = 4 })
		else
			M.StartErrand(Player, Subject, Key, RoomId)
		end
		return
	end
	Local.Begin(Player, Subject, {
		Room = RoomId;
		Key = Key;
		SegmentIndex = State.SegmentIndex;
		Practice = Practice;
		Sub = Sub;
	})
end

-- Night Study: same games, started outside class (e.g. the Vigil's Archive table).
-- No class rewards; StudyHandler decides the payout. InRoom() is checked every tick.
function Shared.StartStudy(Player: Player, Subject: string, InRoom: () -> boolean): boolean
	if Sessions[Player] or not Config.Subjects[Subject] then return false end
	Local.Begin(Player, Subject, { Study = true; InRoom = InRoom })
	return Sessions[Player] ~= nil
end

function Local.Begin(Player: Player, Subject: string, Context)
	local Character = Player.Character
	local Humanoid = Character and Character:FindFirstChildWhichIsA(`Humanoid`)
	if not Humanoid or Humanoid.Health <= 0 or Humanoid:GetAttribute(`Downed`) then return end

	local ClassData = Local.GetClassData(Player, Subject)
	if not ClassData then return end

	local Def = Config.Subjects[Subject]
	local Sub = Context.Sub
	if Sub then -- (1.47) a substitute's twist: another subject's minigame, or one only substitutes run
		if Sub.Game then Def = Sub.Game
		elseif Sub.SwapSubject and Config.Subjects[Sub.SwapSubject] then Def = Config.Subjects[Sub.SwapSubject] end
	end
	local GameModule = ServerStorage.Activities:FindFirstChild(Def.Type)
	if not GameModule then
		warn(`[Activities] missing game module {Def.Type}`)
		return
	end
	local Game = require(GameModule)

	local Now = os.clock()
	local Level = math.clamp(ClassData.Level or 1, 1, Config.MaxLevel)
	local Rule = Sub and Sub.Rule or {}
	local PlayLevel = math.clamp(Level + (Rule.LevelOffset or 0), 1, Config.MaxLevel) -- (1.47) harder / easier today

	local S = {
		Id = HttpService:GenerateGUID(false);
		Player = Player;
		Subject = Subject;
		Room = Context.Room;
		Def = Def;
		Game = Game;
		Level = Level;
		Key = Context.Key;
		SegmentIndex = Context.SegmentIndex;
		Practice = Context.Practice == true;
		Study = Context.Study == true;
		InRoom = Context.InRoom;
		ActionTimes = {};
		Sub = Sub;
		PlayLevel = PlayLevel;
	}

	local StartAt = Now + Config.IntroSeconds + (if Sub then 2 else 0) -- (1.47) a moment longer to read the substitute's rule
	local Ok, Payload = pcall(Game.Start, S, PlayLevel, StartAt)
	if not Ok then
		warn(`[Activities] {Def.Type}.Start failed: {Payload}`)
		return
	end

	local TimeLimit = Game.TimeLimit(PlayLevel) * (Rule.TimeMult or 1)
	if typeof(Payload) == `table` and Payload.TimeLimit then Payload.TimeLimit = TimeLimit end
	S.EndsAt = StartAt + TimeLimit
	S.Freeze = StateManager.CreateState(Character, `InActivity`)
	Sessions[Player] = S

	Local.Send(Player, {
		Type = `Start`;
		Id = S.Id;
		Subject = Subject;
		Title = Def.Title;
		Tagline = if Sub then `{Sub.Sub.Name}: {Sub.RuleName}. {Def.Tagline}` else Def.Tagline;
		Activity = Def.Type;
		Level = PlayLevel;
		Practice = S.Practice;
		Study = S.Study;
		Intro = Config.IntroSeconds + (if Sub then 2 else 0);
		TimeLimit = TimeLimit;
		Payload = Payload;
		Substitute = Sub and { Name = Sub.Sub.Name; Title = Sub.Sub.Title; Rule = Sub.RuleName; RuleText = Sub.RuleText } or nil;
	})
end

function Local.Close(S)
	if Sessions[S.Player] == S then Sessions[S.Player] = nil end
	if S.Freeze then pcall(function() S.Freeze:Destroy() end) end
end

function Local.Cancel(S, Message: string)
	Local.Close(S)
	Local.Send(S.Player, { Type = `Result`; Id = S.Id; Cancelled = true; Message = Message })
end

function Local.Finish(S, Reason: string?)
	if Sessions[S.Player] ~= S then return end
	Local.Close(S)

	local Player = S.Player
	local Ok, Earned, Max = pcall(S.Game.Score, S)
	if not Ok or not Max or Max <= 0 then Earned, Max = 0, 1 end

	local Percent = math.clamp(math.floor(Earned / Max * 100 + 0.5), 0, 100)
	local Grade = Local.GradeFor(Percent)
	local Passed = Percent >= Config.PassPercent

	local Result = {
		Type = `Result`; Id = S.Id; Subject = S.Subject; Title = S.Def.Title;
		Percent = Percent; Grade = Grade; Passed = Passed; Practice = S.Practice; Reason = Reason;
		Yen = 0; LevelUp = false; Level = S.Level;
	}

	-- Night Study: no class rewards; the faction handler pays out instead.
	if S.Study then
		Result.Study = true
		if Shared.StudyHandler then
			local Ok2, Line = pcall(Shared.StudyHandler, Player, S.Subject, Result)
			if Ok2 and Line then Result.Extra = Line end
		end
		Result.Line = Local.Pick(if Passed then Config.TeacherLines.Pass else Config.TeacherLines.Fail)
		Local.Send(Player, Result)
		return
	end

	local ClassData, Profile = Local.GetClassData(Player, S.Subject)
	if ClassData and not S.Practice then
		if Local.GradeRank(Grade) > Local.GradeRank(ClassData.BestGrade) then
			ClassData.BestGrade = Grade
		end

		if Passed then
			ClassData.LastRewardKey = S.Key
			ClassData.Passes += 1
			if ClassData.Level < Config.MaxLevel then
				ClassData.Level += 1
				Result.LevelUp = true
			end
			Result.Level = ClassData.Level

			-- LessonYenBonus: set by Factions (Vigil "Blessed Scholar" perk).
			local Yen = math.floor((Config.RewardYen[Grade] or 0) * (Player:GetAttribute(`LessonYenBonus`) or 1))
			if S.Sub then Yen, Result.SubNote = Local.SubPay(S.Sub, Grade, Yen) end -- (1.47)
			Result.Yen = Yen
			if Yen > 0 then
				Data.UpdateState(Player, { type = `UpdateYen`; amount = Yen })
			end
			Player:SetAttribute(`LessonPassedKey`, S.Key)
		end

		Data.UpdateState(Player, { type = `SetClasses`; classes = Profile.Classes })
		Attendance.SetActivityResult(Player, S.Key, Grade)
	end

	Result.Line = Local.Pick(if S.Practice then Config.TeacherLines.Practice elseif Passed then Config.TeacherLines.Pass else Config.TeacherLines.Fail)
	if S.Sub then -- (1.47) the substitute marks it
		Result.Line = Local.Pick(if Passed then S.Sub.Sub.Lines.Pass else S.Sub.Sub.Lines.Fail)
		Result.Substitute = S.Sub.Sub.Name
		if not Passed and S.Sub.Rule.DoubleOrNothing and not S.Practice then Result.SubNote = `Double or nothing: the house keeps it.` end
	end
	Local.Send(Player, Result)

	if not S.Practice then
		Notifications.Notify(Player, {
			Title = `{S.Subject}: grade {Grade}`;
			Text = if Passed then (if Result.LevelUp then `Passed! Level {Result.Level} unlocked` else `Passed!`) else `Failed. Try again this period.`;
			Kind = if Passed then `Good` else `Bad`;
			Duration = 5;
		})
	end

	Shared.Finished:Fire(Player, S.Subject, Result)
end

-- (1.47) a substitute's pay rule: YenMult, and Double or Nothing (that grade or better doubles, below it pays nothing)
function Local.SubPay(Sub, Grade: string, Yen: number): (number, string?)
	local Rule = Sub.Rule or {}
	local Mult = Rule.YenMult or 1
	local Note = if Mult ~= 1 then `{Sub.RuleName}: pay x{Mult}` else nil
	local D = Rule.DoubleOrNothing
	if D then
		if Local.GradeRank(Grade) >= Local.GradeRank(D.Grade) then
			Mult *= 2
			Note = `Double or nothing: doubled!`
		else
			Mult = 0
			Note = `Double or nothing: the house keeps it.`
		end
	end
	return math.floor(Yen * Mult + 0.5), Note
end

-- (1.47) an errand for a substitute, done before the bell: it counts as passing the lesson with an A
function Shared.GrantErrand(Player: Player, Subject: string, Key: string, Entry)
	local ClassData, Profile = Local.GetClassData(Player, Subject)
	if not ClassData or ClassData.LastRewardKey == Key then return false end
	local Grade = `A`
	local Result = { Type = `Result`; Subject = Subject; Title = `Errand`; Percent = 100; Grade = Grade; Passed = true; Practice = false;
		Reason = `Errand`; Yen = 0; LevelUp = false; Level = ClassData.Level; Errand = true }
	if Local.GradeRank(Grade) > Local.GradeRank(ClassData.BestGrade) then ClassData.BestGrade = Grade end
	ClassData.LastRewardKey = Key
	ClassData.Passes += 1
	if ClassData.Level < Config.MaxLevel then
		ClassData.Level += 1
		Result.LevelUp = true
	end
	Result.Level = ClassData.Level
	local Yen = math.floor((Config.RewardYen[Grade] or 0) * (Player:GetAttribute(`LessonYenBonus`) or 1))
	if Entry then Yen, Result.SubNote = Local.SubPay(Entry, Grade, Yen) end
	Result.Yen = Yen
	if Yen > 0 then Data.UpdateState(Player, { type = `UpdateYen`; amount = Yen }) end
	Player:SetAttribute(`LessonPassedKey`, Key)
	Data.UpdateState(Player, { type = `SetClasses`; classes = Profile.Classes })
	Attendance.SetActivityResult(Player, Key, Grade)
	Notifications.Notify(Player, {
		Title = `{Subject}: errand done, grade {Grade}`;
		Text = (if Result.LevelUp then `Passed! Level {Result.Level} unlocked` else `Passed!`) .. (if Yen > 0 then `  +\u{A5}{Yen}` else ``);
		Kind = `Good`;
		Duration = 6;
	})
	Shared.Finished:Fire(Player, Subject, Result)
	return true
end

function Local.OnAction(Player: Player, Message)
	local S = Sessions[Player]
	if not S or typeof(Message) ~= `table` or Message.Id ~= S.Id then return end

	-- Rate limit: drop floods.
	local Now = os.clock()
	while S.ActionTimes[1] and Now - S.ActionTimes[1] > 1 do table.remove(S.ActionTimes, 1) end
	if #S.ActionTimes >= MAX_ACTIONS_PER_SECOND then return end
	table.insert(S.ActionTimes, Now)

	if Message.Action == `Quit` then
		Local.Cancel(S, `You walked out of the lesson.`)
		return
	end
	if typeof(Message.Action) ~= `string` then return end

	local Ok, Reply, Finished = pcall(S.Game.Handle, S, Message.Action, Message.Data, Now)
	if not Ok then
		warn(`[Activities] {S.Def.Type}.Handle error: {Reply}`)
		return
	end

	if Reply then
		Local.Send(Player, { Type = `Update`; Id = S.Id; Payload = Reply })
	end
	if Finished then
		Local.Finish(S, `Done`)
	end
end

function Local.Tick()
	local Now = os.clock()
	local State = SchoolClock.GetState()

	for Player, S in Sessions do
		if not Player.Parent then
			Local.Close(S)
		elseif S.Study then
			if not (S.InRoom and S.InRoom()) then
				Local.Cancel(S, `You walked away from the study table.`)
			elseif Now >= S.EndsAt then
				Local.Finish(S, `Time`)
			elseif S.Game.Tick then
				local Ok, Finished, Update = pcall(S.Game.Tick, S, Now)
				if Ok and Update then Local.Send(Player, { Type = `Update`; Id = S.Id; Payload = Update }) end
				if Ok and Finished then Local.Finish(S, `Done`) end
			end
		elseif Player:GetAttribute(`ClassInRoom`) ~= true and State.SegmentIndex == S.SegmentIndex then
			Local.Cancel(S, `You left the classroom.`)
		elseif State.SegmentIndex ~= S.SegmentIndex then
			Local.Finish(S, `Bell`) -- class ended: grade what was done
		elseif Now >= S.EndsAt then
			Local.Finish(S, `Time`)
		elseif S.Game.Tick then
			local Ok, Finished, Update = pcall(S.Game.Tick, S, Now)
			if Ok and Update then
				Local.Send(Player, { Type = `Update`; Id = S.Id; Payload = Update })
			end
			if Ok and Finished then
				Local.Finish(S, `Done`)
			end
		end
	end
end

function Local.CreatePrompts()
	local School = workspace:FindFirstChild(`School`)
	if not School then return end

	for _, Class in Classes.Periods do
		local Def = Config.Subjects[Class.Subject]
		local Room = School:FindFirstChild(Class.Room)
		local Desk = Room and Room:FindFirstChild(`TeacherDesk`) :: BasePart?
		if not Def or not Desk or Desk:FindFirstChild(`LessonPrompt`) then continue end

		local Prompt = Instance.new(`ProximityPrompt`)
		Prompt.Name = `LessonPrompt`
		Prompt.ActionText = `Start lesson`
		Prompt.ObjectText = `{Class.Subject}: {Def.Title}`
		Prompt.KeyboardKeyCode = Interaction.PromptKey
		Prompt.GamepadKeyCode = Interaction.GamepadKey
		Prompt.HoldDuration = 0.3
		Prompt.MaxActivationDistance = 12
		Prompt.RequiresLineOfSight = false
		local RoomId = Class.Room
		Prompt.Triggered:Connect(function(Player)
			local Ok, Err = pcall(Local.TryStart, Player, RoomId)
			if not Ok then warn(`[Activities] start failed: {Err}`) end
		end)
		Prompt.Parent = Desk
	end
end

---| API |---

function Shared.IsInActivity(Player: Player): boolean
	return Sessions[Player] ~= nil
end

-- Testing (TestBridge): start without the prompt.
function Shared.StartForTests(Player: Player, RoomId: string)
	Local.TryStart(Player, RoomId)
	return Sessions[Player] ~= nil
end

function Shared.GetSessionForTests(Player: Player)
	return Sessions[Player]
end

-- Testing (TestBridge): act as if the player's client sent this action (same checks and judging).
function Shared.ActionForTests(Player: Player, Action: string, Data: any): boolean
	local S = Sessions[Player]
	if not S then return false end
	Local.OnAction(Player, { Id = S.Id; Action = Action; Data = Data })
	return true
end

function Shared.OnStart()
	Local.CreatePrompts()

	Packets.ActivityAction.OnServerEvent:Connect(function(Player, Message)
		local Ok, Err = pcall(Local.OnAction, Player, Message)
		if not Ok then warn(`[Activities] {Err}`) end
	end)

	Players.PlayerRemoving:Connect(function(Player)
		local S = Sessions[Player]
		if S then Local.Close(S) end
	end)

	task.spawn(function()
		while true do
			task.wait(TICK)
			local Ok, Err = pcall(Local.Tick)
			if not Ok then warn(`[Activities] {Err}`) end
		end
	end)
end

return Shared
