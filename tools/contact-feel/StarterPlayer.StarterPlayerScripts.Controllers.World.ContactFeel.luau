--[[
	ContactFeel (client). Controllers.World.ContactFeel  (contact feel, 2026-11-12; server: Services.Features.ContactFeel)

	Bumping into a background student (a model with NHBrain: Features.Schedules + Services.AI.StudentBrain) feels
	physical. Students stay physics-ghosts for everyone (collision group NHWalkers, CanQuery off: you can't push them
	through walls or have them block doors), so all of this runs on your own client, on your own character.

	They take up space. Each frame, after physics (PostSimulation, so what's drawn is already sorted out), inside RADIUS
	of a student's root (flat distance) you're moved back out along the line between you. An overlap no bigger than one
	frame of your own movement is undone at once (that is the solid stop: your humanoid keeps walking into them and
	gets put back, so you never sink in); a bigger one (they walked into you, or spawned on you) is eased out at
	PUSH_RATE. What's left of your movement along their side carries on, so you slide round them; walking straight at
	them, you're steered to the side you're already a little on (the other side if that one is walled; the push and the
	steer are checked for walls apart, with sphere casts). A push that would go into a wall isn't made, and if
	you're stuck against them (trying to walk but getting nowhere: between two students, or a student and a wall), or
	standing still with one walking into you, for PIN_TIME, they let you through for GHOST_TIME. (Not while an
	impact's slow is on: then being stopped is the point.)
	Seated students are solid too; downed, carried or dead ones aren't.

	Impact, once per student per COOLDOWN, from how fast you were going toward them as you met (v):
	  v < MIN_IMPACT       nothing but the slide
	  brush (to HARD)      you lose BRUSH_SLOW of your speed for BRUSH_TIME, a light camera jolt, a cloth rustle and a
	                       soft thud, and your shoulder twists away (the students' Nudge_Left / Nudge_Right, light)
	  hard (HARD and up)   a near-stop for HARD_TIME, rocked back about a stud, a sharper camera bump, a heavier thud,
	                       the twist at full weight and a short lean back
	The slow is a local WalkSpeed override that keeps to the game's speed writers (the server's Sprint, CombatSpeed,
	stuns): see Local.Slow. The camera jolt is EmitManager.ShakeCamera (it follows the Camera Shake setting); the sounds
	are the game's own (Assets.Sounds), on the effects volume. Reduce Motion skips the lean.

	Each impact is reported to the server (ReplicatedStorage.NHContact.Impact: Model, Speed, Direction), which makes
	the student react to how hard you hit them (Brain.Contact, StudentBrain.Nudges).
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local SoundService = game:GetService(`SoundService`)

local Player = Players.LocalPlayer

local Shared = {}
local Local = {}

---| tuning |---

local FOLDERS = { `NHSchedule`, `NHStudents` } -- where the brain's students live (Combat Test, the Map)
local SCAN_EVERY = 0.5   -- s between looks for students nearby
local SCAN_RANGE = 30    -- studs: a sprinter covers about 20 between looks
local RADIUS = 2.2       -- studs between roots (flat) where the shoulders meet
local RELEASE = 0.6      -- out past RADIUS + this before the same student can be met again
local MAX_DY = 4         -- studs of height between the roots (stairs, a floor above)
local PUSH_RATE = 12     -- 1/s: how fast a big overlap is eased out
local MAX_STEP = 0.35    -- studs a frame, at most, for easing out (a one-frame overlap is undone whatever its size)
local STEER = 0.55       -- head-on, you're steered round them at this share of your WalkSpeed
local HEAD_ON = 0.92     -- dot(walk direction, toward them) above this counts as head-on
local BODY = 1.1         -- studs from your root to your side: the push stops short of walls by this
local PIN_TIME = 0.4     -- s stuck before you're let through
local STUCK = 2          -- studs/s: trying to walk but moving slower than this, in contact, is stuck
local GHOST_TIME = 1.2   -- s a student lets you through after that
local MAX_DT = 1 / 20    -- s: steering, the step back and the stuck timer never take a bigger frame than this
local CAST = 1           -- studs: radius of the wall check's sphere casts (about half your shoulders)

local IMPACTS = true      -- false: the slide only
local MIN_IMPACT = 4
local HARD = 18          -- studs/s: above a walk (14.4, or 12 after a sprint), below a sprint (25 to 40.5)
local COOLDOWN = 0.6
local BRUSH_SLOW, BRUSH_TIME = 0.65, 0.25 -- WalkSpeed x this, for this long
local HARD_SLOW, HARD_TIME = 0.08, 0.3
local FLOOR = 5          -- WalkSpeeds at or below this (stuns, a crawl) are never slowed or restored
local TAIL = 0.3         -- s after a slow ends that an echo of a slowed value is still put right
local ROCK_SPEED, ROCK_TIME = 8, 0.3 -- the hard hit's step back: studs/s at the start, easing to 0 (1.2 studs)
local LEAN, LEAN_IN, LEAN_OUT = math.rad(13), 0.07, 0.33 -- the hard hit's lean back
local REPORT = 4         -- reports a second, at most (the server allows 4)

local IDS = { -- StudentBrain.Nudges' clips (published, R6)
	Nudge_Left = 130323933959810;
	Nudge_Right = 75884392039987;
}

---| state |---

local Cands = {} :: { [Model]: BasePart }   -- students within SCAN_RANGE at the last look
local Touch = {} :: { [Model]: { Side: Vector3? } } -- students we're in contact with
local Cool = {} :: { [Model]: number }       -- no new impact from them until
local Ghost = {} :: { [Model]: number }      -- they let you through until
local PinnedFor = 0
local LastPos = nil :: Vector3?
local NextScan = 0
local Reports = {} :: { number }

local Params = RaycastParams.new()
Params.FilterType = Enum.RaycastFilterType.Exclude
Params.RespectCanCollide = true

local function flat(V: Vector3): Vector3
	return Vector3.new(V.X, 0, V.Z)
end

-- a student we can bump into: alive, not down, not being carried
local function solid(M: Model): boolean
	local H = M:FindFirstChildOfClass(`Humanoid`)
	if not H or H.Health <= 0 or H:GetAttribute(`Downed`) then return false end
	return not (M:GetAttribute(`DownedUntil`) or M:GetAttribute(`Downed`) or M:GetAttribute(`CarriedBy`) or M:GetAttribute(`GrippedBy`))
end

-- you, on your feet and in control of your body
local BUSY_STATES = {
	[Enum.HumanoidStateType.Dead] = true; [Enum.HumanoidStateType.Physics] = true;
	[Enum.HumanoidStateType.Ragdoll] = true; [Enum.HumanoidStateType.FallingDown] = true;
	[Enum.HumanoidStateType.Seated] = true; [Enum.HumanoidStateType.PlatformStanding] = true;
}
local function free(C: Model, Hum: Humanoid, Root: BasePart): boolean
	if Hum.Health <= 0 or Hum.Sit or Hum.PlatformStand or Root.Anchored then return false end
	if Hum:GetAttribute(`Downed`) or C:GetAttribute(`Downed`) or C:GetAttribute(`CarriedBy`) or C:GetAttribute(`GrippedBy`) then return false end
	if C:GetAttribute(`Hidden`) or C:GetAttribute(`SkateboardRiding`) then return false end
	return not BUSY_STATES[Hum:GetState()]
end

function Local.Scan(C: Model, Root: BasePart)
	table.clear(Cands)
	local Ex = { C }
	for _, N in FOLDERS do
		local F = workspace:FindFirstChild(N)
		if F then
			table.insert(Ex, F)
			for _, M in F:GetChildren() do
				if M:IsA(`Model`) and M:GetAttribute(`NHBrain`) == true and solid(M) then
					local R = M:FindFirstChild(`HumanoidRootPart`)
					if R and R:IsA(`BasePart`) and (R.Position - Root.Position).Magnitude < SCAN_RANGE then Cands[M] = R end
				end
			end
		end
	end
	for _, N in { `Live`, `NHFx`, `NHAmbient` } do
		local F = workspace:FindFirstChild(N)
		if F then table.insert(Ex, F) end
	end
	for _, Pl in Players:GetPlayers() do
		if Pl.Character and Pl.Character ~= C then table.insert(Ex, Pl.Character) end -- other players aren't walls
	end
	Params.FilterDescendantsInstances = Ex
	local Now = os.clock()
	for M in Touch do if not Cands[M] then Touch[M] = nil end end
	for M, T in Cool do if T < Now or not M.Parent then Cool[M] = nil end end
	for M, T in Ghost do if T < Now or not M.Parent then Ghost[M] = nil end end
end

-- nothing solid within BODY of your side along Dir: two sphere casts (CAST wide, at the waist and at the knee, so
-- shallow angles and low rims are caught). They start a little behind you, because a cast that starts inside a wall
-- you're already touching doesn't see it.
local function roomFor(Root: BasePart, Dir: Vector3, Dist: number): boolean
	local P = Root.Position - Dir * 0.6
	for _, H in { 0, -1.6 } do
		if workspace:Spherecast(P + Vector3.new(0, H, 0), CAST, Dir * (Dist + BODY - CAST + 0.6), Params) then return false end
	end
	return true
end

---| the slow: a local WalkSpeed override |---

--[[
	The server owns WalkSpeed (Sprint writes 25 / 40.5 / 12, CombatSpeed multiplies, stuns write 0). A value set here
	stays on this client until the server changes it, and the humanoid moves at it (your client simulates you). So:
	  * Raw is the speed the game wants. We write Raw x Factor.
	  * A change we didn't make, above FLOOR, is the game's new speed (a sprint starting or ending): it becomes Raw and
	    is slowed in turn. A value we wrote coming back is an echo (Equip and AnimationController zero WalkSpeed for a
	    frame and put back what they read): ignored. FLOOR and below (a stun, a crawl) is left alone.
	  * At the end Raw goes back, but only if WalkSpeed is still what we wrote; anything else is the game's. For TAIL
	    seconds after that, a value we wrote that comes back (Equip read our slowed value just before the end and puts
	    it back 0.01 s later) is replaced with Raw; a new game speed in that time becomes Raw.
]]
local Slow = nil :: any
local Tail = nil :: RBXScriptConnection?

local function key(V: number): string
	return string.format(`%.3f`, V)
end

function Local.ApplySlow()
	local S = Slow
	if not S or S.Raw <= FLOOR then return end
	local Want = S.Raw * S.Factor
	S.Applied = Want
	S.Wrote[key(Want)] = true
	S.Busy = true
	S.Hum.WalkSpeed = Want
	S.Busy = false
end

function Local.OnSpeed()
	local S = Slow
	if not S or S.Busy then return end
	local W = S.Hum.WalkSpeed
	if W <= FLOOR or S.Wrote[key(W)] then return end
	S.Raw = W
	Local.ApplySlow()
end

function Local.EndTail()
	if Tail then Tail:Disconnect() Tail = nil end
end

function Local.EndSlow()
	local S = Slow
	Slow = nil
	if not S then return end
	S.Conn:Disconnect()
	local Hum = S.Hum
	if not Hum.Parent then return end
	if S.Applied and math.abs(Hum.WalkSpeed - S.Applied) < 1e-3 then Hum.WalkSpeed = S.Raw end
	Local.EndTail()
	local Raw = S.Raw
	local Conn
	Conn = Hum:GetPropertyChangedSignal(`WalkSpeed`):Connect(function()
		local W = Hum.WalkSpeed
		if S.Wrote[key(W)] and key(W) ~= key(Raw) then
			Hum.WalkSpeed = Raw -- our slowed value put back by someone who read it during the slow
		elseif W > FLOOR then
			Raw = W -- the game's own new speed
		end
	end)
	Tail = Conn
	task.delay(TAIL, function()
		Conn:Disconnect()
		if Tail == Conn then Tail = nil end
	end)
end

function Local.Slow(Hum: Humanoid, Factor: number, Seconds: number)
	local Now = os.clock()
	if Slow and Slow.Hum ~= Hum then Local.EndSlow() end
	if Slow then
		Slow.Factor = math.min(Slow.Factor, Factor) -- a hard hit during a brush wins
		Slow.Until = math.max(Slow.Until, Now + Seconds)
	else
		Local.EndTail() -- a new slow takes over from the last one's tail
		if Hum.WalkSpeed <= FLOOR then return end
		Slow = { Hum = Hum; Raw = Hum.WalkSpeed; Factor = Factor; Until = Now + Seconds; Wrote = {} }
		Slow.Conn = Hum:GetPropertyChangedSignal(`WalkSpeed`):Connect(Local.OnSpeed)
	end
	Local.ApplySlow()
end

---| what you feel |---

local Tracks = {} :: { [string]: AnimationTrack }
local TracksFor = nil :: Humanoid?

local function track(Hum: Humanoid, Name: string): AnimationTrack?
	if TracksFor ~= Hum then table.clear(Tracks) TracksFor = Hum end
	if Tracks[Name] then return Tracks[Name] end
	local Animator = Hum:FindFirstChildOfClass(`Animator`)
	if not (Animator and IDS[Name]) then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{IDS[Name]}`
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not (Ok and T) then return nil end
	T.Looped = false
	T.Priority = Enum.AnimationPriority.Action
	Tracks[Name] = T
	return T
end

local function sound(Root: BasePart, Path: { string }, Volume: number, Pitch: number, Cut: number?)
	local S = ReplicatedStorage:FindFirstChild(`Assets`)
	for _, N in Path do S = S and S:FindFirstChild(N) end
	if not (S and S:IsA(`Sound`)) then return end
	local C = S:Clone()
	C.Volume = Volume
	C.PlaybackSpeed = Pitch
	C.Looped = false
	local Master = SoundService:FindFirstChild(`NH_Master`)
	local Fx = Master and Master:FindFirstChild(`NH_Effects`)
	if Fx and Fx:IsA(`SoundGroup`) then C.SoundGroup = Fx end
	C.Parent = Root
	C:Play()
	task.delay(Cut or 2, function() C:Destroy() end)
end

local Lean = nil :: any -- { At, Joint, Prev?, Wrote? }
local Rock = nil :: { At: number, Dir: Vector3 }?

local function shake(Intensity: number, Fade: number)
	pcall(function()
		require(ReplicatedStorage.Functions.EmitManager).ShakeCamera(Intensity, 10, 0, Fade)
	end)
end

function Local.Impact(M: Model, R: BasePart, Speed: number, N: Vector3, VH: Vector3, Hum: Humanoid, Root: BasePart)
	if not IMPACTS then return end
	local Now = os.clock()
	if Now < (Cool[M] or 0) then return end
	Cool[M] = Now + COOLDOWN
	if Speed < MIN_IMPACT then return end
	local Hard = Speed >= HARD
	local K = math.clamp((Speed - MIN_IMPACT) / (40 - MIN_IMPACT), 0, 1) -- 0 a slow brush .. 1 a full sprint
	local Reduced = Player:GetAttribute(`NHReducedMotion`) == true

	Local.Slow(Hum, if Hard then HARD_SLOW else BRUSH_SLOW, if Hard then HARD_TIME else BRUSH_TIME)
	if Hard then
		shake(2.2 + K * 1.6, 0.4)
		sound(Root, { `Sounds`, `Movement`, `Land` }, 0.45 + K * 0.35, 0.78, 1.5)
		sound(Root, { `Sounds`, `SwingSFX`, `Blunt`, `Swing` }, 0.35, 0.65, 0.6)
		Rock = { At = Now; Dir = N }
		if not Reduced then
			local J = Root:FindFirstChild(`RootJoint`)
			if J and J:IsA(`Motor6D`) then Lean = { At = Now; Joint = J } end
		end
	else
		shake(0.7 + K * 1.2, 0.25)
		sound(Root, { `Sounds`, `Movement`, `Land` }, 0.18 + K * 0.3, 0.95, 1.5)
		sound(Root, { `Sounds`, `SwingSFX`, `Blunt`, `Swing` }, 0.22 + K * 0.15, 0.6, 0.6)
	end
	-- the shoulder that met them twists away
	local OnRight = flat(R.Position - Root.Position):Dot(Root.CFrame.RightVector) > 0
	local T = track(Hum, if OnRight then `Nudge_Right` else `Nudge_Left`)
	if T then
		if Hard then T:Play(0.05, 1, 1.05) else T:Play(0.06, 0.45 + K * 0.3, 1.2) end
	end

	-- tell the server (the student reacts to how hard)
	local Remote = ReplicatedStorage:FindFirstChild(`NHContact`)
	Remote = Remote and Remote:FindFirstChild(`Impact`)
	if Remote and Remote:IsA(`RemoteEvent`) then
		while Reports[1] and Now - Reports[1] > 1 do table.remove(Reports, 1) end
		if #Reports < REPORT then
			table.insert(Reports, Now)
			Remote:FireServer(M, Speed, if VH.Magnitude > 1 then VH.Unit else -N)
		end
	end
end

-- the hard hit's step back (after physics, eased out)
function Local.Rock(Dt: number, Root: BasePart)
	if not Rock then return end
	local A = (os.clock() - Rock.At) / ROCK_TIME
	if A >= 1 then
		Rock = nil
	else
		local Step = ROCK_SPEED * (1 - A) * math.min(Dt, MAX_DT)
		if roomFor(Root, Rock.Dir, Step) then Root.CFrame += Rock.Dir * Step end
	end
end

-- the hard hit's lean back (before physics: the Animator has written this frame's pose, the joints aren't solved yet)
function Local.Lean()
	local Now = os.clock()
	if Lean then
		local T = Now - Lean.At
		local J = Lean.Joint
		-- the Animator rewrites Transform each frame while a clip keys the joint; if it didn't this frame, take our last
		-- lean back off first so it never adds up
		local Base = J.Transform
		if Lean.Wrote and Lean.Prev and Base == Lean.Wrote then Base = Lean.Prev end
		if T >= LEAN_IN + LEAN_OUT or not J.Parent then
			if Lean.Wrote and J.Transform == Lean.Wrote then J.Transform = Base end
			Lean = nil
		else
			local W = if T < LEAN_IN then math.sin(T / LEAN_IN * math.pi / 2) else 0.5 + 0.5 * math.cos((T - LEAN_IN) / LEAN_OUT * math.pi)
			local C0 = J.C0.Rotation
			-- rotate the torso about the root's right axis, top going back (root space: +X right, -Z forward)
			local Out = C0:Inverse() * CFrame.Angles(LEAN * W, 0, 0) * C0 * Base
			J.Transform = Out
			Lean.Prev, Lean.Wrote = Base, Out
		end
	end
end

---| each frame |---

function Local.Step(Dt: number)
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`)
	if Slow and (os.clock() >= Slow.Until or Slow.Hum ~= Hum) then Local.EndSlow() end
	if not (C and Hum and Root and Root:IsA(`BasePart`)) or not free(C, Hum, Root) then
		table.clear(Touch)
		PinnedFor = 0
		Rock, Lean = nil, nil
		return
	end
	local Now = os.clock()
	if Now >= NextScan then
		NextScan = Now + SCAN_EVERY
		Local.Scan(C, Root)
	end

	local P = Root.Position
	local VH = flat(Root.AssemblyLinearVelocity)
	local Move = flat(Hum.MoveDirection)
	local Push, Steer = Vector3.zero, Vector3.zero
	local Depth = 0
	local Hits = {} :: { Model }
	local Steering = {} :: { any }
	local Frame = VH.Magnitude * Dt * 1.25 + 0.05 -- an overlap this small is this frame's own step in: undone at once
	-- a teleport (or a respawn) that lands you on a student isn't a bump: no impact, just the push out
	local Jumped = LastPos ~= nil and flat(P - LastPos).Magnitude > math.max(4, Frame * 3)
	for M, R in Cands do
		if not R.Parent or (Ghost[M] and Now < Ghost[M]) then Touch[M] = nil continue end
		local Q = R.Position
		local D = Vector3.new(P.X - Q.X, 0, P.Z - Q.Z)
		local Dist = D.Magnitude
		if Dist > RADIUS + RELEASE or math.abs(Q.Y - P.Y) > MAX_DY then Touch[M] = nil continue end
		if Dist >= RADIUS then continue end
		local N = if Dist > 1e-3 then D / Dist elseif VH.Magnitude > 0.1 then -VH.Unit else -flat(Root.CFrame.LookVector).Unit
		local Into = -VH:Dot(N) -- your speed toward them
		local T = Touch[M]
		if not T then
			T = {}
			Touch[M] = T
			if not Jumped then Local.Impact(M, R, math.max(Into, 0), N, VH, Hum, Root) end
		end
		table.insert(Hits, M)
		local Over = RADIUS - Dist
		local Out = if Over <= Frame then Over else math.max(Frame, math.min(Over * PUSH_RATE * Dt, MAX_STEP))
		Push += N * Out
		Depth += Out
		-- head-on: steer round them, to the side you're already a little on (kept while in contact)
		if Move.Magnitude > 0.1 and Move.Unit:Dot(-N) > HEAD_ON then
			if not T.Side then
				local Lateral = D - Move.Unit * D:Dot(Move.Unit)
				T.Side = if Lateral.Magnitude > 0.05 then Lateral.Unit else flat(Root.CFrame.RightVector).Unit
				T.Flips = 0
			end
			if T.Flips <= 2 then
				Steer += T.Side * Hum.WalkSpeed * STEER
				table.insert(Steering, T)
			end
		end
	end
	if #Hits > 0 then
		-- the push out and the steer are checked for walls apart: a walled steer must not cancel the push
		local Blocked = false
		if Push.Magnitude > 1e-4 then
			if roomFor(Root, Push.Unit, Push.Magnitude) then
				Root.CFrame += Push
			else
				Blocked = true
			end
		end
		local Step = Steer * math.min(Dt, MAX_DT)
		if Step.Magnitude > 1e-4 then
			if roomFor(Root, Step.Unit, Step.Magnitude) then
				Root.CFrame += Step
			else
				-- that side is walled: go round the other way (twice at most, then the stuck rule lets you through)
				for _, T in Steering do T.Side = -T.Side T.Flips += 1 end
			end
		end
		-- pinned: the push can't be made (a wall), you're walking but getting nowhere (two students, a student and a
		-- wall), or one keeps walking into you while you stand there (they'd shove you along their whole path)
		local Progress = if LastPos then flat(Root.Position - LastPos).Magnitude / math.max(Dt, 1e-3) else math.huge
		local Pinned = Blocked or (Move.Magnitude > 0.1 and Progress < STUCK) or (Move.Magnitude < 0.1 and Depth > Frame)
		PinnedFor = if Pinned and not Slow then PinnedFor + math.min(Dt, MAX_DT) else 0
		if PinnedFor > PIN_TIME then
			for _, M in Hits do Ghost[M] = Now + GHOST_TIME Touch[M] = nil end
			PinnedFor = 0
		end
	else
		PinnedFor = 0
	end
	Local.Rock(Dt, Root)
	LastPos = Root.Position
end

local function guard(F: (number) -> ())
	return function(Dt: number)
		local Ok, Err = pcall(F, Dt)
		if not Ok and not Local.Warned then
			Local.Warned = true
			warn(`[ContactFeel] {Err}`)
		end
	end
end

function Shared.OnStart()
	RunService.PreSimulation:Connect(guard(Local.Lean))
	RunService.PostSimulation:Connect(guard(Local.Step))
	Player.CharacterRemoving:Connect(function()
		Local.EndSlow()
		Local.EndTail()
		table.clear(Touch)
		Rock, Lean = nil, nil
		NextScan, LastPos, PinnedFor = 0, nil, 0 -- the new character gets a fresh look and ray filter at once
	end)
end

return Shared
