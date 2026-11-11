--[[
	Training (server). Services.Features.Training   (training minigames, phase 1: 2026-11-11; docs/Training.md)
	The gym stations (CollectionService tag NHTrainStation: a Model with attribute Station = PushUp | PullUp | SitUp |
	Squat, a part named Spot where the student's root goes, and a ProximityPrompt "Train"). One area is trained per set;
	when a set steps the area up, only that area's body meshes change (Appearance.SetArea).

	The server decides everything. Begin rolls a seed (the client draws the same ring plan from Config.Training.Plan);
	Submit carries only press and release times, which are checked (nothing in the future, sorted, at most ~12 a second,
	not machine-perfect) and scored here against the server's own plan. XP, caps, levels, paths, meshes, bests, streak
	Yen and clique standing are all worked out here, and saved in PlayerData.Training (action SetTraining) only.

	Remotes ReplicatedStorage.NHTraining (Ready):
	  Get (RF) -> state             Begin (RF) -> { Ok, Seed, Level, ... }    Submit (RF presses) -> result
	  Leave (RE)    Tutorial (RE)   Settle (RE dy: the client measures its pose; clamped, cosmetic)
	  Event (RE, server -> client) "Enter" { Station, State } | "Left" | "State" { State }
	API: Effects(Player) -> Progression effects, State(Player), Get(Player), TestGrant(Player, Area, Xp) (Studio).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local CollectionService = game:GetService(`CollectionService`)
local RunService = game:GetService(`RunService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Config = require(ReplicatedStorage.Config.Training)
local Appearance = require(ReplicatedStorage.UI.Appearance)

local Shared = {}
local Local = {}

local Seats = {} :: { [Player]: { Station: Model, Id: string, Spot: CFrame, Y: number, Loads: { Instance } } }
local Occupant = {} :: { [Model]: Player }
local Active = {} :: { [Player]: { Seed: number, Level: number, Area: string, Station: string, BeginAt: number, Plan: any } }
local LastBegin = {} :: { [Player]: number }
local LastEnd = {} :: { [Player]: number }
local LastCall = {} :: { [string]: { [Player]: number } }
local Folder: Folder? = nil
local EventRE: RemoteEvent? = nil

local function try(Path: { string })
	local Ok, M = pcall(function()
		local X: Instance = ServerScriptService
		for _, N in Path do X = X:FindFirstChild(N) :: Instance end
		return require(X :: ModuleScript)
	end)
	return if Ok then M else nil
end

---| data |---

function Shared.Get(P: Player)
	local Profile = Data.GetProfile(P)
	if not Profile then return nil end
	return Config.Sanitize(Profile.Training)
end

function Local.Save(P: Player, T)
	Data.UpdateState(P, { type = `SetTraining`; training = T })
end

-- first load: each area starts from the build the student already wears, so saved bodies keep working
function Local.Seed(P: Player)
	local Profile = Data.GetProfile(P)
	if not Profile then return end
	local T = Config.Sanitize(Profile.Training)
	if T.Seeded then return end
	local Look = Appearance.Sanitize(Profile.Appearance)
	local Areas = Appearance.AreaBodies(Look)
	for _, A in Config.Areas do
		local Build, Step = Appearance.BodyBuild(Areas[A])
		local S = T[A]
		if Step > 0 and S.Level < (Config.StepLevels[Step] or 0) then
			S.Level = Config.StepLevels[Step]
			S.Xp = 0
		end
		if Build ~= `Average` then S.Path = Config.BuildPath[Build] or S.Path end
	end
	T.Seeded = true
	Local.Save(P, T)
end

function Local.TierOf(Level: number) return Config.TierFor(Level) end

-- what the client shows: the three areas and everything the cards need
function Shared.State(P: Player)
	local T = Shared.Get(P)
	if not T then return nil end
	local Now = os.time()
	local Day = Config.Day(Now)
	local Out = { Areas = {}; Streak = T.Streak; StreakBest = T.StreakBest; Best = T.Best; Tut = T.Tut; Day = Day;
		StreakAlive = T.Day == Day or T.Day == Day - 1; TrainedToday = T.Day == Day }
	local Look = Appearance.Sanitize((Data.GetProfile(P) or {}).Appearance)
	local Bodies = Appearance.AreaBodies(Look)
	for _, A in Config.Areas do
		local S = T[A]
		local Sore = Config.SoreNow(S, Now)
		local NextAt = Config.NextStepLevel(S.Level)
		local ToStep = if NextAt then Config.TotalTo(NextAt) - (Config.TotalTo(S.Level) + S.Xp) else nil
		local B = Appearance.Bodies[Bodies[A]] or Appearance.Bodies[1]
		local NextName
		if NextAt then
			local Path = if S.Path == `Average` then `Conditioned` else S.Path
			local Idx = Appearance.BodyFor(Appearance.BodyGender(Look.Body), Config.PathBuild[Path], Config.StepFor(NextAt))
			NextName = Idx and Appearance.Bodies[Idx].Name
		end
		Out.Areas[A] = { Level = S.Level; Xp = S.Xp; ToNext = Config.ToNext(S.Level); Path = S.Path; Sore = Sore;
			SoreMult = Config.SoreMult(Sore); Fresh = T.Fresh[A] ~= Day; DayXp = if T.XpDay == Day then T.DayXp[A] else 0;
			Cap = Config.DailyCap; Tier = Config.TierFor(S.Level).Name; Step = Config.StepFor(S.Level); ToStep = ToStep;
			NextStepAt = NextAt; Body = B.Name; NextBody = NextName }
	end
	return Out
end

---| stat effects (Config.Progression.Training; read by Services.Player.Progression) |---

function Shared.Effects(P: Player)
	local E = {}
	local T = Shared.Get(P)
	if not T then return E end
	local Ok, Prog = pcall(require, ReplicatedStorage.Config.Progression)
	local Per = Ok and Prog.Training or nil
	if not Per then return E end
	for _, A in Config.Areas do
		local L = T[A].Level
		if L > 0 then
			for K, V in Per[A] or {} do E[K] = (E[K] or 0) + V * L end
		end
	end
	return E
end

---| stations |---

function Local.Fire(P: Player, Kind: string, D: any?)
	if EventRE and P.Parent then EventRE:FireClient(P, Kind, D) end
end

function Local.StandHeight(Char: Model): number
	local Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	local Leg = Char:FindFirstChild(`Left Leg`) :: BasePart?
	return (if Root then Root.Size.Y / 2 else 1) + (if Hum then Hum.HipHeight else 0) + (if Leg then Leg.Size.Y else 2)
end

function Local.Sit(P: Player, Station: Model)
	local Id = Station:GetAttribute(`Station`)
	local Def = typeof(Id) == `string` and Config.Stations[Id]
	if not Def then return end
	if Seats[P] or (Occupant[Station] and Occupant[Station].Parent) then return end
	local Char = P.Character
	local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not (Root and Hum and Hum.Health > 0) then return end
	if Char:GetAttribute(`Downed`) or Hum:GetAttribute(`Downed`) then return end
	local Tag = P:GetAttribute(`CombatTagUntil`)
	if typeof(Tag) == `number` and Tag > workspace:GetServerTimeNow() then
		pcall(function() require(ServerScriptService.Services.Features.Notifications).Notify(P, { Title = `Training`; Text = `Catch your breath first: you are in a fight.`; Kind = `Warning` }) end)
		return
	end
	if not Data.GetProfile(P) then return end
	local Spot = Station:FindFirstChild(`Spot`) :: BasePart?
	if not Spot then return end
	Local.Seed(P)
	local Up = Local.StandHeight(Char)
	local CF = Spot.CFrame * CFrame.new(0, Up - Spot.Size.Y / 2, 0)
	Occupant[Station] = P
	Seats[P] = { Station = Station; Id = Id; Spot = CF; Y = 0; Loads = {} }
	Root.AssemblyLinearVelocity = Vector3.zero
	Root.Anchored = true
	Root.CFrame = CF
	Char:SetAttribute(`NHTraining`, Id)
	P:SetAttribute(`NHTraining`, Id)
	local Prompt = Station:FindFirstChildWhichIsA(`ProximityPrompt`, true)
	if Prompt then Prompt.Enabled = false end
	Local.Loads(P)
	Local.Fire(P, `Enter`, { Station = Id; State = Shared.State(P) })
end

function Local.Stand(P: Player, Why: string?)
	local S = Seats[P]
	if not S then return end
	Seats[P] = nil
	Active[P] = nil
	if Occupant[S.Station] == P then Occupant[S.Station] = nil end
	local Prompt = S.Station:FindFirstChildWhichIsA(`ProximityPrompt`, true)
	if Prompt then Prompt.Enabled = true end
	for _, L in S.Loads do pcall(function() L:Destroy() end) end
	local Char = P.Character
	if Char then
		Char:SetAttribute(`NHTraining`, nil)
		local Root = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if Root and Root.Anchored then
			-- step off the station, standing, a little in front of it
			Root.CFrame = S.Spot * CFrame.new(0, 0, -2.5)
			Root.Anchored = false
		end
	end
	P:SetAttribute(`NHTraining`, nil)
	LastEnd[P] = os.clock()
	Local.Fire(P, `Left`, { Why = Why })
end

-- the load you train under (a weighted vest, belt or sandbag), fitted to your body type's depth so it never clips
local DEPTH = { lean = 0.87, petite = 0.94, athletic = 1.05, toned = 1.05, strong = 1.07, muscular = 1.14, stocky = 1.19,
	plus = 1.19, heavy = 1.22, curvy = 1.23, female = 1.08, standard = 1.0 }
function Local.Loads(P: Player)
	local S = Seats[P]
	if not S then return end
	for _, L in S.Loads do pcall(function() L:Destroy() end) end
	S.Loads = {}
	local T = Shared.Get(P)
	local Def = Config.Stations[S.Id]
	local Tier = Config.TierFor(T and T[Def.Area].Level or 0)
	if Tier.Load <= 0 then return end
	local Char = P.Character
	local Torso = Char and Char:FindFirstChild(`Torso`) :: BasePart?
	if not Torso then return end
	local Look = Appearance.Sanitize((Data.GetProfile(P) or {}).Appearance)
	local Body = Appearance.Bodies[Appearance.AreaBodies(Look).Torso] or Appearance.Bodies[1]
	local D = DEPTH[Body.Id] or 1.0
	local Leather, Iron, Brass = Color3.fromRGB(58, 20, 24), Color3.fromRGB(38, 36, 40), Color3.fromRGB(176, 128, 62)
	local M = Instance.new(`Model`)
	M.Name = `NHTrainLoad`
	local function part(Size: Vector3, Off: CFrame, Color: Color3, Mat: Enum.Material, Shape: Enum.PartType?)
		local X = Instance.new(`Part`)
		X.Size = Size
		X.Shape = Shape or Enum.PartType.Block
		X.Color = Color
		X.Material = Mat
		X.CanCollide, X.CanQuery, X.CanTouch, X.Massless = false, false, false, true
		X.CastShadow = true
		X.CFrame = Torso.CFrame * Off
		local W = Instance.new(`WeldConstraint`)
		W.Part0, W.Part1 = Torso, X
		W.Parent = X
		X.Parent = M
		return X
	end
	local Th = 0.10 + 0.03 * Tier.Load
	if Def.Load == `Vest` then
		-- front and back plates touching the deepest point of the chest and back; shoulder straps over the top
		for _, Z in { -1, 1 } do
			part(Vector3.new(1.7, 1.25, Th), CFrame.new(0, 0.2, Z * (D / 2 + Th / 2)), Leather, Enum.Material.Leather)
			for K = 1, Tier.Load do
				part(Vector3.new(0.42, 0.28, 0.1), CFrame.new((K - (Tier.Load + 1) / 2) * 0.5, -0.12, Z * (D / 2 + Th + 0.05)), Iron, Enum.Material.Metal)
			end
		end
		for _, X in { -0.55, 0.55 } do
			part(Vector3.new(0.3, 0.06, D + 2 * Th), CFrame.new(X, 1.0 + 0.03, 0), Leather, Enum.Material.Leather)
		end
		part(Vector3.new(0.22, 0.14, 0.04), CFrame.new(0, 0.62, -(D / 2 + Th + 0.02)), Brass, Enum.Material.Metal)
	elseif Def.Load == `Belt` then
		-- a weighted belt round the waist (the torso box is 2 wide), iron weights at the sides
		local H = 0.34
		part(Vector3.new(2.0 + 0.08, H, D + 0.08), CFrame.new(0, -0.8, 0), Leather, Enum.Material.Leather)
		part(Vector3.new(0.4, 0.26, 0.06), CFrame.new(0, -0.8, -(D / 2 + 0.07)), Brass, Enum.Material.Metal)
		for K = 1, Tier.Load do
			for _, X in { -1, 1 } do
				part(Vector3.new(0.12, 0.3, 0.36), CFrame.new(X * (1.04 + 0.06), -0.8, (K - (Tier.Load + 1) / 2) * 0.4), Iron, Enum.Material.Metal)
			end
		end
	elseif Def.Load == `Sandbag` then
		-- a canvas sandbag across the back of the shoulders, behind the head
		local Dia = 0.6 + 0.08 * Tier.Load
		part(Vector3.new(2.7, Dia, Dia), CFrame.new(0, 1.0 + Dia / 2 - 0.15, 0.5 + Dia / 2), Color3.fromRGB(122, 104, 78), Enum.Material.Fabric, Enum.PartType.Cylinder)
		for _, X in { -0.9, 0.9 } do
			part(Vector3.new(0.12, Dia + 0.04, Dia + 0.04), CFrame.new(X, 1.0 + Dia / 2 - 0.15, 0.5 + Dia / 2), Leather, Enum.Material.Leather, Enum.PartType.Cylinder)
		end
	end
	M.Parent = Char
	table.insert(S.Loads, M)
end

---| sets |---

function Local.Limited(P: Player, Name: string, Gap: number): boolean
	local Now = os.clock()
	local T = LastCall[Name] or {}
	LastCall[Name] = T
	if T[P] and Now - T[P] < Gap then return true end
	T[P] = Now
	return false
end

function Shared.Begin(P: Player)
	local S = Seats[P]
	if not S then return { Ok = false; Message = `Use a training station first.` } end
	local Now = os.clock()
	if Active[P] and Now - Active[P].BeginAt > Active[P].Plan.Duration + Config.Check.StalePad then Active[P] = nil end  -- abandoned
	if Active[P] then return { Ok = false; Message = `Finish this set first.` } end
	if (LastBegin[P] and Now - LastBegin[P] < Config.Check.BeginGap) or (LastEnd[P] and Now - LastEnd[P] < 0.8) then
		return { Ok = false; Message = `Catch your breath.` }
	end
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root or (Root.Position - S.Spot.Position).Magnitude > Config.Check.StationRange then
		Local.Stand(P, `Away`)
		return { Ok = false; Message = `You left the station.` }
	end
	local T = Shared.Get(P)
	if not T then return { Ok = false; Message = `Your record isn't loaded yet.` } end
	local Def = Config.Stations[S.Id]
	local Level = T[Def.Area].Level
	local Seed = math.random(1, 2 ^ 30)
	local PlanT = Config.Plan(Seed, Level)
	Active[P] = { Seed = Seed; Level = Level; Area = Def.Area; Station = S.Id; BeginAt = Now; Plan = PlanT }
	LastBegin[P] = Now
	return { Ok = true; Seed = Seed; Level = Level; Area = Def.Area; Station = S.Id; Burnout = PlanT.Burnout; Reps = #PlanT.Rings }
end

-- the press list the client sent, checked; nil + reason if it can't be real
function Local.CleanPresses(Raw: any, Elapsed: number, Plan): ({ any }?, string?)
	if typeof(Raw) ~= `table` then return nil, `bad` end
	if #Raw > #Plan.Rings * 2 + 8 then return nil, `too many presses` end
	local Out = {}
	local Last = -math.huge
	for _, X in Raw do
		if typeof(X) ~= `table` then return nil, `bad` end
		local Tp, Rl = X.T, X.R
		if typeof(Tp) ~= `number` or Tp ~= Tp or Tp < -1 or Tp > 600 then return nil, `bad time` end
		if Rl ~= nil and (typeof(Rl) ~= `number` or Rl ~= Rl or Rl < Tp or Rl > 600) then return nil, `bad release` end
		if Tp > Elapsed + Config.Check.FutureSlack then return nil, `a press from the future` end
		if Rl and Rl > Elapsed + Config.Check.FutureSlack then Rl = Elapsed end
		if Tp < Last then return nil, `out of order` end
		if Tp - Last < Config.Check.MinPressGap then return nil, `faster than a hand can press` end
		Last = Tp
		table.insert(Out, { T = Tp; R = Rl })
	end
	return Out
end

function Shared.Submit(P: Player, Raw: any)
	local A = Active[P]
	Active[P] = nil
	if not A then return { Ok = false; Message = `No set running.` } end
	local Now = os.clock()
	local Elapsed = Now - A.BeginAt
	if Elapsed > A.Plan.Duration + Config.Check.StalePad then return { Ok = false; Message = `That set went stale.` } end
	local Presses, Why = Local.CleanPresses(Raw, Elapsed, A.Plan)
	if not Presses then
		warn(`[Training] {P.Name}: set refused ({Why})`)
		return { Ok = false; Message = `That set doesn't add up.`; Refused = Why }
	end
	local Res = Config.Score(A.Plan, A.Level, Presses)
	-- machine-perfect timing: many hits whose offsets barely vary and sit on zero
	if #Res.Offsets >= Config.Check.BotHits then
		local Sum, Sq = 0, 0
		for _, O in Res.Offsets do Sum += O Sq += O * O end
		local Mean = Sum / #Res.Offsets
		local Sd = math.sqrt(math.max(0, Sq / #Res.Offsets - Mean * Mean))
		if Sd < Config.Check.BotSpread and math.abs(Mean) < Config.Check.BotSpread then
			warn(`[Training] {P.Name}: set refused (machine timing, sd {Sd})`)
			return { Ok = false; Message = `That set doesn't add up.`; Refused = `machine timing` }
		end
	end
	-- nothing scored after the set's own end can count, and nothing after the server's clock
	return Local.Award(P, A, Res)
end

function Local.Award(P: Player, A, Res)
	local T = Shared.Get(P)
	if not T then return { Ok = false; Message = `Your record isn't loaded yet.` } end
	local NowT = os.time()
	local Day = Config.Day(NowT)
	if T.XpDay ~= Day then
		for _, Ar in Config.Areas do T.DayXp[Ar] = 0 end
		T.XpDay = Day
	end
	local S = T[A.Area]
	local Sore = Config.SoreNow(S, NowT)
	local Counts = Res.Reps >= Config.MinRepsForSet
	local Fresh = Counts and T.Fresh[A.Area] ~= Day
	local StreakUp, YenReward = false, nil
	if Counts and T.Day ~= Day then
		if T.Day == Day - 1 then T.Streak += 1 else T.Streak = 1 T.StreakPaid = {} end
		T.Day = Day
		StreakUp = true
		T.StreakBest = math.max(T.StreakBest, T.Streak)
		local Yen = Config.StreakYen[T.Streak]
		if Yen and not T.StreakPaid[tostring(T.Streak)] then
			T.StreakPaid[tostring(T.Streak)] = true
			YenReward = Yen
			Data.UpdateState(P, { type = `UpdateYen`; amount = Yen })
		end
	end
	local StreakB = math.min(Config.StreakCap, Config.StreakPer * (if T.Day == Day then T.Streak else 0))
	local SoreM = Config.SoreMult(Sore)
	local Raw = Res.Points * (if Fresh then Config.FreshMult else 1) * (1 + StreakB) * SoreM
	local Room = math.max(0, Config.DailyCap - (T.DayXp[A.Area] or 0))
	local Xp = math.min(Room, math.floor(Raw + 0.5))
	local Capped = Xp < math.floor(Raw + 0.5)
	if Fresh then T.Fresh[A.Area] = Day end
	T.DayXp[A.Area] = (T.DayXp[A.Area] or 0) + Xp
	-- soreness: this set adds to it
	S.Sore = math.min(Config.Sore.Max, Sore + (if Res.Reps > 0 then (if A.Plan.Burnout then Config.Sore.PerBurnout else Config.Sore.PerSet) else 0))
	S.SoreAt = NowT
	-- levels
	local OldLevel, OldStep = S.Level, Config.StepFor(S.Level)
	S.Xp += Xp
	while S.Level < Config.MaxLevel and S.Xp >= Config.ToNext(S.Level) do
		S.Xp -= Config.ToNext(S.Level)
		S.Level += 1
	end
	if S.Level >= Config.MaxLevel then S.Xp = 0 end
	local NewStep = Config.StepFor(S.Level)
	local StepUp = nil
	if NewStep > OldStep then
		if S.Path == `Average` then S.Path = `Conditioned` end
		local Ok, Name, Changed = Appearance.SetArea(P, A.Area, S.Path, NewStep)
		if Ok and Changed then StepUp = { Area = A.Area; Step = NewStep; Body = Name } end
	end
	-- personal best per station
	local Score = math.floor(Res.Points * 10 + 0.5)
	local B = T.Best[A.Station] or { Score = 0; Combo = 0 }
	local NewBest = Counts and (Score > B.Score or Res.BestCombo > B.Combo)
	if Counts then
		T.Best[A.Station] = { Score = math.max(B.Score, Score); Combo = math.max(B.Combo, Res.BestCombo) }
	end
	-- the Athletes notice gym regulars
	if Counts then
		if T.Athletes.Day ~= Day then T.Athletes = { Day = Day; N = 0 } end
		if T.Athletes.N < Config.Athletes.DailyMax then
			T.Athletes.N += Config.Athletes.PerSet
			local Cliques = try({ `Services`, `Social`, `Cliques` })
			if Cliques then pcall(Cliques.Add, P, `Athletes`, Config.Athletes.PerSet, `Training`) end
		end
	end
	T.LastTrained = NowT
	Local.Save(P, T)
	if S.Level ~= OldLevel then
		local Prog = try({ `Services`, `Player`, `Progression` })
		if Prog then pcall(Prog.Apply, P) end
		if Seats[P] then pcall(Local.Loads, P) end    -- a heavier load at the next tier
	end
	if StepUp then
		local Fx = try({ `Services`, `Features`, `Fx` })
		local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if Fx and Root then pcall(Fx.FireNear, Root.Position, 80, `TrainStep`, { UserId = P.UserId; Area = A.Area; Body = StepUp.Body; Step = StepUp.Step; Test = A.Test }) end
	end
	LastEnd[P] = os.clock()
	return {
		Ok = true; Xp = Xp; Area = A.Area; Station = A.Station; OldLevel = OldLevel; Level = S.Level;
		Counts = { Perfect = Res.Perfect; Great = Res.Great; Good = Res.Good; Miss = Res.Miss; Feint = Res.Feint; Stray = Res.Stray };
		Reps = Res.Reps; BestCombo = Res.BestCombo; Score = Score; Ended = Res.Ended ~= nil; Burnout = A.Plan.Burnout;
		Fresh = Fresh; StreakBonus = StreakB; SoreMult = SoreM; Capped = Capped; Base = math.floor(Res.Points + 0.5);
		Streak = T.Streak; StreakUp = StreakUp; Yen = YenReward; NewBest = NewBest; Best = T.Best[A.Station]; StepUp = StepUp;
		State = Shared.State(P);
	}
end

-- (Studio test bridge) grant area XP through the normal award path
function Shared.TestGrant(P: Player, Area: string, Xp: number)
	if not RunService:IsStudio() then return false end
	local T = Shared.Get(P)
	if not T or not T[Area] then return false end
	local Res = { Points = Xp; Reps = 99; BestCombo = 0; Perfect = 0; Great = 0; Good = 0; Miss = 0; Feint = 0; Stray = 0 }
	local Station = (Seats[P] and Seats[P].Id) or `PushUp`
	return Local.Award(P, { Area = Area; Station = Station; Plan = { Burnout = false }; Level = T[Area].Level; Test = true }, Res)
end

---| setup |---

function Local.Hook(Station: Instance)
	if not Station:IsA(`Model`) then return end
	local Prompt = Station:FindFirstChildWhichIsA(`ProximityPrompt`, true)
	if not Prompt then return end
	Prompt.Triggered:Connect(function(P: Player)
		if Local.Limited(P, `Prompt`, 0.5) then return end
		Local.Sit(P, Station)
	end)
end

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHTraining`
	local function rf(N: string) local R = Instance.new(`RemoteFunction`) R.Name = N R.Parent = F return R end
	local function re(N: string) local R = Instance.new(`RemoteEvent`) R.Name = N R.Parent = F return R end
	local Get, Begin, Submit = rf(`Get`), rf(`Begin`), rf(`Submit`)
	local Leave, Tut, Settle = re(`Leave`), re(`Tutorial`), re(`Settle`)
	EventRE = re(`Event`)
	Folder = F
	Get.OnServerInvoke = function(P) if Local.Limited(P, `Get`, 0.3) then return nil end return Shared.State(P) end
	Begin.OnServerInvoke = function(P) if Local.Limited(P, `Begin`, 0.3) then return { Ok = false; Message = `One moment.` } end return Shared.Begin(P) end
	Submit.OnServerInvoke = function(P, Presses) if Local.Limited(P, `Submit`, 0.5) then return { Ok = false; Message = `One moment.` } end return Shared.Submit(P, Presses) end
	Leave.OnServerEvent:Connect(function(P) Local.Stand(P, `Left`) end)
	Tut.OnServerEvent:Connect(function(P)
		if Local.Limited(P, `Tut`, 2) then return end
		local T = Shared.Get(P)
		if T and not T.Tut then T.Tut = true Local.Save(P, T) end
	end)
	-- the client measured where its pose's lowest limb sits; lower or raise the anchored root (cosmetic, clamped)
	Settle.OnServerEvent:Connect(function(P, Dy)
		if Local.Limited(P, `Settle`, 0.4) then return end
		local S = Seats[P]
		if not S or typeof(Dy) ~= `number` or Dy ~= Dy then return end
		local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not (Root and Root.Anchored) then return end
		S.Y = math.clamp(S.Y + Dy, -4, 1.5)
		Root.CFrame = S.Spot * CFrame.new(0, S.Y, 0)
	end)
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage
	for _, St in CollectionService:GetTagged(`NHTrainStation`) do Local.Hook(St) end
	CollectionService:GetInstanceAddedSignal(`NHTrainStation`):Connect(Local.Hook)
	Data.ProfileLoaded:Connect(function(P) task.defer(Local.Seed, P) end)
	for _, P in Players:GetPlayers() do task.spawn(Local.Seed, P) end
	-- leaving the station: death, respawn, downed, leaving the game
	local function watch(P: Player)
		P.CharacterAdded:Connect(function(Ch)
			if Seats[P] then Local.Stand(P, `Respawn`) end
			local Hum = Ch:WaitForChild(`Humanoid`, 10) :: Humanoid?
			if Hum then
				Hum.Died:Connect(function() if Seats[P] then Local.Stand(P, `Died`) end end)
				Hum:GetAttributeChangedSignal(`Downed`):Connect(function() if Hum:GetAttribute(`Downed`) and Seats[P] then Local.Stand(P, `Downed`) end end)
			end
			Ch:GetAttributeChangedSignal(`Downed`):Connect(function() if Ch:GetAttribute(`Downed`) and Seats[P] then Local.Stand(P, `Downed`) end end)
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, P in Players:GetPlayers() do watch(P) end
	Players.PlayerRemoving:Connect(function(P)
		local S = Seats[P]
		if S and Occupant[S.Station] == P then
			Occupant[S.Station] = nil
			local Prompt = S.Station:FindFirstChildWhichIsA(`ProximityPrompt`, true)
			if Prompt then Prompt.Enabled = true end
		end
		Seats[P], Active[P], LastBegin[P], LastEnd[P] = nil, nil, nil, nil
		for _, T in LastCall do T[P] = nil end
	end)
end

return Shared
