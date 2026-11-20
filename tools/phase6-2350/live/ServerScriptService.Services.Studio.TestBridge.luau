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

-- (2.27) the 64-entry cap's drop order, on stand-in tables (nothing saved)
function Commands.RelationshipCapTest(PlayerName: string)
	local Rep = Social()
	local Rels = {}
	-- 60 Acquaintance students, 3 Friendly, Ezra (important), 1 Hostile: 65 entries, cap 64
	for I = 1, 60 do Rels[`Ac{I}`] = { Value = 0; Met = true; Last = 1000 + I; Flags = {} } end
	for I = 1, 3 do Rels[`Fr{I}`] = { Value = 30; Met = true; Last = 10 + I; Flags = {} } end
	Rels.Ezra = { Value = 0; Met = true; Last = 1; Flags = {} }
	Rels.Ho1 = { Value = -80; Met = true; Last = 2; Flags = {} }
	local Dropped = Rep.TrimForTests(Rels, 64, 5000)
	local Count = 0 for _ in Rels do Count += 1 end
	-- no Acquaintance left: the next drop is the oldest entry that isn't Trusted, Hostile or important
	local Rels2 = {}
	for I = 1, 63 do Rels2[`Fr{I}`] = { Value = 30; Met = true; Last = 100 + I; Flags = {} } end
	Rels2.Tr = { Value = 90; Met = true; Last = 1; Flags = {} }
	Rels2.Ho = { Value = -90; Met = true; Last = 2; Flags = {} }
	local Dropped2 = Rep.TrimForTests(Rels2, 64, 5000)
	return { Dropped = Dropped; Count = Count; EzraKept = Rels.Ezra ~= nil; HostileKept = Rels.Ho1 ~= nil;
		Dropped2 = Dropped2; TrustedKept = Rels2.Tr ~= nil; HostileKept2 = Rels2.Ho ~= nil }
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

-- (2.22.0) New Kid's Enrol step and the saved-stage migration (quests restored afterwards)
function Commands.EnrolSelfTest(PlayerName: string)
	return DeepCopy(QuestsService().EnrolSelfTestForTests(Players:FindFirstChild(PlayerName)))
end

function Commands.ResetQuests(PlayerName: string, AutoStart: boolean?)
	local Player = Players:FindFirstChild(PlayerName)
	QuestsService().ResetForTests(Player)
	if AutoStart then QuestsService().AutoStartForTests(Player) end
	return true
end

-- (2.28) every staff post exists, and every staff member has a look and a talk tree
function Commands.StaffTest(PlayerName: string)
	local Cast = require(game:GetService(`ReplicatedStorage`).Config.Npcs)
	local Looks = require(game:GetService(`ServerScriptService`).Services.Features.NpcLooks)
	local Places = require(game:GetService(`ServerScriptService`).Services.Quests.Places)
	local Out = { Missing = {} }
	for _, Id in { `Sallow`, `Hale`, `Pryce`, `Whitlock`, `Ashgrave` } do
		local Npc = Cast[Id]
		if not Npc then table.insert(Out.Missing, `cast {Id}`) continue end
		if not Npc.Posts then table.insert(Out.Missing, `posts {Id}`) continue end
		for Slot, Key in Npc.Posts do
			if not Places.Find(`NpcPost`, Key) then table.insert(Out.Missing, `post {Id}.{Slot}={Key}`) end
		end
		if not Looks.Specs[Id] then table.insert(Out.Missing, `look {Id}`) end
		if not game:GetService(`ServerStorage`).Dialogue:FindFirstChild(Npc.Dialogue or ``) then table.insert(Out.Missing, `talk {Id}`) end
	end
	return Out
end

-- (2.28) the set rotation, homeroom rooms and skipping (pure)
function Commands.TimetableTest(PlayerName: string)
	local Roster = require(game:GetService(`ServerScriptService`).Services.Social.Roster)
	local Out = { PerRoom = {}, Homeroom = {}, Skips = 0, SkipStable = true }
	for _, Seg in { `Period 1`, `Period 2`, `Period 3`, `Period 4` } do
		local Count = {}
		for _, E in Roster.All() do
			local P = Roster.Plan(Seg, E.Id, 7)
			if P.Room then Count[P.Room] = (Count[P.Room] or 0) + 1 end
		end
		Out.PerRoom[Seg] = Count
	end
	for _, E in Roster.All() do
		local R = Roster.Plan(`Homeroom`, E.Id, 7).Room
		Out.Homeroom[R or `-`] = (Out.Homeroom[R or `-`] or 0) + 1
		for Day = 1, 40 do
			local A = Roster.Plan(`Period 3`, E.Id, Day)
			if A.Skip then Out.Skips += 1 end
			if A.Skip ~= Roster.Plan(`Period 3`, E.Id, Day).Skip then Out.SkipStable = false end
			if A.Skip and E.Clique ~= `Delinquents` then Out.SkipStable = false end
		end
	end
	Out.Seg1SetA = Roster.Plan(`Period 1`, `OdetteMarsh`, 7).Room -- set A, Period 1: R102
	Out.Seg2SetA = Roster.Plan(`Period 2`, `OdetteMarsh`, 7).Room -- set A, Period 2: R103
	return Out
end

-- (2.28) a fight in a class with its teacher at the desk is booked by that teacher; slot 2 is restored by the caller
function Commands.WitnessTest(PlayerName: string, RoomId: string)
	local Player = Players:FindFirstChild(PlayerName)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.School.Teachers).WitnessForTests(Player, RoomId))
end

-- (2.28) bodies only near players: how many students have a body, and how many are asleep at a spot
function Commands.SleepTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Features.Schedules).SleepForTests())
end

-- (2.30) the broadcast: items roll at 40, a PA is limited to one per segment (emergencies aside), the station is on air at night
function Commands.BroadcastTest(PlayerName: string)
	local B = require(game:GetService(`ServerScriptService`).Services.World.Broadcast)
	local Player = Players:FindFirstChild(PlayerName)
	B.PATestReset()
	for I = 1, 45 do B.Post(`IncidentReport`, `Report {I}`) end
	local All = B.Items()
	local First = B.PA(`Test one.`)
	local Second = B.PA(`Test two.`)
	local Emergency = B.PA(`Emergency.`, true)
	B.PATestReset()
	local St = B.Station(Player)
	return { Count = #All; Newest = All[#All].Text; Oldest = All[1].Text; FirstPA = First; SecondPA = Second; EmergencyPA = Emergency;
		StationHasItems = #St.Items > 0; OnAirIsBool = typeof(St.OnAir) == `boolean` }
end

-- (2.30) the curfew rule at a given hour, with the player where the caller put them
function Commands.CurfewTest(PlayerName: string)
	local HM = require(game:GetService(`ServerScriptService`).Services.School.HallMonitor)
	local P = Players:FindFirstChild(PlayerName)
	local A, Why23 = HM.IsAfterHoursForTests(P, 23)
	local B, Why15 = HM.IsAfterHoursForTests(P, 15)
	local C, Why5 = HM.IsAfterHoursForTests(P, 5)
	return { At23 = A; Why23 = Why23; At15 = B; Why15 = Why15; At5 = C; Why5 = Why5 }
end

-- (2.29) the incident bus: Emit fills time, region and witnesses; On hears it; the relationship consumer applies flags
function Commands.IncidentTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Inc, Rep = require(SSS.World.Incidents), require(SSS.Social.Reputation)
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels.MaeGorse and table.clone(Rels.MaeGorse)
	local Heard = {}
	local C = Inc.On(`TestKind`, function(I) table.insert(Heard, I.Kind) end)
	local Hall = workspace.Regions:FindFirstChild(`MainHall`)
	local I = Inc.Emit({ Kind = `TestKind`; Where = Hall and Hall.Position; Who = { { Id = Player; Role = `Doer` } } })
	task.wait(0.3) -- SignalPlus delivers on the next frame
	C:Disconnect()
	local Before = Rep.Entry(Player, `MaeGorse`)
	Inc.Emit({ Kind = `Downed`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } } })
	task.wait(0.3)
	local After = Rep.Entry(Player, `MaeGorse`)
	Rels.MaeGorse = Saved
	Rep.Sync(Player)
	return { Heard = #Heard; Region = I.Region; HasTime = typeof(I.T) == `number`; Truth = I.Truth;
		Witnesses = typeof(I.Witnesses) == `table`; FoughtAdded = (After.Flags.Fought or 0) - (Before.Flags.Fought or 0);
		ValueDelta = After.Value - Before.Value; Recent = #Inc.Recent(5) }
end

-- (2.29) rumours from incidents, their text, and one spread
function Commands.RumourTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local I = { Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow` }; Truth = true; Severity = 2; T = os.time() }
	local R = Ru.Make(I)
	local Text = R and Ru.Text(R)
	local H = R and Ru.Hop(R, Random.new(7))
	return { Made = R ~= nil; HasTime = R ~= nil and typeof(R.T) == `number`; Text = Text; KnowerKit = R and R.Knowers.KitHarrow == true; HopCount = H and H.Hops;
		PlayerStill = H and H.Subject[1].Id == Player; NoTemplate = Ru.Make({ Kind = `Nothing`; Who = {} }) == nil }
end

-- (2.29) the safety rule over many random hops: a player is never added, swapped or moved off their own deed
function Commands.RumourSafetyTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Ru = require(SSS.Social.Rumours)
	local Rng = Random.new(2029)
	local Bad, Mutated = 0, 0
	local Cases = {
		{ Kind = `Downed`; Region = `Commons`; Who = { { Id = Player; Role = `Doer` }, { Id = `MaeGorse`; Role = `Target` } }; Witnesses = { `KitHarrow`, `JaxCalloway` } };
		{ Kind = `Downed`; Region = `MainHall`; Who = { { Id = `RonanFell`; Role = `Doer` }, { Id = Player; Role = `Target` } }; Witnesses = { `KitHarrow` } };
		{ Kind = `Scene`; Scene = `Locker`; Region = `MainHall`; Who = { { Id = `JaxCalloway`; Role = `Doer` }, { Id = `AgnesLowe`; Role = `Target` } }; Witnesses = { `NicoRuiz`, `ClaraWebb` } };
		{ Kind = `Caught`; Reason = `Truancy`; Region = `EastWing`; Who = { { Id = Player; Role = `Target` } }; Witnesses = {} };
	}
	for _, I in Cases do
		I.Truth, I.T, I.Severity = true, os.time(), 2
		for _ = 1, 2500 do
			local R = Ru.Make(I)
			for _ = 1, Rng:NextInteger(1, 6) do
				local Before = R
				R = Ru.Hop(R, Rng)
				if Ru.Text(R) ~= Ru.Text(Before) then Mutated += 1 end
			end
			-- every player in the rumour is in the incident, in the same role; every player in the incident is still there
			for _, S in R.Subject do
				if typeof(S.Id) == `Instance` then
					local Ok = false
					for _, W in I.Who do if W.Id == S.Id and W.Role == S.Role then Ok = true end end
					if not Ok then Bad += 1 end
				end
			end
			for _, W in I.Who do
				if typeof(W.Id) == `Instance` then
					local Still = false
					for _, S in R.Subject do if S.Id == W.Id and S.Role == W.Role then Still = true end end
					if not Still then Bad += 1 end
				end
			end
			-- no rumour about a player may change its place or its size: a mutation there would make it untrue
			local HasPlayer = false
			for _, S in R.Subject do if typeof(S.Id) == `Instance` then HasPlayer = true end end
			if HasPlayer and (R.Where ~= R.Base.Where or R.Size ~= R.Base.Size) then Bad += 1 end
		end
	end
	return { Hops = 10000; Bad = Bad; Mutated = Mutated }
end

-- (2.29) run one scene now at its spot (the player is moved there by the caller); returns how it went
function Commands.SceneTest(PlayerName: string, Id: string)
	local Scenes = require(game:GetService(`ServerScriptService`).Services.World.Scenes)
	local Ok, Why = Scenes.RunForTests(Id)
	return { Ok = Ok; Why = Why; Last = Scenes.LastForTests() }
end

-- (2.28) which post each staff member uses in each segment (pure)
function Commands.StaffPlanTest(PlayerName: string)
	local Npcs = require(game:GetService(`ServerScriptService`).Services.Social.Npcs)
	local Out = {}
	for _, Seg in { { `BeforeSchool`, `Before School` }, { `Class`, `Homeroom` }, { `Class`, `Period 2` }, { `Lunch`, `Lunch` }, { `Night`, `Night` } } do
		local Row = {}
		for _, Id in { `Hale`, `Sallow`, `Ashgrave`, `Ezra` } do Row[Id] = Npcs.PostKey(Id, Seg[1], Seg[2]) or `-` end
		Out[Seg[2]] = Row
	end
	return Out
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

---| (2.24.0) Phase 1: cuts, Decision / Kill objectives |---

local function CineService() return require(game:GetService(`ServerScriptService`).Services.World.Cine) end

-- (2.27) the roster's data and seeding (nothing saved)
function Commands.RosterTest(PlayerName: string)
	return DeepCopy(require(game:GetService(`ServerScriptService`).Services.Social.Roster).SelfTestForTests())
end

-- (2.27) greetings from the saved memory, on a stand-in student; slot 2's entry for her is put back after
function Commands.MemoryTest(PlayerName: string)
	local SSS = game:GetService(`ServerScriptService`).Services
	local Player = Players:FindFirstChild(PlayerName)
	local Rep, Brain = require(SSS.Social.Reputation), require(SSS.AI.StudentBrain)
	local Lines = require(SSS.AI.StudentBrain.Lines)
	local Id = `OdetteMarsh`
	local Rels = Rep.Get(Player).Relationships
	local Saved = Rels[Id] and table.clone(Rels[Id])
	Rels[Id] = nil
	local S = { Index = 999; RosterId = Id; First = `Odette`; Temper = `Warm`; Clique = `Choir`; Memory = {} }
	local Out = {}
	local Ok, Err = pcall(function()
		Out.Fresh = (Brain.GreetingForTests(S, Player)) -- expect Intro
		Rep.Meet(Player, Id)
		Out.AfterMeet = (Brain.GreetingForTests(S, Player)) ~= `Intro`
		Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
		Rep.ChangeRelationship(Player, Id, 12, nil, `Helped`)
		local _, PoolG = Brain.GreetingForTests(S, Player)
		Out.Grateful = PoolG == Lines.Greet.Grateful.Warm
		Rep.ChangeRelationship(Player, Id, -40, nil, `Fought`)
		local _, PoolF = Brain.GreetingForTests(S, Player)
		Out.Grudge = PoolF == Lines.Greet.Grudge.Warm
		Rels[Id] = nil
		Rep.ChangeRelationship(Player, Id, -25, nil, `Fought`) -- a fight before any introduction
		Out.NoIntroAfterFight = (Brain.GreetingForTests(S, Player)) ~= `Intro`
		Out.Attitude = require(SSS.AI.StudentBrain.Talk).Attitude(S, Player) -- Rival: at most Wary
	end)
	if not Ok then Out.Error = tostring(Err) end
	Rels[Id] = Saved
	Rep.Sync(Player)
	return Out
end

-- (2.27) the roster's bodies: ids on the live students, and a look that is the same when built twice
function Commands.Rostered(PlayerName: string)
	local Sched = require(game:GetService(`ServerScriptService`).Services.Features.Schedules)
	local Ids, Seen = {}, {}
	for _, R in Sched.Debug() do if R.RosterId and not Seen[R.RosterId] then Seen[R.RosterId] = true table.insert(Ids, R.RosterId) end end
	local A, B = Sched.LookForTests(`MaeGorse`), Sched.LookForTests(`MaeGorse`)
	return { Students = #Sched.Debug(); Ids = #Ids;
		SameLook = A.Uniform == B.Uniform and A.Skin == B.Skin and A.HairId == B.HairId and A.Bottoms == B.Bottoms and A.Body == B.Body }
end

-- Decision, Kill, a seen Cinematic stage and Requires.Fresh on the real Quests code (a throwaway quest; put back after)
function Commands.Phase1SelfTest(PlayerName: string)
	return DeepCopy(QuestsService().Phase1SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- the group skip vote on the real session code, with stand-ins for the other viewers (nothing is saved)
function Commands.CineVoteTest(PlayerName: string)
	return DeepCopy(CineService().VoteSelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- play a cut for a player now (Opts.Skippable = a replay); returns the session id
-- (2.26.0) After Hours v1 saves: a save on Collected (stage 3) moves past the two new stages; earlier stages stay
function Commands.AfterHoursMigrateTest()
	local Q = QuestsService()
	local Def = require(game:GetService(`ReplicatedStorage`).Config.Quests).Quests.AfterHours
	local Out = {}
	for _, Stage in { 1, 2, 3 } do
		local State = { Stage = Stage; V = 1 }
		Q.MigrateForTests(Def, State)
		Out[`From{Stage}`] = State.Stage
	end
	return Out
end

-- (2.26.0) a story decision as the cut would save it (Quests.Decide), e.g. FileKept = Lose
function Commands.Decide(PlayerName: string, Id: string, Choice: string)
	return QuestsService().Decide(Players:FindFirstChild(PlayerName), Id, Choice)
end

function Commands.PlayCut(PlayerName: string, CutId: string, Skippable: boolean?)
	return CineService().Play({ Players:FindFirstChild(PlayerName) }, CutId, { Skippable = Skippable == true })
end

-- this player's saved cut state ({ [CutId] = "Started" | "Seen" }) and the live sessions
function Commands.CineState(PlayerName: string)
	local Player = Players:FindFirstChild(PlayerName)
	return DeepCopy({ Saved = QuestsService().CineState(Player); Sessions = CineService().SessionsForTests() })
end

-- clear (or set) one cut's saved state: CineMark(name, "Prologue", nil) makes it unseen again
function Commands.CineMark(PlayerName: string, CutId: string, Value: string?)
	local Player = Players:FindFirstChild(PlayerName)
	local S = QuestsService().CineState(Player)
	if not S then return false end
	S[CutId] = Value
	QuestsService().SyncForCine(Player)
	return true
end

---| (2.25.0) interactive cuts: the judge and the graph |---

-- (2.35.0) CineSeam: the glide's length, keys and lint
function Commands.CineSeamTest()
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Fails = {}
	local function check(C, Msg) if not C then table.insert(Fails, Msg) end end
	local A = CFrame.lookAt(Vector3.new(0, 5, 10), Vector3.new(0, 5, 0))
	local Near = A * CFrame.new(1, 0, -1)
	local Far = CFrame.lookAt(Vector3.new(14, 5, -6), Vector3.new(0, 5, 0))
	check(math.abs(Seam.Length(A, A) - 0.6) < 1e-6, "zero move glides 0.6 s")
	check(Seam.Length(A, Far) <= 1.0 and Seam.Length(A, Far) > Seam.Length(A, Near), "longer move glides longer, at most 1.0 s")
	check(math.abs(Seam.Length(A, Far, true) - 0.2) < 1e-6, "Reduce Motion: 0.2 s dissolve")
	local K = Seam.Keys(A, 70, Far, 40, 0.8)
	check(#K == 3 and K[1].t == 0 and math.abs(K[3].t - 0.8) < 1e-6, "three keys over the length")
	check((K[1].pos - A.Position).Magnitude < 1e-4 and (K[3].pos - Far.Position).Magnitude < 1e-4, "keys start and end on the cameras")
	check(K[1].fov == 70 and K[3].fov == 40, "fov carried")
	local Mid = (A.Position + Far.Position) / 2
	check((K[2].pos - Mid).Magnitude > 0.3, "the middle key bends the path")
	check(Seam.Lint(A, Near) == nil, "a short glide passes lint")
	check(Seam.Lint(A, CFrame.lookAt(Vector3.new(0, 5, -30), Vector3.new(0, 5, 0))) ~= nil, "a long glide is flagged")
	check(math.abs(Seam.Ease(0)) < 1e-9 and math.abs(Seam.Ease(1) - 1) < 1e-9 and math.abs(Seam.Ease(0.5) - 0.5) < 1e-9, "smootherstep")
	local Cine = require(ReplicatedStorage.Cine)
	local Cf, Fov = Cine.cameraAt({ shots = { { dur = 2, camera = { cframe = Far, lens = 50 } } } }, 1)
	check((Cf.Position - Far.Position).Magnitude < 1e-4 and math.abs(Fov - Cine.mmToFov(50)) < 1e-4, "cameraAt evaluates a shot")
	for Feel, Deg in { calm = 0.08, tense = 0.25, chase = 0.6 } do
		local Np = Cine.noisePresetForTests(Feel, 40)
		check(Np ~= nil, Feel .. " resolves through the feel branch")
		if Np then
			local Peak = 0
			for _, L in Np.p.x do Peak += 0.5 * L[1] * Np.gain end
			check(math.abs(Peak - Deg) < 1e-6, Feel .. " peak is " .. Deg .. " deg")
			check(#Np.p.x == 2 and Np.p.x[1][2] == 0.4 and Np.p.x[2][2] == 1.1, Feel .. " octaves are 0.4 and 1.1 Hz")
		end
	end
	check(Seam.Lint(A, CFrame.lookAt(A.Position, A.Position + Vector3.new(0, 0, 1))) ~= nil, "a pure turn over 90 deg is flagged")
	check(Seam.Length(A, CFrame.lookAt(Vector3.new(500, 5, 500), Vector3.new(0, 5, 0))) == 1.0, "a very large move glides exactly 1.0 s")
	return #Fails == 0 and "CineSeamTest OK" or table.concat(Fails, "; ")
end

local function CineJudge() return require(game:GetService(`ReplicatedStorage`).Functions.CineJudge) end

-- every scoring rule on fixed inputs; returns { Passed, Failed = { "name: got X, want Y" } }
function Commands.CineJudgeTest()
	local J = CineJudge()
	local Press = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `A`; Good = `A`; Miss = `B` } }
	local Mash = { kind = `Mash`; at = 0; dur = 2; rate = 7; touchRate = 5; on = { Win = `A`; Lose = `B` } }
	local Dir = { kind = `Direction`; at = 0; dur = 0.9; options = { `Left`, `Right` }; answer = `Left`; on = { Right = `A`; Wrong = `B` } }
	local Hold = { kind = `Hold`; at = 0; zoneAt = 1.2; zone = 0.15; on = { Hit = `A`; Miss = `B` } }
	local Choice = { kind = `Choice`; at = 0; dur = 5; options = { { id = `Ask`; text = `Who?` }, { id = `Nod`; text = `...` } }; default = `Nod`;
		on = { Ask = `A`; Nod = `B` } }
	local function taps(N, Dur) local T = {} for I = 1, N do T[I] = (I - 0.5) * Dur / N end return T end
	local Cases = {
		{ `press exact`, Press, { Times = { 0.6 } }, `Perfect`, 3 },
		{ `press +0.12 edge`, Press, { Times = { 0.72 } }, `Perfect`, 3 },
		{ `press +0.2`, Press, { Times = { 0.8 } }, `Good`, 2 },
		{ `press -0.25 edge`, Press, { Times = { 0.35 } }, `Good`, 2 },
		{ `press -0.3`, Press, { Times = { 0.3 } }, `Miss`, 0 },
		{ `press none`, Press, { Times = {} }, `Miss`, 0 },
		{ `press earliest counts`, Press, { Times = { 0.9, 0.6 } }, `Perfect`, 3 }, -- times are sorted: 0.6 is judged
		{ `press reduced widens`, Press, { Times = { 0.9 }; Reduced = true }, `Good`, 2 },
		{ `mash 14 of 14`, Mash, { Times = taps(14, 2) }, `Win`, 2 },
		{ `mash 13`, Mash, { Times = taps(13, 2) }, `Lose`, 0 },
		{ `mash touch 10`, Mash, { Times = taps(10, 2); Touch = true }, `Win`, 2 },
		{ `mash late taps ignored`, Mash, { Times = { 2.5, 2.6, 2.7 } }, `Lose`, 0 },
		{ `dir right`, Dir, { Pick = `Left`; PickAt = 0.5 }, `Right`, 1 },
		{ `dir wrong`, Dir, { Pick = `Right`; PickAt = 0.5 }, `Wrong`, 0 },
		{ `dir late`, Dir, { Pick = `Left`; PickAt = 1.2 }, `Wrong`, 0 },
		{ `dir none`, Dir, {}, `Wrong`, 0 },
		{ `hold hit`, Hold, { Times = { 0.1 }; Release = 1.3 }, `Hit`, 2 },
		{ `hold early`, Hold, { Times = { 0.1 }; Release = 0.9 }, `Miss`, 0 },
		{ `hold never down`, Hold, { Release = 1.2 }, `Miss`, 0 },
		{ `choice picked`, Choice, { Pick = `Ask`; PickAt = 2 }, `Ask`, 1 },
		{ `choice timeout`, Choice, {}, `Nod`, 0 },
		{ `choice bogus id`, Choice, { Pick = `Hack`; PickAt = 1 }, `Nod`, 0 },
	}
	local Out = { Passed = 0; Failed = {} }
	for _, C in Cases do
		local Ok, O, Pts = pcall(J.Evaluate, C[2], C[3])
		if Ok and O == C[4] and Pts == C[5] then Out.Passed += 1
		else table.insert(Out.Failed, `{C[1]}: got {tostring(O)}/{tostring(Pts)}, want {C[4]}/{C[5]}`) end
	end
	-- branch, team, grade
	local function check(Name, Got, Want) if Got == Want then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: got {tostring(Got)}, want {tostring(Want)}`) end end
	check(`branch perfect`, J.Branch(Press, `Perfect`), `A`)
	check(`branch miss`, J.Branch(Press, `Miss`), `B`)
	check(`branch else`, J.Branch({ on = { Else = `Z` } }, `Whatever`), `Z`)
	check(`team majority`, J.Team(Press, { `Miss`, `Miss`, `Good` }), `Miss`)
	check(`team tie -> better`, J.Team(Press, { `Perfect`, `Miss` }), `Perfect`)
	check(`team empty -> miss`, J.Team(Press, {}), `Miss`)
	check(`team choice tie -> earlier option`, J.Team(Choice, { `Nod`, `Ask` }), `Ask`)
	check(`grade S`, J.Grade(9, 10), `S`)
	check(`grade A`, J.Grade(3, 4), `A`)
	check(`grade B`, J.Grade(11, 20), `B`)
	check(`grade C`, J.Grade(7, 20), `C`)
	check(`grade D`, J.Grade(1, 10), `D`)
	check(`grade none`, J.Grade(0, 0), nil)
	check(`max press`, J.MAX.Press, 3)
	return Out
end

-- graph validation on a good graph and on broken ones; returns { Passed, Failed }
function Commands.CineGraphTest()
	local J = CineJudge()
	local Out = { Passed = 0; Failed = {} }
	local function expect(Name, Graph, WantErrs: boolean, Needle: string?)
		local Errs = J.Validate(Graph)
		local Text = table.concat(Errs, " | ")
		local Ok = (#Errs > 0) == WantErrs and (Needle == nil or Text:find(Needle, 1, true) ~= nil)
		if Ok then Out.Passed += 1 else table.insert(Out.Failed, `{Name}: errors [{Text}]`) end
	end
	local function good()
		return { start = `A`; segments = {
			A = { len = 3; prompt = { kind = `Press`; at = 1; beat = 0.6; slow = 0.3; on = { Perfect = `B`; Good = `B`; Miss = `C` } } };
			B = { len = 2; next = `D` }; C = { len = 2; next = `D` };
			D = { len = 3; prompt = { kind = `Mash`; at = 0.5; dur = 1.6; rate = 7; slow = 0.5; on = { Win = `E`; Lose = `E` } } };
			E = { len = 1 } } }
	end
	expect(`good graph`, good(), false)
	local G1 = good() G1.start = `Nope`
	expect(`bad start`, G1, true, `start`)
	local G2 = good() G2.segments.B.next = `Ghost`
	expect(`unknown next`, G2, true, `Ghost`)
	local G3 = good() G3.segments.E.next = `A`
	expect(`loop`, G3, true, `loop`)
	local G4 = good() G4.segments.A.prompt.on.Miss = nil
	expect(`missing branch`, G4, true, `no branch for Miss`)
	local G5 = good() G5.segments.A.len = 1.2
	expect(`tail too short`, G5, true, `tail`)
	local G6 = good() G6.segments.A.next = `B`
	expect(`prompt with next`, G6, true, `no next`)
	-- the longest path: A (1 + 2/0.3) + C 2 + D (0.5 + 2.5/0.5) + E 1 = 7.67 + 2 + 5.5 + 1
	local L = J.LongestPath(good())
	if math.abs(L - (1 + 2 / 0.3 + 2 + 0.5 + 2.5 / 0.5 + 1)) < 0.01 then Out.Passed += 1 else table.insert(Out.Failed, `longest path {L}`) end
	if J.Follows(good(), `B`, `D`) and not J.Follows(good(), `A`, `D`) then Out.Passed += 1 else table.insert(Out.Failed, `follows`) end
	return Out
end

function Commands.CineGrades(PlayerName: string)
	return DeepCopy(QuestsService().CineGrades(Players:FindFirstChild(PlayerName)))
end

-- the group decide, the solo path check, Where and the grade on the real session code, with stand-in viewers
function Commands.CineQteTest(PlayerName: string)
	return DeepCopy(CineService().QteSelfTestForTests(Players:FindFirstChild(PlayerName)))
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

-- (2.31) Standing Paths: the evaluator on made-up facts, then grants on the live player (put back after)
function Commands.PathsTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Paths).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- (2.31) the five counters, each from its real signal; put back after
function Commands.TallyTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Prog = require(SSS.Player.Progression)
	local Before = table.clone(Prog.Get(P).Tally)
	require(SSS.Quests.Duels).Won:Fire(P)
	require(SSS.Quests.Duels).ChampionDefeated:Fire(P)
	require(SSS.School.HallMonitor).Escaped:Fire(P, `Curfew`)
	require(SSS.Features.Beasts).Reward(P, { Name = `Test beast`; Reward = {} })
	task.wait(0.5)
	local After = Prog.Get(P).Tally
	local Out = {}
	for _, K in { `DuelWins`, `Champion`, `Escapes`, `Beasts` } do Out[K] = (After[K] or 0) - (Before[K] or 0) end
	local Pr = Prog.Get(P) Pr.Tally = Before
	require(SSS.Player.Data).UpdateState(P, { type = `SetProgress`; progress = Pr })
	return Out
end

-- (2.31) reaching a tier: the banner event, and a broadcast mention from tier 4 (put back after)
function Commands.PathRewardTest(PlayerName: string)
	local SSS = ServerScriptService.Services
	local P = Players:FindFirstChild(PlayerName)
	local Paths = require(SSS.Player.Paths)
	return DeepCopy(Paths.RewardTestForTests(P))
end

-- (2.31) NPCs and paths: the student pool, and each tree's line with a fake ctx at tier 3 and at tier 1
function Commands.RecognitionTest()
	local Talk = require(ServerScriptService.Services.AI.StudentBrain.Talk)
	local Out = { Pools = {} }
	for _, Path in { `Academic`, `Social`, `Combat`, `Athletic`, `Supernatural` } do
		local Pool = Talk.Pool(nil, `Path`, `Neutral`, Path)
		Out.Pools[Path] = Pool and #Pool or 0
	end
	local Trees = game:GetService(`ServerStorage`).Dialogue
	local function fake(Tier: number)
		return { PathTier = function() return Tier end; Member = function() return false end; State = function() return `Acquaintance` end;
			Decided = function() return nil end; Objective = function() return nil end }
	end
	Out.Lines = {}
	for _, Name in { `Sallow`, `Pryce`, `Whitlock`, `Ezra`, `Vesper` } do
		local Tree = require(Trees[Name]) -- the templates return { Start, Nodes }
		local Hub = Tree.Nodes and Tree.Nodes.Hub
		local T = Hub and Hub.Text
		local At3 = if typeof(T) == `function` then T(fake(3)) else T
		local At1 = if typeof(T) == `function` then T(fake(1)) else T
		Out.Lines[Name] = { Differs = At3 ~= At1; At3 = At3 }
	end
	return Out
end

-- (2.32) the Permanent Record: Honours on made-up facts and once on the live player; entries, and every file number
function Commands.HonoursTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Honours).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end
function Commands.RecordTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Record).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

-- (2.33) trophies: the nine rules on made-up facts, and one granted once on the live player (taken back after)
function Commands.TrophyTest(PlayerName: string)
	return DeepCopy(require(ServerScriptService.Services.Player.Trophies).SelfTestForTests(Players:FindFirstChild(PlayerName)))
end

function Commands.WardrobeTest(PlayerName: string) -- (2.34)
	return DeepCopy(table.pack(require(ServerScriptService.Services.Player.Paths).WardrobeSelfTestForTests(Players:FindFirstChild(PlayerName))))
end

function Commands.TodayTest(PlayerName: string) -- (2.34) the Today card's server lines
	local P = Players:FindFirstChild(PlayerName)
	local T = require(ServerScriptService.Services.Features.Phone).Today(P)
	return DeepCopy({ Ok = typeof(T) == `table`; Today = T })
end

return Shared
