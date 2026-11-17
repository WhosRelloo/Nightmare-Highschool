--[[
	Cine director (client, Phase 1 / 2.24.0). Controllers.Cine. Spec: docs/expansion/04-Cinematic-Framework.md.
	The server (Services.World.Cine) says when; this plays it. Remote: ReplicatedStorage.NHCine.

	A cut is a module in ReplicatedStorage.Cinematics.<Id> (data plus a Build function):
		Set     the set it's staged on: workspace.NHCineSets.<Set> holds named marks (Parts). Each place has its own set,
		        so the same cut ports to the Map by placing the same marks in the real rooms.
		Actors  { Name, From = "Self" | "Npc:<Config.Npcs id>", Mark, Pose, Color? }: client-side clones on marks. The
		        player appears as a local clone; their real character stays where it is (hidden on this screen only).
		Build(Ctx) -> { shots = { Cine shots }, events = { timed director events }, duration? }
	The shot list is played by ReplicatedStorage.Cine (the cinematic toolkit's shot player: sizes, lenses, moves,
	handheld noise, DOF, grade). The camera is only ever taken through CameraLease ("Cine").

	Director events (t in seconds from the start): say = { who, text, expr?, dur? } (subtitle + talking face),
	pose = { who, ...angles, speed? }, look = { who, at = actor | mark | "Camera" | false }, walk = { who, to = mark, dur },
	bell = true, sound = { id, volume?, speed? }, card = { title, sub?, dur }, veil = { alpha, dur }, call = fn(Ctx).
	Poses (R6, radians, eased): RS / LS / RH / LH = arm or leg forward, Lean (torso pitch), Twist (torso yaw),
	Yaw / Pitch (head). Every actor breathes and drifts a little: nobody is ever dead still.

	Reduce Motion: moves become cuts (each moving shot holds its last framing), no handheld noise, no Dutch roll.
	Shared.Replay(Id) asks the server to play a seen cut again (the journal's "Watch again").
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Cine`))
local CameraLease = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CameraLease`))
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))

local Player = Players.LocalPlayer
local LEASE = `Cine`
local LETTERBOX = 2.28 -- the frame the bars leave on 16:9 (CineUI's 11% bars): shots are framed for it

local Shared = {}
local Local = {}
local Current = nil -- the cut playing now
local Remote: RemoteEvent? = nil

local function UI() return require(script.Parent:WaitForChild(`Gui`):WaitForChild(`CineUI`)) end
local function CineLib() return require(ReplicatedStorage:WaitForChild(`Cine`)) end
local function FaceTalk()
	local Ok, M = pcall(function() return require(script.Parent:WaitForChild(`Character`):WaitForChild(`FaceTalk`)) end)
	return if Ok then M else nil
end

function Local.HoldHour(Hour: number?)
	local Ok = pcall(function()
		require(script.Parent:WaitForChild(`World`):WaitForChild(`DayCycle`)).HoldHour(`Cine`, Hour)
	end)
	if not Ok and Hour then pcall(function() game:GetService(`Lighting`).ClockTime = Hour end) end
end

local function reduced(): boolean
	local Ok, R = pcall(Kit.ReducedMotion)
	return Ok and R == true
end

local function send(Message)
	if Remote then Remote:FireServer(Message) end
end

---| waiting for the school (ENTER SCHOOL: the menu finishes, you respawn) |---

function Local.Ready(Timeout: number): boolean
	local T0 = os.clock()
	while os.clock() - T0 < Timeout do
		local C = Player.Character
		local Cam = workspace.CurrentCamera
		if Player:GetAttribute(`InMainMenu`) ~= true and C and C.Parent and not C:GetAttribute(`MenuPlaced`)
			and C:FindFirstChild(`HumanoidRootPart`) and Cam and Cam.CameraType == Enum.CameraType.Custom then
			return true
		end
		task.wait(0.1)
	end
	return Player:GetAttribute(`InMainMenu`) ~= true and Player.Character ~= nil
end

---| the world behind the cut: everyone else is hidden on this screen while it plays |---

function Local.HideLive(Cut)
	Cut.HiddenParts = {}
	Cut.HiddenGuis = {}
	local function hide(D: Instance)
		-- a deferred hide that lands after the cut ended (ShowLive cleared the tables) does nothing
		if not (Cut.Live and Cut.HiddenParts and Cut.HiddenGuis) then return end
		if D:IsA(`BasePart`) or D:IsA(`Decal`) then
			if Cut.HiddenParts[D] == nil then Cut.HiddenParts[D] = (D :: any).LocalTransparencyModifier end
			;(D :: any).LocalTransparencyModifier = 1
		elseif D:IsA(`BillboardGui`) or D:IsA(`SurfaceGui`) then
			if Cut.HiddenGuis[D] == nil then Cut.HiddenGuis[D] = (D :: any).Enabled end
			;(D :: any).Enabled = false
		end
	end
	-- every body in the world that isn't one of the cut's actors: players, the cast (Live), background students
	-- (NHAmbient), the class in session (NHSchedule), substitutes, shopkeepers, dummies... wherever they're kept
	local Live = workspace:FindFirstChild(`Live`)
	local Roots = {} :: { Instance }
	local Seen = {} :: { [Instance]: boolean }
	local function add(R: Instance?)
		if not R or Seen[R] or (Cut.Folder and R:IsDescendantOf(Cut.Folder)) then return end
		Seen[R] = true
		table.insert(Roots, R)
	end
	add(Live)
	for _, P in Players:GetPlayers() do add(P.Character) end
	for _, D in workspace:GetDescendants() do
		if D:IsA(`Humanoid`) and D.Parent and not (Live and D:IsDescendantOf(Live)) then add(D.Parent) end
	end
	local function watch(R: Instance)
		for _, D in R:GetDescendants() do hide(D) end
		table.insert(Cut.Conns, R.DescendantAdded:Connect(function(D) if Cut.Live then task.defer(hide, D) end end))
	end
	for _, R in Roots do watch(R) end
	-- someone who turns up mid-cut (a class changing over, a respawn) is hidden too
	table.insert(Cut.Conns, workspace.DescendantAdded:Connect(function(D)
		if not Cut.Live or not D:IsA(`Humanoid`) then return end
		task.defer(function()
			local M = D.Parent
			if M and not Seen[M] and not (Cut.Folder and M:IsDescendantOf(Cut.Folder)) and not (Live and M:IsDescendantOf(Live)) then
				Seen[M] = true
				watch(M)
			end
		end)
	end))
end

function Local.ShowLive(Cut)
	for D, V in Cut.HiddenParts or {} do if D.Parent then pcall(function() (D :: any).LocalTransparencyModifier = V end) end end
	for D, V in Cut.HiddenGuis or {} do if D.Parent then pcall(function() (D :: any).Enabled = V end) end end
	Cut.HiddenParts, Cut.HiddenGuis = nil, nil
end

---| actors: client-side clones on marks |---

-- From: "Self" | "Npc:<Config.Npcs id>" | "Watcher:<Config.Stealth zone>" | "Ambient" (a background student from
-- workspace.NHAmbient, a different one per actor), or a list of these tried in order (the Custodian is at his day post
-- by day and the Records Office watcher at night)
function Local.SourceFor(Cut, From: any): Model?
	if typeof(From) == `table` then
		for _, One in From do
			local M = Local.SourceFor(Cut, One)
			if M then return M end
		end
		return nil
	end
	if typeof(From) ~= `string` then return nil end
	if From == `Self` then return Player.Character end
	local Live = workspace:FindFirstChild(`Live`) or workspace
	local NpcId = From:match(`^Npc:(.+)$`)
	if NpcId then
		local Best = nil
		for _, M in Live:GetChildren() do
			if M:IsA(`Model`) and M:GetAttribute(`NpcId`) == NpcId and M:FindFirstChildOfClass(`Humanoid`) then
				Best = M
				if M:GetAttribute(`Role`) == `Leader` then break end -- the talkable one (Social.Npcs) over a watcher
			end
		end
		return Best
	end
	local Zone = From:match(`^Watcher:(.+)$`)
	if Zone then
		for _, M in Live:GetChildren() do
			if M:IsA(`Model`) and M:GetAttribute(`Role`) == `Watcher` and M:GetAttribute(`WatcherZone`) == Zone then return M end
		end
		return nil
	end
	if From == `Ambient` then
		local Folder = workspace:FindFirstChild(`NHAmbient`)
		if not Folder then return nil end
		-- standing or sitting students only (not the barber's customer, the sprawled one or the gym)
		local Pool = {}
		for _, M in Folder:GetChildren() do
			if M:IsA(`Model`) and M:FindFirstChild(`Torso`) and M:FindFirstChild(`HumanoidRootPart`) and not Cut.Used[M] then
				table.insert(Pool, M)
			end
		end
		table.sort(Pool, function(A, B) return A:GetFullName() < B:GetFullName() end) -- the same faces each replay
		return Pool[1]
	end
	return nil
end

-- (the Animator stays: actors play the game's own clips, e.g. the Default walk)
local STRIP = { `Script`, `LocalScript`, `ProximityPrompt`, `BillboardGui`, `ForceField`, `Tool`, `Sound`,
	`BodyMover`, `AlignPosition`, `AlignOrientation`, `LinearVelocity`, `AngularVelocity`, `VectorForce` }

-- the game's unarmed walk (what every NPC walks with: AI.AI.Animate), and the pace it covers at 1x
local WALK_PACE = 5.3
local function walkAnim(): Animation?
	local Ok, A = pcall(function() return ReplicatedStorage.Assets.Animations.Default.Movement.Walk end)
	return if Ok and A and A:IsA(`Animation`) then A else nil
end

function Local.MakeActor(Cut, Spec)
	Cut.Used = Cut.Used or {}
	local Src = Local.SourceFor(Cut, Spec.From)
	if not Src then return nil end
	Cut.Used[Src] = true
	local WasArchivable = Src.Archivable
	Src.Archivable = true
	local Ok, M = pcall(function() return Src:Clone() end)
	Src.Archivable = WasArchivable
	if not (Ok and M) then return nil end
	for _, D in M:GetDescendants() do
		if not D.Parent then continue end -- already gone with an ancestor
		-- props carried along with a background student (the gym kid's barbell): only the body and what it wears stay
		if D:IsA(`Model`) and not D:FindFirstAncestorWhichIsA(`Accessory`) then D:Destroy() continue end
		for _, Class in STRIP do
			if D:IsA(Class) then D:Destroy() break end
		end
	end
	M.Name = `CineActor_{Spec.Name}`
	for _, D in M:GetDescendants() do
		if D:IsA(`BasePart`) then
			D.Anchored = D.Name == `HumanoidRootPart`
			D.CanCollide = false
			D.CanQuery = false
			D.CanTouch = false
			D.LocalTransparencyModifier = 0
		end
	end
	local Hum = M:FindFirstChildOfClass(`Humanoid`)
	if Hum then
		Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		pcall(function() Hum.EvaluateStateMachine = false end)
		Hum.PlatformStand = true
		-- a fresh Animator: the source's own tracks (a sitting loop, a gym rep) must not come along
		local Old = Hum:FindFirstChildOfClass(`Animator`)
		if Old then Old:Destroy() end
		Instance.new(`Animator`).Parent = Hum
	end
	for _, Attr in { `NHInCine`, `NH_Evolving`, `Protected`, `Presence`, `Departing` } do M:SetAttribute(Attr, nil) end
	-- a face nobody sees (the Night Custodian): whichever body the clone came from, the painted face goes and the head
	-- sits in shadow (as NpcLooks.Shadow does for his day post)
	if Spec.Faceless or Src:GetAttribute(`NHFaceless`) then
		local Head = M:FindFirstChild(`Head`)
		if Head and Head:IsA(`BasePart`) then
			for _, D in Head:GetDescendants() do
				if D:IsA(`Decal`) then D.Transparency = 1 elseif D:IsA(`SurfaceGui`) then D.Enabled = false end
			end
			Head.Color = Color3.fromRGB(28, 26, 30)
		end
	end
	local Torso = M:FindFirstChild(`Torso`)
	local Root = M:FindFirstChild(`HumanoidRootPart`)
	if not (Torso and Root) then M:Destroy() return nil end
	local A = {
		Name = Spec.Name; Model = M; Root = Root; Torso = Torso; Head = M:FindFirstChild(`Head`); Src = Src;
		Display = Spec.Display or (if Spec.From == `Self` then `You` else (Src:GetAttribute(`NpcId`) and Src.Name) or Spec.Name);
		Color = Spec.Color;
		J = {
			Neck = Torso:FindFirstChild(`Neck`); RS = Torso:FindFirstChild(`Right Shoulder`); LS = Torso:FindFirstChild(`Left Shoulder`);
			RH = Torso:FindFirstChild(`Right Hip`); LH = Torso:FindFirstChild(`Left Hip`); Root = Root:FindFirstChild(`RootJoint`);
		};
		Cur = {}; Target = {}; Speed = 6; Seed = math.random() * 100; Walk = nil; LookAt = nil;
	}
	local Mark = Spec.Mark and Cut.Ctx.Mark(Spec.Mark)
	A.Base = if Mark then Mark.CFrame else Root.CFrame
	Local.SetPose(A, Spec.Pose or `Stand`, 100)
	A.Root.CFrame = Local.RootFor(A, A.Base)
	M.Parent = Cut.Folder
	return A
end

-- named poses (R6, radians): what each joint does, before the life layer
local POSES = {
	Stand = { RS = 0.05; LS = 0.05; RH = 0; LH = 0; Lean = 0; Twist = 0; Yaw = 0; Pitch = 0 };
	Sit = { RS = 0.55; LS = 0.5; RH = 1.57; LH = 1.57; Lean = 0.08; Twist = 0; Yaw = 0; Pitch = -0.05 };
	SitHands = { RS = 0.95; LS = 0.9; RH = 1.57; LH = 1.57; Lean = 0.16; Twist = 0; Yaw = 0; Pitch = 0.08 };
	-- reading from a register held at the chest: eyes down, but the face still reads to a camera at eye height
	Read = { RS = 0.85; LS = 0.55; RH = 0; LH = 0.04; Lean = 0.05; Twist = 0.08; Yaw = -0.05; Pitch = 0.12 };
	Hold = { RS = 1.0; LS = 0.95; RH = 0; LH = 0; Lean = 0.12; Twist = 0; Yaw = 0; Pitch = 0.42 };
}
Shared.POSES = POSES

function Local.SetPose(A, Pose, Speed: number?)
	local Base = if typeof(Pose) == `string` then POSES[Pose] else nil
	if Base then
		A.PoseName = Pose
		for K, V in Base do A.Target[K] = V end
	elseif typeof(Pose) == `table` then
		for K, V in Pose do if typeof(V) == `number` then A.Target[K] = V end end
	end
	if Speed and Speed >= 100 then for K, V in A.Target do A.Cur[K] = V end end
	A.Speed = Speed or 6
end

-- where the root goes for a mark. A standing mark is on the floor (the root is 3 studs up); a seat mark is on the top of
-- the seat (R6 sitting: the hips 1 below the root, the thighs' underside half a stud below that). Set marks at seats
-- carry the attribute Seat = true; an actor walking off a seat to a floor mark changes pose on the way.
function Local.RootFor(A, Mark: CFrame): CFrame
	-- the height follows the legs, not the pose's name: thighs level (hips at 90 degrees) = seated (1.5 over the seat),
	-- legs straight = standing (3 over the floor), and in between while getting up or sitting down, so the body never
	-- pops up or sinks through the chair
	local Hips = ((A.Cur.RH or 0) + (A.Cur.LH or 0)) / 2
	local Seated = math.clamp(Hips / 1.57, 0, 1)
	return Mark * CFrame.new(0, 3 + (1.5 - 3) * Seated, 0)
end

-- a walk plays the game's own walk clip (owner: reuse existing animations). Its rate is set every frame from how fast
-- the actor is really moving (the walk eases in and out), so the feet stay planted instead of skating
function Local.WalkClip(A, Delta: Vector3, Dur: number)
	local Anim = walkAnim()
	local Hum = A.Model:FindFirstChildOfClass(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	-- a step or two (getting up out of a chair into the aisle) stays on the pose layer, which blends out of the seated
	-- pose; the clip is for real walks
	if not (Anim and Animator) or Delta.Magnitude < 4 then return end
	if not A.WalkTrack then
		local Ok, Track = pcall(function() return Animator:LoadAnimation(Anim) end)
		if not Ok or not Track then return end
		Track.Looped = true
		Track.Priority = Enum.AnimationPriority.Movement
		A.WalkTrack = Track
	end
	A.WalkDist = Delta.Magnitude
	A.WalkTrack:Play(0.2, 1, 0.05)
end

function Local.StopWalkClip(A)
	if A.WalkTrack and A.WalkTrack.IsPlaying then A.WalkTrack:Stop(0.25) end
end

local AXIS = { RS = 1; LS = -1; RH = 1; LH = -1 }

function Local.StepActor(A, Dt: number, Clock: number, Cam: Camera)
	local K = 1 - math.exp(-Dt * A.Speed)
	for Key, V in A.Target do
		local C = A.Cur[Key] or V
		A.Cur[Key] = C + (V - C) * K
	end
	local P = A.Cur
	-- life: a 4 s breath, a slow weight drift, small head drift (owner's style: never dead still)
	local Breath = math.sin((Clock + A.Seed) * math.pi / 2) * 0.012
	local Drift = math.noise(Clock * 0.35, A.Seed, 0) * 0.025
	local HeadDrift = math.noise(Clock * 0.5, A.Seed, 3) * 0.05
	local Yaw, Pitch = P.Yaw or 0, P.Pitch or 0
	-- looking at someone: the head turns (up to 70 degrees), the torso follows a little
	local LookTwist = 0
	if A.LookAt then
		local Target = nil
		if A.LookAt == `Camera` then Target = Cam.CFrame.Position
		elseif typeof(A.LookAt) == `Instance` then
			local H = A.LookAt:IsA(`Model`) and (A.LookAt:FindFirstChild(`Head`) or A.LookAt.PrimaryPart) or A.LookAt
			Target = H and (H :: BasePart).Position
		elseif typeof(A.LookAt) == `Vector3` then Target = A.LookAt end
		if Target and A.Head then
			local Rel = A.Torso.CFrame:PointToObjectSpace(Target)
			local Want = math.clamp(math.atan2(-Rel.X, -Rel.Z), -1.2, 1.2)
			local Up = math.clamp(math.atan2(Rel.Y - 1.5, math.sqrt(Rel.X ^ 2 + Rel.Z ^ 2)), -0.6, 0.5)
			A.LookYaw = (A.LookYaw or 0) + (Want - (A.LookYaw or 0)) * K
			A.LookPitch = (A.LookPitch or 0) + (Up - (A.LookPitch or 0)) * K
		end
	else
		A.LookYaw = (A.LookYaw or 0) * (1 - K)
		A.LookPitch = (A.LookPitch or 0) * (1 - K)
	end
	Yaw += (A.LookYaw or 0) * 0.8
	Pitch -= (A.LookPitch or 0)
	LookTwist = (A.LookYaw or 0) * 0.2
	-- walking: the root travels, limbs swing, the body bobs
	local Swing, Bob = 0, 0
	local Clip = A.WalkTrack ~= nil and A.WalkTrack.IsPlaying
	if A.Walk then
		local W = A.Walk
		local U = math.clamp((Clock - W.T0) / W.Dur, 0, 1)
		local E = U * U * (3 - 2 * U)
		A.Base = W.From:Lerp(W.To, E)
		if Clip and A.WalkDist then
			-- the clip's rate = the real speed (smoothstep's slope 6u(1-u)) over the pace it covers at 1x
			local Speed = A.WalkDist * 6 * U * (1 - U) / W.Dur
			A.WalkTrack:AdjustSpeed(math.max(0.05, Speed / WALK_PACE))
		elseif not Clip then
			-- no clip available: a stride matched to distance so the feet don't skate (2.1 studs per step)
			local Phase = (A.Base.Position - W.From.Position).Magnitude / 2.1 * math.pi
			local Amt = math.sin(math.min(U, 1 - U, 0.2) / 0.2 * math.pi / 2)
			Swing = math.sin(Phase) * 0.55 * Amt
			Bob = math.abs(math.cos(Phase)) * 0.12 * Amt
		end
		if U >= 1 then A.Walk = nil Local.StopWalkClip(A) end
	end
	A.Root.CFrame = Local.RootFor(A, A.Base) * CFrame.new(0, Bob - 0.06 * Breath, 0)
	-- while the walk clip plays it owns the limbs and the hips; only the head's look is ours
	if Clip then
		if A.J.Neck then A.J.Neck.Transform = CFrame.Angles(-(Pitch + Breath * 0.5), 0, Yaw + HeadDrift) end
		return
	end
	local J = A.J
	if J.RS then J.RS.Transform = CFrame.Angles(0, 0, AXIS.RS * ((P.RS or 0) + Swing + Breath)) end
	if J.LS then J.LS.Transform = CFrame.Angles(0, 0, AXIS.LS * ((P.LS or 0) - Swing + Breath)) end
	if J.RH then J.RH.Transform = CFrame.Angles(0, 0, AXIS.RH * ((P.RH or 0) - Swing)) end
	if J.LH then J.LH.Transform = CFrame.Angles(0, 0, AXIS.LH * ((P.LH or 0) + Swing)) end
	if J.Root then J.Root.Transform = CFrame.Angles(-((P.Lean or 0) + Breath + Drift * 0.3), 0, (P.Twist or 0) + LookTwist + Drift) end
	if J.Neck then J.Neck.Transform = CFrame.Angles(-(Pitch + Breath * 0.5), 0, Yaw + HeadDrift) end
end

---| props for the cuts |---

function Local.Prop(Cut, Name: string, Props, Parent: Instance?)
	local P = Instance.new(`Part`)
	P.Name = `CineProp_{Name}`
	P.CanCollide = false
	P.CanQuery = false
	P.CanTouch = false
	P.Anchored = true
	for K, V in Props or {} do (P :: any)[K] = V end
	P.Parent = Parent or Cut.Folder
	return P
end

-- a prop held in an actor's hand (the register, Mira's file)
function Local.Hold(Cut, A, Name: string, Size: Vector3, Color: Color3, Offset: CFrame)
	local Arm = A and A.Model:FindFirstChild(`Right Arm`)
	if not Arm then return nil end
	local P = Local.Prop(Cut, Name, { Size = Size; Color = Color; Material = Enum.Material.Fabric; Anchored = false; Massless = true })
	P.CFrame = Arm.CFrame * Offset
	local W = Instance.new(`Weld`)
	W.Part0 = Arm
	W.Part1 = P
	W.C0 = Offset
	W.Parent = P
	return P
end

---| events |---

function Local.Fire(Cut, E)
	local Ctx = Cut.Ctx
	if E.say then
		local S = E.say
		local A = Cut.Actors[S.who]
		local Text = if typeof(S.text) == `function` then S.text(Ctx) else S.text
		local Dur = S.dur or math.clamp(#Text / 14 + 0.8, 1.4, 5)
		pcall(function() UI().Subtitle(S.name or (A and A.Display) or S.who, Text, Dur, (A and A.Color) or S.color) end)
		local FT = FaceTalk()
		if FT and A and FT.Say then pcall(FT.Say, A.Model, Text, S.expr) end
	end
	if E.pose then
		local A = Cut.Actors[E.pose.who]
		if A then Local.SetPose(A, E.pose.name or E.pose, E.pose.speed) end
	end
	if E.look then
		local A = Cut.Actors[E.look.who]
		if A then
			local At = E.look.at
			if At == false or At == nil then A.LookAt = nil
			elseif At == `Camera` then A.LookAt = `Camera`
			elseif Cut.Actors[At] then A.LookAt = Cut.Actors[At].Model
			else A.LookAt = Ctx.Mark(At) end
			if E.look.speed then A.Speed = E.look.speed end
		end
	end
	if E.place then -- straight onto a mark (between shots), optionally in a new pose
		local A = Cut.Actors[E.place.who]
		local To = Ctx.Mark(E.place.to)
		if A and To then
			A.Walk = nil
			Local.StopWalkClip(A)
			if A.WalkTrack then A.WalkTrack:Stop(0) end
			if E.place.pose then Local.SetPose(A, E.place.pose, 100) end
			A.Base = To.CFrame
			A.Root.CFrame = Local.RootFor(A, A.Base)
		end
	end
	if E.walk then
		local A = Cut.Actors[E.walk.who]
		local To = Ctx.Mark(E.walk.to)
		if A and To then
			if E.walk.pose then Local.SetPose(A, E.walk.pose, E.walk.speed or 8) end
			A.Walk = { From = A.Base; To = To.CFrame; T0 = Cut.Clock; Dur = E.walk.dur or 2 }
			Local.WalkClip(A, (To.CFrame.Position - A.Base.Position) * Vector3.new(1, 0, 1), A.Walk.Dur)
		end
	end
	if E.bell then
		Local.Sound(Cut, { id = `rbxassetid://9113584435`; volume = E.bell.volume or 0.55; speed = E.bell.speed or 0.62 })
		pcall(function() UI().Ring() end)
		Local.SwingBell(Cut)
	end
	if E.sound then Local.Sound(Cut, E.sound) end
	if E.card then pcall(function() UI().Card(E.card.title, E.card.sub, E.card.dur or 3) end) end
	if E.veil then pcall(function() UI().Veil(E.veil.alpha, E.veil.dur or 0.5) end) end
	if E.call then task.spawn(E.call, Ctx) end
end

function Local.Sound(Cut, S)
	local Snd = Instance.new(`Sound`)
	Snd.SoundId = S.id
	Snd.Volume = S.volume or 0.5
	Snd.PlaybackSpeed = S.speed or 1
	Snd.Parent = SoundService
	Snd:Play()
	table.insert(Cut.Sounds, Snd)
	Snd.Ended:Connect(function() Snd:Destroy() end)
end

-- the hallway bell (the set's Bell mark names the bell part): a local swing, put back exactly afterwards
function Local.SwingBell(Cut)
	local Mark = Cut.Ctx.Mark(`Bell`)
	local Name = Mark and Mark:GetAttribute(`BellPart`)
	local Bell = nil
	if typeof(Name) == `string` then
		-- the part with that name nearest the Bell mark: the Map has 61 bells with the same full name, so the
		-- name says which part of the bell swings and the mark says which bell
		local Leaf = Name:match(`([^%.]+)$`)
		local Best = 8
		for _, D in workspace:GetDescendants() do
			if D:IsA(`BasePart`) and D.Name == Leaf then
				local Dist = (D.Position - Mark.Position).Magnitude
				if Dist < Best then Bell, Best = D, Dist end
			end
		end
	end
	if not Bell or reduced() then return end
	local Home = Bell.CFrame
	Cut.Restore[Bell] = Cut.Restore[Bell] or Home
	task.spawn(function()
		local T0 = os.clock()
		while Cut.Live and os.clock() - T0 < 2.2 do
			local T = os.clock() - T0
			local A = math.sin(T * 17) * 0.22 * math.exp(-T * 1.6)
			Bell.CFrame = Home * CFrame.new(0, 0.3, 0) * CFrame.Angles(A, 0, 0) * CFrame.new(0, -0.3, 0)
			RunService.RenderStepped:Wait()
		end
		if Bell.Parent then Bell.CFrame = Home end
	end)
end

---| playing |---

function Local.Strip(Cut, Shots)
	-- Reduce Motion (doc 04 §3): moves become cuts, no handheld noise, no Dutch roll
	if not Cut.Ctx.Reduced then return Shots end
	for _, S in Shots do
		S.noise = nil
		S.shake = nil
		local Cam = S.camera
		if Cam then
			if Cam.keys and #Cam.keys > 1 then
				local Last = table.clone(Cam.keys[#Cam.keys])
				Last.t = 0
				Last.roll = 0
				Cam.keys = { Last }
			end
			Cam.to, Cam.orbit, Cam.crane, Cam.dolly, Cam.zoom = nil, nil, nil, nil, nil
			if Cam.frame then Cam.frame.roll = 0 end
		end
	end
	return Shots
end

function Local.Context(Cut, Message)
	local Sets = workspace:FindFirstChild(`NHCineSets`)
	local Set = Sets and Sets:FindFirstChild(Cut.Def.Set or ``)
	local Name = typeof(Message.Name) == `string` and Message.Name or Player.DisplayName
	local Ctx = {
		Id = Cut.Id; Set = Set; Name = Name; First = Name:match(`^(%S+)`) or Name; Reduced = reduced();
		Self = Player.Character; Folder = Cut.Folder; Replay = Message.Skippable == true;
	}
	function Ctx.Mark(N: string): BasePart?
		local M = Set and Set:FindFirstChild(N)
		return if M and M:IsA(`BasePart`) then M else nil
	end
	function Ctx.CF(N: string): CFrame
		local M = Ctx.Mark(N)
		return if M then M.CFrame else CFrame.new()
	end
	function Ctx.Pos(N: string, Offset: Vector3?): Vector3
		return Ctx.CF(N).Position + (Offset or Vector3.zero)
	end
	function Ctx.Actor(N: string): Model?
		local A = Cut.Actors[N]
		return A and A.Model
	end
	function Ctx.ActorPart(N: string, Part: string): BasePart?
		local A = Cut.Actors[N]
		return A and A.Model:FindFirstChild(Part)
	end
	function Ctx.Prop(N: string, Props) return Local.Prop(Cut, N, Props) end
	function Ctx.Hold(Who: string, N: string, Size: Vector3, Color: Color3, Offset: CFrame)
		return Local.Hold(Cut, Cut.Actors[Who], N, Size, Color, Offset)
	end
	Cut.Ctx = Ctx
	return Ctx
end

function Local.Play(Message)
	if Current then Local.Finish(Current, `Replaced`, true) end
	local Module = ReplicatedStorage:FindFirstChild(`Cinematics`) and ReplicatedStorage.Cinematics:FindFirstChild(Message.Id)
	if not Module then
		warn(`[Cine] no cut {Message.Id}`)
		send({ Kind = `Done`; Session = Message.Session })
		return
	end
	local Def = require(Module)
	local Cut = { Id = Message.Id; Session = Message.Session; Def = Def; Live = true; Conns = {}; Sounds = {}; Actors = {};
		Restore = {}; Clock = 0; Fired = 1; Group = Message.Group == true; Token = {} }
	Current = Cut
	-- black first: the menu's "The bell is ringing..." hands straight over to the cut
	local Gui = UI()
	Gui.Veil(1, 0)
	if not Local.Ready(Config.StartGrace - 2) or Current ~= Cut then
		if Current == Cut then Local.Finish(Cut, `NotReady`) end
		return
	end
	Cut.Folder = Instance.new(`Folder`)
	Cut.Folder.Name = `NHCineActors`
	Cut.Folder.Parent = workspace
	local Ctx = Local.Context(Cut, Message)
	for _, Spec in Def.Actors or {} do
		local Ok, A = pcall(Local.MakeActor, Cut, Spec)
		if Ok and A then Cut.Actors[Spec.Name] = A elseif not Ok then warn(`[Cine] actor {Spec.Name}: {A}`) end
	end
	local Ok, Built = pcall(Def.Build, Ctx)
	if not Ok then
		warn(`[Cine] {Message.Id}: {Built}`)
		Local.Finish(Cut, `Error`)
		return
	end
	-- Def.Clock: the time of day the cut is set at (the roll call is morning, COLLECTED is midnight), on this screen
	-- only; it's held every frame (the school clock may write Lighting) and put back when the cut ends
	if typeof(Def.Clock) == `number` then
		Cut.ClockWas = game:GetService(`Lighting`).ClockTime
		Local.HoldHour(Def.Clock) -- the whole day/night look (Controllers.World.DayCycle), not just the sun
	end
	Cut.Events = Built.events or {}
	table.sort(Cut.Events, function(A, B) return (A.t or 0) < (B.t or 0) end)
	local Shots = Local.Strip(Cut, Built.shots)
	Local.HideLive(Cut)
	-- the lease lives through Finish's fade to black too (EndingAt): if the watchdog ended it mid-fade, the camera came
	-- back early and the handle's stop then set it Scriptable again with nobody left to release it
	if not CameraLease.Take(LEASE, function()
		if Cut.Live and Current == Cut then return true end
		return Cut.EndingAt ~= nil and os.clock() - Cut.EndingAt < 3
	end) then
		Local.Finish(Cut, `NoCamera`)
		return
	end
	Gui.Show({ Skippable = Message.Skippable; Group = Cut.Group; Votes = Message.Votes; Need = Message.Need })
	Gui.Veil(1, 0)
	-- a group cut runs on the server's clock: everyone is on the same frame (late joiners start mid-cut)
	local Start = if Cut.Group then math.max(0, workspace:GetServerTimeNow() - (Message.StartAt or 0)) else 0
	Cut.Clock = Start
	while Cut.Fired <= #Cut.Events and (Cut.Events[Cut.Fired].t or 0) < Start - 0.05 do
		local E = Cut.Events[Cut.Fired]
		Cut.Fired += 1
		if E.pose or E.look or E.walk then Local.Fire(Cut, E) end -- catch the actors up, but no stale lines or sounds
	end
	local Lib = CineLib()
	local Last = os.clock()
	Cut.Handle = Lib.play({ name = Message.Id; letterbox = LETTERBOX; grade = Built.grade; shots = Shots }, {
		start = Start; overlay = false; autoStop = false;
		onFrame = function(H)
			if not Cut.Live then return end
			local Now = os.clock()
			local Dt = math.min(Now - Last, 0.1)
			Last = Now
			Cut.Clock = H.time
			if Cut.ClockWas then game:GetService(`Lighting`).ClockTime = Def.Clock end
			while Cut.Fired <= #Cut.Events and (Cut.Events[Cut.Fired].t or 0) <= H.time do
				local E = Cut.Events[Cut.Fired]
				Cut.Fired += 1
				local Ok2, Err = pcall(Local.Fire, Cut, E)
				if not Ok2 then warn(`[Cine] event: {Err}`) end
			end
			local Cam = workspace.CurrentCamera
			for _, A in Cut.Actors do pcall(Local.StepActor, A, Dt, H.time, Cam) end
		end;
		onDone = function() if Current == Cut then Local.Finish(Cut, `Done`) end end;
	})
	-- CameraLease owns the camera type: the shot player must never put back the Scriptable it saw when it started
	Cut.Handle._restoreCameraType = nil
	if not Built.keepBlack then Gui.Veil(0, if Start > 0 then 0.2 else 0.8) end
	send({ Kind = `Began`; Session = Cut.Session; At = Message.StartAt })
end

-- How: Done (played out), Skipped / Timeout / Died (the server ended it), Replaced, NotReady, NoCamera, Error
function Local.Finish(Cut, How: string, Quiet: boolean?)
	if not Cut.Live then return end
	Cut.Live = false
	Cut.EndingAt = os.clock()
	if Current == Cut then Current = nil end
	local Gui = UI()
	-- out through black, never a pop back to the gameplay camera (doc 04 §4)
	local Black = How ~= `Done` and How ~= `NotReady`
	if Black then Gui.Veil(1, 0.25) task.wait(0.25) end
	if Cut.Handle then pcall(function() Cut.Handle:stop() end) end
	for _, Cn in Cut.Conns do Cn:Disconnect() end
	for _, S in Cut.Sounds do pcall(function() S:Destroy() end) end
	for Part, CF in Cut.Restore do if Part.Parent then Part.CFrame = CF end end
	if Cut.ClockWas then
		Cut.ClockWas = nil
		Local.HoldHour(nil) -- DayCycle puts the real school hour (sun and look) back at once
	end
	if Cut.Folder then Cut.Folder:Destroy() end
	Local.ShowLive(Cut)
	pcall(function() UI().ClearSubtitle() end)
	Cut.EndingAt = nil
	CameraLease.Release(LEASE)
	-- belt and braces: nobody else holds the camera, so it must be the normal one now
	if not CameraLease.Held() and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom then CameraLease.Restore() end
	Gui.Hide(0.45)
	Gui.Veil(0, 0.6)
	if not Quiet and (How == `Done` or How == `NotReady` or How == `Error` or How == `NoCamera`) then
		send({ Kind = `Done`; Session = Cut.Session })
	end
end

---| API |---

function Shared.IsPlaying(): boolean return Current ~= nil end

function Shared.Replay(Id: string)
	if Current then return end
	send({ Kind = `Replay`; Id = Id })
end

-- Studio: a cut's shot list for Cine.analyze / capture, built against the live actors without the remote
function Shared.BuildForTests(Id: string)
	local Def = require(ReplicatedStorage.Cinematics[Id])
	local Cut = { Id = Id; Def = Def; Actors = {}; Restore = {}; Conns = {}; Sounds = {}; Used = {} }
	Cut.Folder = Instance.new(`Folder`)
	Cut.Folder.Name = `NHCineActors`
	Cut.Folder.Parent = workspace
	local Ctx = Local.Context(Cut, { Name = Player.DisplayName })
	for _, Spec in Def.Actors or {} do
		local A = Local.MakeActor(Cut, Spec)
		if A then Cut.Actors[Spec.Name] = A end
	end
	return Cut, Def.Build(Ctx), Local
end

function Shared.OnStart()
	Remote = ReplicatedStorage:WaitForChild(`NHCine`, 60) :: RemoteEvent?
	if not Remote then warn(`[Cine] no NHCine remote`) return end
	UI().OnSkip(function()
		local Cut = Current
		if not Cut then return end
		if Cut.Group then
			send({ Kind = `Vote`; Session = Cut.Session })
		else
			send({ Kind = `Skip`; Session = Cut.Session })
			task.spawn(Local.Finish, Cut, `Skipped`, true)
		end
	end)
	Remote.OnClientEvent:Connect(function(Message)
		if typeof(Message) ~= `table` then return end
		if Message.Kind == `Play` then
			task.spawn(function()
				local Ok, Err = pcall(Local.Play, Message)
				if not Ok then
					warn(`[Cine] {Err}`)
					if Current and Current.Session == Message.Session then Local.Finish(Current, `Error`) end
				end
			end)
		elseif Message.Kind == `Votes` then
			if Current and Current.Session == Message.Session then
				pcall(function() UI().Votes(Message.Votes or 0, Message.Need or 1) end)
			end
		elseif Message.Kind == `End` then
			if Current and Current.Session == Message.Session then task.spawn(Local.Finish, Current, Message.How or `Ended`, true) end
		end
	end)
	-- a respawn ends the cut here too (CameraLease drops every lease then)
	Player.CharacterAdded:Connect(function()
		if Current then task.spawn(Local.Finish, Current, `Died`, true) end
	end)
end

return Shared
