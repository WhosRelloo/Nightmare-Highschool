--[[
	Nav (server). Services.AI.Nav  (NH core add-on for the Map place, 2026-11-10)

	The walking that school NPCs use. Owner: "COMPLETELY upgrade their pathfinding & awareness". Compared with
	Features.Schedules' walker (one ComputeAsync, no jumping, no doors, give up after 3 s stuck), an agent here:
	  * plans with PathfindingService through doors: every leaf of a door-kit door (tag NHDoor, not Locked) gets a
	    PassThrough PathfindingModifier labelled NHDoorway while the game runs, and the agent opens the door
	    (Features.Doors.Toggle, swinging away from it) as it walks up, then walks through;
	  * can take steps and ledges (Jump waypoints; the Map's entrance steps need them);
	  * smooths the path (cuts to the furthest waypoint it has a clear, floored line to, never past a door or jump);
	  * steers around other NPCs and players (predicted closest approach, players get right of way) and slows in crowds;
	  * re-plans when the path is blocked (Path.Blocked), when it drifts off the path, or when it stops making
	    progress, escalating: hop a ledge -> sidestep -> back off and re-plan -> give up (the goal is remembered as
	    unreachable for a while so the caller picks another);
	  * matches its walk clip to its real speed, eases in at the goal, and can be cancelled every frame (ShouldStop).
	Paths are planned through a small queue (a few at a time), so many NPCs never flood PathfindingService.

	Debug: workspace attribute NHNavDebug = true draws each agent's path (Studio).

	API
	  Nav.Agent(Model, Opts?) -> agent      Opts: Radius, Height, Speed (studs/s), Name
	  agent:GoTo(Goal: Vector3, Opts?) -> (ok: boolean, why: string?)    yields; Opts: Speed, Arrive, ShouldStop (fn -> bool), Face (Vector3?)
	  agent:Stop()                          stop moving now (also cancels a GoTo in progress)
	  agent:Velocity() -> Vector3
	  Nav.Floor(Pos: Vector3, Up: number?) -> Vector3?     the walkable floor under a point
	  Nav.Unreachable(Goal) -> boolean      true if a goal near there failed lately
	  Nav.Agents() -> { agent }
]]

local CollectionService = game:GetService(`CollectionService`)
local PathfindingService = game:GetService(`PathfindingService`)
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Nav = {}
local Local = {}

local DOOR_LABEL = `NHDoorway`
local MAX_PLANS_AT_ONCE = 3
local FAIL_MEMORY = 25          -- seconds a goal this agent couldn't reach is avoided
local LOOKAHEAD = 7             -- waypoints the smoother may skip ahead
local DOOR_REACH = 7            -- open a door this far before its doorway
local AVOID_RADIUS = 7
local PERSONAL = 2.6            -- the gap kept from others when passing

local Studio = RunService:IsStudio()
local Agents = {} :: { [any]: boolean }
local Failed = {} :: { { At: Vector3, Until: number } }
local Planning = 0

---| world queries |---

local function exclusions(): { Instance }
	local Ex = {}
	for _, N in { `Live`, `NHFx`, `NHStudents`, `NHSchedule`, `NHAmbient`, `NHNavDebug`, `School NPC Spots` } do
		local F = workspace:FindFirstChild(N)
		if F then table.insert(Ex, F) end
	end
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ex, P.Character) end end
	return Ex
end

local RayP = RaycastParams.new()
RayP.FilterType = Enum.RaycastFilterType.Exclude
RayP.RespectCanCollide = true
local RayRefresh = 0
local function rayParams(): RaycastParams
	if os.clock() - RayRefresh > 2 then
		RayRefresh = os.clock()
		RayP.FilterDescendantsInstances = exclusions()
	end
	return RayP
end

-- the first solid, visible-or-colliding surface along a ray (skips invisible non-colliders)
local function cast(From: Vector3, Dir: Vector3): RaycastResult?
	return workspace:Raycast(From, Dir, rayParams())
end

function Nav.Floor(Pos: Vector3, Up: number?): Vector3?
	local Hit = cast(Pos + Vector3.new(0, Up or 4, 0), Vector3.new(0, -((Up or 4) + 12), 0))
	if Hit and Hit.Normal.Y > 0.6 then return Hit.Position end
	return nil
end

-- a clear, floored straight line for a body of radius R from A to B (both at floor height)
local function lineClear(A: Vector3, B: Vector3, R: number): boolean
	local Flat = Vector3.new(B.X - A.X, 0, B.Z - A.Z)
	local Len = Flat.Magnitude
	if Len < 0.5 then return true end
	if math.abs(B.Y - A.Y) > 1.6 then return false end
	local Dir = Flat / Len
	local Side = Vector3.new(-Dir.Z, 0, Dir.X) * (R * 0.9)
	for _, H in { 1.2, 3.2 } do
		for _, Off in { Vector3.zero, Side, -Side } do
			if cast(A + Vector3.new(0, H, 0) + Off, Flat) then return false end
		end
	end
	-- floor all the way (no gaps, no drops)
	local Steps = math.clamp(math.floor(Len / 3), 1, 12)
	for I = 1, Steps do
		local P = A:Lerp(B, I / (Steps + 1))
		local F = Nav.Floor(P, 2.5)
		if not F or math.abs(F.Y - P.Y) > 1.4 then return false end
	end
	return true
end

---| doors |---

local Doors = nil
local function doorsModule()
	if Doors == nil then
		local Ok, M = pcall(require, ServerScriptService.Services.Features.Doors)
		Doors = if Ok then M else false
	end
	return Doors or nil
end

local function leaves(Model: Instance): { BasePart }
	local Out = {}
	for _, P in Model:GetDescendants() do
		if P:IsA(`BasePart`) and P:GetAttribute(`DoorLeaf`) then table.insert(Out, P) end
	end
	return Out
end

function Local.MarkDoor(Model: Instance)
	if not Model:IsA(`Model`) or not Model:IsDescendantOf(workspace) then return end
	local function apply()
		local Locked = Model:GetAttribute(`Locked`) == true
		for _, Leaf in leaves(Model) do
			local M = Leaf:FindFirstChild(`NHNavDoor`)
			if Locked then
				if M then M:Destroy() end
			elseif not M then
				M = Instance.new(`PathfindingModifier`)
				M.Name = `NHNavDoor`
				M.Label = DOOR_LABEL
				M.PassThrough = true
				M.Parent = Leaf
			end
		end
	end
	apply()
	Model:GetAttributeChangedSignal(`Locked`):Connect(apply)
end

-- the door model whose doorway is near a point (within R)
local DoorList = {}
local function doorNear(P: Vector3, R: number): Model?
	local Best, BestD = nil, R
	for _, D in DoorList do
		if D.Parent and D:GetAttribute(`Locked`) ~= true then
			local Dist = (D:GetPivot().Position - P).Magnitude
			if Dist < BestD then Best, BestD = D, Dist end
		end
	end
	return Best
end

-- open a closed door, swinging away from the agent; true once it is open (or there was nothing to open)
local function openDoor(Door: Model, From: Vector3): boolean
	if Door:GetAttribute(`Open`) == true then return true end
	local M = doorsModule()
	if not (M and M.Toggle) then return false end
	if Door:GetAttribute(`OneWay`) ~= true then
		Door:SetAttribute(`OpenDir`, if Door:GetPivot():PointToObjectSpace(From).Z < 0 then 1 else -1)
	end
	pcall(M.Toggle, Door, nil)
	return Door:GetAttribute(`Open`) == true
end

---| planning |---

-- failures are remembered per agent: one student stuck somewhere odd mustn't put a spot off-limits for everyone
local function rememberFail(Agent, Goal: Vector3)
	Agent.Failed = Agent.Failed or {}
	table.insert(Agent.Failed, { At = Goal; Until = os.clock() + FAIL_MEMORY })
end

function Nav.Unreachable(Goal: Vector3, Agent: any?): boolean
	local Now = os.clock()
	local List = Agent and Agent.Failed or Failed
	for I = #List, 1, -1 do
		local F = List[I]
		if F.Until < Now then table.remove(List, I)
		elseif (F.At - Goal).Magnitude < 4 then return true end
	end
	return false
end

-- a fresh Path for each plan, computed on its own thread with a time limit: a ComputeAsync that never returns
-- (it happens on a busy live map) must not hold a planning slot, or every other NPC waits behind it forever
local function plan(Agent, From: Vector3, To: Vector3): { PathWaypoint }?
	local Queued = os.clock()
	while Planning >= MAX_PLANS_AT_ONCE and os.clock() - Queued < 5 do task.wait(0.05) end
	Planning += 1
	local Path = PathfindingService:CreatePath(Agent.Params)
	local Done, Ok = false, false
	task.spawn(function()
		Ok = pcall(function() Path:ComputeAsync(From, To) end)
		Done = true
	end)
	local Until = os.clock() + 4
	while not Done and os.clock() < Until do task.wait(0.05) end
	Planning -= 1
	if not (Done and Ok and Path.Status == Enum.PathStatus.Success) then
		if not Done then Agent.Timeouts = (Agent.Timeouts or 0) + 1 end
		return nil
	end
	-- no leaps of faith: the planner will happily route a jump out of a second-floor window (the Map's courtyard has
	-- no ground-floor way in yet). A drop of more than 5 studs anywhere on the path means "no path".
	local Points = Path:GetWaypoints()
	for I = 2, #Points do
		if Points[I - 1].Position.Y - Points[I].Position.Y > 5 then
			Agent.Drops = (Agent.Drops or 0) + 1
			return nil
		end
	end
	Agent.Path = Path
	return Points
end

---| debug |---

local function drawPath(Agent, Points)
	if not (RunService:IsStudio() and workspace:GetAttribute(`NHNavDebug`) == true) then
		if Agent.Debug then Agent.Debug:Destroy() Agent.Debug = nil end
		return
	end
	local Root = workspace:FindFirstChild(`NHNavDebug`)
	if not Root then Root = Instance.new(`Folder`) Root.Name = `NHNavDebug` Root.Parent = workspace end
	if Agent.Debug then Agent.Debug:Destroy() end
	local F = Instance.new(`Folder`)
	F.Name = Agent.Name
	for I, W in Points do
		local P = Instance.new(`Part`)
		P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
		P.Shape = Enum.PartType.Ball
		P.Size = Vector3.one * 0.5
		P.Material = Enum.Material.Neon
		P.Color = if W.Action == Enum.PathWaypointAction.Jump then Color3.fromRGB(255, 200, 60)
			elseif W.Label == DOOR_LABEL then Color3.fromRGB(90, 200, 255)
			else Color3.fromRGB(200, 60, 80)
		P.Position = W.Position + Vector3.new(0, 0.3, 0)
		P.Name = tostring(I)
		P.Parent = F
	end
	F.Parent = Root
	Agent.Debug = F
end

---| the agent |---

local AgentMT = {}
AgentMT.__index = AgentMT

function Nav.Agent(Model: Model, Opts: { [string]: any }?)
	local O = Opts or {}
	local Hum = Model:FindFirstChildOfClass(`Humanoid`) :: Humanoid
	local Root = Model:FindFirstChild(`HumanoidRootPart`) :: BasePart
	local Radius = O.Radius or 1.25
	local Agent = setmetatable({
		Model = Model; Hum = Hum; Root = Root; Name = O.Name or Model.Name;
		Radius = Radius; Speed = O.Speed or 6;
		Params = {
			AgentRadius = Radius; AgentHeight = O.Height or 5; AgentCanJump = true; AgentCanClimb = false;
			WaypointSpacing = 4; Costs = { [DOOR_LABEL] = 6; Jump = 4; Water = math.huge; NHAvoid = 25 };
		};
		Moving = false; Token = 0; LastPos = Root.Position; Vel = Vector3.zero;
	}, AgentMT)
	Agents[Agent] = true
	Model.Destroying:Connect(function() Agents[Agent] = nil if Agent.Debug then Agent.Debug:Destroy() end end)
	return Agent
end

function Nav.Agents()
	local Out = {}
	for A in Agents do if A.Model.Parent then table.insert(Out, A) end end
	return Out
end

function AgentMT:Velocity(): Vector3
	return self.Vel
end

function AgentMT:Stop()
	self.Token += 1
	self.Moving = false
	if self.Hum then self.Hum:Move(Vector3.zero) end
end

-- everyone the agent should keep clear of: other NPC agents and player characters. In a doorway or on steps
-- (Tight) other NPCs are ignored: they never collide, and steering round each other there jams the doorway.
local function neighbours(Self, Tight: boolean): { { P: Vector3, V: Vector3, Player: boolean } }
	local Out = {}
	local My = Self.Root.Position
	if not Tight then
		for A in Agents do
			if A ~= Self and A.Root and A.Model.Parent then
				local P = A.Root.Position
				if (P - My).Magnitude < AVOID_RADIUS then table.insert(Out, { P = P; V = A.Vel; Player = false }) end
			end
		end
	end
	for _, Pl in Players:GetPlayers() do
		local R = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if R and R:IsA(`BasePart`) and (R.Position - My).Magnitude < AVOID_RADIUS + 3 then
			table.insert(Out, { P = R.Position; V = R.AssemblyLinearVelocity; Player = true })
		end
	end
	return Out
end

-- a sideways nudge away from whoever we are about to walk into (predicted closest approach within 1.6 s), and a
-- slow-down behind someone in the way. Only ever sideways and slower, never backwards: pushing straight back made
-- students in a doorway shove each other out of it forever.
local function avoidance(Self, Want: Vector3, Speed: number, Tight: boolean): (Vector3, number, number)
	local My = Self.Root.Position
	local MyV = Want * Speed
	local Push = Vector3.zero
	local Crowd = 0
	local Slow = 1
	local Side = Vector3.new(-Want.Z, 0, Want.X)
	for _, N in neighbours(Self, Tight) do
		local Rel = Vector3.new(N.P.X - My.X, 0, N.P.Z - My.Z)
		local RelV = Vector3.new(N.V.X - MyV.X, 0, N.V.Z - MyV.Z)
		local Dist = Rel.Magnitude
		if Dist < 4 then Crowd += 1 end
		local T = 0
		local VV = RelV:Dot(RelV)
		if VV > 1e-3 then T = math.clamp(-Rel:Dot(RelV) / VV, 0, 1.6) end
		local Closest = Rel + RelV * T
		local Gap = PERSONAL + (if N.Player then 0.8 else 0)
		if Closest.Magnitude < Gap and (T > 0 or Dist < Gap) then
			-- the sideways part of "away" only; head-on, step to our right
			local Lateral = Side * (-Closest):Dot(Side)
			if Lateral.Magnitude < 0.05 then Lateral = Side * 0.5 end
			local W = (Gap - Closest.Magnitude) / Gap * (1 - T / 1.8)
			Push += Lateral.Unit * W * (if N.Player then 1.5 else 0.7)
			-- someone right in front, going our way or standing: ease off rather than push
			local Ahead = Rel:Dot(Want)
			if Ahead > 0 and Dist < 3 then Slow = math.min(Slow, math.clamp(Dist / 3, 0.3, 1)) end
		end
	end
	local Dir = Want + Push * 1.2
	if Dir.Magnitude < 1e-3 or Dir:Dot(Want) < 0.2 then Dir = (Want + Push.Unit * 0.6) end
	return Dir.Unit, Crowd, Slow
end

-- the furthest waypoint ahead we can walk straight to (never past a jump or a doorway)
local function furthestClear(Self, Points, I: number): number
	local From = Self.Root.Position - Vector3.new(0, Self.Up, 0)
	local Best = I
	for J = I + 1, math.min(#Points, I + LOOKAHEAD) do
		local Prev = Points[J - 1]
		if Prev.Action == Enum.PathWaypointAction.Jump or Prev.Label == DOOR_LABEL then break end
		if Points[J].Action == Enum.PathWaypointAction.Jump or Points[J].Label == DOOR_LABEL then break end
		if lineClear(From, Points[J].Position, Self.Radius) then Best = J else break end
	end
	return Best
end

local function flat(V: Vector3): Vector3 return Vector3.new(V.X, 0, V.Z) end

function AgentMT:GoTo(Goal: Vector3, Opts: { [string]: any }?): (boolean, string?)
	local O = Opts or {}
	local Hum, Root = self.Hum, self.Root
	if not (Hum and Root and self.Model.Parent) then return false, `gone` end
	self.Token += 1
	local My = self.Token
	self.Moving = true
	self.Blocks = 0
	self.Up = self.Up or (Root.Size.Y / 2 + Hum.HipHeight + 2)
	local Arrive = O.Arrive or 1.6
	local BaseSpeed = O.Speed or self.Speed
	local ShouldStop = O.ShouldStop
	local function cancelled(): boolean
		return self.Token ~= My or not self.Model.Parent or Hum.Health <= 0 or (ShouldStop ~= nil and ShouldStop() == true)
	end

	if (flat(Root.Position - Goal)).Magnitude <= Arrive then self:Stop() return true end
	if Nav.Unreachable(Goal, self) then self.Moving = false return false, `unreachable` end

	local Replans = 0
	while Replans <= 3 do
		if cancelled() then self.Moving = false Hum:Move(Vector3.zero) return false, `cancelled` end
		local Start = Root.Position - Vector3.new(0, self.Up - 1, 0)
		if Studio then self.Model:SetAttribute(`NHNav`, `planning ({Replans} replans, {self.Timeouts or 0} timeouts)`) end
		local Points = plan(self, Start, Goal)
		if not Points then
			-- no path: a short, clear hop straight there is fine; anything else is unreachable from here
			if (Root.Position - Goal).Magnitude < 10 and lineClear(Start, Goal, self.Radius) then
				Points = { { Position = Goal; Action = Enum.PathWaypointAction.Walk; Label = `` } }
				self.Fallback = Points
			else
				Replans += 1
				if Replans > 1 then break end
				task.wait(0.4)
				continue
			end
		end
		drawPath(self, Points)
		-- Path.Blocked fires a lot on a live map (doors swinging, the oaks swaying, anything that touches the navmesh),
		-- so it only counts when the blocked waypoint is close ahead and the way to it really is shut
		local BlockedAt = nil
		local BlockConn = if self.Path and Points ~= self.Fallback then self.Path.Blocked:Connect(function(Idx) BlockedAt = Idx end) else nil

		local I = if #Points > 1 then 2 else 1
		self.Passed = 1
		local Best, Since = math.huge, os.clock()
		local Escalate = 0
		local NextSmooth = 0
		local Side = if math.random() < 0.5 then 1 else -1
		local SidestepUntil = 0
		local Result = nil

		while true do
			if cancelled() then Result = `cancelled` break end
			local Now = os.clock()
			local Pos = Root.Position
			local Feet = Pos - Vector3.new(0, self.Up, 0)
			if BlockedAt then
				local Idx = BlockedAt
				BlockedAt = nil
				local BW = Points[Idx]
				if Idx >= I and BW and BW.Label ~= DOOR_LABEL and Now - (self.LastBlockReplan or 0) > 2
					and (BW.Position - Feet).Magnitude < 14 and not lineClear(Feet, BW.Position, self.Radius) then
					self.LastBlockReplan = Now
					self.LastBlockedIdx = Idx
					Result = `blocked`
					break
				end
			end
			local W = Points[I]
			-- skip ahead along a clear line (5 Hz)
			if Now >= NextSmooth and I < #Points then
				NextSmooth = Now + 0.2
				I = furthestClear(self, Points, I)
				W = Points[I]
			end
			local ToW = flat(W.Position - Pos)
			local D = ToW.Magnitude
			local Last = I == #Points

			-- doors: open the one we are walking up to (ahead of us, on the way to this waypoint)
			local Door = doorNear(W.Position, DOOR_REACH) or (if W.Label == DOOR_LABEL then doorNear(W.Position, 12) else nil)
			local DoorAhead = Door and flat(Door:GetPivot().Position - Pos):Dot(ToW) > 0
			if Door and DoorAhead and Door:GetAttribute(`Open`) ~= true and (Door:GetPivot().Position - Pos).Magnitude < DOOR_REACH + 2 then
				Hum:Move(Vector3.zero)
				openDoor(Door, Pos)
				local Wait = os.clock() + 0.8
				while Door:GetAttribute(`Open`) ~= true and os.clock() < Wait and not cancelled() do task.wait(0.05) end
				task.wait(0.25) -- the leaves swing clear
				Since = os.clock()
			end

			-- arrived at this waypoint?
			local Reach = if Last then Arrive elseif W.Action == Enum.PathWaypointAction.Jump then 1.6 else 2.2
			if D < Reach then
				if Last then Result = `ok` break end
				if W.Action == Enum.PathWaypointAction.Jump then Hum.Jump = true end
				I += 1
				Best, Since, Escalate = math.huge, Now, 0
				continue
			end
			-- jump the waypoint's ledge as we reach it
			if W.Action == Enum.PathWaypointAction.Jump and D < 3.2 and W.Position.Y > Feet.Y + 0.8 then Hum.Jump = true end

			-- progress / stuck handling
			if D < Best - 0.25 then
				Best, Since = D, Now
			elseif Now - Since > 1.1 then
				Escalate += 1
				Since = Now
				if Escalate == 1 then
					Hum.Jump = true -- a lip or a step the path didn't mark
				elseif Escalate == 2 then
					SidestepUntil = Now + 0.7 -- slide along whatever is in the way
					Side = -Side
				elseif Escalate == 3 then
					Hum:Move(-ToW.Unit) -- back off a step and plan again from here
					task.wait(0.4)
					Result = `stuck`
					break
				end
			end
			-- off the path (shoved, fell): plan again
			-- off the path (shoved, fell): far from every waypoint we could be between (the smoother cuts long straight
			-- halls, so the target itself can legitimately be 60 studs ahead)
			if Now >= (self.NextLostCheck or 0) then
				self.NextLostCheck = Now + 0.5
				local Near = math.huge
				for K = math.max(1, (self.Passed or 1)), I do
					local A, B = Points[math.max(1, K - 1)].Position, Points[K].Position
					local AB = flat(B - A)
					local T = if AB.Magnitude > 1e-3 then math.clamp(flat(Feet - A):Dot(AB) / AB:Dot(AB), 0, 1) else 0
					local Dk = flat(Feet - (A + (B - A) * T)).Magnitude
					if Dk < Near then Near = Dk if Dk < 4 then self.Passed = math.max(1, K - 1) end end
				end
				if Near > 14 or Feet.Y < W.Position.Y - 12 then self.OffBy = Near Result = `lost` break end
			end

			-- steer
			local Want = if D > 1e-3 then ToW / D else Vector3.zero
			if Now < SidestepUntil then Want = (Want + Vector3.new(-Want.Z, 0, Want.X) * Side * 1.3).Unit end
			local Tight = doorNear(Pos, 7) ~= nil or math.abs(W.Position.Y - Feet.Y) > 1.2
			local Dir, Crowd, Slow = avoidance(self, Want, BaseSpeed, Tight)
			local Speed = BaseSpeed * (if Crowd >= 2 then 0.8 else 1) * Slow
			if Studio and Now >= (self.NextDiag or 0) then
				self.NextDiag = Now + 0.25
				self.Model:SetAttribute(`NHNav`, string.format(`wp %d/%d %s%s d=%.1f esc=%d replans=%d%s`, I, #Points,
					if W.Action == Enum.PathWaypointAction.Jump then `jump ` else ``, if W.Label == DOOR_LABEL then `door ` else ``,
					D, Escalate, Replans, if Tight then ` tight` else ``))
			end
			-- ease in at the goal
			local ToGoal = flat(Points[#Points].Position - Pos).Magnitude
			if ToGoal < 3 then Speed *= math.clamp(ToGoal / 3, 0.45, 1) end
			Hum.WalkSpeed = Speed
			Hum:Move(Dir)
			-- velocity estimate (for others' avoidance)
			local Dt = RunService.Heartbeat:Wait()
			self.Vel = (Root.Position - Pos) / math.max(Dt, 1 / 240)
		end
		if BlockConn then BlockConn:Disconnect() end
		if Studio then self.Model:SetAttribute(`NHNavWhy`, tostring(Result) .. (if Result == `blocked` then ` #` .. tostring(self.LastBlockedIdx) else ``) .. (if self.OffBy then string.format(` off=%.0f`, self.OffBy) else ``)) end
		if Result == `ok` then
			Hum:Move(Vector3.zero)
			self.Vel = Vector3.zero
			self.Moving = false
			if O.Face then
				local P = Root.Position
				Root.CFrame = CFrame.lookAt(P, Vector3.new(O.Face.X, P.Y, O.Face.Z))
			end
			return true
		elseif Result == `cancelled` then
			Hum:Move(Vector3.zero)
			self.Vel = Vector3.zero
			self.Moving = false
			return false, `cancelled`
		end
		-- a real block re-plans for free (up to 6 times); getting stuck or lost counts toward giving up
		if Result == `blocked` then
			self.Blocks = (self.Blocks or 0) + 1
			if self.Blocks > 6 then Replans += 1 end
		else
			Replans += 1
		end
	end
	self.Blocks = 0
	Hum:Move(Vector3.zero)
	self.Vel = Vector3.zero
	self.Moving = false
	rememberFail(self, Goal)
	return false, `unreachable`
end

-- walk a short way without planning (step aside, back off): straight, with avoidance, for at most Seconds
function AgentMT:Shuffle(Dir: Vector3, Seconds: number, Speed: number?)
	local Hum, Root = self.Hum, self.Root
	if not (Hum and Root) then return end
	self.Token += 1
	local My = self.Token
	local Until = os.clock() + Seconds
	local D = flat(Dir)
	if D.Magnitude < 1e-3 then return end
	D = D.Unit
	-- don't shuffle off a ledge or into a wall
	local Feet = Root.Position - Vector3.new(0, (self.Up or 3), 0)
	if not lineClear(Feet, Feet + D * (Speed or 5) * Seconds, self.Radius * 0.8) then
		local Alt = Vector3.new(-D.Z, 0, D.X)
		if lineClear(Feet, Feet + Alt * 3, self.Radius * 0.8) then D = Alt
		elseif lineClear(Feet, Feet - Alt * 3, self.Radius * 0.8) then D = -Alt
		else return end
	end
	Hum.WalkSpeed = Speed or 5
	while os.clock() < Until and self.Token == My and self.Model.Parent do
		local Pos = Root.Position
		Hum:Move(D)
		local Dt = RunService.Heartbeat:Wait()
		self.Vel = (Root.Position - Pos) / math.max(Dt, 1 / 240)
	end
	if self.Token == My then Hum:Move(Vector3.zero) self.Vel = Vector3.zero end
end

function AgentMT:Face(At: Vector3)
	local Root = self.Root
	if not Root then return end
	local P = Root.Position
	local To = Vector3.new(At.X, P.Y, At.Z)
	if (To - P).Magnitude < 0.1 then return end
	Root.CFrame = CFrame.lookAt(P, To)
end

---| start |---

local Started = false
function Nav.Init()
	if Started then return end
	Started = true
	-- only real doors: a door-kit frame with no leaf (the builder's archways) has nothing to open
	local function add(D: Instance)
		if not (D:IsA(`Model`) and D:IsDescendantOf(workspace)) or #leaves(D) == 0 then return end
		table.insert(DoorList, D)
		Local.MarkDoor(D)
	end
	for _, D in CollectionService:GetTagged(`NHDoor`) do task.spawn(add, D) end
	CollectionService:GetInstanceAddedSignal(`NHDoor`):Connect(add)
end

return Nav
