--[[ (2.29) Scenes (server). Services.World.Scenes: the scene director (docs/expansion/13-Living-School.md §4.2).
	Every TickSeconds, for a scene that fits the time, find its spot; if a player is within SeeRange, the region has had no
	scene for RegionCooldown, no cut is playing and it isn't class time in a classroom, roll TryChance and run it:
	borrow the cast (Schedules.Borrow), play the steps, wait on the prompt, emit the outcome as a Scene incident
	(Incidents: rumours, relationships), give the cast back (Schedules.Release).
	API: Run(Id, Pos?), Tick(), RunForTests(Id), LastForTests(), PressForTests(P) ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Config = require(ReplicatedStorage.Config.Scenes)
local Interaction = require(ReplicatedStorage.Config.Interaction)

local Shared = {}
local Local = {}
local LastByRegion = {} :: { [string]: number }
local Running = false
local Last = nil
local PressNow: Player? = nil -- tests: PressForTests presses the running scene's prompt

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

function Local.Spot(Kind: string): (Vector3?, BasePart?)
	if Kind == `Hall` then
		return svc(`Features.Schedules`).HallSpotFor(), nil
	elseif Kind == `Lockers` then
		local Props = workspace.School.Quests:FindFirstChild(`HallwayProps`)
		local L = Props and Props:FindFirstChild(`Locker`)
		if L then return L:GetPivot().Position + L:GetPivot().LookVector * 0.5, nil end
	elseif Kind == `Notice` then
		local B = workspace.School.NHProps:FindFirstChild(`NoticeBoard_143.5`)
		if B then return B:GetPivot().Position, B.PrimaryPart or B:FindFirstChildWhichIsA(`BasePart`) end
	elseif Kind == `RecordsDoor` then
		local E = workspace:FindFirstChild(`Area_RecordsExit`, true)
		if E then return E.Position, E end
	elseif Kind:sub(1, 7) == `Region:` then
		local B = workspace.Regions:FindFirstChild(Kind:sub(8))
		if B then return Vector3.new(B.Position.X, 4, B.Position.Z), B end
	end
	return nil, nil
end

function Local.Floor(P: Vector3): Vector3
	local Hit = workspace:Raycast(P + Vector3.new(0, 6, 0), Vector3.new(0, -20, 0))
	return if Hit then Hit.Position else P
end

function Local.PlayerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and (Root.Position - P).Magnitude <= R then return true end
	end
	return false
end

function Local.Fits(Def, Seg): boolean
	if Def.Night then return require(ServerScriptService.Services.School.SchoolClock).IsNight() end
	return Def.When ~= nil and Seg ~= nil and table.find(Def.When, Seg.Kind) ~= nil
end

function Local.Say(S, Text: string)
	if not S.Model then return end
	S.SaidAt = os.clock()
	S.Model:SetAttribute(`NHSay`, Text)
	S.Model:SetAttribute(`NHSayFor`, math.clamp(1.8 + #Text * 0.06, 2.4, 6))
	S.Model:SetAttribute(`NHSayAt`, workspace:GetServerTimeNow())
	task.wait(math.clamp(1.4 + #Text * 0.05, 1.8, 4))
end

function Local.Fill(Text: string, Cast): string
	return (Text:gsub("{A}", Cast[1] and Cast[1].First or `you`):gsub("{B}", Cast[2] and Cast[2].First or `you`)) -- plain patterns: {..} in backticks interpolates
end

function Local.Figure(Pos: Vector3, Dist: number, Seconds: number)
	local T = ReplicatedStorage:FindFirstChild(`NHCineCast`) and ReplicatedStorage.NHCineCast:FindFirstChild(`Strikethrough`)
	if not T then return end
	local F = T:Clone()
	local Away = (workspace.Regions:FindFirstChild(`MainHall`) and workspace.Regions.MainHall.CFrame.RightVector) or Vector3.xAxis
	F:PivotTo(CFrame.lookAt(Local.Floor(Pos + Away * Dist) + Vector3.new(0, 3, 0), Pos))
	for _, D in F:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true D.CanCollide = false D.CanQuery = false end end
	F.Parent = workspace
	task.delay(Seconds, function() F:Destroy() end)
end

function Local.Prompt(S, Spot: BasePart?, Text: string, Seconds: number): Player?
	local Holder = (S and S.Root) or Spot
	if not Holder then task.wait(Seconds) return nil end
	local P = Instance.new(`ProximityPrompt`)
	P.ActionText = Text P.ObjectText = `` P.KeyboardKeyCode = Interaction.PromptKey P.GamepadKeyCode = Interaction.GamepadKey
	P.HoldDuration = 0 P.MaxActivationDistance = 12 P.RequiresLineOfSight = false
	P.Parent = Holder
	local Who = nil
	local C = P.Triggered:Connect(function(Pl) Who = Pl end)
	local T0 = os.clock()
	while not Who and os.clock() - T0 < Seconds do
		task.wait(0.2)
		if PressNow then Who, PressNow = PressNow, nil end
	end
	C:Disconnect() P:Destroy()
	return Who
end

function Shared.Run(Id: string, Pos: Vector3?): (boolean, string?)
	local Def = Config[Id]
	if not (typeof(Def) == `table` and Def.Steps) then return false, `NoScene` end
	if Running then return false, `Busy` end
	local Spot, SpotPart = Local.Spot(Def.Spot)
	Spot = Pos or Spot
	if not Spot then return false, `NoSpot` end
	local Sched, Roster = svc(`Features.Schedules`), svc(`Social.Roster`)
	local Cast
	if Def.Cast.Rival then
		-- the first student, then one from a clique that is their rival (Config.Cliques RivalPairs)
		local Pairs = require(ReplicatedStorage.Config.Cliques).RivalPairs
		local function rivals(X, Y) for _, P in Pairs do if (P[1] == X and P[2] == Y) or (P[2] == X and P[1] == Y) then return true end end return false end
		local Has = {}
		for _, S in Sched.Students() do
			if S.Model and S.Root and not S.InScene and (S.Root.Position - Spot).Magnitude <= 40 then Has[S.Clique or ``] = true end
		end
		local First = Sched.Borrow(Spot, 1, function(S)
			for C in Has do if rivals(S.Clique, C) then return true end end
			return false
		end)
		if not First then return false, `NoRivals` end
		local Second = Sched.Borrow(Spot, 1, function(S) return rivals(First[1].Clique, S.Clique) end)
		if not Second then Sched.Release(First[1]) return false, `NoRivals` end
		Cast = { First[1], Second[1] }
	else
		Cast = Sched.Borrow(Spot, Def.Cast.Count)
	end
	if not Cast then return false, `NoCast` end
	Running = true
	local Region = Def.Region or svc(`World.Incidents`).RegionAt(Spot) or `school` -- the scene knows its own place
	LastByRegion[Region] = os.clock()
	local Pressed: Player? = nil
	local Ok, Err = pcall(function()
		for _, St in Def.Steps do
			local Op = St[1]
			if Op == `go` then
				local S = Cast[St[2]]
				local Goal = Local.Floor(Spot + St[3])
				if S and S.Agent then require(ServerScriptService.Services.AI.StudentBrain).GoTo(S, Goal, function() return S.InScene == true end) end
			elseif Op == `face` then
				local S = Cast[St[2]]
				local At = if St[3] == `spot` then Spot else (Cast[St[3]] and Cast[St[3]].Root and Cast[St[3]].Root.Position)
				if S and S.Agent and At then S.Agent:Face(At) end
			elseif Op == `say` then
				Local.Say(Cast[St[2]], Local.Fill(St[3], Cast))
			elseif Op == `wait` then
				task.wait(St[2])
			elseif Op == `figure` then
				Local.Figure(Spot, St[2], St[3])
			elseif Op == `fx` then
				local S = Cast[St[2]]
				if S and S.Model then S.Model:SetAttribute(`NHMood`, `Startled`) end
			elseif Op == `prompt` then
				Pressed = Local.Prompt(Cast[St[2]], SpotPart, St[3], St[4])
			end
		end
		local Out = if Pressed then Def.Pressed else Def.Missed
		for _, L in Out.Lines or {} do Local.Say(Cast[L[1]], Local.Fill(L[2], Cast)) end
		if Pressed and Out.Note then
			pcall(function() require(ServerScriptService.Services.Features.Notifications).Notify(Pressed, { Title = `The notice board`; Text = Out.Note; Kind = `Info`; Duration = 6 }) end)
		end
		local Who = {}
		if Cast[1] then table.insert(Who, { Id = Cast[1].RosterId; Role = `Doer` }) end
		if Cast[2] then table.insert(Who, { Id = Cast[2].RosterId; Role = `Target` }) end
		if Pressed and Out.Helper then
			table.insert(Who, { Id = Pressed; Role = `Helper` })
			if not Cast[2] then table.insert(Who, { Id = Cast[1].RosterId; Role = `Target` }) end
		end
		local Witnesses = {}
		for _, S in Cast do table.insert(Witnesses, S.RosterId) end
		for _, Id2 in Roster.Near(Spot, 40) do if not table.find(Witnesses, Id2) then table.insert(Witnesses, Id2) end end
		svc(`World.Incidents`).Emit({ Kind = `Scene`; Scene = Id; Where = Spot; Region = Region; Who = Who; Witnesses = Witnesses;
			Severity = Out.Size or 1; Size = Out.Size or 1; Extra = Out.Extra; Pressed = Pressed ~= nil })
		Last = { Id = Id; Region = Region; Cast = #Cast; Pressed = Pressed ~= nil }
	end)
	for _, S in Cast do Sched.Release(S) end
	Running = false
	if not Ok then warn(`[Scenes] {Id}: {Err}`) return false, `Error` end
	return true, nil
end

local HoldUntil = 0 -- (tests) RunForTests holds the director off so it doesn't take the cast first
function Shared.Tick()
	if Running or os.clock() < HoldUntil then return end
	if workspace:GetAttribute(`NHCinePlaying`) then return end
	local State = require(ServerScriptService.Services.School.SchoolClock).GetState()
	local Seg = State and State.Segment
	for Id, Def in Config do
		if typeof(Def) ~= `table` or not Def.Steps or not Local.Fits(Def, Seg) then continue end
		local Spot = Local.Spot(Def.Spot)
		if not (Spot and Local.PlayerNear(Spot, Config.SeeRange)) then continue end
		local Region = Def.Region or svc(`World.Incidents`).RegionAt(Spot) or `school`
		if os.clock() - (LastByRegion[Region] or -1e9) < Config.RegionCooldown then continue end
		if Seg and Seg.Kind == `Class` and Region:match(`^R10%d`) then continue end
		if math.random() < Config.TryChance then task.spawn(Shared.Run, Id) return end
	end
end

function Shared.RunForTests(Id: string)
	HoldUntil = os.clock() + 300
	LastByRegion = {}
	return Shared.Run(Id)
end
function Shared.LastForTests() return Last end
function Shared.PressForTests(P: Player) PressNow = P end

function Shared.OnStart()
	task.spawn(function()
		while true do
			task.wait(Config.TickSeconds)
			local Ok, Err = pcall(Shared.Tick)
			if not Ok then warn(`[Scenes] {Err}`) end
		end
	end)
end

return Shared
