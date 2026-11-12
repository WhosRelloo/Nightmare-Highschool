--[[
	NPC daily schedules (server). Services.Features.Schedules
	Fourteen background students live by the school timetable (Config.SchoolSchedule segments, Config.Classes rooms):
	  Night / Morning   off campus (not spawned)
	  Before School     walk in from the gate and mill about the hallway
	  Class             the first six take seats in that period's room (chairs stay free for players); the rest
	                    are "in the east wing" (they walk out and come back at the next break)
	  Passing           the hallway: walk, chat in pairs, lean on the wall, sit on a hall bench (1.18.4)
	  Break             with their clique at its hangout (Config.Cliques, NHCliqueSpot markers; 1.20)
	  Lunch             the concession stand (NHLunchSpot markers): queue up, eat
	  After School      athletes to their club (gym, field, pitch), everyone else to their clique's hangout; some head home at 14:00+
	  Evening           everyone drifts home by 19:00
	Same students every day (looks are rolled once per server). They never collide with players (collision group
	NHWalkers), walk and idle like an unarmed player (the Default movement pack), and the owner's sitting / leaning /
	eating clips. Anything that needs a player-free school can call Schedules.Pause(true).
	(1.86.2) The Map place's NPC brain (Services.AI.StudentBrain): they walk with Services.AI.Nav (doors, steps,
	smoothing, avoidance, re-planning), notice the world with Services.AI.Senses and react (back away from danger,
	watch fights, make way, step back, glance, greet), talk in voices (Controllers.World.NpcLook), fidget, and lean
	only against a real wall. This module still decides where they go.
	Folder workspace.NHSchedule. Each model: attribute Role = "Ambient", NHActivity = what they're doing.
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local PathfindingService = game:GetService(`PathfindingService`)
local PhysicsService = game:GetService(`PhysicsService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Classes = require(ReplicatedStorage.Config.Classes)
local BenchTaken
local Seats = require(ServerScriptService.Services.Features.Seats) -- where hips go on the school's seat props
local Brain = require(ServerScriptService.Services.AI.StudentBrain) -- (1.86.2) walking, senses, reactions, voices
local CliqueConfig = require(ReplicatedStorage.Config.Cliques) -- each student's clique (1.20)
local CollectionService2 = game:GetService(`CollectionService`)
local SpotTaken = {} :: { [BasePart]: any }
-- (audit) declared up here: Local.Unseat uses it, and below its old spot it was a nil global inside Unseat
local ChairBy = {} :: { [Model]: any }
local SpotFailed = {} :: { [BasePart]: number } -- spots nobody could walk to lately (skipped for 2 minutes)

local COUNT = 14
local IN_CLASS = 6
local WALK_SPEED = 6 -- a stroll: the walk clip plays at about 1.1x, feet on the ground (WALK_PACE)
local WALK_PACE = 5.3 -- studs/s the Default walk clip covers at 1x (measured, 2026-11-03)
local RUN_PACE = 16 -- (1.86.2) the run clip, for backing away from danger
local ANIM = {
	Walk = 180426354; Idle = 180435571; Sprint = 0; -- fallbacks only: see below
	Sitting = 103637860968444; Lean = 129824051499811; Eat = 126575676069500; SitChill = 124142826216078;
}
-- they walk and idle like an unarmed player (owner, 2026-11-03): the player's own Default movement pack
do
	local Pack = ReplicatedStorage:FindFirstChild(`Assets`)
	Pack = Pack and Pack:FindFirstChild(`Animations`)
	Pack = Pack and Pack:FindFirstChild(`Default`)
	Pack = Pack and Pack:FindFirstChild(`Movement`)
	for _, N in { `Walk`, `Idle`, `Sprint` } do
		local A = Pack and Pack:FindFirstChild(N)
		local Id = A and A:IsA(`Animation`) and tonumber(A.AnimationId:match(`%d+`))
		if Id then ANIM[N] = Id end
	end
end
local CLUBS = { `Gymnasium`, `Field`, `Pitch`, `Archive` }

local Shared = {}
local Local = {}
local Folder: Folder? = nil
local Students = {} -- [i] = { Index, Look, Club, Model?, Hum?, Job (token), Tracks }
local Paused = false
local Segment = nil
local Plan = { Kind = `Off` } -- (1.86.2) what the brain's lines talk about: { Kind, SegName, DayName }

---| places |---

function Local.Box(Inst: Instance?): (CFrame?, Vector3?)
	if not Inst then return nil, nil end
	local Ok, CF, Size = pcall(function()
		if Inst:IsA(`BasePart`) then return Inst.CFrame, Inst.Size end
		return Inst:GetBoundingBox()
	end)
	if Ok then return CF, Size end
	return nil, nil
end

function Local.Floor(At: Vector3): Vector3?
	local RP = RaycastParams.new()
	RP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = {}
	for _, N in { `Live`, `NHFx`, `NHAmbient`, `NHSchedule` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	RP.FilterDescendantsInstances = Ex
	RP.RespectCanCollide = true
	local Hit = workspace:Raycast(At + Vector3.new(0, 8, 0), Vector3.new(0, -40, 0), RP)
	return if Hit and Hit.Normal.Y > 0.6 then Hit.Position else nil
end

function Local.Gate(): Vector3
	local S = workspace:FindFirstChild(`Map`) and workspace.Map:FindFirstChild(`SpawnLocation`)
	local P = if S then S.Position + Vector3.new(8, 0, 8) else Vector3.new(0, 1, 0)
	return Local.Floor(P) or P
end

function Local.HallSpot(): Vector3?
	local CF, Size = Local.Box(workspace.School and workspace.School:FindFirstChild(`Hallway`))
	if not CF then return nil end
	for _ = 1, 6 do
		local P = (CF * CFrame.new((math.random() - 0.5) * (Size.X - 16), 0, (math.random() - 0.5) * (Size.Z - 5))).Position
		local F = Local.Floor(P)
		if F then return F end
	end
	return nil
end

-- the room's chairs, in a stable order (nearest the door first)
function Local.Chairs(RoomId: string): { Model }
	local Room = workspace.School:FindFirstChild(RoomId)
	local CF, Size = Local.Box(Room)
	local Props = workspace.School:FindFirstChild(`NHProps`)
	if not (CF and Props) then return {} end
	local Out = {}
	for _, P in Props:GetChildren() do
		if P.Name == `StudentChair` and P:IsA(`Model`) then
			local L = CF:PointToObjectSpace(P:GetPivot().Position)
			if math.abs(L.X) < Size.X / 2 and math.abs(L.Z) < Size.Z / 2 then table.insert(Out, P) end
		end
	end
	local Door = Room:FindFirstChild(`Door`)
	local From = if Door and Door:IsA(`BasePart`) then Door.Position else CF.Position
	table.sort(Out, function(A, B)
		local Da, Db = (A:GetPivot().Position - From).Magnitude, (B:GetPivot().Position - From).Magnitude
		if math.abs(Da - Db) > 0.1 then return Da < Db end
		return A:GetPivot().Position.X < B:GetPivot().Position.X
	end)
	return Out
end

function Local.ClubSpot(Club: string): Vector3?
	local Where = if Club == `Archive` then workspace.School:FindFirstChild(`Archive`)
		else (workspace:FindFirstChild(`Sports`) and workspace.Sports:FindFirstChild(Club))
	local CF, Size = Local.Box(Where)
	if not CF then return nil end
	local Edge = if Club == `Archive` then 0.3 else 0.42
	for _ = 1, 8 do
		local Side = if math.random() < 0.5 then -1 else 1
		local P = (CF * CFrame.new((math.random() - 0.5) * Size.X * 0.7, 0, Side * Size.Z * Edge)).Position
		local F = Local.Floor(P)
		if F then return F end
	end
	return nil
end

---| bodies |---

function Local.Groups()
	pcall(function() PhysicsService:RegisterCollisionGroup(`NHWalkers`) end)
	for _, G in { `Entity`, `NPC`, `NHWalkers`, `SportBall` } do -- (audit) players are Entity, AI NPCs NPC (no `Characters` group exists)
		pcall(function() PhysicsService:CollisionGroupSetCollidable(`NHWalkers`, G, false) end)
	end
end

function Local.Look(): any
	local Appearance = require(ReplicatedStorage.UI.Appearance)
	local Look = Appearance.Sanitize(nil)
	Look.UseAvatar = false
	Look.Uniform = math.random(1, #Appearance.Uniforms)
	Look.Bottoms = math.random(1, math.min(6, #Appearance.BottomsList))
	Look.Skin = math.random(1, #Appearance.Skins)
	Look.HairColor = math.random(1, #Appearance.HairColors)
	Look.Body = math.random(1, 2)
	-- (1.71) clothes by the NPC's gender (UI.Appearance), never the admin kit
	Look.Uniform = Appearance.RandomPiece(Appearance.Uniforms, Look)
	Look.Bottoms = Appearance.RandomPiece(Appearance.BottomsList, Look)
	Look.EyeSet = if Appearance.IsFemale(Look) then 2 else 1
	Look.Eyes = math.random(1, #Appearance.Eyes)
	local Cat = ReplicatedStorage:FindFirstChild(`NHHairCatalog`)
	if Cat then
		local Pool = {}
		for _, H in Cat:GetChildren() do
			if H:GetAttribute(`Group`) == (if Appearance.IsFemale(Look) then `Female` else `Male`) then table.insert(Pool, H:GetAttribute(`AssetId`)) end
		end
		if #Pool > 0 then Look.HairId = Pool[math.random(1, #Pool)] end
	end
	Look.Created = true
	return Look
end

function Local.Track(S, Name: string, Looped: boolean): AnimationTrack?
	S.Tracks = S.Tracks or {}
	if S.Tracks[Name] then return S.Tracks[Name] end
	if (ANIM[Name] or 0) == 0 then return nil end
	local Animator = S.Hum and (S.Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, S.Hum))
	if not Animator then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{ANIM[Name]}`
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	T.Looped = Looped
	T.Priority = if Name == `Walk` or Name == `Idle` or Name == `Sprint` then Enum.AnimationPriority.Movement else Enum.AnimationPriority.Action
	S.Tracks[Name] = T
	return T
end

function Local.Pose(S, Name: string?)
	for K, T in S.Tracks or {} do
		if K ~= `Walk` and K ~= `Idle` and K ~= `Sprint` and K ~= Name and T.IsPlaying then T:Stop(0.3) end
	end
	if Name then
		local T = Local.Track(S, Name, true)
		if T and not T.IsPlaying then T:Play(0.3) end
	end
end

function Local.Spawn(S, At: Vector3)
	local Rig = ServerScriptService.Services.AI.AI:FindFirstChild(`Rig`)
	if not (Rig and Folder) then return end
	local M = Rig:Clone()
	M.Name = `Student`
	M:SetAttribute(`Role`, `Ambient`)
	M:SetAttribute(`NHScheduled`, S.Index)
	if S.Clique then M:SetAttribute(`Clique`, S.Clique) end
	local Animate = M:FindFirstChild(`Animate`)
	if Animate then Animate:Destroy() end
	local Hum = M:FindFirstChildOfClass(`Humanoid`) :: Humanoid
	local Root = M:FindFirstChild(`HumanoidRootPart`) :: BasePart
	Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	Hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	Hum.WalkSpeed = WALK_SPEED
	Hum.BreakJointsOnDeath = false
	Hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	Hum:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false)
	Hum:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = `NHWalkers` D.CanQuery = false D.CanTouch = false end
	end
	local Up = Root.Size.Y / 2 + Hum.HipHeight + (M:FindFirstChild(`Left Leg`) and M[`Left Leg`].Size.Y or 2)
	M:PivotTo(CFrame.new(At + Vector3.new(0, Up, 0)) * Root.CFrame:Inverse() * M:GetPivot())
	S.Up = Up
	M.Parent = Folder
	pcall(function() Root:SetNetworkOwner(nil) end)
	pcall(function()
		local Appearance = require(ReplicatedStorage.UI.Appearance)
		local L = table.clone(S.Look)
		Appearance.ApplyTo(M, L)
	end)
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then D.CollisionGroup = `NHWalkers` D.CanQuery = false D.CanTouch = false end
	end
	S.Model, S.Hum, S.Root, S.Tracks = M, Hum, Root, {}
	local Walk, Idle, Run = Local.Track(S, `Walk`, true), Local.Track(S, `Idle`, true), Local.Track(S, `Sprint`, true)
	if Idle then Idle:Play() end
	Hum.Running:Connect(function(Speed)
		if not (Walk and Idle) then return end
		if Speed > 10 and Run then -- (1.86.2) running from danger
			if Walk.IsPlaying then Walk:Stop(0.15) end
			if not Run.IsPlaying then Run:Play(0.15) end
			Run:AdjustSpeed(Speed / RUN_PACE)
		elseif Speed > 0.5 then
			if Run and Run.IsPlaying then Run:Stop(0.15) end
			if not Walk.IsPlaying then Walk:Play(0.2) end
			Walk:AdjustSpeed(Speed / WALK_PACE) -- matched to how fast they move, so the feet don't slide
		else
			if Walk.IsPlaying then Walk:Stop(0.2) end
			if Run and Run.IsPlaying then Run:Stop(0.2) end
		end
	end)
	Brain.Attach(S) -- (1.86.2) the navigator, the senses, the voice and the reactions
end

function Local.Despawn(S)
	Brain.Detach(S)
	if S.Model then S.Model:Destroy() end
	S.Model, S.Hum, S.Root, S.Tracks, S.Seated = nil, nil, nil, nil, nil
end

---| moving |---

-- a free place on the floor beside a seat: floor level (the lowest surface found around it), nothing in the way
function Local.StandSpot(S, Front: boolean?): Vector3?
	local R = S.Root
	local Look, Right = R.CFrame.LookVector, R.CFrame.RightVector
	local Away = if Front then Look else -Look
	local Tries = { Away * 2.2, Away * 3.2, Right * 2.4, -Right * 2.4, Away * 2.2 + Right * 2.2, Away * 2.2 - Right * 2.2, -Away * 2.6, Away * 4.5 }
	local Hits = {}
	local Low = math.huge
	for I, Off in Tries do
		local F = Local.Floor(R.Position + Off)
		if F then Hits[I] = F Low = math.min(Low, F.Y) end
	end
	local OP = OverlapParams.new()
	OP.FilterType = Enum.RaycastFilterType.Exclude
	local Ex = { S.Model }
	for _, N in { `Live`, `NHFx`, `NHAmbient`, `NHSchedule` } do local Fo = workspace:FindFirstChild(N) if Fo then table.insert(Ex, Fo) end end
	OP.FilterDescendantsInstances = Ex
	OP.RespectCanCollide = true
	for I = 1, #Tries do
		local F = Hits[I]
		if F and F.Y < Low + 0.6 and #workspace:GetPartBoundsInBox(CFrame.new(F + Vector3.new(0, 2.6, 0)), Vector3.new(1.6, 3.6, 1.6), OP) == 0 then
			return F
		end
	end
	for I = 1, #Tries do if Hits[I] and Hits[I].Y < Low + 0.6 then return Hits[I] end end
	return Local.Floor(R.Position)
end

function Local.Unseat(S)
	if not (S.Seated and S.Root) then return end
	local Front = S.StandFront
	if ChairBy[S.Seated] == S then ChairBy[S.Seated] = nil end -- (1.47) the class chair is free again
	S.Seated, S.SeatSide, S.StandFront = nil, nil, nil
	Local.Pose(S, nil)
	-- stand up behind the chair (the desk is in front), or in front of a bench. Rows can be tight (1.20: in R103 the
	-- spot behind a chair is the next row's desk, and students stood up on top of it), so try a few places around
	-- the seat and take the first one at floor level with room to stand.
	local F = Local.StandSpot(S, Front)
	if F then
		local Look = S.Root.CFrame.LookVector
		S.Model:PivotTo(CFrame.lookAt(F + Vector3.new(0, S.Up or 3, 0), F + Vector3.new(Look.X, S.Up or 3, Look.Z)) * S.Root.CFrame:Inverse() * S.Model:GetPivot())
	end
	S.Root.Anchored = false
end

-- walk to a point along a path; returns false if the job changed or it failed
function Local.Flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

-- (1.46.1) a student-wide line at waist height from From to To that no wall or prop crosses
local LineParams = RaycastParams.new()
LineParams.FilterType = Enum.RaycastFilterType.Exclude
LineParams.RespectCanCollide = true
function Local.LineClear(From: Vector3, To: Vector3): boolean
	local Ex = {}
	for _, N in { `Live`, `NHFx`, `NHAmbient`, `NHSchedule`, `NHLostFound` } do local F = workspace:FindFirstChild(N) if F then table.insert(Ex, F) end end
	LineParams.FilterDescendantsInstances = Ex
	local Flat = Vector3.new(To.X - From.X, 0, To.Z - From.Z)
	if Flat.Magnitude < 0.5 then return true end
	local Side = Vector3.new(-Flat.Unit.Z, 0, Flat.Unit.X) * 0.9
	for _, Off in { Vector3.zero, Side, -Side } do
		if workspace:Raycast(From + Off, Flat, LineParams) then return false end
	end
	return true
end

-- (1.86.2) walk with the brain's navigator (Services.AI.Nav: doors, steps, smoothing, avoidance, re-planning). It
-- pauses for a reaction and carries on; it stops when the job changes. Before 1.86.2 this was a single
-- PathfindingService path (backup: ServerStorage.NH_Backup.Schedules_pre1862).
function Local.WalkTo(S, Job, Goal: Vector3): boolean
	if not (S.Hum and S.Root) then return false end
	Local.Unseat(S)
	Local.Pose(S, nil)
	S.Leaning = false
	local Ok = Brain.GoTo(S, Goal, function() return S.Job == Job and not Paused and S.Model ~= nil end)
	return Ok and S.Job == Job and S.Root ~= nil and (S.Root.Position - Goal).Magnitude < 8
end

function Local.Face(S, Toward: Vector3)
	if not S.Root then return end
	local P = S.Root.Position
	S.Root.CFrame = CFrame.lookAt(P, Vector3.new(Toward.X, P.Y, Toward.Z))
end

-- Sit on a seat prop (a chair, or one place on a bench with Side studs sideways). The seat props don't take raycasts,
-- so the surface comes from Services.Features.Seats; once the pose is on, the hips are settled onto it (the pose
-- moves the torso, so the root alone can't place them: before 1.19 the students sank into their chairs).
function Local.Sit(S, Chair: Model, Side: number?, Pose: string?)
	if not (S.Root and Chair.Parent) then return end
	local CF = Chair:GetPivot() * CFrame.new(Side or 0, 0, 0)
	local Top = Seats.Top(Chair, Side)
	local Look = (CF * CFrame.new(0, 0, -5)).Position
	if S.Agent then S.Agent:Stop() end -- (1.86.2)
	S.Leaning = false
	S.Root.Anchored = true
	local Want = CFrame.lookAt(Vector3.new(Top.X, Top.Y + 1.05, Top.Z), Vector3.new(Look.X, Top.Y + 1.05, Look.Z))
	S.Model:PivotTo(Want * S.Root.CFrame:Inverse() * S.Model:GetPivot())
	S.Seated = Chair
	S.SeatSide = Side
	-- benches: stand up in front of them (chairs: behind, the desk is in front)
	S.StandFront = Seats.Kind(Chair) == `HallBench` or Seats.Kind(Chair) == `Sofa`
	Local.Pose(S, Pose or `Sitting`)
	local Model = S.Model
	Seats.SettleWhenPosed(Model, S.Hum, Top, Seats.Back(Chair), function() return S.Seated == Chair and S.Model == Model end,
		if S.StandFront then 0.15 else 0.35, ANIM[Pose or `Sitting`], Chair)
end

---| activities |---

function Local.Arrive(S, Job): boolean
	if S.Model then return true end
	Local.Spawn(S, Local.Gate())
	task.wait(0.2)
	return S.Job == Job
end

function Local.Leave(S, Job)
	if not S.Model then return end
	S.Model:SetAttribute(`NHActivity`, `Going home`)
	Local.WalkTo(S, Job, Local.Gate())
	if S.Job == Job then Local.Despawn(S) end
end

-- a free place on one of the hallway benches (two places each)
BenchTaken = {}
function Local.FreeBench(): (Model?, number?)
	local Props = workspace.School:FindFirstChild(`NHProps`)
	local Free = {}
	for _, P in (Props and Props:GetChildren()) or {} do
		if P:IsA(`Model`) and Seats.Kind(P) == `HallBench` then
			for _, Side in Seats.Places.HallBench do
				-- a place is taken from the moment someone heads for it until they get up (or are gone)
				local Who = BenchTaken[P.Name .. Side]
				if not (Who and Who.Model) then table.insert(Free, { P, Side }) end
			end
		end
	end
	if #Free == 0 then return nil, nil end
	local Pick = Free[math.random(1, #Free)]
	return Pick[1], Pick[2]
end

function Local.Mingle(S, Job)
	if not Local.Arrive(S, Job) then return end
	S.Model:SetAttribute(`NHActivity`, `Hallway`)
	while S.Job == Job and not Paused do
		local Spot = Local.HallSpot()
		if Spot then Local.WalkTo(S, Job, Spot) end
		if S.Job ~= Job then return end
		-- sit on a hall bench, or stand and chat, or lean for a bit
		local Bench, Side = nil, nil
		if math.random() < 0.3 then Bench, Side = Local.FreeBench() end
		if Bench then
			BenchTaken[Bench.Name .. Side] = S
			local Front = (Bench:GetPivot() * CFrame.new(Side, 0, -2.4)).Position
			if Local.WalkTo(S, Job, Local.Floor(Front) or Front) and S.Job == Job then
				Local.Sit(S, Bench, Side, if math.random() < 0.5 then `SitChill` else `Sitting`)
				Brain.Idle(S, math.random(80, 200) / 10, function() return S.Job == Job and not Paused end)
			end
			if BenchTaken[Bench.Name .. Side] == S then BenchTaken[Bench.Name .. Side] = nil end
			if S.Job == Job then Local.Unseat(S) end
		else
			-- (1.86.2, owner 1.78.6) lean only with a real wall behind them (a few steps to one is fine)
			local Valid = function() return S.Job == Job and not Paused end
			if math.random() < 0.4 then Brain.LeanOnWall(S, true, Valid) end
			Brain.Idle(S, math.random(60, 160) / 10, Valid)
			Local.Pose(S, nil)
		end
	end
end

-- (1.47) the chair each student has claimed for class (heading for it or sitting in it), so players and students
-- never share one (Features.PlayerSeats asks ChairTaken; a chair a player sits in is skipped here)
function Shared.ChairTaken(Chair: Model): boolean
	local Who = ChairBy[Chair]
	return Who ~= nil and Who.Model ~= nil and Who.Model.Parent ~= nil
end
function Local.FreeChair(S, Chairs: { Model }, Seat: number): Model?
	for C, Who in ChairBy do if Who == S then ChairBy[C] = nil end end
	local PS = nil
	pcall(function() PS = require(ServerScriptService.Services.Features.PlayerSeats) end)
	for K = 0, #Chairs - 1 do
		local C = Chairs[(Seat - 1 + K) % #Chairs + 1]
		local Who = ChairBy[C]
		local Taken = Who and Who ~= S and Who.Model and Who.Model.Parent
		if not Taken and not (PS and PS.IsOccupied(C)) then
			ChairBy[C] = S
			return C
		end
	end
	return nil
end

function Local.Class(S, Job, RoomId: string, Seat: number)
	if not Local.Arrive(S, Job) then return end
	local Chairs = Local.Chairs(RoomId)
	local Chair = if #Chairs > 0 then Local.FreeChair(S, Chairs, Seat) else nil
	if not Chair then Local.Mingle(S, Job) return end
	S.Model:SetAttribute(`NHActivity`, `In class ({RoomId})`)
	local Front = (Chair:GetPivot() * CFrame.new(0, 0, 2.5)).Position
	Local.WalkTo(S, Job, Local.Floor(Front) or Front)
	if S.Job == Job then
		Local.Sit(S, Chair)
		Brain.Idle(S, 3600, function() return S.Job == Job and not Paused and S.Seated == Chair end) -- (1.86.2)
	end
end

function Local.Lunch(S, Job, Slot: number)
	if not Local.Arrive(S, Job) then return end
	S.Model:SetAttribute(`NHActivity`, `Lunch`)
	local Spots = CollectionService:GetTagged(`NHLunchSpot`)
	table.sort(Spots, function(A, B) return A.Position.X + A.Position.Z * 0.01 < B.Position.X + B.Position.Z * 0.01 end)
	local Stand = workspace:FindFirstChild(`NHConcession`)
	local Goal
	if Spots[Slot] then
		-- the queue at the counter
		Goal = Spots[Slot].Position + Vector3.new((math.random() - 0.5) * 1.2, 0, (math.random() - 0.5) * 1.2)
	elseif Stand then
		-- everyone else hangs about in a loose arc in front of the stand, eating
		local CF = Stand:GetPivot()
		local Front = Spots[1] and (Spots[1].Position - CF.Position) * Vector3.new(1, 0, 1) or CF.LookVector
		Front = if Front.Magnitude > 0 then Front.Unit else Vector3.new(1, 0, 0)
		local Right = Front:Cross(Vector3.yAxis)
		local A = (Slot - #Spots - 1) / math.max(1, COUNT - #Spots - 1) * 2 - 1 -- -1 .. 1 across the arc
		local R = 9 + math.random() * 5
		local P = CF.Position + Front * (R * math.cos(A * 1.1)) + Right * (R * math.sin(A * 1.1))
		Goal = Local.Floor(P)
	end
	Goal = Goal or Local.HallSpot()
	if not Goal then return end
	Local.WalkTo(S, Job, Goal)
	if S.Job ~= Job then return end
	if Stand then Local.Face(S, Stand:GetPivot().Position) end
	task.wait(math.random(20, 60) / 10)
	if S.Job == Job then Local.Pose(S, `Eat`) end
end

-- a free gathering spot at the student's clique hangout (NHCliqueSpot parts, attribute = the clique)
-- (1.28 turf wars, Social.CliqueFights) a clique whose hangout is held by a rival hangs out elsewhere (the hallways),
-- and the holders hang out at the hangout they took as well as their own
function Local.SpotOwner(SpotClique: string, Clique: string): boolean
	if SpotClique == Clique then return workspace:GetAttribute(`NHTurfHolder_{Clique}`) == nil end
	return workspace:GetAttribute(`NHTurfHolder_{SpotClique}`) == Clique
end

function Local.FreeSpot(Clique: string): BasePart?
	local Free = {}
	for _, P in CollectionService2:GetTagged(`NHCliqueSpot`) do
		if P:IsA(`BasePart`) and Local.SpotOwner(P:GetAttribute(`NHCliqueSpot`) or ``, Clique) and P:IsDescendantOf(workspace) then
			local Who = SpotTaken[P]
			if not (Who and Who.Model) and os.clock() - (SpotFailed[P] or -1e9) > 120 then table.insert(Free, P) end
		end
	end
	if #Free == 0 then return nil end
	return Free[math.random(1, #Free)]
end

-- hang out with your clique (1.20): walk to a free spot at its hangout, face the group, stand and chat a while,
-- now and then shift to another spot
function Local.Hangout(S, Job)
	if not Local.Arrive(S, Job) then return end
	local Def = S.Clique and CliqueConfig.Defs[S.Clique]
	if not Def then Local.Mingle(S, Job) return end
	S.Model:SetAttribute(`NHActivity`, `Hanging out: {Def.HangoutName}`)
	while S.Job == Job and not Paused do
		local Spot = Local.FreeSpot(S.Clique)
		if not Spot then Local.Mingle(S, Job) return end
		local Owner = CliqueConfig.Defs[Spot:GetAttribute(`NHCliqueSpot`) or ``]
		S.Model:SetAttribute(`NHActivity`, `Hanging out: {(Owner or Def).HangoutName}`) -- a held rival hangout says so
		SpotTaken[Spot] = S
		local Ok = Local.WalkTo(S, Job, Local.Floor(Spot.Position) or Spot.Position)
		if S.Job ~= Job then if SpotTaken[Spot] == S then SpotTaken[Spot] = nil end return end
		if Ok then
			Local.Face(S, Spot.Position + Spot.CFrame.LookVector * 6)
			if math.random() < 0.3 then Brain.LeanOnWall(S, false, function() return S.Job == Job end) end -- (1.86.2) only on a wall
			Local.Linger(S, Job, math.random(150, 320) / 10)
		else
			SpotFailed[Spot] = os.clock() -- no way there from here: try another spot
			task.wait(1)
		end
		Local.Pose(S, nil)
		if SpotTaken[Spot] == S then SpotTaken[Spot] = nil end
	end
end

-- (1.27, Cliques Phase 2) while hanging out: watch a scuffle nearby (workspace NHScuffleAt, Social.CliqueFights), and
-- turn to face a student your clique respects or hates (their CliqueTier_<Id> attribute, Social.Cliques)
local LINGER_FACE = { Respected = true; Hostile = true }
function Local.Linger(S, Job, Seconds: number)
	local Until = os.clock() + Seconds
	local Range = (CliqueConfig.Fights and CliqueConfig.Fights.FacingRange) or 10
	while os.clock() < Until and S.Job == Job and not Paused do
		Brain.Idle(S, 1, function() return S.Job == Job and not Paused end) -- (1.86.2) fidgets, chats, mutters
		local R = S.Root
		if not R then return end
		local At = workspace:GetAttribute(`NHScuffleAt`)
		if typeof(At) == `Vector3` and (At - R.Position).Magnitude <= 50 then
			Local.Face(S, At)
		elseif S.Clique then
			for _, P in Players:GetPlayers() do
				local PR = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
				if PR and (PR.Position - R.Position).Magnitude <= Range and LINGER_FACE[P:GetAttribute(`CliqueTier_{S.Clique}`) or ``] then
					Local.Face(S, PR.Position)
					break
				end
			end
		end
	end
end

function Local.Club(S, Job)
	if not Local.Arrive(S, Job) then return end
	S.Model:SetAttribute(`NHActivity`, `Club: {S.Club}`)
	while S.Job == Job and not Paused do
		local Spot = Local.ClubSpot(S.Club) or Local.HallSpot()
		if Spot then Local.WalkTo(S, Job, Spot) end
		if S.Job ~= Job then return end
		Brain.Idle(S, math.random(120, 260) / 10, function() return S.Job == Job and not Paused end) -- (1.86.2)
	end
end

---| the clock |---

-- start a new job for one student (cancels whatever they were doing)
function Local.Assign(S, Fn, ...)
	local Job = {}
	S.Job = Job
	local Args = table.pack(...)
	S.LastJob = { Fn = Fn; Args = Args } -- (1.86.2) Brain's Replan starts it again after a reaction
	local Now = S.ReplanNow
	S.ReplanNow = nil
	task.spawn(function()
		if not Now then task.wait(math.random() * 4) end -- don't all leave on the same frame
		if S.Job ~= Job then return end
		local Ok, Err = pcall(Fn, S, Job, table.unpack(Args, 1, Args.n))
		if not Ok then warn(`[Schedules] {Err}`) end
	end)
end

function Local.OnSegment(State)
	local Seg = State.Segment
	local Kind = Seg.Kind
	local Hour = State.Hour or math.floor((State.MinuteOfDay or 0) / 60)
	Plan = { Kind = Kind; SegName = Seg.Name; DayName = State.DayName or (typeof(State.Day) == `string` and State.Day or nil) }
	for I, S in Students do
		if Kind == `Night` or Kind == `Morning` then
			if S.Model then Local.Assign(S, Local.Leave) else S.Job = {} end
		elseif Kind == `BeforeSchool` or Kind == `Passing` then
			Local.Assign(S, Local.Mingle)
		elseif Kind == `Break` then
			Local.Assign(S, Local.Hangout) -- with their clique
		elseif Kind == `Class` then
			local Period = Classes.Periods[Seg.Name]
			if Period and I <= IN_CLASS then
				Local.Assign(S, Local.Class, Period.Room, I)
			else
				Local.Assign(S, Local.Leave) -- the east wing
			end
		elseif Kind == `Lunch` then
			Local.Assign(S, Local.Lunch, I)
		elseif Kind == `AfterSchool` then
			-- a third head home after 14:00
			if Hour >= 14 and I % 3 == 0 then Local.Assign(S, Local.Leave)
			elseif S.Clique == `Athletes` then Local.Assign(S, Local.Club)
			else Local.Assign(S, Local.Hangout) end
		elseif Kind == `Evening` then
			if Hour >= 19 or I % 2 == 0 then Local.Assign(S, Local.Leave) else Local.Assign(S, Local.Hangout) end
		end
	end
end

function Shared.Pause(On: boolean)
	Paused = On
	if On then
		for _, S in Students do S.Job = {} Local.Despawn(S) end
	else
		Segment = nil -- re-plan on the next tick
	end
end

-- tests: plan a period without moving the school clock (moving it can mark test players absent)
function Shared.PlanForTests(Kind: string, Name: string?, Hour: number?)
	Segment = `test:{Kind}:{Name or ``}`
	Local.TestUntil = os.clock() + 150 -- the clock loop leaves the test plan alone for a while
	Local.OnSegment({ Segment = { Kind = Kind; Name = Name or Kind }; Hour = Hour or 10 })
end

function Shared.Debug()
	local Out = {}
	for _, S in Students do
		table.insert(Out, { Index = S.Index; Club = S.Club; Clique = S.Clique; Spawned = S.Model ~= nil; Activity = S.Model and S.Model:GetAttribute(`NHActivity`); Seated = S.Seated ~= nil })
	end
	return Out
end

function Shared.OnStart()
	Local.Groups()
	Folder = Instance.new(`Folder`)
	Folder.Name = `NHSchedule`
	Folder.Parent = workspace
	for I = 1, COUNT do
		local Ok, Look = pcall(Local.Look)
		local Clique = CliqueConfig.Students[I] or `Ordinary`
		if Ok and Look then
			local Appearance = require(ReplicatedStorage.UI.Appearance)
			local L = CliqueConfig.Defs[Clique] and CliqueConfig.Defs[Clique].Look
			if L then
				local Female = require(ReplicatedStorage.UI.Appearance).IsFemale(Look)
				local Tops = table.clone(L.Tops or {})
				if Female then for _, T in L.FemaleTops or {} do table.insert(Tops, T) end end
				local Bottoms = if Female and L.FemaleBottoms then L.FemaleBottoms else L.Bottoms
				Look.Uniform = Appearance.IndexOf(Appearance.Uniforms, Tops[math.random(1, #Tops)]) or Look.Uniform
				if Bottoms and #Bottoms > 0 then Look.Bottoms = Appearance.IndexOf(Appearance.BottomsList, Bottoms[math.random(1, #Bottoms)]) or Look.Bottoms end
			end
		end
		Students[I] = { Index = I; Look = if Ok then Look else nil; Club = CLUBS[(I - 1) % #CLUBS + 1]; Clique = Clique;
			-- (1.86.2) a personality and a voice (Config.NpcVoice: Girl / Boy by body, a personal pitch +-8%)
			Bravery = math.random(10, 85) / 100; Social = math.random(15, 95) / 100; Speed = 5.4 + math.random() * 1.6;
			VoiceSet = if Ok and Look and require(ReplicatedStorage.UI.Appearance).IsFemale(Look) then `Girl` else `Boy`;
			Voice = 0.92 + math.random() * 0.16;
		}
	end
	Brain.Init({
		Pose = Local.Pose;
		Unseat = Local.Unseat;
		Students = function() return Students end;
		Plan = function() return Plan end;
		-- after backing away from danger: start the current job again, straight away
		Replan = function(S)
			local L = S.LastJob
			if not (L and S.Model) or Paused then return end
			S.ReplanNow = true
			Local.Assign(S, L.Fn, table.unpack(L.Args, 1, L.Args.n))
		end;
	})
	task.spawn(function()
		task.wait(6) -- the map, props and stand go up first
		local Clock = require(ServerScriptService.Services.School.SchoolClock)
		while true do
			local Ok, State = pcall(Clock.GetState)
			if Ok and State and State.Segment and not Paused and os.clock() > (Local.TestUntil or 0) then
				local Key = `{State.Day}:{State.SegmentIndex}:{State.Segment.Kind == `AfterSchool` and (State.Hour or 0) >= 14 and `late` or ``}:{State.Segment.Kind == `Evening` and (State.Hour or 0) >= 19 and `late` or ``}`
				if Key ~= Segment then
					Segment = Key
					local Ok2, Err = pcall(Local.OnSegment, State)
					if not Ok2 then warn(`[Schedules] {Err}`) end
				end
			end
			task.wait(1)
		end
	end)
end

return Shared
