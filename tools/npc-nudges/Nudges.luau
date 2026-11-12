--[[
	Nudges (server). Services.AI.StudentBrain.Nudges  (1.86.3)

	What a student does when a player actually brushes past or barges into them, after the crowd footage the owner
	picked (design canvas "NPC Nudge Animations"). StudentBrain sets Brain.OnBump to Nudges.Handle.
	  Nudge_Left / Nudge_Right  a brush on that shoulder: the torso twists away, the bumped shoulder rolls back, the head
	                            stays on the passer (NpcLook, from the brain's NHLookAt). Hips are unkeyed, so the walk or
	                            idle keeps the legs. The student slides 0.45 studs away from the passer over 0.25 s.
	  Shove_Forward             a sprinter hitting them from behind or behind-side: fold, low stagger, rise, look back.
	                            The walk stops and the body is carried about 3 studs along the push, fading out.
	Players don't collide with students (NHWalkers), so "contact" is the passer's root coming within CONTACT studs.
	MakeWay fires about a second early, so the handler waits for that contact and does nothing if it never comes.
	Each play varies speed and weight, and a student can't be nudged again for COOLDOWN seconds.

	The clips: ServerStorage.NHNudges (built by tools/npc-nudges/build_nudges.luau). Until the owner publishes them
	and fills IDS, Studio plays the local KeyframeSequences and live servers keep the brain's old step aside.
]]

local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Nav = require(ServerScriptService.Services.AI.Nav)

local Nudges = {}

-- the published animation ids (owner: publish ServerStorage.NHNudges under the group and put the ids here)
local IDS = {
	Nudge_Left = 0;
	Nudge_Right = 0;
	Shove_Forward = 0;
}

local CONTACT = 3          -- studs between roots that counts as a brush
local CROWD_CONTACT = 3.8  -- Space: Senses calls someone within 3.6 for 1.2 s crowding
local WAIT_CONTACT = 1.4   -- how long MakeWay waits for the brush before letting it go
local SHOVE_SPEED = 20     -- a passer this fast (sprinting, dashing) shoves instead of brushing
local SIDE_STEP = 0.45
local SIDE_TIME = 0.25
local CARRY = 3
local CARRY_TIME = 0.7
local COOLDOWN = 1.5

local Studio = RunService:IsStudio()
local Ids = {} :: { [string]: string }

local function idOf(Name: string): string?
	if Ids[Name] then return Ids[Name] end
	local Id = IDS[Name]
	if Id and Id ~= 0 then
		Ids[Name] = `rbxassetid://{Id}`
	elseif Studio then
		local KS = ServerStorage:FindFirstChild(`NHNudges`) and ServerStorage.NHNudges:FindFirstChild(Name)
		if not KS then return nil end
		local Ok, Temp = pcall(function() return KeyframeSequenceProvider:RegisterKeyframeSequence(KS) end)
		if not Ok then return nil end
		Ids[Name] = Temp
	else
		return nil
	end
	return Ids[Name]
end

local function track(S, Name: string): AnimationTrack?
	S.NudgeTracks = S.NudgeTracks or {}
	if S.NudgeTracks[Name] then return S.NudgeTracks[Name] end
	local Id = idOf(Name)
	local Animator = Id and S.Hum and (S.Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, S.Hum))
	if not Animator then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = Id
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	T.Looped = false
	T.Priority = if Name == `Shove_Forward` then Enum.AnimationPriority.Action2 else Enum.AnimationPriority.Action
	S.NudgeTracks[Name] = T
	return T
end

local function flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

local function lookAt(S, P: Vector3, Seconds: number)
	S.Model:SetAttribute(`NHLookAt`, P)
	S.Model:SetAttribute(`NHLookUntil`, workspace:GetServerTimeNow() + Seconds)
end

local function rootOf(Rec): BasePart?
	local R = Rec.Root or (Rec.Player and Rec.Player.Character and Rec.Player.Character:FindFirstChild(`HumanoidRootPart`))
	return if R and R:IsA(`BasePart`) and R.Parent then R else nil
end

-- nothing solid (and a floor) along the way: students never slide into a wall or off a ledge
local Params = RaycastParams.new()
Params.FilterType = Enum.RaycastFilterType.Exclude
Params.RespectCanCollide = true
local function clear(S, Dir: Vector3, Dist: number): boolean
	local Ex = { S.Model }
	for _, N in { `Live`, `NHFx`, `NHStudents`, `NHSchedule`, `NHAmbient` } do
		local F = workspace:FindFirstChild(N)
		if F then table.insert(Ex, F) end
	end
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ex, P.Character) end end
	Params.FilterDescendantsInstances = Ex
	local From = S.Root.Position
	if workspace:Raycast(From, Dir * (Dist + 1), Params) then return false end
	local Feet = From - Vector3.new(0, S.Up or 3, 0)
	local Floor = Nav.Floor(Feet + Dir * Dist, 1.5)
	return Floor ~= nil and math.abs(Floor.Y - Feet.Y) < 1.2
end

-- move the root Dist studs along Dir over Seconds, fast at first (the walk or idle carries on underneath)
local function slide(S, Dir: Vector3, Dist: number, Seconds: number, Face: Vector3?)
	if not clear(S, Dir, Dist) then
		Dist = if clear(S, Dir, Dist * 0.4) then Dist * 0.4 else 0
	end
	local Root = S.Root
	local Start = os.clock()
	local Done = 0
	local Turn0 = Root.CFrame.LookVector
	while Root.Parent do
		local A = math.clamp((os.clock() - Start) / Seconds, 0, 1)
		local Want = Dist * (1 - (1 - A) ^ 3)
		local P = Root.Position + Dir * (Want - Done)
		Done = Want
		local Look = Turn0
		if Face then Look = Turn0:Lerp(Face, math.clamp(A * 5, 0, 1)) end
		if flat(Look).Magnitude > 1e-3 then
			Root.CFrame = CFrame.lookAt(P, P + flat(Look))
		else
			Root.CFrame = Root.CFrame.Rotation + P
		end
		if A >= 1 then break end
		RunService.Heartbeat:Wait()
	end
end

local function side(S, Rec, PasserPos: Vector3)
	local Rel = flat(PasserPos - S.Root.Position)
	local Right = S.Root.CFrame.RightVector
	local OnRight = Rel:Dot(Right) > 0
	local T = track(S, if OnRight then `Nudge_Right` else `Nudge_Left`)
	if not T then return end
	T:Play(0.06, math.random(70, 100) / 100, math.random(90, 115) / 100)
	lookAt(S, PasserPos + Vector3.new(0, 1.5, 0), 1.6)
	slide(S, flat(if OnRight then -Right else Right).Unit, SIDE_STEP, SIDE_TIME)
	task.wait(0.35)
end

local function shove(S, Rec, Push: Vector3)
	local T = track(S, `Shove_Forward`)
	if not T then return end
	if S.Agent then S.Agent:Stop() end
	local Speed = math.random(95, 108) / 100
	T:Play(0.05, 1, Speed)
	S.Model:SetAttribute(`NHMood`, `Startled`)
	slide(S, Push, CARRY, CARRY_TIME, Push)
	-- the look back, after the rise (the canvas's F46)
	task.wait(math.max(0, 1.3 / Speed - CARRY_TIME))
	local R = rootOf(Rec)
	if R and S.Model then lookAt(S, R.Position + Vector3.new(0, 1.5, 0), 1.4) end
	task.wait(0.45 / Speed)
end

-- Brain.OnBump: true when the nudge handled it (the brain skips its step aside)
function Nudges.Handle(S, Rec, Kind: string): boolean
	if S.Seated or not (S.Model and S.Hum and S.Root and Rec) then return false end
	if os.clock() < (S.NudgeReady or 0) then return false end
	if not (idOf(`Nudge_Left`) and idOf(`Nudge_Right`) and idOf(`Shove_Forward`)) then return false end
	local R = rootOf(Rec)
	if not R then return false end
	-- wait for the brush itself (Space: they're already on top of us)
	local Until = os.clock() + (if Kind == `Space` then 0 else WAIT_CONTACT)
	local Reach = if Kind == `Space` then CROWD_CONTACT else CONTACT
	local Dist = flat(R.Position - S.Root.Position).Magnitude
	while Dist > Reach do
		if os.clock() > Until or not (R.Parent and S.Root.Parent) then return true end -- no brush: carry on walking
		RunService.Heartbeat:Wait()
		Dist = flat(R.Position - S.Root.Position).Magnitude
	end
	S.NudgeReady = os.clock() + COOLDOWN + 2
	local V = flat(R.AssemblyLinearVelocity)
	local Look = flat(S.Root.CFrame.LookVector).Unit
	local Behind = flat(S.Root.Position - R.Position).Unit:Dot(Look) > -0.3 -- the passer is behind or beside us
	if V.Magnitude >= SHOVE_SPEED and V.Unit:Dot(Look) > 0.35 and Behind then
		shove(S, Rec, V.Unit)
	else
		side(S, Rec, R.Position)
		-- someone standing on top of us: still back off afterwards, as the brain did
		if Kind == `Space` and S.Agent and R.Parent then
			S.Agent:Shuffle(S.Root.Position - R.Position, 0.6, 4)
			S.Agent:Face(R.Position)
		end
	end
	S.NudgeReady = os.clock() + COOLDOWN
	return true
end

return Nudges
