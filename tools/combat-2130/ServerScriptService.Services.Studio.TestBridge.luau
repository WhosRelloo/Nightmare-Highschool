--[[
	TestBridge (Studio only)

	Lives under Services.Studio, so ModuleLoader only starts it inside Studio.
	Creates ServerStorage.NHTestBridge (BindableFunction) so test tooling can run
	checks inside the game's own module instances (same require cache as the game).

	Usage (server): ServerStorage.NHTestBridge:Invoke("Command", ...)
]]

---| Services |---

local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Shared = {}
local Commands = {}

local function GetAI()
	return require(ServerScriptService.Services.AI.AI)
end

-- Prefers characters that EntityLoader has initialized (they get an Accessory folder).
local function FindCharacter(Name: string): Model?
	local Fallback = nil
	for _, Model in workspace.Live:GetChildren() do
		if Model.Name == Name and Model:FindFirstChildWhichIsA(`Humanoid`) then
			if Model:FindFirstChild(`Accessory`) then
				return Model
			end
			Fallback = Fallback or Model
		end
	end
	return Fallback
end

local function Describe(Model: Model)
	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`)
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	return {
		Name = Model.Name;
		Health = Humanoid and Humanoid.Health;
		Equip = Humanoid and Humanoid:GetAttribute(`Equip`);
		Posture = Humanoid and Humanoid:GetAttribute(`Posture`);
		WalkSpeed = Humanoid and Humanoid.WalkSpeed;
		Position = Root and Root.Position;
	}
end

-- Spawn AI NPCs through the real AI service.
function Commands.SpawnAI(Count: number?, Position: Vector3?, ConfigOverrides: { [string]: any }?)
	local AI = GetAI()
	local Config = table.clone(require(ReplicatedStorage.Config.NPC).Default)
	for Key, Value in ConfigOverrides or {} do
		Config[Key] = Value
	end

	local Names = {}
	for Index = 1, Count or 1 do
		local Npc = AI.Spawn(workspace.Live, script, nil, Config)
		if Npc and Npc.Character then
			if Position then
				Npc.Character:PivotTo(CFrame.new(Position + Vector3.new(Index * 4, 0, 0)))
			end
			table.insert(Names, Npc.Character.Name)
		end
	end
	return Names
end

-- Snapshot of every active AI NPC.
-- 1.23 enemy tests: make an NPC fight a given character (threat), and read its counters
function Commands.AIThreat(NpcName: string, AttackerName: string, Amount: number?)
	local Npc, Attacker = FindCharacter(NpcName), FindCharacter(AttackerName)
	if not (Npc and Attacker) then return false end
	GetAI().AddThreat(Npc, Attacker, Amount or 500)
	return true
end

function Commands.AIStats(NpcName: string)
	local Npc = FindCharacter(NpcName)
	if not Npc then return nil end
	local Out = { Tier = Npc:GetAttribute(`Difficulty`) }
	for K, V in Npc:GetAttributes() do
		local Key = K:match(`^NHStat_(.+)`)
		if Key then Out[Key] = V end
	end
	local H = Npc:FindFirstChildWhichIsA(`Humanoid`)
	Out.Health = H and math.floor(H.Health)
	return Out
end

-- 1.27 cliques Phase 2: start a scuffle or a confrontation by hand, and read what's going on
function Commands.Scuffle(Defender: string, Attacker: string)
	return require(ServerScriptService.Services.Social.CliqueFights).StartScuffle(Defender, Attacker)
end
function Commands.Confront(PlayerName: string, Clique: string)
	return require(ServerScriptService.Services.Social.CliqueFights).Confront(Players:FindFirstChild(PlayerName), Clique, -80)
end
function Commands.TurfWin(Owner: string, Rival: string, Winner: string) -- 1.28: count a scuffle result toward turf
	return require(ServerScriptService.Services.Social.CliqueFights).RecordWin(Owner, Rival, Winner, nil)
end
function Commands.FightState()
	return require(ServerScriptService.Services.Social.CliqueFights).State()
end
-- 1.33 cliques Phase 4: pranks, rumbles, dares, the bulletin
local function Pranks() return require(ServerScriptService.Services.Social.CliquePranks) end
local function Events() return require(ServerScriptService.Services.Social.CliqueEvents) end
function Commands.Prank(By: string, Victim: string) return Pranks().NpcPrank(By, Victim) end
function Commands.PrankMine(PlayerName: string, Victim: string, UseKit: boolean?) -- UseKit: spend a real kit (else skip it)
	return Pranks().PlayerPrank(Players:FindFirstChild(PlayerName), Victim, not UseKit)
end
function Commands.Messes() return Pranks().State() end
function Commands.PrankHit(PlayerName: string, Down: boolean?) return Pranks().TestHit(Players:FindFirstChild(PlayerName), Down) end
function Commands.CleanAll() Pranks().CleanAll() return true end
function Commands.Rumble(A: string, B: string, Now: boolean?) -- Now: start it now; else plan it for tomorrow (texts everyone)
	local F = require(ServerScriptService.Services.Social.CliqueFights)
	if Now then return F.StartRumble(A, B) end
	return F.PlanRumble(A, B)
end
function Commands.RumbleState() return require(ServerScriptService.Services.Social.CliqueFights).Rumble() end
function Commands.Dares(PlayerName: string) return Events().SendDares(Players:FindFirstChild(PlayerName), true) end
function Commands.Today(PlayerName: string) return Events().Today(Players:FindFirstChild(PlayerName)) end
function Commands.DareFor(Leader: string) return require(ServerScriptService.Services.Quests.Quests).DareFor(Leader) end
-- 1.34 cliques Phase 5: showdowns
local function Showdowns() return require(ServerScriptService.Services.Social.CliqueShowdowns) end
function Commands.Showdown(PlayerName: string, Clique: string, Path: string?) return Showdowns().StartFight(Players:FindFirstChild(PlayerName), Clique, Path) end
function Commands.ShowdownState() return Showdowns().State() end
function Commands.ShowdownHurt(Clique: string, Amount: number) return Showdowns().HurtForTests(Clique, Amount) end
function Commands.ShowdownWin(PlayerName: string, Clique: string) return Showdowns().WinForTests(Players:FindFirstChild(PlayerName), Clique) end
function Commands.CanShowdown(PlayerName: string, Clique: string) return Showdowns().CanChallenge(Players:FindFirstChild(PlayerName), Clique) end
-- 1.35 cliques Phase 6: membership. MemberTest treats a no-slot player as a member at a rank (nothing saved); nil clique ends it.
local function Membership() return require(ServerScriptService.Services.Social.CliqueMembership) end
function Commands.MemberTest(PlayerName: string, Clique: string?, Rank: string?) return Membership().TestMember(Players:FindFirstChild(PlayerName), Clique, Rank) end
function Commands.MemberState(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local M = Membership()
	local Crew = 0
	for _, C in (workspace:FindFirstChild(`Live`) and workspace.Live:GetChildren() or {}) do if C:GetAttribute(`NHCrewOf`) == P.UserId then Crew += 1 end end
	return { Current = M.Current(P); Rank = M.Rank(P); Crew = Crew; NHClique = P:GetAttribute(`NHClique`); Summary = M.Summary(P) }
end
-- (1.38.3) CliqueCanJoin: a second Commands.CanJoin (the factions one, further down) used to replace this one
function Commands.CliqueCanJoin(PlayerName: string, Clique: string) return { Membership().CanJoin(Players:FindFirstChild(PlayerName), Clique) } end
function Commands.GuardDuty(PlayerName: string, Clique: string) return require(ServerScriptService.Services.Social.CliquePranks).GuardDuty(Players:FindFirstChild(PlayerName), Clique) end

-- 1.39 bundle 1: the daily special, the superlatives, the notice board
local function Sup() return require(ServerScriptService.Services.Social.Superlatives) end
function Commands.SupCount(PlayerName: string, Id: string, N: number?) Sup().Count(Players:FindFirstChild(PlayerName), Id, N) return Sup().State(Players:FindFirstChild(PlayerName)) end
function Commands.SupFlush() return Sup().FlushForTests() end
function Commands.SupFetch(Week: number?) return Sup().FetchForTests(Week) end
function Commands.SupAward(PlayerName: string) return Sup().AwardForTests(Players:FindFirstChild(PlayerName)) end
function Commands.SupState(PlayerName: string) return Sup().State(Players:FindFirstChild(PlayerName)) end
function Commands.BoardRefresh() return require(ServerScriptService.Services.Features.NoticeBoard).RefreshForTests() end
-- 1.40 report cards
local function Reports() return require(ServerScriptService.Services.School.ReportCards) end
function Commands.ReportClass(PlayerName: string, Subject: string, Status: string, Grade: string?) Reports().Class(Players:FindFirstChild(PlayerName), Subject, Status, Grade) return Reports().State(Players:FindFirstChild(PlayerName)) end
function Commands.ReportViolation(PlayerName: string) Reports().Violation(Players:FindFirstChild(PlayerName)) return true end
function Commands.ReportState(PlayerName: string) return Reports().State(Players:FindFirstChild(PlayerName)) end
function Commands.ReportList(PlayerName: string) return Reports().List(Players:FindFirstChild(PlayerName)) end
function Commands.ReportDeliver(PlayerName: string) return Reports().DeliverForTests(Players:FindFirstChild(PlayerName)) end -- hand out this week's card now
-- 1.42 Lost & Found
local function Lost() return require(ServerScriptService.Services.Features.LostFound) end
function Commands.LostSpawn(Id: string?, At: Vector3?) local M = Lost().SpawnForTests(Id, At and CFrame.new(At)) return M and M:GetFullName() end
function Commands.LostState() return Lost().State() end
-- 1.45 the fortune teller
local function Fortune() return require(ServerScriptService.Services.Features.Fortune) end
function Commands.FortuneRead(PlayerName: string, Card: string?) return Fortune().ReadForTests(Players:FindFirstChild(PlayerName), Card) end
function Commands.FortuneReset(PlayerName: string) return Fortune().ResetForTests(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneHints(PlayerName: string) return Fortune().Hints(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneToday(PlayerName: string) return Fortune().Today(Players:FindFirstChild(PlayerName)) end
function Commands.FortuneStanding(PlayerName: string, Id: string, Value: number?) return Fortune().StandingForTests(Players:FindFirstChild(PlayerName), Id, Value) end
function Commands.TodaySpecial() local It = require(ReplicatedStorage.Config.Items).TodaySpecial() return It and It.Id end
function Commands.AIStatus()
	local Result = {}
	for _, Npc in GetAI().GetActive() do
		if not Npc.Character then continue end
		local Info = Describe(Npc.Character)
		Info.State = Npc.State
		Info.Target = Npc.Target and Npc.Target.Name
		Info.Action = Npc.ActionManager and Npc.ActionManager.Action
		table.insert(Result, Info)
	end
	return Result
end

function Commands.DestroyAI()
	GetAI().DestroyAll()
	return true
end

-- Current action + states for any character in Live.
function Commands.Inspect(Name: string)
	local Model = FindCharacter(Name)
	if not Model then return nil end

	local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
	local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
	local TagService = require(ReplicatedStorage.Packages.Core.TagService)

	local States = {}
	for _, State in StateManager.getEntityCache(Model).States do
		table.insert(States, State.Name)
	end

	local Info = Describe(Model)
	Info.Action = ActionManager.new(Model).Action
	Info.States = States
	Info.Tags = TagService:ReturnTags(Model)
	return Info
end

-- Make a character perform an action through the real ActionManager (server side).
function Commands.DoAction(Name: string, Action: string, ...)
	local Model = FindCharacter(Name)
	if not Model then return false end

	local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
	if Action == `M1` then
		ActionManager.M1(Model)
		return true
	end
	return ActionManager.new(Model):Activate(Action, ...) == true
end

---| Downed / Carry / Grip |---

local function GetDowned()
	return require(ServerScriptService.Services.Features.Downed)
end

-- Deal damage through the real combat damage entry point (can down the target).
function Commands.Damage(Name: string, Amount: number, AttackerName: string?)
	local Target = FindCharacter(Name)
	if not Target then return nil end
	return GetDowned().ApplyDamage(Target, Amount, AttackerName and FindCharacter(AttackerName) or nil)
end

function Commands.ToggleCarry(ActorName: string)
	local Actor = FindCharacter(ActorName)
	return Actor and GetDowned().ToggleCarry(Actor)
end

function Commands.Grip(ActorName: string)
	local Actor = FindCharacter(ActorName)
	return Actor and GetDowned().StartGrip(Actor)
end

function Commands.Recover(Name: string)
	local Target = FindCharacter(Name)
	if Target then GetDowned().Recover(Target) end
	return Target ~= nil
end

local EventLog = {}
local Recording = false

function Commands.RecordEvents()
	table.clear(EventLog)
	if Recording then return true end
	Recording = true

	local function Log(Text: string)
		table.insert(EventLog, string.format("%.2f %s", os.clock(), Text))
	end
	local function NameOf(Model: Model?) return Model and Model.Name or "nil" end

	local Downed = GetDowned()
	Downed.OnDowned:Connect(function(Target, Attacker) Log(`Downed {NameOf(Target)} by {NameOf(Attacker)}`) end)
	Downed.OnRecovered:Connect(function(Target) Log(`Recovered {NameOf(Target)}`) end)
	Downed.OnExecuted:Connect(function(Gripper, Target) Log(`Executed {NameOf(Target)} by {NameOf(Gripper)}`) end)
	Downed.OnDefeated:Connect(function(Target, Killer) Log(`Defeated {NameOf(Target)} killer={NameOf(Killer)}`) end)
	GetAI().NPCDefeated:Connect(function(Npc, Killer) Log(`NPCDefeated {NameOf(Npc)} killer={NameOf(Killer)}`) end)
	return true
end

function Commands.Events()
	return table.clone(EventLog)
end

---| Player data |---

-- Read-only copy of a player's saved profile data.
function Commands.Profile(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return nil end
	local Data = require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Data and table.clone(Data)
end

---| School clock |---

---| Combat log (2.13.0, combat concept 14) |---

function Commands.CombatLog(Count: number?)
	return require(ServerStorage.Packages.CombatLog).Get(Count)
end

function Commands.CombatLogClear()
	require(ServerStorage.Packages.CombatLog).Clear()
	return true
end

function Commands.SetTime(TimeText: string, Day: number?)
	require(ServerScriptService.Services.School.SchoolClock).SetTime(TimeText, Day)
	return true
end

function Commands.ClockState()
	local Clock = require(ServerScriptService.Services.School.SchoolClock)
	local State = Clock.GetState()
	return {
		Day = State.DayName;
		Time = State.ClockText;
		Period = State.Segment.Name;
		Kind = State.Segment.Kind;
		MinutesLeft = State.MinutesLeft;
		SchoolHours = State.IsSchoolHours;
		ExpMultiplier = Clock.GetExpMultiplier();
		LightingClockTime = game:GetService(`Lighting`).ClockTime;
	}
end

function Commands.SetClockSpeed(RealSecondsPerGameHour: number)
	require(ServerScriptService.Services.School.SchoolClock).SetSpeed(RealSecondsPerGameHour)
	return true
end

function Commands.Notify(PlayerName: string, Title: string, Text: string?, Kind: string?)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return false end
	require(ServerScriptService.Services.Features.Notifications).Notify(Player, { Title = Title; Text = Text; Kind = Kind })
	return true
end

---| Attendance |---

function Commands.Attendance(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Profile and Profile.Attendance
end

function Commands.ResetAttendanceSession(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return false end
	require(ServerScriptService.Services.School.Attendance).ResetSessionForTests(Player)
	return true
end

-- test cleanup: overwrite fields of the loaded slot's attendance record (Recent, Totals, ...)
function Commands.SetAttendance(PlayerName: string, Fields: { [string]: any })
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	if not (Profile and typeof(Profile.Attendance) == `table`) then return false end
	for Key, Value in Fields do Profile.Attendance[Key] = Value end
	return true
end

---| Discipline |---

function Commands.Discipline(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	return Player and require(ServerScriptService.Services.School.Discipline).GetData(Player)
end

function Commands.AddViolation(PlayerName: string, Type: string)
	local Player = Players:FindFirstChild(PlayerName)
	return Player and require(ServerScriptService.Services.School.Discipline).AddViolation(Player, Type, { Witness = `Test` }) ~= nil
end

function Commands.SetDiscipline(PlayerName: string, Fields: { [string]: any })
	local Player = Players:FindFirstChild(PlayerName)
	local Data = Player and require(ServerScriptService.Services.School.Discipline).GetData(Player)
	if not Data then return false end
	for Key, Value in Fields do Data[Key] = Value end
	return true
end

function Commands.Incidents()
	local Out = {}
	for _, I in require(ServerScriptService.Services.School.Discipline).GetIncidents() do
		table.insert(Out, `{I.Time} {I.Type} suspect={I.Suspect and I.Suspect.Name} witness={I.Witness} recognized={I.Recognized}`)
	end
	return Out
end

function Commands.Monitors()
	return require(ServerScriptService.Services.School.HallMonitor).GetMonitors()
end

---| Class activities |---

-- AutoPlay (optional, 0..1): for Lab Mix, also start the auto-player at that accuracy (see AutoLab).
function Commands.StartLesson(PlayerName: string, RoomId: string, AutoPlay: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Started = Player and require(ServerScriptService.Services.School.Activities).StartForTests(Player, RoomId)
	if Started and AutoPlay then Commands.AutoLab(PlayerName, AutoPlay) end
	return Started
end

-- 1.47 substitute days
local function Subs() return require(ServerScriptService.Services.School.Substitutes) end
function Commands.SubForce(Subject: string, SubId: string, Twist: string?, Extra: string?, Variant: number?) return Subs().ForceForTests(Subject, SubId, Twist, Extra, Variant) end
function Commands.SubClear() return Subs().ClearForTests() end
function Commands.SubState() return Subs().State() end
function Commands.SubPickUp(PlayerName: string) return Subs().PickUpForTests(Players:FindFirstChild(PlayerName)) end
function Commands.SubHandIn(PlayerName: string) return Subs().HandInForTests(Players:FindFirstChild(PlayerName)) end
-- play Candle Vigil / Seance Sequence through the real action path (tool round trips are too slow to react)
function Commands.AutoVigil(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Candles then return false end
	task.spawn(function()
		local Seen = {}
		while Activities.GetSessionForTests(Player) == S do
			for I, C in S.Candles do
				if C.State == `Gutter` and not Seen[C] then
					Seen[C] = C.Until
					if math.random() <= (Accuracy or 0.9) then task.delay(0.4, function() if Activities.GetSessionForTests(Player) == S then Activities.ActionForTests(Player, `Tend`, { Index = I }) end end) end
				elseif C.State ~= `Gutter` then Seen[C] = nil end
			end
			task.wait(0.1)
		end
	end)
	return true
end
function Commands.AutoSeance(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Seq then return false end
	task.spawn(function()
		while Activities.GetSessionForTests(Player) == S do
			if os.clock() >= S.ShowUntil + 0.1 then
				local Want = S.Seq[S.Pos]
				local Press = if math.random() <= (Accuracy or 0.95) then Want else (Want % 6) + 1
				Activities.ActionForTests(Player, `Press`, { Index = Press })
			end
			task.wait(0.3)
		end
	end)
	return true
end

-- Testing only: play Lab Mix for a player. Tool round trips are far too slow to hit a rhythm chart, and
-- with no presses six missed notes blow the beaker ~7 s into the song (the real rule). Each note is hit
-- on its beat with probability Accuracy (default 0.85) through the real action path; the rest are missed.
function Commands.AutoLab(PlayerName: string, Accuracy: number?)
	local Player = Players:FindFirstChild(PlayerName)
	local Activities = require(ServerScriptService.Services.School.Activities)
	local S = Player and Activities.GetSessionForTests(Player)
	if not S or not S.Notes or not S.StartAt then return false end
	local Ping = 0
	pcall(function() Ping = math.clamp(Player:GetNetworkPing(), 0, 0.35) end)
	local Planned = 0
	for _, Note in S.Notes do
		if math.random() <= (Accuracy or 0.85) then
			Planned += 1
			task.delay(math.max(0, S.StartAt + Note.Time + Ping + 0.075 - os.clock()), function()
				if Activities.GetSessionForTests(Player) == S then
					Activities.ActionForTests(Player, `Hit`, { Lane = Note.Lane })
				end
			end)
		end
	end
	return { Notes = #S.Notes; Planned = Planned }
end

-- Peek at the server-side session (answers etc.) to drive a test player.
function Commands.Lesson(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local S = Player and require(ServerScriptService.Services.School.Activities).GetSessionForTests(Player)
	if not S then return nil end

	local Out = { Id = S.Id; Type = S.Def.Type; Level = S.Level; Practice = S.Practice; Index = S.Index; Answer = S.Answer; Word = S.Word; Correct = S.Correct }
	if S.Cards then
		Out.Pairs = {}
		for Index, Card in S.Cards do Out.Pairs[Index] = Card.Pair end
		Out.Matched = S.Matched
	end
	if S.Notes then
		Out.Notes = {}
		for _, Note in S.Notes do table.insert(Out.Notes, { Lane = Note.Lane; Time = Note.Time }) end
		Out.StartAt = S.StartAt
		Out.Now = os.clock()
		Out.Hits = S.Hits
	end
	return Out
end

-- Testing only: slow a lesson's per-item timer (tool round trips are slower than a human).
function Commands.SlowLesson(PlayerName: string, Seconds: number)
	local Player = Players:FindFirstChild(PlayerName)
	local S = Player and require(ServerScriptService.Services.School.Activities).GetSessionForTests(Player)
	if not S then return false end
	S.TimePer = Seconds
	S.EndsAt = os.clock() + Seconds * 12
	if S.Deadline then S.Deadline = os.clock() + Seconds end
	return true
end

function Commands.Classes(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	return Profile and Profile.Classes
end

local PeriodLog = {}
function Commands.RecordPeriods()
	table.clear(PeriodLog)
	if not Commands._PeriodHooked then
		Commands._PeriodHooked = true
		require(ServerScriptService.Services.School.SchoolClock).PeriodChanged:Connect(function(State, Old)
			table.insert(PeriodLog, `{Old and Old.Name or "-"} -> {State.Segment.Name} at {State.ClockText}`)
		end)
	end
	return true
end

function Commands.Periods()
	return table.clone(PeriodLog)
end

---| Social (factions, reputation, dialogue) |---

local function Social() return require(ServerScriptService.Services.Social.Reputation) end
local function FactionsService() return require(ServerScriptService.Services.Social.Factions) end

local function DeepCopy(Value)
	if typeof(Value) ~= `table` then return Value end
	local Copy = {}
	for K, V in Value do Copy[K] = DeepCopy(V) end
	return Copy
end

-- Full social block + perk attributes.
function Commands.Social(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	if not Player then return nil end
	local Attributes = {}
	for Name, Value in Player:GetAttributes() do
		if Name:find(`^Perk_`) or Name:find(`^Faction_`) or Name == `LessonYenBonus` or Name == `Title` then
			Attributes[Name] = Value
		end
	end
	return { Social = DeepCopy(Social().Get(Player)); Attributes = Attributes }
end

-- Wipe social data back to new-player defaults.
function Commands.ResetSocial(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Profile = Player and require(ServerScriptService.Services.Player.Data).GetProfile(Player)
	if not Profile then return false end
	Profile.Social = nil
	Social().Get(Player)
	for Id in require(ReplicatedStorage.Config.Factions).Factions do
		FactionsService().AddStanding(Player, Id, -1000, nil, true)
	end
	Social().Sync(Player)
	return true
end

function Commands.AddStanding(PlayerName: string, Id: string, Amount: number)
	local Player = Players:FindFirstChild(PlayerName)
	FactionsService().AddStanding(Player, Id, Amount, `Test`)
	local F = FactionsService().Get(Player, Id)
	return F and { Standing = F.Standing; Rank = F.Rank; Member = F.Member }
end

function Commands.SetFlag(PlayerName: string, Id: string, Flag: string)
	FactionsService().SetFlag(Players:FindFirstChild(PlayerName), Id, Flag)
	return true
end

function Commands.AddRep(PlayerName: string, Category: string, Amount: number)
	local Player = Players:FindFirstChild(PlayerName)
	Social().Add(Player, Category, Amount, `Test`)
	return Social().Value(Player, Category)
end

function Commands.Relationship(PlayerName: string, NpcId: string, Change: number?)
	local Player = Players:FindFirstChild(PlayerName)
	if Change then Social().ChangeRelationship(Player, NpcId, Change, `Test`) end
	return { Social().Relationship(Player, NpcId) }
end

function Commands.CanJoin(PlayerName: string, Id: string)
	return { FactionsService().CanJoin(Players:FindFirstChild(PlayerName), Id) }
end

function Commands.MissionStatus(PlayerName: string, Id: string)
	return { FactionsService().MissionStatus(Players:FindFirstChild(PlayerName), Id) }
end

-- Talk to a leader (skips the prompt, keeps the server range checks).
function Commands.Talk(PlayerName: string, NpcId: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Npcs = require(ServerScriptService.Services.Social.Npcs)
	return Npcs.TalkForTests(Player, NpcId)
end

function Commands.Dialogue(PlayerName: string)
	return require(ServerScriptService.Services.Social.Dialogue).PeekForTests(Players:FindFirstChild(PlayerName))
end

function Commands.Choose(PlayerName: string, Index: number)
	local Dialogue = require(ServerScriptService.Services.Social.Dialogue)
	local Player = Players:FindFirstChild(PlayerName)
	Dialogue.ChooseForTests(Player, Index)
	return Dialogue.PeekForTests(Player)
end

-- Choose by the text of the reply (first label containing Text).
function Commands.Say(PlayerName: string, Text: string)
	local Dialogue = require(ServerScriptService.Services.Social.Dialogue)
	local Player = Players:FindFirstChild(PlayerName)
	local Peek = Dialogue.PeekForTests(Player)
	if not Peek then return nil end
	for Index, Label in Peek.Choices do
		if Label:find(Text, 1, true) then
			Dialogue.ChooseForTests(Player, Index)
			return Dialogue.PeekForTests(Player) or { Closed = true }
		end
	end
	return { NotOffered = Text; Choices = Peek.Choices }
end

function Commands.LeaderModel(NpcId: string)
	local Model = require(ServerScriptService.Services.Social.Npcs).Get(NpcId)
	return Model and Describe(Model)
end

function Commands.MarkWall(PlayerName: string, WallId: string)
	return require(ServerScriptService.Services.Social.Pranks).MarkForTests(Players:FindFirstChild(PlayerName), WallId)
end

function Commands.ResetWalls(PlayerName: string)
	require(ServerScriptService.Services.Social.Pranks).ResetForTests(Players:FindFirstChild(PlayerName))
	return true
end

function Commands.NightStudy(PlayerName: string, Subject: string?, IgnoreCooldown: boolean?)
	return require(ServerScriptService.Services.Social.Hangouts).StudyForTests(Players:FindFirstChild(PlayerName), Subject, IgnoreCooldown)
end

---| Quests |---

local function QuestsService() return require(ServerScriptService.Services.Quests.Quests) end
local function Places() return require(ServerScriptService.Services.Quests.Places) end

function Commands.QuestState(PlayerName: string)
	return DeepCopy(QuestsService().StateForTests(Players:FindFirstChild(PlayerName)))
end

function Commands.ResetQuests(PlayerName: string, AutoStart: boolean?)
	local Player = Players:FindFirstChild(PlayerName)
	QuestsService().ResetForTests(Player)
	if AutoStart then QuestsService().AutoStartForTests(Player) end
	return true
end

function Commands.StartQuest(PlayerName: string, Id: string)
	return QuestsService().Start(Players:FindFirstChild(PlayerName), Id)
end

function Commands.CanStartQuest(PlayerName: string, Id: string)
	return { QuestsService().CanStart(Players:FindFirstChild(PlayerName), Id) }
end

function Commands.QuestProgress(PlayerName: string, Type: string, Key: any, Extra: any?)
	QuestsService().Progress(Players:FindFirstChild(PlayerName), Type, Key, Extra)
	return true
end

function Commands.SetQuestDeadline(PlayerName: string, Id: string, Seconds: number)
	QuestsService().SetDeadlineForTests(Players:FindFirstChild(PlayerName), Id, Seconds)
	return true
end

-- Move the player next to a map part found by attribute (QuestObject / QuestArea / NpcPost ...).
function Commands.GoTo(PlayerName: string, Attribute: string, Value: any, Offset: Vector3?)
	local Player = Players:FindFirstChild(PlayerName)
	local Part = Places().Find(Attribute, Value)
	if not Player or not Player.Character or not Part then return false end
	Player.Character:PivotTo(CFrame.new(Part.Position + (Offset or Vector3.new(0, 3, 3))))
	return true
end

-- Use a quest object (server range checks still apply).
function Commands.UseObject(PlayerName: string, ObjectId: string)
	local Player = Players:FindFirstChild(PlayerName)
	QuestsService().OnInteract(Player, ObjectId)
	return true
end

function Commands.Link(PlayerName: string, Case: string, A: string, B: string)
	return { require(ServerScriptService.Services.Quests.Investigation).Link(Players:FindFirstChild(PlayerName), Case, A, B) }
end

function Commands.Deduce(PlayerName: string, Case: string, Option: number)
	return { require(ServerScriptService.Services.Quests.Investigation).Deduce(Players:FindFirstChild(PlayerName), Case, Option) }
end

function Commands.Stealth(PlayerName: string, Zone: string?)
	local Stealth = require(ServerScriptService.Services.Quests.Stealth)
	local Player = Players:FindFirstChild(PlayerName)
	local W = Zone and Stealth.WatcherForTests(Zone)
	return {
		Meter = Player and Stealth.MeterForTests(Player);
		Hidden = Player and Stealth.IsHidden(Player);
		Watcher = W and Describe(W);
		WatcherPos = W and W:GetPivot().Position and tostring(W:GetPivot().Position);
	}
end

function Commands.MoveWatcher(Zone: string, Position: Vector3, LookAt: Vector3?)
	local W = require(ServerScriptService.Services.Quests.Stealth).WatcherForTests(Zone)
	if not W then return false end
	W:PivotTo(if LookAt then CFrame.lookAt(Position, LookAt) else CFrame.new(Position))
	return true
end

function Commands.Hide(PlayerName: string, Leave: boolean?)
	local Stealth = require(ServerScriptService.Services.Quests.Stealth)
	local Player = Players:FindFirstChild(PlayerName)
	if Leave then Stealth.Unhide(Player) return true end
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Best, BestD = nil, math.huge
	for _, Spot in Places().FindAll(`HidingSpot`) do
		local D = (Spot.Position - Root.Position).Magnitude
		if D < BestD then Best, BestD = Spot, D end
	end
	return Best and Stealth.Hide(Player, Best) or false
end

function Commands.DuelTest(PlayerName: string, OpponentName: string)
	local Player = Players:FindFirstChild(PlayerName)
	local Opponent = FindCharacter(OpponentName)
	return Opponent ~= nil and require(ServerScriptService.Services.Quests.Duels).DuelForTests(Player, Opponent)
end

function Commands.DuelState()
	return require(ServerScriptService.Services.Quests.Duels).StateForTests()
end

---| Main menu / slots |---

function Commands.Slots(PlayerName: string)
	return require(ServerScriptService.Services.Player.Slots).List(Players:FindFirstChild(PlayerName))
end

function Commands.ChooseSlot(PlayerName: string, Slot: number)
	return { require(ServerScriptService.Services.Player.Slots).ChooseForTests(Players:FindFirstChild(PlayerName), Slot) }
end

function Commands.Identity(PlayerName: string)
	return require(ServerScriptService.Services.Player.Identity).Get(Players:FindFirstChild(PlayerName))
end

function Commands.SetName(PlayerName: string, Name: string)
	return { require(ServerScriptService.Services.Player.Identity).SetName(Players:FindFirstChild(PlayerName), Name) }
end

function Commands.SpinClan(PlayerName: string)
	return { require(ServerScriptService.Services.Player.Identity).SpinClan(Players:FindFirstChild(PlayerName)) }
end

-- (homes) the student's room, saved housing and who's where; force a look; or run a made-up report card through
-- Homes.Adjust / AfterCard (the allowance math and Mom & Dad's text), paying it like ReportCards does
function Commands.HomeInfo(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local R = P and Homes.RoomOf(P)
	local Shown = {}
	if R then
		for _, D in R.Model:GetDescendants() do
			if D:GetAttribute(`NHHomeState`) and D ~= R.Model then
				local Vis = D:IsA(`BasePart`) and D.Transparency < 1
				if not D:IsA(`BasePart`) then for _, X in D:GetDescendants() do if X:IsA(`BasePart`) and X.Transparency < 1 and X.Name ~= `NHTrophyShown` and not X.Name:find(`TrophySpot`) then Vis = true break end end end
				if Vis then table.insert(Shown, D.Name) end
			end
		end
		table.sort(Shown)
	end
	return { Housing = P and Homes.Get(P); State = R and R.State; Slot = R and R.Slot; Pivot = R and R.Model:GetPivot().Position; Shown = Shown; InHome = P and P:GetAttribute(`NHInHome`) }
end
function Commands.HomeEnter(PlayerName: string, OwnerName: string?)
	local P = Players:FindFirstChild(PlayerName)
	local O = OwnerName and Players:FindFirstChild(OwnerName)
	return { require(ServerScriptService.Services.Features.Homes).Enter(P, O and O.UserId or nil) }
end
function Commands.HomeLeave(PlayerName: string)
	require(ServerScriptService.Services.Features.Homes).Leave(Players:FindFirstChild(PlayerName))
	return true
end
function Commands.HomeState(PlayerName: string, StateId: string)
	return require(ServerScriptService.Services.Features.Homes).SetStateForTests(Players:FindFirstChild(PlayerName), StateId)
end
function Commands.HomeCard(PlayerName: string, Average: string?, Allowance: number?)
	local P = Players:FindFirstChild(PlayerName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local Card = { Average = Average; Allowance = Allowance or 0 }
	Homes.Adjust(P, Card)
	if Card.Allowance > 0 then require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `UpdateYen`; amount = Card.Allowance }) end
	Homes.AfterCard(P, Card)
	return { Allowance = Card.Allowance; Parents = Card.Parents; CutOff = Card.CutOff; Housing = Homes.Get(P) }
end

-- (homes) give a beast trophy and redraw the owner's trophy shelf; returns the trophies on it
function Commands.HomeTrophy(PlayerName: string, ItemId: string)
	local P = Players:FindFirstChild(PlayerName)
	require(ServerScriptService.Services.Features.Inventory).Grant(P, ItemId, 1)
	return require(ServerScriptService.Services.Features.Homes).TrophiesForTests(P)
end
-- (homes) a host invites a guest; returns the result and whether the guest may visit now
function Commands.HomeInvite(HostName: string, GuestName: string)
	local H, G = Players:FindFirstChild(HostName), Players:FindFirstChild(GuestName)
	local Homes = require(ServerScriptService.Services.Features.Homes)
	local Ok, Why = Homes.Invite(H, G and G.UserId)
	return { Ok = Ok; Why = Why; CanVisit = G and H and Homes.CanVisit(G, H.UserId) }
end
-- (height) spin the height; or mark it not yet revealed, so the creator plays the first-roll reveal again
function Commands.SpinHeight(PlayerName: string)
	return { require(ServerScriptService.Services.Player.Identity).SpinHeight(Players:FindFirstChild(PlayerName)) }
end
function Commands.HeightUnseen(PlayerName: string)
	local P = Players:FindFirstChild(PlayerName)
	local Identity = require(ServerScriptService.Services.Player.Identity)
	local I = P and Identity.Get(P)
	if not I then return false end
	I.Height.Seen = false
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetIdentity`; identity = I })
	Identity.Notify(P) -- the client's copy too
	return true, I.Height
end

-- Runs the real receipt handler with a made-up receipt (Config.Shop key, receipt id).
function Commands.GrantProduct(PlayerName: string, Key: string, PurchaseId: string)
	return require(ServerScriptService.Services.Player.Purchases).ProcessForTests(Players:FindFirstChild(PlayerName), Key, PurchaseId)
end

-- Stranger system: From introduces themselves to To; Strangers lists what a player's client was sent.
function Commands.Introduce(From: string, To: string)
	return { require(ServerScriptService.Services.Social.Strangers).IntroduceForTests(Players:FindFirstChild(From), Players:FindFirstChild(To)) }
end

function Commands.Strangers(PlayerName: string)
	return require(ServerScriptService.Services.Social.Strangers).SentForTests(Players:FindFirstChild(PlayerName))
end

-- Progression: give EXP, read the record sheet, spend points.
function Commands.GiveExp(PlayerName: string, Amount: number, Category: string?)
	return require(ServerScriptService.Services.Player.Progression).AwardForTests(Players:FindFirstChild(PlayerName), Amount, Category)
end

function Commands.Progress(PlayerName: string)
	return require(ServerScriptService.Services.Player.Progression).Sheet(Players:FindFirstChild(PlayerName))
end

function Commands.SpendStat(PlayerName: string, StatId: string, Count: number?)
	return { require(ServerScriptService.Services.Player.Progression).Spend(Players:FindFirstChild(PlayerName), StatId, Count or 1) }
end

-- Races: force a lineage, then measure a hit through Downed.ApplyDamage (race family bonuses included)
function Commands.SetRace(PlayerName: string, Race: string, Sub: string?, Tier: number?)
	return { require(ReplicatedStorage.Lineage).SetForTests(Players:FindFirstChild(PlayerName), Race, Sub, Tier) }
end

-- Evolution: hunger, forcing a tier-up (plays the cutscene), opening the rite
-- Sports: clubs, venues, drills (Services.Sports.*)
local function Sports(Name) return require(ServerScriptService.Services.Sports[Name]) end
function Commands.JoinClub(PlayerName: string, ClubId: string?)
	local P = Players:FindFirstChild(PlayerName)
	if ClubId == nil or ClubId == `` then return { Sports(`Clubs`).Leave(P) } end
	return { Sports(`Clubs`).Join(P, ClubId) }
end
-- test cleanup: put a slot's places found back exactly (a list of region ids)
function Commands.RegionSet(PlayerName: string, Ids: { string })
	local P = Players:FindFirstChild(PlayerName)
	if not P then return false end
	local Found = {}
	for _, Id in Ids or {} do Found[Id] = true end
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetRegions`; regions = { Found = Found } })
	return require(ServerScriptService.Services.Features.Regions).State(P)
end
-- test cleanup: overwrite fields of a slot's progress (Level, Exp, Points)
function Commands.SetProgressFields(PlayerName: string, Fields: { [string]: any })
	local P = Players:FindFirstChild(PlayerName)
	local Prog = require(ServerScriptService.Services.Player.Progression)
	local Pr = P and Prog.Get(P)
	if not Pr then return false end
	for K, V in Fields do Pr[K] = V end
	require(ServerScriptService.Services.Player.Data).UpdateState(P, { type = `SetProgress`; progress = Pr })
	P:SetAttribute(`Level`, Pr.Level)
	return Prog.Sheet(P)
end
function Commands.RegionState(PlayerName: string) return require(ServerScriptService.Services.Features.Regions).State(Players:FindFirstChild(PlayerName)) end
function Commands.RegionReset(PlayerName: string) return require(ServerScriptService.Services.Features.Regions).Reset(Players:FindFirstChild(PlayerName)) end
-- 1.20 cliques: schedule test plans and clique standing
function Commands.SchedulePlan(Kind: string, Name: string?, Hour: number?) return require(ServerScriptService.Services.Features.Schedules).PlanForTests(Kind, Name, Hour) end
function Commands.ScheduleDebug() return require(ServerScriptService.Services.Features.Schedules).Debug() end
function Commands.Cliques(PlayerName: string) return require(ServerScriptService.Services.Social.Cliques).State(Players:FindFirstChild(PlayerName)) end
function Commands.CliqueAdd(PlayerName: string, Id: string, Amount: number, Reason: string?) return require(ServerScriptService.Services.Social.Cliques).Add(Players:FindFirstChild(PlayerName), Id, Amount, Reason) end
function Commands.ClubSheet(PlayerName: string) return Sports(`Clubs`).Sheet(Players:FindFirstChild(PlayerName)) end
function Commands.SportForce(Venue: string, A: string, B: string, Solo: boolean?)
	local PA, PB = {}, {}
	for N in string.gmatch(A or ``, `[^,]+`) do table.insert(PA, Players:FindFirstChild(N)) end
	for N in string.gmatch(B or ``, `[^,]+`) do table.insert(PB, Players:FindFirstChild(N)) end
	return { Sports(`Matches`).ForceStart(Venue, PA, PB, Solo) }
end
function Commands.SportState(Venue: string)
	local m = Sports(`Matches`).Get(Venue)
	if not m then return nil end
	local B = m.B
	return { Phase = m.Phase; Clock = m.Clock; Score = m.Score; A = #m.Teams.A; B = #m.Teams.B; QueueA = #m.Queue.A; QueueB = #m.Queue.B;
		Holder = B and B.Ball and B.Ball.Holder and B.Ball.Holder.Name; BallState = B and B.Ball and B.Ball.State; ShotClock = B and B.ShotClock;
		HalfCourt = B and B.HalfCourt; Possession = B and B.Possession; Ranked = m.Ranked; Plug = m.Plug ~= nil }
end
-- run a sport action as if the client sent it (goes through the same rules)
function Commands.SportAction(PlayerName: string, Action: string, Args: any)
	local P = Players:FindFirstChild(PlayerName)
	local m = Sports(`Matches`).MatchOf(P)
	if m and m.Plug then return { pcall(m.Plug.OnAction, m, P, Action, Args or {}) } end
	for _, Name in { `Basketball`, `Soccer`, `Football` } do local M = game.ServerScriptService.Services.Sports:FindFirstChild(Name) if M then local R = require(M).DrillAction(P, Action, Args or {}) if R then return { R } end end end return { false }
end
function Commands.AwardExp(PlayerName: string, Key: string)
	return require(ServerScriptService.Services.Player.Progression).Award(Players:FindFirstChild(PlayerName), Key, nil, `Test`)
end
function Commands.FootballState(Venue: string)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not m then return nil end
	local S = m.S
	local H = S and S.Ball and S.Ball.Holder
	return { Phase = m.Phase; Clock = m.Clock; Score = m.Score; A = #m.Teams.A; B = #m.Teams.B; Plug = m.Plug ~= nil;
		Mode = S and S.Mode; Offence = S and S.Offence; Down = S and S.Down; LOS = S and S.LOS; ToGoX = S and S.ToGoX; Kind = S and S.Kind;
		QB = S and S.QB and S.QB.Name; Kicker = S and S.Kicker and S.Kicker.Name; Holder = H and H.Name; BallState = S and S.Ball and S.Ball.State;
		Air = S and S.Air and S.Air.Kind; Loose = S and S.Air and S.Air.Loose; Call = S and S.Call; Message = m.Message;
		BallPos = S and S.Ball and S.Ball.Part.Position; Dummies = S and S.Dummies and #S.Dummies or 0; Stats = m.Stats }
end
-- Studio only: put the ball on a down and a spot (yards to the goal) for the side with it, then huddle
function Commands.FootballSpot(Down: number, ToGoal: number, Venue: string?)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not (m and m.Plug and m.Plug._Local and m.S and m.Phase == `Live`) then return false end
	local L, S = m.Plug._Local, m.S
	S.LOS = L.SpotX(m, S.Offence, 60 - ToGoal)
	S.Down = Down
	local Goal = S.GoalX[S.Offence]
	S.ToGoX = S.LOS + S.Dir[S.Offence] * 10 * S.Yard
	if (S.ToGoX - Goal) * S.Dir[S.Offence] > 0 then S.ToGoX = Goal end
	S.Kind = nil
	L.Huddle(m, `Test spot`)
	return true
end
-- Studio only: a test defender that chases the ball carrier (Team = "A" or "B")
function Commands.FootballDummy(Team: string, Venue: string?)
	local m = Sports(`Matches`).Get(Venue or `Field`)
	if not (m and m.Plug and m.Plug.AddDummy) then return false end
	return m.Plug.AddDummy(m, Team or `B`) ~= nil
end
function Commands.SportEnd(Venue: string)
	local m = Sports(`Matches`).Get(Venue)
	if m and m.Phase ~= `Waiting` then m:End(nil, `Test`) end
	return m and m.Phase
end
function Commands.SportClock(Venue: string, Seconds: number)
	local m = Sports(`Matches`).Get(Venue)
	if m then m.Clock = Seconds end
	return m and m.Clock
end

function Commands.GiveHunger(PlayerName: string, Amount: number)
	return require(ServerScriptService.Services.Player.Evolution).Feed(Players:FindFirstChild(PlayerName), Amount, `Test`)
end

function Commands.Evolve(PlayerName: string, Tier: number)
	return require(ServerScriptService.Services.Player.Evolution).Evolve(Players:FindFirstChild(PlayerName), Tier)
end

function Commands.RaceDamage(AttackerName: string, TargetName: string, Damage: number)
	local Downed = require(ServerScriptService.Services.Features.Downed)
	local A, T = FindCharacter(AttackerName), FindCharacter(TargetName)
	local H = T and T:FindFirstChildOfClass(`Humanoid`)
	if not (A and H) then return `missing` end
	local Before = H.Health
	Downed.ApplyDamage(T, Damage, A)
	return Before - H.Health
end

-- (training 1.81) the game's own Training instance: Training(name, "State") | ("Get") | ("Grant", area, xp) |
-- ("Submit", presses) (a forged result through the real check) | ("Begin")
function Commands.Training(PlayerName: string, Action: string, ...)
	local T = require(ServerScriptService.Services.Features.Training)
	local P = Players:FindFirstChild(PlayerName)
	if Action == `State` then return T.State(P) end
	if Action == `Get` then return T.Get(P) end
	if Action == `Grant` then return T.TestGrant(P, ...) end
	if Action == `Begin` then return T.Begin(P) end
	if Action == `Set` then return T.TestSet(P, ...) end -- (1.86) area, level, xp, resetBody
	if Action == `Submit` then return T.Submit(P, ...) end
	if Action == `Moment` then -- replay a step-up moment (the banner, flex and burst) without changing anything
		local Area = ...
		local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
		require(ServerScriptService.Services.Features.Fx).FireNear(Root.Position, 80, `TrainStep`, { UserId = P.UserId; Area = Area or `Arms`; Body = `Toned`; Step = 1; Test = true })
		return true
	end
	if Action == `Look` then
		local Profile = require(ServerScriptService.Services.Player.Data).GetProfile(P)
		return Profile and Profile.Appearance
	end
	return `unknown`
end

-- (batch 54) put snacks in a test student's Locker through the real Inventory service (Grant pins them too), or take them back
function Commands.GrantItem(PlayerName: string, Id: string, N: number?)
	return require(ServerScriptService.Services.Features.Inventory).Grant(Players:FindFirstChild(PlayerName), Id, N)
end

-- (hunger 1.0) the game's own Body instance: Body(name, "State") | ("Set", n) | ("Tick", seconds) | ("Eat", itemId) |
-- ("Fed", kind) | ("Effects") | ("Saved") (the save as it is in the profile)
function Commands.Body(PlayerName: string, Action: string, ...)
	local B = require(ServerScriptService.Services.Features.Body)
	local P = Players:FindFirstChild(PlayerName)
	if Action == `State` then return B.State(P) end
	if Action == `Set` then return B.TestSet(P, ...) end
	if Action == `Tick` then return B.TestTick(P, ...) end
	if Action == `Eat` then return B.Ate(P, require(ReplicatedStorage.Config.Items).ById[(...)]) end
	if Action == `Fed` then return B.Fed(P, ...) end
	if Action == `Effects` then return B.Effects(P) end
	if Action == `Saved` then
		local Profile = require(ServerScriptService.Services.Player.Data).GetProfile(P)
		return Profile and Profile.Body
	end
	return `unknown`
end

function Commands.EnterSchool(PlayerName: string)
	return require(ServerScriptService.Services.Player.Slots).EnterForTests(Players:FindFirstChild(PlayerName))
end

function Shared.OnStart()
	if not RunService:IsStudio() then
		return
	end

	local Existing = ServerStorage:FindFirstChild(`NHTestBridge`)
	if Existing then Existing:Destroy() end

	local Bridge = Instance.new(`BindableFunction`)
	Bridge.Name = `NHTestBridge`
	Bridge.OnInvoke = function(CommandName: string, ...)
		local Command = Commands[CommandName]
		if not Command then
			return false, `Unknown command {CommandName}`
		end
		return pcall(Command, ...)
	end
	Bridge.Parent = ServerStorage
end

return Shared
