--[[ (2.29) Incidents (server). Services.World.Incidents: one bus for things that happen in the school
	(docs/expansion/13-Living-School.md §4.1).
	Emit({ Kind, Where?, Region?, Who = { { Id = Player | npc id, Role = "Doer" | "Target" | "Helper" } }?, Witnesses?,
	       Severity?, Truth? = true, ... }) -> the incident (with T, Region and Witnesses filled in)
	On(Kind | "*", fn) -> connection; Emitted (signal); Recent(N); RegionAt(Pos) -> region name?
	Emitters: CliqueFights (Scuffle), Downed.OnDowned (Downed), HallMonitor.Caught (Caught), Discipline.ViolationAdded
	(Violation), Pranks.Marked (Prank), Matches (Match), Beasts (Beast), NHMoonEvent (Moon), World.Scenes (Scene).
	Consumer here: relationships (a player who downs a rostered student: -15 Fought; helps one: +10 Helped;
	pranks with one present as target: -8 Pranked). ]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)

local Shared = {}
local Local = {}
Shared.Emitted = SignalPlus()
local Log = {} -- newest first, at most 50
local WITNESS_RADIUS = 40

local function svc(Path: string)
	local Node = ServerScriptService.Services
	for Seg in Path:gmatch(`[^%.]+`) do Node = Node and Node:FindFirstChild(Seg) end
	if not Node then return nil end
	local Ok, M = pcall(require, Node)
	return if Ok then M else nil
end

function Shared.RegionAt(Pos: Vector3?): string?
	local Folder = workspace:FindFirstChild(`Regions`)
	if not (Pos and Folder) then return nil end
	local Best, BestVol = nil, math.huge -- the smallest box that holds the point (a room inside a hall wins)
	for _, Box in Folder:GetChildren() do
		if Box:IsA(`BasePart`) then
			local L = Box.CFrame:PointToObjectSpace(Pos)
			local H = Box.Size / 2
			if math.abs(L.X) <= H.X and math.abs(L.Z) <= H.Z then
				local Vol = Box.Size.X * Box.Size.Z
				if Vol < BestVol then Best, BestVol = (Box:GetAttribute(`RegionId`) or Box.Name), Vol end
			end
		end
	end
	return Best
end

function Local.PosOf(Id): Vector3?
	if typeof(Id) == `Instance` and Id:IsA(`Player`) then
		local R = Id.Character and Id.Character:FindFirstChild(`HumanoidRootPart`)
		return R and R.Position
	end
	local Roster = svc(`Social.Roster`)
	local W = Roster and typeof(Id) == `string` and Roster.WhereNow(Id)
	return W and W.At
end

function Shared.Emit(I)
	I.T = os.time()
	if I.Truth == nil then I.Truth = true end
	I.Who = I.Who or {}
	if not I.Where then
		for _, W in I.Who do I.Where = Local.PosOf(W.Id) if I.Where then break end end
	end
	I.Region = I.Region or Shared.RegionAt(I.Where)
	if not I.Witnesses then
		local Roster = svc(`Social.Roster`)
		I.Witnesses = if Roster and I.Where then Roster.Near(I.Where, WITNESS_RADIUS) else {}
	end
	table.insert(Log, 1, I)
	while #Log > 50 do table.remove(Log) end
	Shared.Emitted:Fire(I)
	return I
end

function Shared.On(Kind: string, Fn)
	return Shared.Emitted:Connect(function(I)
		if Kind == `*` or I.Kind == Kind then
			local Ok, Err = pcall(Fn, I)
			if not Ok then warn(`[Incidents] {Kind}: {Err}`) end
		end
	end)
end

function Shared.Recent(N: number?)
	local Out = {}
	for K = 1, math.min(N or 10, #Log) do Out[K] = Log[K] end
	return Out
end

-- the relationship consumer (2.27 flags): only a real player's deed against or for a rostered student counts
function Local.Relationships(I)
	local Rep, Roster = svc(`Social.Reputation`), svc(`Social.Roster`)
	if not (Rep and Roster) then return end
	local Doer, Target, Helper
	for _, W in I.Who do
		if W.Role == `Doer` then Doer = W.Id elseif W.Role == `Target` then Target = W.Id elseif W.Role == `Helper` then Helper = W.Id end
	end
	local function isPlayer(X) return typeof(X) == `Instance` and X:IsA(`Player`) end
	if (I.Kind == `Downed` or I.Kind == `Scene` and I.Hostile) and isPlayer(Doer) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Doer, Target, -15, nil, `Fought`)
	end
	if isPlayer(Helper) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Helper, Target, 10, nil, `Helped`)
	end
	if I.Kind == `Scene` and I.Pranked and isPlayer(Doer) and Roster.IsRostered(Target) then
		Rep.ChangeRelationship(Doer, Target, -8, nil, `Pranked`)
	end
end

function Shared.OnStart()
	Shared.On(`*`, Local.Relationships)
	-- the systems that already fire signals
	task.defer(function()
		local Downed = svc(`Features.Downed`)
		if Downed then Downed.OnDowned:Connect(function(Target: Model, Attacker: Model?)
			local TP, AP = Players:GetPlayerFromCharacter(Target), Attacker and Players:GetPlayerFromCharacter(Attacker)
			local TId = TP or Target:GetAttribute(`NHStudentId`) or Target:GetAttribute(`NpcId`) or Target.Name
			local AId = AP or (Attacker and (Attacker:GetAttribute(`NHStudentId`) or Attacker:GetAttribute(`NpcId`) or Attacker.Name))
			local R = Target:FindFirstChild(`HumanoidRootPart`)
			Shared.Emit({ Kind = `Downed`; Where = R and R.Position; Severity = 2;
				Who = { { Id = AId; Role = `Doer` }, { Id = TId; Role = `Target` } } })
		end) end
		local HM = svc(`School.HallMonitor`)
		if HM then HM.Caught:Connect(function(Player: Player, Reason: string, LetOff: boolean?)
			Shared.Emit({ Kind = `Caught`; Reason = Reason; LetOff = LetOff == true; Severity = 1; Who = { { Id = Player; Role = `Target` } } })
		end) end
		local Disc = svc(`School.Discipline`)
		if Disc then Disc.ViolationAdded:Connect(function(Player: Player, Record)
			Shared.Emit({ Kind = `Violation`; Type = Record.Type; Witness = Record.Witness; Severity = 1; Who = { { Id = Player; Role = `Target` } } })
		end) end
		local Pranks = svc(`Social.Pranks`)
		if Pranks then Pranks.Marked:Connect(function(Player: Player, WallId: string, Info)
			Shared.Emit({ Kind = `Prank`; Wall = WallId; Seen = Info and (Info.Recognized or Info.Spotted); Severity = 1; Who = { { Id = Player; Role = `Doer` } } })
		end) end
	end)
	workspace:GetAttributeChangedSignal(`NHMoonEvent`):Connect(function()
		local E = workspace:GetAttribute(`NHMoonEvent`)
		if E then Shared.Emit({ Kind = `Moon`; Event = E; Severity = 1 }) end
	end)
end

function Shared.ClearForTests() table.clear(Log) end

return Shared
