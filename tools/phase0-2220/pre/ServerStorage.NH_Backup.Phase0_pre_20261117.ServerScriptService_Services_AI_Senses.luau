--[[
	Senses (server). Services.AI.Senses  (NH core add-on for the Map place, 2026-11-10)

	What a school NPC notices. Each perceiver keeps a memory of every player it has seen or heard:
	  Sight    a view cone (wide peripheral, narrow focus) out to ViewRange, shorter at night and against sneaking
	           students (the Progression stat NH_Stealth). A real line of sight from the NPC's eyes to the head or
	           chest (walls, closed doors and props block it; glass and leaves you can see through don't). Awareness
	           of a player builds up over time (faster in the focus cone, close up, or when they move) and fades
	           when they're out of sight, so a glimpse at the edge of the eye isn't instant recognition.
	  Hearing  sounds anyone can raise (Senses.Emit): fights (every hit, Features.Downed.OnDamage), someone downed
	           or finished, doors opening, a student sprinting or landing nearby. Loudness falls off with distance and
	           through walls (muffled by a third), so a fight round the corner is heard but not seen.
	  Reading  for each player it knows about: are they fighting (CombatTagUntil), transformed, downed, walking
	           toward me, right up close, standing facing me (staring), following me?
	Ticks are budgeted: about 5 per second near players, 1 per second when nobody is within 120 studs.

	API
	  Senses.Perceiver(Model, Profile?) -> p     Profile: ViewRange, Fov, Focus, Hearing, Bravery
	  p:Tick() -> snapshot                        (the director calls it; also cached as p.Last)
	  snapshot = { Focus = rec?, Threat = { Pos, Kind, Level, From }?, Approaching = rec?, Crowding = rec?,
	               Staring = rec?, Following = rec?, Heard = { Kind, Pos, At, Loud }? }
	  rec = { Player, Root, Aware (0..1), Pos, Seen (time), Dist, Facing, Closing, Fighting, Monster, Downed }
	  Senses.Emit(Kind, Pos, Loudness, Source?)   Kind: Fight, Scream, Door, Footsteps, Shout
]]

local CollectionService = game:GetService(`CollectionService`)
local Lighting = game:GetService(`Lighting`)
local Players = game:GetService(`Players`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Senses = {}
local Local = {}

local Perceivers = {} :: { [any]: boolean }
local Events = {} :: { { Kind: string, Pos: Vector3, Loud: number, At: number, Source: Instance? } }
local EVENT_LIFE = 8

---| sounds |---

function Senses.Emit(Kind: string, Pos: Vector3, Loudness: number, Source: Instance?)
	table.insert(Events, { Kind = Kind; Pos = Pos; Loud = Loudness; At = os.clock(); Source = Source })
	if #Events > 64 then table.remove(Events, 1) end
end

---| sight |---

local SightP = RaycastParams.new()
SightP.FilterType = Enum.RaycastFilterType.Exclude
local SightRefresh = 0
local function sightParams(): RaycastParams
	if os.clock() - SightRefresh > 2 then
		SightRefresh = os.clock()
		local Ex = {}
		for _, N in { `NHStudents`, `NHSchedule`, `NHAmbient`, `NHFx`, `NHNavDebug`, `School NPC Spots` } do
			local F = workspace:FindFirstChild(N)
			if F then table.insert(Ex, F) end
		end
		SightP.FilterDescendantsInstances = Ex
	end
	return SightP
end

-- true when nothing opaque stands between two points (see-through parts let the look past: glass, leaves)
local function canSee(From: Vector3, To: Vector3, Target: Model): boolean
	local Dir = To - From
	local P = sightParams()
	local Start = From
	for _ = 1, 4 do
		local Hit = workspace:Raycast(Start, Dir, P)
		if not Hit then return true end
		if Hit.Instance:IsDescendantOf(Target) then return true end
		local I = Hit.Instance
		local SeeThrough = I.Transparency > 0.45 or (I:IsA(`BasePart`) and (I.Material == Enum.Material.Glass or I.Material == Enum.Material.ForceField))
		if not SeeThrough then return false end
		Start = Hit.Position + Dir.Unit * 0.05
		Dir = To - Start
		if Dir.Magnitude < 0.1 then return true end
	end
	return false
end

local function isNight(): boolean
	local T = Lighting.ClockTime
	return T < 6 or T >= 19.5
end

---| the perceiver |---

local PMT = {}
PMT.__index = PMT

function Senses.Perceiver(Model: Model, Profile: { [string]: any }?)
	local Pr = Profile or {}
	local Self = setmetatable({
		Model = Model;
		Head = Model:FindFirstChild(`Head`);
		Root = Model:FindFirstChild(`HumanoidRootPart`);
		ViewRange = Pr.ViewRange or 70;
		Fov = math.rad((Pr.Fov or 150) / 2);
		Focus = math.rad((Pr.Focus or 50) / 2);
		Hearing = Pr.Hearing or 1;
		Bravery = Pr.Bravery or 0.4;
		Known = {} :: { [Player]: any };
		NextTick = 0;
		Last = {};
		HeardAt = 0;
	}, PMT)
	Perceivers[Self] = true
	Model.Destroying:Connect(function() Perceivers[Self] = nil end)
	return Self
end

local function serverNow(): number return workspace:GetServerTimeNow() end

-- how the NPC reads a player right now (from what it can see of them)
local function read(Self, Rec, Pl: Player, Char: Model, Root: BasePart)
	local My = Self.Root.Position
	local Rel = Root.Position - My
	local Flat = Vector3.new(Rel.X, 0, Rel.Z)
	Rec.Dist = Flat.Magnitude
	local V = Root.AssemblyLinearVelocity
	local FlatV = Vector3.new(V.X, 0, V.Z)
	-- closing speed: how fast they are coming at me
	Rec.Closing = if Rec.Dist > 0.1 then -FlatV:Dot(Flat / Rec.Dist) else 0
	Rec.Speed = FlatV.Magnitude
	-- are they facing me (their body, the best the server knows of where they look)
	local Look = Root.CFrame.LookVector
	Rec.Facing = if Rec.Dist > 0.1 then Vector3.new(Look.X, 0, Look.Z).Unit:Dot(-Flat / Rec.Dist) else 0
	Rec.Fighting = (tonumber(Pl:GetAttribute(`CombatTagUntil`)) or 0) > serverNow()
	Rec.Monster = Char:GetAttribute(`Transformation`) ~= nil and Char:GetAttribute(`Transformation`) ~= false
	Rec.Downed = Char:GetAttribute(`DownedUntil`) ~= nil
	Rec.Stealth = tonumber(Char:GetAttribute(`NH_Stealth`)) or 1
end

function PMT:Tick()
	local Now = os.clock()
	local Head, Root = self.Head, self.Root
	if not (Head and Root and self.Model.Parent) then return self.Last end
	local Eye = Head.Position + Head.CFrame.LookVector * 0.4
	local Forward = Root.CFrame.LookVector
	local Dt = math.clamp(Now - (self.LastTick or Now), 0, 1)
	self.LastTick = Now
	local Range = self.ViewRange * (if isNight() then 0.5 else 1)

	local Snap = {}
	local Nearest = math.huge
	for _, Pl in Players:GetPlayers() do
		local Char = Pl.Character
		local PR = Char and Char:FindFirstChild(`HumanoidRootPart`)
		local PH = Char and Char:FindFirstChild(`Head`)
		local Rec = self.Known[Pl]
		if PR and PR:IsA(`BasePart`) and PH and PH:IsA(`BasePart`) and Pl:GetAttribute(`InMainMenu`) ~= true then
			if not Rec then
				Rec = { Player = Pl; Aware = 0; Seen = 0; Near = 0; Behind = 0; Stare = 0 }
				self.Known[Pl] = Rec
			end
			Rec.Root = PR
			local Rel = PH.Position - Eye
			local Dist = Rel.Magnitude
			Nearest = math.min(Nearest, Dist)
			local Visible = false
			local Gain = 0
			local Stealth = tonumber(Char:GetAttribute(`NH_Stealth`)) or 1
			local Eff = Range / math.max(0.4, Stealth)
			if Dist < Eff then
				local Ang = math.acos(math.clamp(Forward:Dot(Rel.Unit), -1, 1))
				local InView = Ang <= self.Fov or Dist < 3.5 -- right next to you, you just know
				if InView and (canSee(Eye, PH.Position, Char) or canSee(Eye, PR.Position, Char)) then
					Visible = true
					local Cone = if Ang <= self.Focus then 1 else 0.35
					local Near = 1 - math.clamp(Dist / Eff, 0, 1)
					local Moving = math.clamp(PR.AssemblyLinearVelocity.Magnitude / 16, 0, 1)
					Gain = Cone * (0.35 + Near * 1.6) * (0.8 + Moving * 0.6)
				end
			end
			if Visible then
				Rec.Aware = math.clamp(Rec.Aware + Gain * Dt * 1.8, 0, 1)
				if Rec.Aware > 0.25 then
					Rec.Seen = Now
					Rec.Pos = PR.Position
					read(self, Rec, Pl, Char, PR)
				end
			else
				Rec.Aware = math.max(0, Rec.Aware - Dt * 0.12)
				if Rec.Dist and Rec.Pos then Rec.Dist = (Vector3.new(Rec.Pos.X, 0, Rec.Pos.Z) - Vector3.new(Root.Position.X, 0, Root.Position.Z)).Magnitude end
			end
			Rec.Visible = Visible
			-- loud running: you hear someone sprint up behind you
			local V = PR.AssemblyLinearVelocity
			if V.Magnitude > 19 and (PR.Position - Root.Position).Magnitude < 18 * self.Hearing then
				Rec.Aware = math.max(Rec.Aware, 0.5)
				Rec.Pos, Rec.Seen = PR.Position, Now
				read(self, Rec, Pl, Char, PR)
			end
		elseif Rec then
			Rec.Visible = false
			Rec.Aware = math.max(0, Rec.Aware - Dt * 0.2)
		end
	end
	for Pl, Rec in self.Known do
		if not Pl.Parent or (Rec.Aware <= 0 and Now - Rec.Seen > 60) then self.Known[Pl] = nil end
	end

	-- read the room
	local Focus, FocusScore = nil, 0
	for _, Rec in self.Known do
		if Rec.Aware >= 0.3 and Rec.Dist and Now - Rec.Seen < 4 then
			-- staring: close-ish, facing me, not moving much, for a while
			if Rec.Visible and Rec.Dist < 16 and (Rec.Facing or 0) > 0.85 and (Rec.Speed or 0) < 4 then Rec.Stare += Dt else Rec.Stare = math.max(0, Rec.Stare - Dt * 2) end
			-- following: behind me (outside my view), within 12, keeping up while I walk
			local Behind = Rec.Pos and Root.CFrame:PointToObjectSpace(Rec.Pos).Z > 2
			if Behind and Rec.Dist < 12 and Root.AssemblyLinearVelocity.Magnitude > 2 and (Rec.Speed or 0) > 2 then Rec.Behind += Dt else Rec.Behind = math.max(0, Rec.Behind - Dt) end
			if Rec.Dist < 3.6 and Rec.Visible then Rec.Near += Dt else Rec.Near = 0 end

			local Score = Rec.Aware * (1 - math.clamp(Rec.Dist / 40, 0, 0.9))
			if Rec.Fighting then Score += 0.6 end
			if Rec.Monster then Score += 0.5 end
			if (Rec.Closing or 0) > 4 then Score += 0.3 end
			if Rec.Stare > 1 then Score += 0.4 end
			if Score > FocusScore then Focus, FocusScore = Rec, Score end

			-- coming straight at me: about a second from reaching me (so a sprint is noticed earlier than a stroll)
			if Rec.Dist < 14 and (Rec.Closing or 0) > 5 and Rec.Dist / Rec.Closing < 1.1 then Snap.Approaching = Rec end
			if Rec.Near > 1.2 then Snap.Crowding = Rec end
			if Rec.Stare > 2.5 then Snap.Staring = Rec end
			if Rec.Behind > 8 then Snap.Following = Rec end
			-- something to keep away from: a fight, a monster, a body
			local Kind = if Rec.Fighting then `Fight` elseif Rec.Monster then `Monster` elseif Rec.Downed then `Body` else nil
			if Kind and Rec.Pos then
				local Level = (if Kind == `Fight` then 1 elseif Kind == `Monster` then 0.8 else 0.5) * (1 - math.clamp(Rec.Dist / 60, 0, 1))
				if not Snap.Threat or Level > Snap.Threat.Level then Snap.Threat = { Pos = Rec.Pos; Kind = Kind; Level = Level; From = Rec } end
			end
		end
	end
	Snap.Focus = Focus

	-- hearing
	for I = #Events, 1, -1 do
		local E = Events[I]
		if Now - E.At > EVENT_LIFE then table.remove(Events, I)
		elseif E.At > self.HeardAt then
			local Dist = (E.Pos - Root.Position).Magnitude
			local Loud = E.Loud * self.Hearing
			if Dist < Loud then
				local Muffled = not canSee(Eye, E.Pos + Vector3.new(0, 2, 0), self.Model)
				if not Muffled or Dist < Loud * 0.66 then
					Snap.Heard = Snap.Heard or E
					if E.Kind == `Fight` or E.Kind == `Scream` then
						local Level = (if E.Kind == `Scream` then 0.9 else 0.7) * (1 - Dist / Loud)
						if not Snap.Threat or Level > Snap.Threat.Level then Snap.Threat = { Pos = E.Pos; Kind = `Fight`; Level = Level; Heard = true } end
					end
				end
			end
		end
	end
	self.HeardAt = Now

	-- the next tick: faster with players about
	self.NextTick = Now + (if Nearest < 120 then 0.2 else 1)
	self.Last = Snap
	return Snap
end

function PMT:Due(): boolean
	return os.clock() >= self.NextTick
end

---| world sounds |---

local Started = false
function Senses.Init()
	if Started then return end
	Started = true
	task.spawn(function()
		local Ok, Downed = pcall(require, ServerScriptService.Services.Features.Downed)
		if not Ok then return end
		local function at(M: Instance?): Vector3?
			local R = M and M:FindFirstChild(`HumanoidRootPart`)
			return R and R:IsA(`BasePart`) and R.Position or nil
		end
		if Downed.OnDamage then
			Downed.OnDamage:Connect(function(Target, _Damage, Attacker)
				local P = at(Target) or at(Attacker)
				if P then Senses.Emit(`Fight`, P, 55, Attacker) end
			end)
		end
		if Downed.OnDefeated then
			Downed.OnDefeated:Connect(function(Model)
				local P = at(Model)
				if P then Senses.Emit(`Scream`, P, 80, Model) end
			end)
		end
		if Downed.OnExecuted then
			Downed.OnExecuted:Connect(function(_Gripper, Target)
				local P = at(Target)
				if P then Senses.Emit(`Scream`, P, 70, Target) end
			end)
		end
	end)
	-- doors opening and closing
	local function door(D: Instance)
		if not D:IsA(`Model`) then return end
		D:GetAttributeChangedSignal(`Open`):Connect(function()
			Senses.Emit(`Door`, D:GetPivot().Position + Vector3.new(0, 3, 0), 22, D)
		end)
	end
	for _, D in CollectionService:GetTagged(`NHDoor`) do door(D) end
	CollectionService:GetInstanceAddedSignal(`NHDoor`):Connect(door)
end

return Senses
