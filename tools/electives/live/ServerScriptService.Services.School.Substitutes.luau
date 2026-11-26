--[[
	Substitute teachers (server). Services.School.Substitutes   (1.47; the cast and rules: Config.Substitutes)

	The week's plan is drawn from the school week's number (Superlatives' week: floor(EventDay / 5)) with a seeded Random,
	so every server covers the same classes: DaysPerWeek of the five school days, each with one random subject, a
	substitute (no one twice in a week while the cast lasts), the Gambler's variant, and a twist (or none).

	On a covered day the substitute sits at the covered room's teacher's desk from 6 AM to the end of the school day, in
	the teacher's chair at the end of it, lounging (the slacker's SitChill; Features.Seats rests the hips and thighs on the
	cushion, clear of the chair back), or stands on
	clear floor beside the desk if the room has no chair. Talk to them for their rule (a line and a notice).
	School.Activities asks For(Subject) when a lesson starts: the rule changes the level, time and pay, a Swap or Game
	twist changes the minigame, and an Errand twist sends the student off instead (StartErrand).

	Errands: the thing turns up on a clear floor spot in the errand's region. Only the student it's for can pick it up; it
	rides in the right hand (NHErrandHeld). While on the errand the student has a hall pass for the covered room
	(Player attribute NHHallPass = room id: Attendance counts them as in class, so the hall monitor leaves them be).
	Hand it to the substitute before the bell and it counts as an A (Activities.GrantErrand). The bell, leaving, or going
	down ends it. NHErrandText is what the clock shows.

	API: Plan(Week?) -> { [weekday] = Entry }, Today() -> Entry?, For(Subject) -> Entry? (today's, if it covers that
	subject), Upcoming() -> Entry? (the next covered day later this week), StartErrand(P, Subject, Key, RoomId).
	Entry = { Day (event day), Weekday, Subject, Room, Sub (cast def), RuleName, RuleText, Rule, Twist?, Game?, Errand? }
	Tests: ForceForTests(Subject, SubId, Twist?, Extra?) covers Subject today, ClearForTests(), State().
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Config = require(ReplicatedStorage.Config.Substitutes)
local Classes = require(ReplicatedStorage.Config.Classes)
local Electives = require(ReplicatedStorage.Config.Electives)

local Shared = {}
local Local = {}

local Forced = nil            -- a test override for today
local NpcFor = {} :: { [string]: Model }   -- room -> the substitute standing there
local Errands = {} :: { [Player]: any }
local PlanCache = {}

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Part in Path:gmatch(`[^%.]+`) do Node = Node:FindFirstChild(Part) if not Node then return nil end end
	local Ok, Mod = pcall(require, Node)
	return Ok and Mod or nil
end

function Local.Clock()
	local C = svc(`School.SchoolClock`)
	local Ok, S = pcall(function() return C.GetState() end)
	return Ok and S or nil
end

function Local.EventDay(): number?
	local S = Local.Clock()
	if not (S and S.Day) then return nil end
	local Hour = S.Hour or ((S.MinuteOfDay or 720) / 60)
	return if Hour >= 6 then S.Day else S.Day - 1
end

function Local.RoomFor(Subject: string): string?
	for _, P in Classes.Periods do if P.Subject == Subject then return P.Room end end -- base
	local D = Electives.Get(Subject)
	return D and D.Room or nil
end

-- (Electives) an elective only meets on elective days; the Specimen twist only fits a bench (elective) class
function Local.IsElective(Subject: string): boolean
	return Electives.Get(Subject) ~= nil
end

function Local.SubjectsFor(Weekday: number): { string }
	local Day = Classes.IsElectiveSlot(`Period 3`, Weekday)
	local List = {}
	for _, S in Config.Subjects do
		if Day or not Local.IsElective(S) then table.insert(List, S) end
	end
	return List
end

---| the week's plan |---

function Local.Entry(Rng: Random, Day: number, Weekday: number, Sub, Subject: string)
	local E = { Day = Day; Weekday = Weekday; Subject = Subject; Room = Local.RoomFor(Subject); Sub = Sub;
		RuleName = Sub.RuleName; RuleText = Sub.RuleText; Rule = Sub.Rule or {} }
	if Sub.Variants then
		local V = Sub.Variants[Rng:NextInteger(1, #Sub.Variants)]
		E.RuleName, E.RuleText, E.Rule = V.RuleName, V.RuleText, V.Rule or {}
	end
	if Rng:NextNumber() < (Sub.TwistChance or 0) then
		local Twists = Sub.Twists
		if not Local.IsElective(Subject) then
			Twists = {}
			for _, T in Sub.Twists do if T ~= `Specimen` then table.insert(Twists, T) end end
		end
		local Twist = Twists[Rng:NextInteger(1, #Twists)]
		E.Twist = Twist
		if Twist == `Swap` then
			local Others = {}
			for _, S in Config.Subjects do if S ~= Subject and not Local.IsElective(S) then table.insert(Others, S) end end
			E.SwapSubject = Others[Rng:NextInteger(1, #Others)]
		elseif Twist == `Game` then
			local Ids = {}
			for Id in Config.Games do table.insert(Ids, Id) end
			table.sort(Ids)
			E.Game = Config.Games[Ids[Rng:NextInteger(1, #Ids)]]
		elseif Twist == `Errand` then
			local Id = Sub.Errands[Rng:NextInteger(1, #Sub.Errands)]
			E.ErrandId = Id
			E.Errand = Config.Errands[Id]
		end
	end
	return E
end

function Shared.Plan(Week: number?)
	local W = Week
	if not W then local D = Local.EventDay() W = D and math.floor(D / Config.SchoolDays) end
	if not W then return {} end
	if PlanCache[W] then return PlanCache[W] end
	local Rng = Random.new(W * 104729 + 7)
	local Count = Rng:NextInteger(Config.DaysPerWeek[1], Config.DaysPerWeek[2])
	local Days = {}
	for D = 0, Config.SchoolDays - 1 do table.insert(Days, D) end
	for I = #Days, 2, -1 do local J = Rng:NextInteger(1, I) Days[I], Days[J] = Days[J], Days[I] end
	local Cast = table.clone(Config.Cast)
	for I = #Cast, 2, -1 do local J = Rng:NextInteger(1, I) Cast[I], Cast[J] = Cast[J], Cast[I] end
	local Plan = {}
	for I = 1, Count do
		local Weekday = Days[I]
		local Pool = Local.SubjectsFor(Weekday)
		local Subject = Pool[Rng:NextInteger(1, #Pool)]
		local Sub = Cast[(I - 1) % #Cast + 1]
		Plan[Weekday] = Local.Entry(Rng, W * Config.SchoolDays + Weekday, Weekday, Sub, Subject)
	end
	PlanCache[W] = Plan
	return Plan
end

function Shared.Today()
	local D = Local.EventDay()
	if not D then return nil end
	if Forced and Forced.Day == D then return Forced end
	return Shared.Plan(math.floor(D / Config.SchoolDays))[D % Config.SchoolDays]
end

function Shared.For(Subject: string)
	local E = Shared.Today()
	return if E and E.Subject == Subject then E else nil
end

function Shared.Upcoming()
	local D = Local.EventDay()
	if not D then return nil end
	local Plan = Shared.Plan(math.floor(D / Config.SchoolDays))
	for W = D % Config.SchoolDays + 1, Config.SchoolDays - 1 do
		if Plan[W] then return Plan[W] end
	end
	return nil
end

---| the substitute at the desk |---

function Local.Desk(RoomId: string): BasePart?
	local School = workspace:FindFirstChild(`School`)
	local Room = School and School:FindFirstChild(RoomId)
	local Desk = Room and Room:FindFirstChild(`TeacherDesk`)
	return if Desk and Desk:IsA(`BasePart`) then Desk else nil
end

-- where the substitute stands: behind the desk, on the far side from the students' chairs, facing them
function Local.StandAt(RoomId: string): CFrame?
	local Desk = Local.Desk(RoomId)
	if not Desk then return nil end
	local School = workspace.School
	local Room = School:FindFirstChild(RoomId)
	local Sum, N = Vector3.zero, 0
	local Props = School:FindFirstChild(`NHProps`)
	local Zone
	for _, D in Room:GetDescendants() do if D:IsA(`BasePart`) and D.Name == `Zone` then Zone = D break end end
	for _, P in (Props and Props:GetChildren()) or {} do
		if P:IsA(`Model`) and P.Name:match(`^StudentChair`) then
			local At = P:GetPivot().Position
			local Inside = (At - Desk.Position).Magnitude < 40
			if Zone then
				local L = Zone.CFrame:PointToObjectSpace(At)
				Inside = math.abs(L.X) <= Zone.Size.X / 2 and math.abs(L.Z) <= Zone.Size.Z / 2
			end
			if Inside then Sum += At N += 1 end
		end
	end
	local Toward = if N > 0 then (Sum / N - Desk.Position) * Vector3.new(1, 0, 1) else -Desk.CFrame.LookVector * Vector3.new(1, 0, 1)
	if Toward.Magnitude < 0.1 then Toward = Vector3.new(0, 0, -1) end
	Toward = Toward.Unit
	local Behind = Desk.Position - Toward * (math.min(Desk.Size.X, Desk.Size.Z) / 2 + 1.6)
	-- the floor there
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, F in { `Live`, `NHSchedule`, `NHAmbient`, `NHSubstitutes` } do local X = workspace:FindFirstChild(F) if X then table.insert(Ex, X) end end
	RP.FilterDescendantsInstances = Ex
	local Hit = workspace:Raycast(Behind + Vector3.new(0, 6, 0), Vector3.new(0, -14, 0), RP)
	local Floor = if Hit then Hit.Position.Y else Desk.Position.Y - Desk.Size.Y / 2
	local Pos = Vector3.new(Behind.X, Floor, Behind.Z)
	return CFrame.lookAt(Pos, Pos + Toward)
end

-- the room's teacher's chair (the TeacherChair prop nearest the teacher's desk, within 7 studs: since 1.47 it stands at
-- the end of the desk, Studio/teacher_chairs.luau)
function Local.Chair(RoomId: string): Model?
	local Desk = Local.Desk(RoomId)
	local Props = workspace.School:FindFirstChild(`NHProps`)
	if not Desk then return nil end
	local Best, BD
	for _, P in (Props and Props:GetChildren()) or {} do
		if P:IsA(`Model`) and P.Name:match(`^TeacherChair`) then
			local D = (P:GetPivot().Position - Desk.Position) * Vector3.new(1, 0, 1)
			if D.Magnitude < 7 and (not BD or D.Magnitude < BD) then Best, BD = P, D.Magnitude end
		end
	end
	return Best
end

-- (owner) the substitute lounges in the chair: the staff-room slacker's sit, feet kicked up (AmbientNpcs ANIM.SitChill)
local SIT_CHILL = 124142826216078

-- clear floor beside the desk (either end, the teacher's side), for a room without a chair
function Local.BesideDesk(RoomId: string, At: CFrame): CFrame
	local Desk = Local.Desk(RoomId)
	if not Desk then return At end
	local OP = OverlapParams.new()
	OP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, F in { `Live`, `NHSchedule`, `NHAmbient`, `NHSubstitutes`, `Regions` } do local X = workspace:FindFirstChild(F) if X then table.insert(Ex, X) end end
	OP.FilterDescendantsInstances = Ex
	local Half = math.max(Desk.Size.X, Desk.Size.Z) / 2
	for _, Side in { 1, -1 } do
		for _, Extra in { 1.3, 2, 2.8 } do
			local C = At * CFrame.new(Side * (Half + Extra), 0, -1.2)
			if #workspace:GetPartBoundsInBox(C + Vector3.new(0, 2.4, 0), Vector3.new(1.8, 4.2, 1.8), OP) == 0 then return C end
		end
	end
	return At
end

function Local.Tag(Model: Model, Sub)
	local Tag = Instance.new(`BillboardGui`)
	Tag.Name = `NameTag`
	Tag.Size = UDim2.new(0, 220, 0, 40)
	Tag.StudsOffset = Vector3.new(0, 2.8, 0)
	Tag.MaxDistance = 70
	local Name = Instance.new(`TextLabel`)
	Name.Size = UDim2.new(1, 0, 0.6, 0)
	Name.BackgroundTransparency = 1
	Name.Font = Enum.Font.GothamBold
	Name.TextSize = 16
	Name.TextColor3 = Sub.Color
	Name.TextStrokeTransparency = 0.3
	Name.Text = Sub.Name
	Name.Parent = Tag
	local Role = Instance.new(`TextLabel`)
	Role.Position = UDim2.fromScale(0, 0.6)
	Role.Size = UDim2.new(1, 0, 0.4, 0)
	Role.BackgroundTransparency = 1
	Role.Font = Enum.Font.Gotham
	Role.TextSize = 12
	Role.TextColor3 = Color3.fromRGB(220, 220, 220)
	Role.TextStrokeTransparency = 0.4
	Role.Text = `Substitute · {Sub.Title}`
	Role.Parent = Tag
	Tag.Parent = Model:FindFirstChild(`Head`)
end

function Local.Folder(): Folder
	local F = workspace:FindFirstChild(`NHSubstitutes`)
	if not F then F = Instance.new(`Folder`) F.Name = `NHSubstitutes` F.Parent = workspace end
	return F
end

function Local.Say(P: Player, Model: Model, Text: string)
	local Cl = svc(`Social.Cliques`)
	if Cl and Cl.SayTo then pcall(Cl.SayTo, P, Model, Text) end
end

function Local.Notify(P: Player, Title: string, Text: string?, Kind: string?, Duration: number?)
	local N = svc(`Features.Notifications`)
	if N then pcall(N.Notify, P, { Title = Title; Text = Text; Kind = Kind or `Info`; Duration = Duration or 6 }) end
end

function Local.Spawn(E)
	local At = Local.StandAt(E.Room)
	if not At then warn(`[Substitutes] no teacher's desk in {E.Room}`) return nil end
	local AI = ServerScriptService.Services.AI.AI
	local Model = AI.Rig:Clone()
	Model.Name = E.Sub.Name
	Model:SetAttribute(`NHSubstitute`, E.Sub.Id)
	Model:SetAttribute(`NHSubRoom`, E.Room)
	Model:SetAttribute(`Role`, `Staff`)
	local Animate = AI.Animate:Clone()
	Animate.Parent = Model
	Animate.Enabled = true
	local Hum = Model:FindFirstChildWhichIsA(`Humanoid`)
	local Root = Model:FindFirstChild(`HumanoidRootPart`)
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Model.Parent = Local.Folder()
	Root.Anchored = true
	local Chair = Local.Chair(E.Room)
	local Seats = svc(`Features.Seats`)
	if Chair and Seats then
		-- sit in the teacher's chair, facing where the chair faces
		local Top = Seats.Top(Chair)
		local Face = Chair:GetPivot().LookVector * Vector3.new(1, 0, 1)
		local Want = CFrame.lookAt(Top + Vector3.new(0, 1.05, 0), Top + Vector3.new(0, 1.05, 0) + (if Face.Magnitude > 0 then Face.Unit else At.LookVector))
		Model:PivotTo(Want * Root.CFrame:Inverse() * Model:GetPivot())
		local Animator = Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, Hum)
		local Anim = Instance.new(`Animation`)
		Anim.AnimationId = `rbxassetid://{SIT_CHILL}`
		local Ok, Track = pcall(function() return Animator:LoadAnimation(Anim) end)
		if Ok and Track then Track.Looped = true Track.Priority = Enum.AnimationPriority.Action Track:Play(0.3) end
		Model:SetAttribute(`NHSeated`, true)
		-- once the pose is on: hips and thighs on the cushion, clear of the chair back and the wall behind
		Seats.SettleWhenPosed(Model, Hum, Top, Seats.Back(Chair), function() return Model.Parent ~= nil end, 0.15, SIT_CHILL, Chair)
	else
		-- stand on clear floor: the root sits a leg's length + half the root above it
		local Leg = Model:FindFirstChild(`Left Leg`)
		local Up = (Leg and Leg.Size.Y or 2) + Root.Size.Y / 2
		local Spot = Local.BesideDesk(E.Room, At)
		Model:PivotTo(Spot * CFrame.new(0, Up, 0) * Root.CFrame:Inverse() * Model:GetPivot())
	end
	local Looks = svc(`Features.NpcLooks`)
	if Looks then task.spawn(Looks.Apply, Model, E.Sub.Look) end
	Local.Tag(Model, E.Sub)
	local Interaction = require(ReplicatedStorage.Config.Interaction)
	local Prompt = Instance.new(`ProximityPrompt`)
	Prompt.Name = `TalkPrompt`
	Prompt.ActionText = `Talk`
	Prompt.ObjectText = E.Sub.Name
	Prompt.KeyboardKeyCode = Interaction.PromptKey
	Prompt.GamepadKeyCode = Interaction.GamepadKey
	Prompt.HoldDuration = 0
	Prompt.MaxActivationDistance = 10
	Prompt.RequiresLineOfSight = false
	Prompt.Parent = Root
	Prompt.Triggered:Connect(function(P)
		local Ok, Err = pcall(Local.Talk, P, E, Model)
		if not Ok then warn(`[Substitutes] {Err}`) end
	end)
	return Model
end

function Local.Talk(P: Player, E, Model: Model)
	local Er = Errands[P]
	if Er and Er.Entry.Room == E.Room then
		if Er.Held then Local.CompleteErrand(P) return end
		Local.Say(P, Model, `Well? {Er.Def.Text} won't fetch itself. {Er.Def.Place}.`)
		return
	end
	local Lines = E.Sub.Lines.Hello
	Local.Say(P, Model, Lines[math.random(1, #Lines)])
	Local.Notify(P, `{E.Sub.Name}: {E.RuleName}`, E.RuleText, `Info`, 8)
end

function Local.Refresh()
	local E = Shared.Today()
	local S = Local.Clock()
	local Hour = S and (S.Hour or ((S.MinuteOfDay or 0) / 60)) or 0
	-- covered rooms stay staffed from 6 AM through the school day
	local Want = {}
	if E and E.Room and Hour >= 6 and Hour < 17 then Want[E.Room] = E end
	for Room, M in NpcFor do
		local W = Want[Room]
		if not (W and M.Parent and M:GetAttribute(`NHSubstitute`) == W.Sub.Id) then
			if M.Parent then M:Destroy() end
			NpcFor[Room] = nil
		end
	end
	for Room, W in Want do
		if not NpcFor[Room] then
			local M = Local.Spawn(W)
			if M then NpcFor[Room] = M end
		end
	end
end

---| errands |---

function Local.RegionBox(Id: string): BasePart?
	local F = workspace:FindFirstChild(`Regions`)
	for _, B in (F and F:GetDescendants()) or {} do
		if B:IsA(`BasePart`) and (B:GetAttribute(`RegionId`) or B.Name) == Id then return B end
	end
	return nil
end

-- a clear floor spot inside the region box: no prop within a body's width, floor under it
function Local.ErrandSpot(Id: string): Vector3?
	local B = Local.RegionBox(Id)
	if not B then return nil end
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, F in { `Live`, `NHSchedule`, `NHAmbient`, `NHSubstitutes`, `Regions`, `NHLostFound` } do local X = workspace:FindFirstChild(F) if X then table.insert(Ex, X) end end
	RP.FilterDescendantsInstances = Ex
	RP.RespectCanCollide = true
	local OP = OverlapParams.new()
	OP.FilterType = Enum.RaycastFilterType.Exclude
	OP.FilterDescendantsInstances = Ex
	local Rng = Random.new()
	for _ = 1, 60 do
		local L = Vector3.new(Rng:NextNumber(-0.4, 0.4) * B.Size.X, 0, Rng:NextNumber(-0.4, 0.4) * B.Size.Z)
		local P = B.CFrame:PointToWorldSpace(L)
		local Top = B.Position.Y + B.Size.Y / 2
		-- region boxes don't always sit on the floor (some float well above the room), so cast all the way down and
		-- take the lowest walkable surface in the column: the room's floor, not its roof
		local Hit, Ground, From = nil, nil, Vector3.new(P.X, Top, P.Z)
		for _ = 1, 8 do
			local H = workspace:Raycast(From, Vector3.new(0, -(From.Y + 20), 0), RP)
			if not H then break end
			if H.Normal.Y > 0.8 and H.Instance.Size.Y < 3 then
				-- the map's baseplate runs under every building: only the floor if nothing else is
				if H.Instance.Name == `Baseplate` or H.Instance:IsA(`Terrain`) then Ground = Ground or H else Hit = H end
			end
			From = H.Position - Vector3.new(0, 0.05, 0)
		end
		Hit = Hit or Ground
		if Hit then
			local Clear = #workspace:GetPartBoundsInBox(CFrame.new(Hit.Position + Vector3.new(0, 2.4, 0)), Vector3.new(2.5, 4.2, 2.5), OP) == 0
			if Clear then return Hit.Position end
		end
	end
	return nil
end

function Local.ItemModel(Def): Model
	local Lib = ServerStorage:FindFirstChild(`NHProps`)
	local T = Lib and Lib:FindFirstChild(Def.Prop)
	local M
	if T and T:IsA(`Model`) then
		M = T:Clone()
	else
		M = Instance.new(`Model`)
		local P = Instance.new(`Part`)
		P.Size = Vector3.new(0.9, 0.3, 0.7)
		P.Color = Color3.fromRGB(150, 120, 90)
		P.Parent = M
		M.PrimaryPart = P
	end
	for _, P in M:GetDescendants() do
		if P:IsA(`BasePart`) then P.Anchored, P.CanCollide, P.CanTouch, P.CanQuery, P.Massless = true, false, false, true, true end
	end
	return M
end

function Local.ClearErrand(P: Player)
	local Er = Errands[P]
	Errands[P] = nil
	if Er then
		if Er.Item and Er.Item.Parent then Er.Item:Destroy() end
	end
	if P.Parent then
		P:SetAttribute(`NHHallPass`, nil)
		P:SetAttribute(`NHErrandText`, nil)
		local C = P.Character
		local H = C and C:FindFirstChild(`NHErrandHeld`)
		if H then H:Destroy() end
	end
end

function Local.PickUp(P: Player)
	local Er = Errands[P]
	if not Er or Er.Held then return end
	local C = P.Character
	local Hand = C and (C:FindFirstChild(`RightHand`) or C:FindFirstChild(`Right Arm`))
	if not Hand then return end
	if Er.Item and Er.Item.Parent then Er.Item:Destroy() end
	local M = Local.ItemModel(Er.Def)
	M.Name = `NHErrandHeld`
	local Root = M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)
	for _, Pt in M:GetDescendants() do
		if Pt:IsA(`BasePart`) then
			Pt.Anchored = false Pt.CanQuery = false
			if Pt ~= Root then local W = Instance.new(`WeldConstraint`) W.Part0 = Root W.Part1 = Pt W.Parent = Pt end
		end
	end
	M:PivotTo(Hand.CFrame * CFrame.new(0, -(Hand.Size.Y / 2) - 0.05, -0.15) * CFrame.Angles(math.rad(-90), 0, 0))
	local W = Instance.new(`WeldConstraint`)
	W.Part0 = Hand W.Part1 = Root W.Parent = Root
	M.Parent = C
	Er.Held = true
	Er.Item = nil
	P:SetAttribute(`NHErrandText`, `Errand: bring {Er.Def.Text} back to {Er.Entry.Sub.Name} before the bell`)
	Local.Notify(P, `Got it`, `Now take {Er.Def.Text} back to {Er.Entry.Sub.Name} in {Classes.Rooms[Er.Entry.Room] or Er.Entry.Room}.`, `Good`, 5)
end

function Shared.StartErrand(P: Player, Subject: string, Key: string, RoomId: string)
	local E = Shared.For(Subject)
	if not (E and E.Errand) then return false end
	if Errands[P] then
		Local.Notify(P, `You're already on an errand`, P:GetAttribute(`NHErrandText`))
		return false
	end
	local At = Local.ErrandSpot(E.Errand.Region)
	if not At then
		warn(`[Substitutes] no spot for the errand in {E.Errand.Region}`)
		return false
	end
	local M = Local.ItemModel(E.Errand)
	M.Name = `NHErrand_{P.UserId}`
	M:PivotTo(CFrame.new(At) * CFrame.Angles(0, math.random() * math.pi * 2, 0))
	M.Parent = Local.Folder()
	local Root = M.PrimaryPart or M:FindFirstChildWhichIsA(`BasePart`, true)
	local Interaction = require(ReplicatedStorage.Config.Interaction)
	local Pr = Instance.new(`ProximityPrompt`)
	Pr.Name = `NHErrandPickUp`
	Pr.ActionText = `Pick up`
	Pr.ObjectText = `{E.Errand.Text} ({E.Sub.Name}'s)`
	Pr.KeyboardKeyCode = Interaction.PromptKey
	Pr.GamepadKeyCode = Interaction.GamepadKey
	Pr.HoldDuration = 0.3
	Pr.MaxActivationDistance = 8
	Pr.RequiresLineOfSight = false
	Pr.Parent = Root
	Pr.Triggered:Connect(function(Who)
		if Who ~= P then Local.Notify(Who, `That's not yours to take`) return end
		pcall(Local.PickUp, P)
	end)
	local Glint = Instance.new(`ParticleEmitter`)
	Glint.Texture = `rbxasset://textures/particles/sparkles_main.dds`
	Glint.Rate = 2 Glint.Lifetime = NumberRange.new(0.6, 1) Glint.Speed = NumberRange.new(0.2)
	Glint.Size = NumberSequence.new(0.35, 0) Glint.LightEmission = 0.8
	Glint.Color = ColorSequence.new(Color3.fromRGB(255, 236, 190))
	Glint.Parent = Root
	local State = Local.Clock()
	Errands[P] = { Entry = E; Def = E.Errand; Subject = Subject; Key = Key; Room = RoomId; Item = M; Held = false;
		SegmentIndex = State and State.SegmentIndex }
	P:SetAttribute(`NHHallPass`, RoomId)
	P:SetAttribute(`NHErrandText`, `Errand: fetch {E.Errand.Text} from {E.Errand.Place} for {E.Sub.Name}`)
	local Model = NpcFor[E.Room]
	if Model then Local.Say(P, Model, E.Sub.Lines.Errand) end
	Local.Notify(P, `{E.Sub.Name}: an errand`, `Fetch {E.Errand.Text} from {E.Errand.Place} and bring it back before the bell. You have a hall pass.`, `Info`, 8)
	return true
end

function Local.CompleteErrand(P: Player)
	local Er = Errands[P]
	if not (Er and Er.Held) then return end
	-- (audit) handed in after the bell (before TickErrands noticed): it no longer pays as the ended period's A
	local State = Local.Clock()
	if State and Er.SegmentIndex and State.SegmentIndex ~= Er.SegmentIndex then
		Local.ClearErrand(P)
		Local.Notify(P, `The bell rang`, `{Er.Entry.Sub.Name} gave up waiting for {Er.Def.Text}.`, `Bad`, 6)
		return
	end
	local Act = svc(`School.Activities`)
	Local.ClearErrand(P)
	local Model = NpcFor[Er.Entry.Room]
	if Model then
		local Lines = Er.Entry.Sub.Lines.Pass
		Local.Say(P, Model, Lines[math.random(1, #Lines)])
	end
	if Act and Act.GrantErrand then pcall(Act.GrantErrand, P, Er.Subject, Er.Key, Er.Entry) end
end

function Local.TickErrands()
	local State = Local.Clock()
	for P, Er in Errands do
		if not P.Parent then Errands[P] = nil continue end
		local Hum = P.Character and P.Character:FindFirstChildWhichIsA(`Humanoid`)
		local Down = not Hum or Hum.Health <= 0 or Hum:GetAttribute(`Downed`)
		if State and Er.SegmentIndex and State.SegmentIndex ~= Er.SegmentIndex then
			Local.ClearErrand(P)
			Local.Notify(P, `The bell rang`, `{Er.Entry.Sub.Name} gave up waiting for {Er.Def.Text}.`, `Bad`, 6)
		elseif Down then
			Local.ClearErrand(P)
			Local.Notify(P, `Errand dropped`, `You went down. {Er.Def.Text} is lost again.`, `Bad`, 5)
		end
	end
end

---| tests |---

-- cover Subject today with a substitute (Twist: nil / `Swap` / `Game` / `Errand`; Extra: the swapped subject, the
-- game id, or the errand id)
function Shared.ForceForTests(Subject: string, SubId: string, Twist: string?, Extra: string?, Variant: number?)
	local Sub = Config.ById[SubId]
	local D = Local.EventDay()
	if not (Sub and D) then return nil end
	local E = { Day = D; Weekday = D % Config.SchoolDays; Subject = Subject; Room = Local.RoomFor(Subject); Sub = Sub;
		RuleName = Sub.RuleName; RuleText = Sub.RuleText; Rule = Sub.Rule or {} }
	if Sub.Variants then
		local V = Sub.Variants[Variant or 1]
		E.RuleName, E.RuleText, E.Rule = V.RuleName, V.RuleText, V.Rule or {}
	end
	E.Twist = Twist
	if Twist == `Swap` then E.SwapSubject = Extra or `Chemistry`
	elseif Twist == `Game` then E.Game = Config.Games[Extra or `CandleVigil`]
	elseif Twist == `Errand` then E.ErrandId = Extra or Sub.Errands[1] E.Errand = Config.Errands[E.ErrandId] end
	Forced = E
	Local.Refresh()
	return { Subject = E.Subject; Room = E.Room; Sub = Sub.Name; Rule = E.RuleName; Twist = E.Twist }
end

function Shared.ClearForTests()
	Forced = nil
	for P in table.clone(Errands) do Local.ClearErrand(P) end
	Local.Refresh()
	return true
end

function Shared.PickUpForTests(P: Player)
	local Er = Errands[P]
	if not Er then return false end
	Local.PickUp(P)
	return Er.Held
end

function Shared.HandInForTests(P: Player)
	local Er = Errands[P]
	if not (Er and Er.Held) then return false end
	Local.CompleteErrand(P)
	return true
end

function Shared.State()
	local E = Shared.Today()
	local Plan = Shared.Plan()
	local Week = {}
	for W, X in Plan do Week[tostring(W)] = { Subject = X.Subject; Sub = X.Sub.Id; Rule = X.RuleName; Twist = X.Twist; Swap = X.SwapSubject; Game = X.Game and X.Game.Type; Errand = X.ErrandId } end
	local Out = { EventDay = Local.EventDay(); Today = E and { Subject = E.Subject; Room = E.Room; Sub = E.Sub.Id; Twist = E.Twist }; Week = Week; Npcs = {}; Errands = {} }
	for Room, M in NpcFor do Out.Npcs[Room] = M.Parent and M:GetFullName() or nil end
	for P, Er in Errands do Out.Errands[P.Name] = { Held = Er.Held; Item = Er.Item and Er.Item:GetFullName(); Text = Er.Def.Text } end
	return Out
end

---| start |---

function Shared.OnStart()
	Players.PlayerRemoving:Connect(function(P) Local.ClearErrand(P) end)
	task.spawn(function()
		while true do
			pcall(Local.Refresh)
			pcall(Local.TickErrands)
			task.wait(2)
		end
	end)
end

return Shared
