--[[
	Nudges (server). NH Combat Test: Services.AI.StudentBrain.Nudges (1.86.3); Map: Services.Features.MapStudents.Nudges
	(1.86.5). The same file in both places.

	What a student does when a player actually brushes past or barges into them, after the crowd footage the owner
	picked (design canvas "NPC Nudge Animations"). StudentBrain sets Brain.OnBump to Nudges.Handle; MapStudents calls
	it from React.MakeWay and React.Space.
	  Nudge_Left / Nudge_Right  a brush on that shoulder: the torso twists away, the bumped shoulder rolls back, the head
	                            stays on the passer (NpcLook, from the brain's NHLookAt). Hips are unkeyed, so the walk or
	                            idle keeps the legs. The student slides 0.45 studs away from the passer over 0.25 s.
	  Shove_Forward             a sprinter hitting them from behind or behind-side: fold, low stagger, rise, look back.
	                            The walk stops and the body is carried about 3 studs along the push, fading out.
	                            The carry and the fold stop short of walls; with no room to fold, it's the twist.
	Players don't collide with students (NHWalkers), so "contact" is the passer's root coming within CONTACT studs.
	MakeWay fires about a second early, so the handler waits for that contact and does nothing if it never comes.
	Each play varies speed and weight, and a student can't be nudged again for COOLDOWN seconds.

	(contact feel, 2026-11-12) The player's client feels the bump too (Controllers.World.ContactFeel) and reports it
	(Features.ContactFeel -> Brain.Contact). Nudges.Remember keeps that impact's speed and direction in the ram memory,
	and Handle with Kind "Contact" plays the reaction at once, so a student reacts to a real bump even when Senses never
	flagged an approach (from behind, standing still, in a crowd). A report that comes in while MakeWay is still waiting
	for the brush ends the wait. A shove carries further the faster the hit (CARRY up to CARRY x CARRY_SCALE, still short
	of walls), and Nudges.OnContact (set by the brain) says the bump line at the moment of contact.

	The clips are published under the group (IDS, 1.86.4). Their source is NH Combat Test's ServerStorage.NHNudges,
	built by tools/npc-nudges/build_nudges.luau. With an id of 0, Studio plays that local KeyframeSequence instead, and
	live servers keep the brain's old step aside.
]]

local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Nav = require(ServerScriptService.Services.AI.Nav)

local Nudges = {}

-- the published animation ids (group 15981569)
local IDS = {
	Nudge_Left = 130323933959810;
	Nudge_Right = 75884392039987;
	Shove_Forward = 102977211838873;
}

local CONTACT = 3          -- studs between roots that counts as a brush
local CROWD_CONTACT = 3.8  -- Space: Senses calls someone within 3.6 for 1.2 s crowding
local WAIT_CONTACT = 1.4   -- how long MakeWay waits for the brush before letting it go
local SHOVE_SPEED = 20     -- a passer this fast (sprinting, dashing) shoves instead of brushing
local SIDE_STEP = 0.45
local SIDE_TIME = 0.25
local CARRY = 3
local CARRY_SCALE = 1.5    -- (contact feel) a hit at SHOVE_SPEED carries CARRY, faster ones up to CARRY x this
local CARRY_TIME = 0.7
local FOLD_REACH = 3       -- the shove's head comes 2.4 studs ahead of the root at the fold (frame 6), plus hair and a margin
local COOLDOWN = 1.5
local RAM_MEMORY = 0.6     -- seconds a player's top speed is remembered (a sprinter who rams and stops dead still shoves)

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

-- each player's top speed (and which way they were going) over the last RAM_MEMORY seconds. Seen is only what the
-- server measured itself (the contact report is checked against it); Recent also takes the reported impacts.
type Ram = { Speed: number, At: number, Dir: Vector3 }
local Recent = {} :: { [Player]: Ram }
local Seen = {} :: { [Player]: Ram }
local function keep(T: { [Player]: Ram }, Pl: Player, Speed: number, Dir: Vector3, Now: number)
	local Last = T[Pl]
	if not Last or Speed >= Last.Speed or Now - Last.At > RAM_MEMORY then
		T[Pl] = { Speed = Speed; At = Now; Dir = Dir }
	end
end
RunService.Heartbeat:Connect(function()
	local Now = os.clock()
	for _, Pl in Players:GetPlayers() do
		local R = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if R and R:IsA(`BasePart`) then
			local V = flat(R.AssemblyLinearVelocity)
			local Dir = if V.Magnitude > 1 then V.Unit else Vector3.zero
			keep(Recent, Pl, V.Magnitude, Dir, Now)
			keep(Seen, Pl, V.Magnitude, Dir, Now)
		end
	end
end)
Players.PlayerRemoving:Connect(function(Pl) Recent[Pl] = nil Seen[Pl] = nil end)

-- (contact feel) the top speed the server itself saw this player move at over the last RAM_MEMORY seconds
function Nudges.TopSpeed(Pl: Player): number
	local S = Seen[Pl]
	return if S and os.clock() - S.At <= RAM_MEMORY then S.Speed else 0
end

-- (contact feel) a bump the player's client felt (already checked by Features.ContactFeel): remember how hard
function Nudges.Remember(Pl: Player, Speed: number, Dir: Vector3)
	local D = flat(Dir)
	keep(Recent, Pl, Speed, if D.Magnitude > 0.1 then D.Unit else Vector3.zero, os.clock())
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
local function filter(S)
	local Ex = { S.Model }
	for _, N in { `Live`, `NHFx`, `NHStudents`, `NHSchedule`, `NHAmbient` } do
		local F = workspace:FindFirstChild(N)
		if F then table.insert(Ex, F) end
	end
	for _, P in Players:GetPlayers() do if P.Character then table.insert(Ex, P.Character) end end
	Params.FilterDescendantsInstances = Ex
end

local function clear(S, Dir: Vector3, Dist: number): boolean
	filter(S)
	local From = S.Root.Position
	if workspace:Raycast(From, Dir * (Dist + 1), Params) then return false end
	local Feet = From - Vector3.new(0, S.Up or (S.Agent and S.Agent.Up) or 3, 0)
	local Floor = Nav.Floor(Feet + Dir * Dist, 1.5)
	return Floor ~= nil and math.abs(Floor.Y - Feet.Y) < 1.2
end

-- how far ahead along Dir is free at waist, chest and head height (up to Max): the shove needs room to fold
local function room(S, Dir: Vector3, Max: number): number
	filter(S)
	local Free = Max
	for _, H in { 0, 1, 1.5 } do
		local From = S.Root.Position + Vector3.new(0, H, 0)
		local Hit = workspace:Raycast(From, Dir * Max, Params)
		if Hit then Free = math.min(Free, flat(Hit.Position - From).Magnitude) end
	end
	-- with the arms out front the body is about 4 studs wide: sweep a box that size too (posts and railings slip
	-- between single rays)
	local At = S.Root.Position + Vector3.new(0, 0.75, 0)
	local Hit = workspace:Blockcast(CFrame.lookAt(At, At + Dir), Vector3.new(4, 3.5, 0.5), Dir * Max, Params)
	if Hit then Free = math.min(Free, Hit.Distance) end
	return Free
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
	-- tests read what was decided at the moment of contact (Studio only)
	if Studio then S.Model:SetAttribute(`NHNudge`, string.format(`%s side %.2f look %s at %.2f`, if OnRight then `Right` else `Left`, Rel:Dot(Right), tostring(Right), os.clock())) end
	T:Play(0.06, math.random(70, 100) / 100, math.random(90, 115) / 100)
	lookAt(S, PasserPos + Vector3.new(0, 1.5, 0), 1.6)
	slide(S, flat(if OnRight then -Right else Right).Unit, SIDE_STEP, SIDE_TIME)
	task.wait(0.35)
end

local function shove(S, Rec, Push: Vector3, Carry: number)
	local T = track(S, `Shove_Forward`)
	if not T then return end
	if S.Agent then S.Agent:Stop() end
	if Studio then S.Model:SetAttribute(`NHNudge`, string.format(`Shove at %.2f`, os.clock())) end
	local Speed = math.random(95, 108) / 100
	T:Play(0.05, 1, Speed)
	S.Model:SetAttribute(`NHMood`, `Startled`)
	slide(S, Push, Carry, CARRY_TIME, Push)
	-- the look back, after the rise (the canvas's F46)
	task.wait(math.max(0, 1.3 / Speed - CARRY_TIME))
	local R = rootOf(Rec)
	if R and S.Model then lookAt(S, R.Position + Vector3.new(0, 1.5, 0), 1.4) end
	if Nudges.OnShove then task.spawn(Nudges.OnShove, S, Rec) end -- (line matrix) the brain's "Shoved" line
	task.wait(0.45 / Speed)
end

-- set by the brain (StudentBrain): called once a shoved student has turned to look back, to say their line
Nudges.OnShove = nil :: ((any, any) -> ())?
-- (contact feel) set by the brain: called the moment contact is made, with the kind, the hit's speed and whether
-- it's a shove (to say the bump line then, not on the approach)
Nudges.OnContact = nil :: ((any, any, string, number, boolean) -> ())?

-- Brain.OnBump: true when the nudge handled it (the brain skips its step aside). Kind: "MakeWay", "Space", or
-- "Contact" (a bump the player's client reported: react now)
function Nudges.Handle(S, Rec, Kind: string): boolean
	if S.Seated or not (S.Model and S.Hum and S.Root and Rec) then return false end
	if os.clock() < (S.NudgeReady or 0) or S.NudgeWaiting then return false end
	if not (idOf(`Nudge_Left`) and idOf(`Nudge_Right`) and idOf(`Shove_Forward`)) then return false end
	local R = rootOf(Rec)
	if not R then return false end
	-- wait for the brush itself (Space: they're already on top of us; Contact: it happened)
	local Until = os.clock() + (if Kind == `MakeWay` then WAIT_CONTACT else 0)
	local Reach = if Kind == `Space` then CROWD_CONTACT elseif Kind == `Contact` then math.huge else CONTACT
	local Dist = flat(R.Position - S.Root.Position).Magnitude
	S.NudgeWaiting = true
	S.NudgeHit = nil
	while Dist > Reach and not S.NudgeHit do
		if os.clock() > Until or not (R.Parent and S.Root.Parent) then S.NudgeWaiting = nil return true end -- no brush: carry on walking
		RunService.Heartbeat:Wait()
		Dist = flat(R.Position - S.Root.Position).Magnitude
	end
	S.NudgeWaiting = nil
	-- a reported bump ended the wait (Brain.Contact): it's who actually hit us
	local Hit = S.NudgeHit
	S.NudgeHit = nil
	if Hit and rootOf(Hit) then
		Rec, R = Hit, rootOf(Hit) :: BasePart
		Dist = flat(R.Position - S.Root.Position).Magnitude
	end
	S.NudgeReady = os.clock() + COOLDOWN + 2
	local V = flat(R.AssemblyLinearVelocity)
	local Look = flat(S.Root.CFrame.LookVector).Unit
	local Away = flat(S.Root.Position - R.Position)
	local Overlap = Away.Magnitude < 1 -- they ran right into us: where they stand says nothing about where they came from
	Away = if Away.Magnitude > 0.1 then Away.Unit else Look
	-- a sprinter who rams us and stops dead still counts: their top speed, and its direction, a moment ago
	local Ram = Rec.Player and Recent[Rec.Player]
	if Ram and os.clock() - Ram.At > RAM_MEMORY then Ram = nil end
	local Speed = math.max(V.Magnitude, Rec.Speed or 0, if Ram then Ram.Speed else 0)
	local Push = if V.Magnitude > 2 then V.Unit elseif Ram and Ram.Dir.Magnitude > 0 then Ram.Dir else Away
	local Behind = Overlap or Away:Dot(Look) > -0.3 -- the passer is behind or beside us
	local Room = if Speed >= SHOVE_SPEED and Push:Dot(Look) > 0.35 and Behind then room(S, Push, CARRY * CARRY_SCALE + FOLD_REACH + 1) else 0
	local Shove = Room >= FOLD_REACH + 0.4
	-- (contact feel) the faster the hit, the further the carry (still short of what's ahead)
	local Carry = math.min(CARRY * math.clamp(Speed / SHOVE_SPEED, 1, CARRY_SCALE), Room - FOLD_REACH)
	if Studio then
		S.Model:SetAttribute(`NHNudgeWhy`, string.format(`%s: speed %.0f, push.look %.2f, behind %s, room %.1f, dist %.1f, carry %.1f`, Kind, Speed, Push:Dot(Look), tostring(Behind), Room, Dist, if Shove then Carry else 0))
	end
	if Nudges.OnContact then task.spawn(Nudges.OnContact, S, Rec, Kind, Speed, Shove) end
	if Shove then
		shove(S, Rec, Push, Carry)
	else -- a brush, or a shove with a wall right ahead (no room to fold forward): the twist
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
