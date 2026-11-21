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

	(2.25.0) Interactive cuts: the module also exports Def.Graph = { start, segments = { [Name] = { len, next?, prompt? } } }
	(CineJudge validates it) and Build returns { segments = { [Name] = { shots, events } }, grade? }: each segment's events
	are timed from that segment's start. A prompt opens at prompt.at (CinePrompt, drawn by CineUI) and slows the scene to
	prompt.slow; a solo viewer branches the moment the prompt closes, a group at the server's Branch. A cut without a Graph
	plays as one segment, Main.

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
local Judge = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CineJudge`))
local function Prompt() return require(script.Parent:WaitForChild(`CinePrompt`)) end
local function touch(): boolean
	local UIS = game:GetService(`UserInputService`)
	return UIS.TouchEnabled and not UIS.KeyboardEnabled
end

local Player = Players.LocalPlayer
local LEASE = `Cine`
local LETTERBOX = 2.28 -- the frame the bars leave on 16:9 (CineUI's 11% bars): shots are framed for it

local Shared = {}
local Local = {}
local Current = nil -- the cut playing now
local HeldCut = nil -- (task 10) a cut with Def.EndHold that played out: its last frame and title stay up until ReleaseHold
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

-- the player's gameplay FOV (what CameraLease.Restore puts back): the Settings value, else 70
function Local.SettingsFov(): number
	local Ok, Fov = pcall(function()
		return require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Settings`)).Get(`FieldOfView`)
	end)
	return if Ok and typeof(Fov) == `number` and Fov >= 30 and Fov <= 120 then Fov else 70
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

-- (task 9 fix round 1, I3) Controllers.Hometown hides other tutorial players' characters (NHHiddenLocal = true) and
-- restores them itself when it lets go. The cut records the UNHIDDEN value of anything Hometown already holds, and ShowLive
-- leaves a thing Hometown still holds alone, so a cut ending never re-hides someone Hometown has released nor un-hides
-- someone it still hides.
local function hometownHolds(D: Instance): boolean
	local A = D.Parent
	while A and A ~= workspace do
		if A:GetAttribute(`NHHiddenLocal`) == true then return true end
		A = A.Parent
	end
	return false
end

function Local.HideLive(Cut)
	Cut.HiddenParts = {}
	Cut.HiddenGuis = {}
	local function hide(D: Instance)
		-- a deferred hide that lands after the cut ended (ShowLive cleared the tables) does nothing
		if not (Cut.Live and Cut.HiddenParts and Cut.HiddenGuis) then return end
		if D:IsA(`BasePart`) or D:IsA(`Decal`) then
			if Cut.HiddenParts[D] == nil then Cut.HiddenParts[D] = if hometownHolds(D) then 0 else (D :: any).LocalTransparencyModifier end
			;(D :: any).LocalTransparencyModifier = 1
		elseif D:IsA(`BillboardGui`) or D:IsA(`SurfaceGui`) then
			if Cut.HiddenGuis[D] == nil then
				Cut.HiddenGuis[D] = if hometownHolds(D) then (D:GetAttribute(`NHEn`) ~= false) else (D :: any).Enabled
			end
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
	for D, V in Cut.HiddenParts or {} do
		if D.Parent and not hometownHolds(D) then pcall(function() (D :: any).LocalTransparencyModifier = V end) end
	end
	for D, V in Cut.HiddenGuis or {} do
		if D.Parent and not hometownHolds(D) then pcall(function() (D :: any).Enabled = V end) end
	end
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
	local Template = From:match(`^Template:(.+)$`)
	if Template then
		local Cast = ReplicatedStorage:FindFirstChild(`NHCineCast`)
		local M = Cast and Cast:FindFirstChild(Template)
		return if M and M:IsA(`Model`) then M else nil
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

-- (2.26.0) any clip playing on an actor (the toolkit's anim event, the walk) owns the limbs: the pose layer keeps only the
-- head's look, so a clip is never overwritten by the procedural breathing
function Local.HasClip(A): boolean
	local Hum = A.Model:FindFirstChildOfClass(`Humanoid`)
	local An = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not An then return false end
	for _, T in An:GetPlayingAnimationTracks() do
		if T.WeightCurrent > 0.05 then return true end
	end
	return false
end

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
	local Clip = (A.WalkTrack ~= nil and A.WalkTrack.IsPlaying) or Local.HasClip(A)
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
	if E.card then pcall(function() UI().Card(E.card.title, E.card.sub, E.card.dur or 3, E.card.hold) end) end
	if E.veil then pcall(function() UI().Veil(E.veil.alpha, E.veil.dur or 0.5) end) end
	if E.fx then Local.Fx(Cut, E.fx) end
	if E.move then Local.Move(Cut, E.move) end
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

-- an existing effect from ReplicatedStorage.Assets.Effects (dotted path), emitted at an actor's part, a mark or a CFrame
function Local.Fx(Cut, F)
	local Src = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Effects`)
	for Part in tostring(F.template):gmatch(`[^%.]+`) do Src = Src and Src:FindFirstChild(Part) end
	if not Src then warn(`[Cine] no effect {tostring(F.template)}`) return end
	local At = F.at
	local CF = if typeof(At) == `CFrame` then At
		elseif typeof(At) == `Instance` and At:IsA(`Model`) then ((At:FindFirstChild(F.part or `Torso`) or At.PrimaryPart) :: BasePart).CFrame
		elseif typeof(At) == `Instance` and At:IsA(`BasePart`) then At.CFrame else nil
	if not CF then return end
	local Holder = Instance.new(`Part`)
	Holder.Name = `CineFx`
	Holder.Anchored, Holder.CanCollide, Holder.CanQuery, Holder.CanTouch = true, false, false, false
	Holder.Transparency = 1
	Holder.Size = Vector3.one * 0.2
	Holder.CFrame = CF
	Holder.Parent = Cut.Folder
	local C = Src:Clone()
	C.Parent = Holder
	if C:IsA(`Attachment`) then C.CFrame = CFrame.identity end
	for _, D in Holder:GetDescendants() do
		if D:IsA(`ParticleEmitter`) then
			if F.color then D.Color = ColorSequence.new(F.color) end
			D.Enabled = false
			D:Emit(F.count or 10)
		end
	end
	task.delay(F.life or 3, function() if Holder.Parent then Holder:Destroy() end end)
end

-- a scene part moved on this screen only (a desk shoved), put back exactly when the cut ends
function Local.Move(Cut, M)
	local P = M.part
	if typeof(P) ~= `Instance` or not P:IsA(`BasePart`) or typeof(M.to) ~= `CFrame` then return end
	Cut.Restore[P] = Cut.Restore[P] or P.CFrame
	TweenService:Create(P, TweenInfo.new(M.dur or 0.3, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { CFrame = M.to }):Play()
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
	Ctx.Flags = if typeof(Message.Flags) == `table` then Message.Flags else {}
	function Ctx.GameClip(Path: string): string?
		local I = ReplicatedStorage:FindFirstChild(`Assets`) and ReplicatedStorage.Assets:FindFirstChild(`Animations`)
		for Part in Path:gmatch(`[^%.]+`) do I = I and I:FindFirstChild(Part) end
		return if I and I:IsA(`Animation`) then I.AnimationId else nil
	end
	function Ctx.Clip(Name: string): string?
		local Ok, Clips = pcall(function() return require(ReplicatedStorage.Config.CineClips) end)
		local Id = Ok and Clips[Name]
		if typeof(Id) == `string` and Id:sub(1, 7) == `Assets:` then return Ctx.GameClip(Id:sub(8)) end
		if typeof(Id) == `string` and Id ~= `` then return Id end
		local Folder = ReplicatedStorage:FindFirstChild(`NHCineClips`)
		local Seq = Folder and Folder:FindFirstChild(Name, true)
		if Seq and Seq:IsA(`KeyframeSequence`) then
			local Pid = Seq:GetAttribute(`PreviewId`)
			if not Pid then
				local Ok2, Got = pcall(function() return game:GetService(`AnimationClipProvider`):RegisterAnimationClip(Seq) end)
				if Ok2 then Pid = tostring(Got) Seq:SetAttribute(`PreviewId`, Pid) end
			end
			return Pid
		end
		return nil
	end
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
	-- (task 10) a cut's own loops (a bus driving in) stop when it ends; its cleanups (tracks it loaded) run at Finish
	function Ctx.Alive(): boolean return Cut.Live == true end
	-- (task 11 fix round 2) runs at FULL BLACK when the cut ends any way but Done (Skipped / Timeout / Aborted ...), with How, and
	-- only if no newer cut has started: the place to put the player where the cut's end state is (the skip's own dip hides it)
	function Ctx.OnBlack(Fn: (string) -> ())
		Cut.AtBlack = Cut.AtBlack or {}
		table.insert(Cut.AtBlack, Fn)
	end
	function Ctx.OnEnd(Fn: () -> ())
		Cut.Cleanups = Cut.Cleanups or {}
		table.insert(Cut.Cleanups, Fn)
	end
	-- runs when the cut is over for good: at Finish, or, for a cut that ends held (Def.EndHold), when the hold is released
	function Ctx.OnRelease(Fn: () -> ())
		Cut.AfterHold = Cut.AfterHold or {}
		table.insert(Cut.AfterHold, Fn)
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
	-- (2.35.0) a seamless cut (spec §2) starts from the live view: no black, no clones of you, no hidden world
	Cut.Seamless = Message.Seamless == true
	Cut.Replay = Message.Replay == true -- (task 10) a journal replay: never a held ending
	-- black first: the menu's "The bell is ringing..." hands straight over to the cut
	local Gui = UI()
	if not Cut.Seamless then
		Gui.Veil(1, 0)
		Player:SetAttribute(`NHCineSeam`, nil) -- (an earlier seamless cut's blend may have been cut short by this one)
	end
	if HeldCut then Local.ReleaseHold() end -- the tutorial's title hold ends when the next cut starts (the Prologue)
	if not Local.Ready(Config.StartGrace - 2) or Current ~= Cut then
		if Current == Cut then Local.Finish(Cut, `NotReady`) end
		return
	end
	Cut.Folder = Instance.new(`Folder`)
	Cut.Folder.Name = `NHCineActors`
	Cut.Folder.Parent = workspace
	local Ctx = Local.Context(Cut, Message)
	for _, Spec in Def.Actors or {} do
		if Cut.Seamless and Spec.From == `Self` then continue end -- your real character acts (Controllers.CineActor)
		if Cut.Seamless then
			-- a clone would pop in and out in plain view (no veil): the per-player cast is Hometown's (task 9)
			warn(`[Cine] {Message.Id}: seamless cuts ignore Def.Actors ({Spec.Name})`)
			continue
		end
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
	if typeof(Def.Clock) == `number` and Cut.Seamless then
		warn(`[Cine] {Message.Id}: seamless cuts ignore Def.Clock (the hour would snap in view)`)
	elseif typeof(Def.Clock) == `number` then
		Cut.ClockWas = game:GetService(`Lighting`).ClockTime
		Local.HoldHour(Def.Clock) -- the whole day/night look (Controllers.World.DayCycle), not just the sun
	end
	-- (2.25.0) every cut is a graph of segments; a plain cut is one segment, Main
	Cut.Built = Built
	Cut.Interactive = typeof(Def.Graph) == `table`
	if Cut.Interactive then
		Cut.Graph = Def.Graph
	elseif typeof(Built.segments) == `table` then
		-- (2.35.0) the segments form without a prompt graph (doc 12 §3: Build returns { start, segments }): each
		-- segment's next is its own (a shots segment's next, or a beat's ends.next)
		local Nodes = {}
		for N, S in Built.segments do
			Nodes[N] = { len = if S.beat then 0 else Local.ShotsLength(S.shots or {}); next = S.next }
		end
		Cut.Graph = { start = Built.start or `Main`; segments = Nodes }
	else
		Cut.Graph = { start = `Main`; segments = { Main = { len = Local.ShotsLength(Built.shots or {}) } } }
	end
	Built.segments = Built.segments or { Main = { shots = Built.shots; events = Built.events } }
	local StartSeg = Built.segments[Cut.Graph.start]
	-- (task 8 fix round 1) the gameplay FOV as the cut starts: every segment's shot player restores to it (a segment that
	-- starts after a beat would otherwise "restore" to the beat rig's lens when the cut ends)
	Cut.GameFov = Local.SettingsFov()
	-- (task 8 fix rounds 1-2) a seamless cut with a graded exposure holds ONLY the day cycle's exposure write (it rewrites
	-- ExposureCompensation every 0.2 s, which snapped the grade back mid-cut); its grade, ambient, atmosphere and sky keep
	-- running, so nothing pops. A per-session name, so a superseded cut can't free the new one's hold
	if Cut.Seamless and typeof(Built.grade) == `table` and Built.grade.exposure ~= nil then
		Cut.DayHold = `Cine:{tostring(Cut.Session)}`
		pcall(function() require(script.Parent:WaitForChild(`World`):WaitForChild(`DayCycle`)).HoldExposure(Cut.DayHold, true) end)
	end
	local OpensOnBeat = StartSeg ~= nil and StartSeg.beat ~= nil
	Cut.Solo = not Cut.Group
	Cut.Scale = 1
	Cut.PromptCount = 0
	if not Cut.Seamless then Local.HideLive(Cut) end
	if not CameraLease.Take(LEASE, function()
		if Cut.Live and Current == Cut then return true end
		return (Cut.EndingAt ~= nil and os.clock() - Cut.EndingAt < 3) or HeldCut == Cut
	end) then
		Local.Finish(Cut, `NoCamera`)
		return
	end
	if Cut.Seamless then
		Gui.FadeHud(true, 0.4)
		Gui.SetSkippable(Message.Skippable == true)
		Player:SetAttribute(`NHCineSeam`, `In`)
		-- a cut that opens on a walk-and-talk beat keeps the controls on (spec §3): Begin waits for its first shots
		if not OpensOnBeat then task.spawn(function() require(script.Parent.CineActor).Begin() end) end
	else
		Gui.Show({ Skippable = Message.Skippable; Group = Cut.Group; Votes = Message.Votes; Need = Message.Need })
		Gui.Veil(1, 0)
	end
	-- a group cut runs on the server's clock (late joiners start mid-way through the first segment)
	local Start = if Cut.Group then math.max(0, workspace:GetServerTimeNow() - (Message.StartAt or 0)) else 0
	Local.PlaySegment(Cut, Cut.Graph.start, Start)
	if not Cut.Seamless and not Built.keepBlack then Gui.Veil(0, if Start > 0 then 0.2 else 0.8) end
	send({ Kind = `Began`; Session = Cut.Session; At = Message.StartAt })
end

function Local.ShotsLength(Shots): number
	local T = 0
	for _, S in Shots do T += S.dur or 0 end
	return T
end

-- one segment: its shots on the toolkit's player, its events on the segment's clock, its prompt when its time comes
function Local.PlaySegment(Cut, Name: string, Start: number?)
	if not Cut.Live then return end
	local Seg = Cut.Built.segments[Name]
	local Node = Cut.Graph.segments[Name]
	if not (Seg and Node) then warn(`[Cine] no segment {Name}`) Local.Finish(Cut, `Error`) return end
	-- (2.35.0) a walk-and-talk beat (spec §3): the player keeps moving, a rig frames them (Controllers.CineBeat)
	if Seg.beat then Local.PlayBeat(Cut, Name, Seg, Node) return end
	if Cut.Handle then pcall(function() Cut.Handle:stop() end) end -- (no camera type restore: the next shot cuts in this frame)
	pcall(function() Prompt().Cancel() end)
	Player:SetAttribute(`NHCinePrompt`, nil)
	Cut.Seg = Name
	Cut.Prompt = nil
	Cut.Scale = 1
	Cut.Path = (Cut.Path or ``) .. (if Cut.Path then `>` else ``) .. Name
	Player:SetAttribute(`NHCinePath`, Cut.Path) -- tests read the path taken
	Start = Start or 0
	-- (2.35.0) a seamless cut's start segment opens with the glide from the live camera; its events (and prompt) shift
	-- by the glide's length
	local Shots = Local.Strip(Cut, Seg.shots)
	local Shift = 0
	local LookIn = nil
	local Dissolve = false
	-- (2.35.0) shots after a beat glide in from the beat's camera the same way (spec §3 Endings: the handoff uses §2), and
	-- take the controls then (a beat leaves them on)
	-- (fix round 1) the glide out of a beat starts from the beat's rig, still stepping (GlideTrack), so it carries on
	-- with the rig's motion; NHCineSeam is "BeatOut" for it (camcheck measures it)
	local FromBeat = Cut.FromBeat == true
	local BeatRig = Cut.BeatRig
	if Cut.Seamless and ((not Cut.Glided and Name == Cut.Graph.start) or FromBeat) then
		Cut.Glided = true
		Cut.FromBeat = nil
		Cut.BeatRig = nil
		if FromBeat then
			Player:SetAttribute(`NHCineSeam`, `BeatOut`)
			task.spawn(function() require(script.Parent.CineActor).Begin() end)
		end
		if Cut.Ctx.Reduced then
			-- Reduce Motion (spec §2.1): no camera move at all; a 0.2 s fade through black, the cut's camera put in at black
			Dissolve = true
			UI().Veil(1, 0.1)
			task.wait(0.1)
			UI().Veil(1, 0) -- fully black before the cut's camera goes in
			if not Cut.Live or Cut.Seg ~= Name then return end
		else
			Shots = Local.GlideIn(Cut, Shots, if FromBeat then BeatRig else nil)
			Shift = Cut.GlideLen or 0
			LookIn = if Cut.BeatLook then nil else Shift -- a beat already carries the look: it stays on
		end
	end
	Cut.Events = {}
	for _, E in Seg.events or {} do
		if Shift > 0 then E = table.clone(E) E.t = (E.t or 0) + Shift end
		table.insert(Cut.Events, E)
	end
	table.sort(Cut.Events, function(A, B) return (A.t or 0) < (B.t or 0) end)
	Cut.Fired = 1
	while Cut.Fired <= #Cut.Events and (Cut.Events[Cut.Fired].t or 0) < Start - 0.05 do
		local E = Cut.Events[Cut.Fired]
		Cut.Fired += 1
		if E.pose or E.look or E.walk or E.place then pcall(Local.Fire, Cut, E) end -- catch the actors up, no stale lines
	end
	local Def = Cut.Def
	local Lib = CineLib()
	local Last = os.clock()
	Cut.LastShot = Shots[#Shots] -- the blend out keeps this shot's camera moving (BlendOut's From end)
	-- the look a beat carried: put back the exposure and drop it in the frame this player puts the same grade back on
	if Cut.BeatLook then Local.DropLook(Cut.BeatLook, true) Cut.BeatLook = nil end
	-- a seamless cut has no bars, so its shots are framed for the full screen (and the glide aims at that framing)
	Cut.Handle = Lib.play({ name = `{Cut.Id}.{Name}`; letterbox = if Cut.Seamless then nil else LETTERBOX; grade = Cut.Built.grade; shots = Shots }, {
		start = Start; overlay = false; autoStop = false; lookIn = LookIn;
		onFrame = function(H)
			if not Cut.Live or Cut.Seg ~= Name then return end
			if Shift > 0 and Cut.Glide and H.time < Shift then Local.GlideTrack(Cut, H.time) end
			local Now = os.clock()
			local Dt = math.min(Now - Last, 0.1) * Cut.Scale
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
			if Node.prompt and not Cut.Prompt and H.time >= Node.prompt.at + Shift then Local.OpenPrompt(Cut, Name, Node.prompt) end
		end;
		onDone = function() if Cut.Live and Cut.Seg == Name then Local.SegmentDone(Cut, Name) end end;
	})
	Cut.Handle._restoreCameraType = nil
	if Cut.GameFov then Cut.Handle._restoreFov = Cut.GameFov end
	if Dissolve then
		UI().Veil(0, 0.1)
		task.delay(0.1, function() if Cut.Live then Player:SetAttribute(`NHCineSeam`, `Cut`) end end)
	end
	-- (2.35.0) seamless cuts report every segment too: the server writes the resume checkpoint (Tutorial.Checkpoint)
	if Cut.Interactive or Cut.Seamless then send({ Kind = `Seg`; Session = Cut.Session; Name = Name; At = workspace:GetServerTimeNow() - Start }) end
end

-- (2.35.0) a beat segment (spec §3). Controls stay on (no CineActor.Begin; shots before it hand them back). The way in
-- blends from the camera that was showing: the last shot carried on (as the blend out does), the live gameplay camera
-- following your root when the cut opens on this beat (that blend IS the glide in), or the previous beat's rig. The look
-- (grade, DOF) of the shots before carries through the beat. When it ends, its rig keeps stepping (Cut.BeatRig) for
-- the blend out or the next shots' glide in.
function Local.PlayBeat(Cut, Name: string, Seg, Node)
	local Cam = workspace.CurrentCamera
	pcall(function() Prompt().Cancel() end)
	Player:SetAttribute(`NHCinePrompt`, nil)
	Cut.Seg = Name
	Cut.Prompt = nil
	Cut.Scale = 1
	Cut.Path = (Cut.Path or ``) .. (if Cut.Path then `>` else ``) .. Name
	Player:SetAttribute(`NHCinePath`, Cut.Path)
	-- (fix round 1) Beat = true: the server holds its timeout while the player drives (spec §4.3)
	if Cut.Interactive or Cut.Seamless then send({ Kind = `Seg`; Session = Cut.Session; Name = Name; Beat = true; At = workspace:GetServerTimeNow() }) end
	local Entry = nil
	local CF0, Fov0 = Cam.CFrame, Cam.FieldOfView
	if Cut.Handle then
		-- from shots: keep the look, stop the player (stop() writes the gameplay FOV: put the shot's back for this frame)
		local Look = nil
		pcall(function() Look = Cut.Handle:detachLook() end)
		pcall(function() Cut.Handle:stop() end)
		Cut.Handle = nil
		Cam.CFrame, Cam.FieldOfView = CF0, Fov0
		if Look and (#Look.effects > 0 or Look.restoreExposure) then
			if Cut.BeatLook then Local.DropLook(Look, false) else Cut.BeatLook = Look end
		end
		local Track = if Cut.LastShot then { Probe = { letterbox = nil; shots = { Cut.LastShot } }; T = Cut.LastShot.dur or 0 } else nil
		Entry = { From = Local.Carry(CF0, Fov0, Track); Phase = `BeatIn` }
		Cut.LastShot = nil
		if Cut.Seamless then pcall(function() require(script.Parent.CineActor).Release() end) end -- controls back on
	elseif Cut.BeatRig then
		local Rig = Cut.BeatRig
		Entry = { From = function() return Rig.Step() end; Phase = `BeatIn` }
	elseif Cut.Seamless and not Cut.Glided and Name == Cut.Graph.start then
		-- the cut opens on this beat: from the live camera, carried along with a walking player (GlideTrack's follow)
		Cut.Glided = true
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local RootFrom = Root and Root.Position
		if Root and Local.RootAtRender and (Local.RootAtRender - Root.Position).Magnitude < 4 then RootFrom = Local.RootAtRender end
		Entry = { From = function()
			if Root and Root.Parent and RootFrom then return CF0 + (Root.Position - RootFrom), Fov0 end
			return CF0, Fov0
		end; Phase = `In` }
		-- (fix round 1) the cut's grade eases in over this blend, as it does over the glide in (Cut.BeatLook owns it)
		if Cut.Built.grade and not Cut.BeatLook then
			local Base = game:GetService(`Lighting`).ExposureCompensation
			Cut.BeatLook = { effects = {}; exposure = Base; restoreExposure = Base }
			Entry.Grade = { g = Cut.Built.grade; base = Base }
		end
	end
	Cut.BeatRig = nil
	if Entry and Cut.Ctx.Reduced then
		-- Reduce Motion: no camera move; a 0.2 s fade through black, the rig's camera put in at black
		UI().Veil(1, 0.1)
		task.wait(0.1)
		UI().Veil(1, 0)
		if not Cut.Live or Cut.Seg ~= Name then return end
		task.delay(0.05, function() UI().Veil(0, 0.1) end)
		Entry.Len = 1e-3 -- the rig (and the grade) go in at black
	end
	local Out = {}
	task.spawn(function()
		local Ok, Next = pcall(require(script.Parent.CineBeat).Run, Cut, Name, Seg.beat, Cut.Ctx, Entry, Out, Cut.BeatLook)
		if not Ok then warn(`[Cine] beat {Name}: {Next}`) Next = nil end
		if not (Cut.Live and Cut.Seg == Name) then return end
		Cut.BeatRig = Out.Rig
		Next = Next or Node.next
		if Next then
			Cut.FromBeat = true
			Local.PlaySegment(Cut, Next)
		else
			task.spawn(Local.EndGraph, Cut)
		end
	end)
end

-- the camera a blend starts from, still moving. Track = a shot: re-evaluated at its end time on its live subject, and
-- its motion since FromCF was taken is carried onto FromCF (the blend leaves with the old camera's own velocity);
-- Track.Fn = a beat's rig, stepped on
function Local.Carry(FromCF: CFrame, FromFov: number, Track: any?): () -> (CFrame, number)
	if not Track then return function() return FromCF, FromFov end end
	if Track.Fn then
		return function()
			local Ok, A, B = pcall(Track.Fn)
			if Ok and typeof(A) == `CFrame` and typeof(B) == `number` then return A, B end
			return FromCF, FromFov
		end
	end
	local Lib = CineLib()
	local Ok0, L0, L0Fov = pcall(Lib.cameraAt, Track.Probe, Track.T)
	if not Ok0 or typeof(L0) ~= `CFrame` then return function() return FromCF, FromFov end end
	return function()
		local Ok, L, LFov = pcall(Lib.cameraAt, Track.Probe, Track.T)
		if not Ok or typeof(L) ~= `CFrame` then return FromCF, FromFov end
		local Turn = L.Rotation * (L0 :: CFrame).Rotation:Inverse()
		return CFrame.new(FromCF.Position + (L.Position - (L0 :: CFrame).Position)) * Turn * FromCF.Rotation,
			FromFov + ((LFov :: number) - (L0Fov :: number))
	end
end

-- (2.35.0) the glide in (spec §2.1): from the live camera's CFrame and FOV into shot 1's first frame (no noise), along
-- CineSeam's curved keys with an ease-in-out, 0.6-1.0 s (0.2 s with Reduce Motion). NHCineSeam goes In -> Cut at its end.
function Local.GlideIn(Cut, Shots, Rig: any?)
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Lib = CineLib()
	local Cam = workspace.CurrentCamera
	local FromCF, FromFov = Cam.CFrame, Cam.FieldOfView
	local ToCF, ToFov = Lib.cameraAt({ letterbox = nil; shots = { Shots[1] } }, 0)
	local Lint = Seam.Lint(FromCF, ToCF)
	if Lint then warn(`[Cine] {Cut.Id}: {Lint}`) end
	local Len = Seam.Length(FromCF, ToCF, Cut.Ctx.Reduced)
	local Glide = { name = `GlideIn`; dur = Len; dof = Shots[1].dof; subject = Shots[1].subject;
		camera = { keys = Seam.Keys(FromCF, FromFov, ToCF, ToFov, Len); ease = `inout` } }
	Cut.GlideLen = Len
	-- the keys end on shot 1's first frame as it is NOW; GlideTrack moves that endpoint with the live one every frame
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	-- (fix round 2) FromCF is the LAST render's camera (a Play lands at network receive, before this frame's render), so
	-- the follow is measured from the root as it was at that render, not now (one physics step on): from "now", the
	-- first glide frame re-showed the previous frame's camera (a one-frame hold on a walking player, then a catch-up)
	local RootFrom = Root and Root.Position
	if Root and Local.RootAtRender and (Local.RootAtRender - Root.Position).Magnitude < 4 then RootFrom = Local.RootAtRender end
	Cut.Glide = { Probe = { letterbox = nil; shots = { Shots[1] } };
		To = CFrame.lookAt(ToCF.Position, ToCF.Position + ToCF.LookVector * 10); ToFov = ToFov; Len = Len; FromRot = FromCF.Rotation;
		Root = Root; RootFrom = RootFrom; Rig = Rig; FromCF = FromCF; FromFov = FromFov }
	task.delay(Len, function() if Cut.Live then Player:SetAttribute(`NHCineSeam`, `Cut`) end end)
	-- shot 1's handheld noise ramps in over 0.3 s, so the glide doesn't land on a non-zero noise sample
	local First = table.clone(Shots[1])
	First.noiseIn = 0.3
	local Out = { Glide, First }
	for I = 2, #Shots do table.insert(Out, Shots[I]) end
	return Out
end

-- (fix round 1) the glide's target tracks shot 1's live first frame (its subject may still be moving: a player who was
-- walking when the cut fired): after the shot player writes the keyed glide, the difference between the live and the
-- frozen target is added in, weighted by the glide's ease, so the last glide frame IS shot 1's first frame. The start
-- end moves too: the player's displacement since the glide began, weighted by (1 - ease), so a glide that starts on a
-- walking player leaves with the live camera's own velocity instead of stopping dead (the Custom camera follows the root)
function Local.GlideTrack(Cut, T: number)
	local G = Cut.Glide
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Ok, Live, LiveFov = pcall(CineLib().cameraAt, G.Probe, 0)
	if not Ok or typeof(Live) ~= `CFrame` then return end
	local W = Seam.Ease(T / G.Len)
	local Cam = workspace.CurrentCamera
	local C = Cam.CFrame
	local Follow = if G.Root and G.Root.Parent and G.RootFrom then G.Root.Position - G.RootFrom else Vector3.zero
	local FromRot = G.FromRot
	local FovFrom = 0
	if G.Rig then
		-- (fix round 1) out of a beat: the start end is the beat's rig as it moves on (position, turn and FOV)
		local Ok2, RCF, RFov = pcall(G.Rig.Step)
		if Ok2 and typeof(RCF) == `CFrame` then
			Follow = RCF.Position - G.FromCF.Position
			FromRot = RCF.Rotation
			FovFrom = (RFov :: number) - G.FromFov
		end
	end
	-- the rotation is an eased slerp from the live camera's to shot 1's live first frame (the keys' look points swing
	-- the view unevenly on a big turn, when they pass close to the camera); the position keeps the keys' curved path
	Cam.CFrame = CFrame.new(C.Position + Follow * (1 - W) + (Live.Position - G.To.Position) * W) * FromRot:Lerp(Live.Rotation, W)
	Cam.FieldOfView = math.clamp(Cam.FieldOfView + FovFrom * (1 - W) + ((LiveFov :: number) - G.ToFov) * W, 1, 120)
end

-- Look (from Handle:detachLook): the grade, bloom and DOF ease to neutral and the exposure back over the blend
function Local.EaseLook(Look, E: number)
	if not Look then return end
	Look.Start = Look.Start or {}
	for _, Fx in Look.effects do
		local S = Look.Start[Fx]
		if not S then
			S = {}
			for _, K in { `Contrast`, `Saturation`, `Brightness`, `TintColor`, `Intensity`, `FarIntensity`, `NearIntensity` } do
				local Ok, V = pcall(function() return (Fx :: any)[K] end)
				if Ok then S[K] = V end
			end
			Look.Start[Fx] = S
		end
		for K, V in S do
			pcall(function()
				if typeof(V) == `Color3` then (Fx :: any)[K] = V:Lerp(Color3.new(1, 1, 1), E) else (Fx :: any)[K] = V * (1 - E) end
			end)
		end
	end
	if Look.restoreExposure then
		game:GetService(`Lighting`).ExposureCompensation = Look.exposure + (Look.restoreExposure - Look.exposure) * E
	end
end

function Local.DropLook(Look, Restore: boolean)
	if not Look then return end
	for _, Fx in Look.effects do pcall(function() Fx:Destroy() end) end
	if Restore and Look.restoreExposure then game:GetService(`Lighting`).ExposureCompensation = Look.restoreExposure end
end

-- (2.35.0) the glide out onto the live Custom camera (spec delta 3): the camera module reads Camera.CFrame back every
-- frame, so before it runs we put back its own last CFrame; after it runs we save that and write the blend. The
-- endpoint is whatever the Custom camera renders: the release can't jump. Someone else taking the camera mid-blend
-- (a new lease) ends it at once.
-- Returns true if the blend was cut short by another lease (a new cut took the camera).
-- Track (optional): the cut's last shot; the From end keeps moving as that shot's camera would (a shot tracking a walking
-- player), so the blend leaves with the cut camera's own velocity instead of freezing it
function Local.BlendOut(Cut, FromCF: CFrame, FromFov: number, Seconds: number, Look: any?, GameFov: number?, Track: any?): boolean
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local Cam = workspace.CurrentCamera
	-- (2.35.0) Local.Carry; Track.Fn (a beat's rig) instead of a shot keeps the From end following you
	local from = Local.Carry(FromCF, FromFov, Track)
	local Own: CFrame? = nil
	local OwnFov: number? = GameFov
	local T0 = os.clock()
	local Pre, Post = `NHCineBlendPre`, `NHCineBlendPost`
	local Stolen = false
	RunService:BindToRenderStep(Pre, Enum.RenderPriority.Camera.Value - 1, function()
		if Stolen then return end
		if Own then Cam.CFrame = Own end
		if OwnFov then Cam.FieldOfView = OwnFov end
	end)
	RunService:BindToRenderStep(Post, Enum.RenderPriority.Camera.Value + 1, function()
		if Stolen or CameraLease.Held() then Stolen = true return end
		Own, OwnFov = Cam.CFrame, Cam.FieldOfView
		local E = Seam.Ease((os.clock() - T0) / Seconds)
		local FromNow, FromNowFov = from()
		Cam.CFrame = Seam.Blend(FromNow, Own :: CFrame, E)
		Cam.FieldOfView = FromNowFov + ((OwnFov :: number) - FromNowFov) * E
		Local.EaseLook(Look, E)
	end)
	while os.clock() - T0 < Seconds and not Stolen do RunService.RenderStepped:Wait() end
	RunService:UnbindFromRenderStep(Post)
	RunService.RenderStepped:Wait()                          -- one frame where Pre still restores the module's own CFrame
	RunService:UnbindFromRenderStep(Pre)
	-- stolen: the new cut captured the exposure as it was, so it is left alone (only the old effects go)
	Local.DropLook(Look, not Stolen)
	return Stolen
end

function Local.SegmentDone(Cut, Name: string)
	local Node = Cut.Graph.segments[Name]
	if Node.prompt then
		-- the tail ran out before the branch was known (a slow server in a group cut): ask where the cut is
		if not Cut.Solo then send({ Kind = `Where`; Session = Cut.Session }) end
		return
	end
	if Node.next then Local.PlaySegment(Cut, Node.next) return end
	task.spawn(Local.EndGraph, Cut)
end

function Local.OpenPrompt(Cut, SegName: string, P)
	Cut.Prompt = { Seg = SegName }
	Cut.PromptCount += 1
	Cut.Scale = P.slow or 1
	pcall(function() Cut.Handle:setTimeScale(Cut.Scale) end)
	Player:SetAttribute(`NHCinePrompt`, P.kind)
	local Reduced = Cut.Ctx and Cut.Ctx.Reduced or false
	local Opened = workspace:GetServerTimeNow()
	Prompt().Open(P, { Reduced = Reduced; Touch = touch() }, function(Input)
		Player:SetAttribute(`NHCinePrompt`, nil)
		if not Cut.Live or Cut.Seg ~= SegName then return end
		send({ Kind = `Input`; Session = Cut.Session; Seg = SegName; Opened = Opened; Times = Input.Times; Pick = Input.Pick;
			PickAt = Input.PickAt; Release = Input.Release; Touch = Input.Touch; Reduced = Input.Reduced })
		if Cut.Solo then
			local Outcome = Judge.Evaluate(P, Input)
			local Next = Judge.Branch(P, Outcome)
			if Next then Local.Branch(Cut, SegName, Next, nil) end
		else
			task.delay(1.5, function()
				if Cut.Live and Cut.Seg == SegName then send({ Kind = `Where`; Session = Cut.Session }) end
			end)
		end
	end)
end

-- cut to the next segment on the branch (solo: now; group: at the server's StartAt, inside the slow-motion hold)
function Local.Branch(Cut, From: string, Next: string, StartAt: number?)
	if not Cut.Live or Cut.Seg ~= From then return end
	local Delay = if StartAt then math.max(0, StartAt - workspace:GetServerTimeNow()) else 0
	local function go() if Cut.Live and Cut.Seg == From then Local.PlaySegment(Cut, Next) end end
	if Delay > 0 then task.delay(Delay, go) else go() end
end

-- the end of the last segment: an interactive cut asks for its grade (server-judged) and shows the card first
function Local.EndGraph(Cut)
	if not Cut.Interactive then Local.Finish(Cut, `Done`) return end
	Cut.GradeMsg = nil
	send({ Kind = `Grade`; Session = Cut.Session })
	local T0 = os.clock()
	while Cut.Live and not Cut.GradeMsg and os.clock() - T0 < 2 do task.wait(0.05) end
	if not Cut.Live then return end
	local G = Cut.GradeMsg
	if G and G.Grade and G.Show ~= false then
		local Seconds = Config.GradeCard or 2.5
		pcall(function() UI().GradeCard(G.Grade, G.Perfects or 0, Cut.PromptCount or 0, Seconds) end)
		task.wait(Seconds)
	end
	if Cut.Live then Local.Finish(Cut, `Done`) end
end

-- How: Done (played out), Skipped / Aborted / Timeout / Died (the server ended it; Aborted = Tutorial.Leave), Replaced, NotReady, NoCamera, Error
function Local.Finish(Cut, How: string, Quiet: boolean?)
	if not Cut.Live then return end
	Cut.Live = false
	pcall(function() Prompt().Cancel() end)
	Player:SetAttribute(`NHCinePrompt`, nil)
	Cut.EndingAt = os.clock()
	if Current == Cut then Current = nil end
	local Gui = UI()
	local Seamless = Cut.Seamless == true
	-- (task 10) Def.EndHold: the tutorial's last cut ends on its title; there is no glide out. The frame freezes where it is, the
	-- title card stays, the player stays held, until ReleaseHold (the next cut, leaving Wickfield, a respawn)
	-- Only the real thing holds: in Wickfield (NHTutorial) and not a replay. Anything else blends out as usual, so a replay
	-- from the journal can never strand the player under a frozen title.
	local Hold = Seamless and How == `Done` and Cut.Def.EndHold == true and Cut.Replay ~= true
		and Player:GetAttribute(`NHTutorial`) == true
	local Blended = Seamless and How == `Done` and not Hold
	local function actor() return require(script.Parent:WaitForChild(`CineActor`)) end
	local Superseded = false
	if Hold then
		HeldCut = Cut
		Player:SetAttribute(`NHCineSeam`, nil)
		Player:SetAttribute(`NHCineHold`, true)
		pcall(function() Gui.SetSkippable(false) end) -- nothing left to skip
		-- safety net: no next cut (the Prologue) within 10 s -> dip to black and let go; a hold is never forever
		task.delay(10, function()
			if HeldCut == Cut then pcall(function() UI().Dip(0.3, function() Local.ReleaseHold() end) end) end
		end)
	end
	if Blended then
		-- (2.35.0) out without black (spec §2.2): control comes back as the glide onto the Custom camera starts
		local Cam = workspace.CurrentCamera
		local FromCF, FromFov = Cam.CFrame, Cam.FieldOfView
		local Look = nil
		if Cut.Handle then
			pcall(function() Look = Cut.Handle:detachLook() end) -- the look eases out over the blend, not popped by stop()
			pcall(function() Cut.Handle:stop() end)
			-- (task 8 fix round 1) stopped once: the cleanup's stop() below would write the handle's restore FOV again
			-- AFTER the blend (a jump, and a stale FOV left behind when that value wasn't the gameplay one)
			Cut.Handle = nil
		end
		if Cut.BeatLook then -- (2.35.0) a cut that ends on a beat: the look it carried eases out the same way
			if Look then Local.DropLook(Look, false) end
			Look, Cut.BeatLook = Cut.BeatLook, nil
			Look.exposure = game:GetService(`Lighting`).ExposureCompensation -- graded now (a look built by the beat started at the base)
		end
		Player:SetAttribute(`NHCineSeam`, `Out`)
		pcall(function() actor().Release() end)
		local Stolen = false
		if Cut.Ctx and Cut.Ctx.Reduced then
			-- Reduce Motion: a 0.2 s fade through black, the gameplay camera put back at black; no camera move (stop()
			-- wrote the gameplay FOV: the cut's last frame stays up until the screen is black; the lease is still ours)
			Cam.CFrame, Cam.FieldOfView = FromCF, FromFov
			Gui.Veil(1, 0.1)
			task.wait(0.1)
			Gui.Veil(1, 0) -- fully black before anything changes (a slow frame can leave the tween short)
			Local.DropLook(Look, true)
			if Current == nil then CameraLease.Release(LEASE) end
			Gui.Veil(0, 0.1)
			task.wait(0.1)
		else
			CameraLease.Release(LEASE)
			-- stop() and the lease's Restore write the gameplay FOV, and this can run inside the shot player's own render
			-- step (its onDone), before the blend's binds first run: put the cut's last frame back for this frame, and
			-- hand the blend the gameplay FOV as the camera module's own (the module never writes FOV itself)
			local GameFov = Cam.FieldOfView
			Cam.CFrame, Cam.FieldOfView = FromCF, FromFov
			local Rig = Cut.BeatRig
			local Track = if Rig then { Fn = function() return Rig.Step() end }
				elseif Cut.LastShot then { Probe = { letterbox = nil; shots = { Cut.LastShot } }; T = Cut.LastShot.dur or 0 } else nil
			Stolen = Local.BlendOut(Cut, FromCF, FromFov, 0.8, Look, GameFov, Track)
		end
		-- (fix round 1) a cut that started during the blend owns the attribute, the HUD and the "Cine" lease now
		Superseded = Current ~= nil or Stolen
		if not Superseded then
			Player:SetAttribute(`NHCineSeam`, nil)
			Gui.FadeHud(false, 0.4)
		end
	end
	-- out through black, never a pop back to the gameplay camera (doc 04 §4); a seamless skip dips (spec §2.3)
	local Black = How ~= `Done` and How ~= `NotReady`
	if Seamless and not Blended and not Hold then
		Player:SetAttribute(`NHCineSeam`, nil)
		pcall(function() actor().Release() end)
	end
	local function atBlack()
		if Current ~= nil then return end -- a newer cut owns the player now
		for _, Fn in Cut.AtBlack or {} do pcall(Fn, How) end
		Cut.AtBlack = nil
	end
	local Dipped = false
	if Black and Seamless and (How == `Skipped` or How == `Aborted`) then
		-- the jump to the end state happens at full black: the cut stops, the camera goes back to the gameplay camera
		Dipped = true
		Gui.Dip(0.25, function()
			atBlack()
			if Cut.Handle then pcall(function() Cut.Handle:stop() end) end
			if Cut.BeatLook then Local.DropLook(Cut.BeatLook, true) Cut.BeatLook = nil end
			CameraLease.Release(LEASE)
			if not CameraLease.Held() and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom then CameraLease.Restore() end
		end)
	elseif Black then
		Gui.Veil(1, 0.25) task.wait(0.25)
		Gui.Veil(1, 0)
		atBlack()
	end
	if not Hold then
		if Cut.Handle then pcall(function() Cut.Handle:stop() end) end
		if Cut.BeatLook then Local.DropLook(Cut.BeatLook, true) Cut.BeatLook = nil end
	end
	Cut.BeatRig = nil
	for _, Cn in Cut.Conns do Cn:Disconnect() end
	-- (task 10 fix round 1) a held cut keeps its tracks and loops' cleanups until the hold is released: stopped now, the
	-- bus would fall to its rest pose under the frozen title
	if not Hold then
		for _, Fn in Cut.Cleanups or {} do pcall(Fn) end
		Cut.Cleanups = nil
		for _, Fn in Cut.AfterHold or {} do pcall(Fn) end
		Cut.AfterHold = nil
	end
	for _, S in Cut.Sounds do pcall(function() S:Destroy() end) end
	for Part, CF in Cut.Restore do if Part.Parent then Part.CFrame = CF end end
	if Cut.ClockWas then
		Cut.ClockWas = nil
		Local.HoldHour(nil) -- DayCycle puts the real school hour (sun and look) back at once
	end
	if Cut.Folder then Cut.Folder:Destroy() end
	Local.ShowLive(Cut)
	Cut.EndingAt = nil
	if not Superseded and not Hold then
		pcall(function() UI().ClearSubtitle() end)
		CameraLease.Release(LEASE)
		-- belt and braces: nobody else holds the camera, so it must be the normal one now
		if not CameraLease.Held() and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom then CameraLease.Restore() end
	end
	if Cut.DayHold and not Hold then
		local Name = Cut.DayHold
		Cut.DayHold = nil
		pcall(function() require(script.Parent:WaitForChild(`World`):WaitForChild(`DayCycle`)).HoldExposure(Name, false) end)
	end
	if Hold then
		-- nothing else changes: the HUD stays away, the camera and the card stay (ReleaseHold puts everything back)
	elseif Seamless and (Blended or Dipped) then
		if Dipped then Gui.FadeHud(false, 0.4) end
	else
		Gui.Hide(0.45)
		Gui.Veil(0, 0.6)
	end
	if not Quiet and (How == `Done` or How == `NotReady` or How == `Error` or How == `NoCamera`) then
		send({ Kind = `Done`; Session = Cut.Session })
	end
end

-- (task 10) ends an EndHold cut's hold: the title away, the controls back, the camera and the look handed back. Under a
-- veil when there is one (the next cut's black), else a quick fade.
function Local.ReleaseHold()
	local Cut = HeldCut
	if not Cut then return end
	HeldCut = nil
	Player:SetAttribute(`NHCineHold`, nil)
	for _, Fn in Cut.Cleanups or {} do pcall(Fn) end
	Cut.Cleanups = nil
	for _, Fn in Cut.AfterHold or {} do pcall(Fn) end
	Cut.AfterHold = nil
	pcall(function() UI().ClearCard(0.2) end)
	pcall(function() require(script.Parent:WaitForChild(`CineActor`)).Release() end)
	if Cut.Handle then pcall(function() Cut.Handle:stop() end) Cut.Handle = nil end
	if Cut.BeatLook then Local.DropLook(Cut.BeatLook, true) Cut.BeatLook = nil end
	if Current == nil then
		CameraLease.Release(LEASE)
		if not CameraLease.Held() and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom then CameraLease.Restore() end
	end
	if Cut.DayHold then
		local Name = Cut.DayHold
		Cut.DayHold = nil
		pcall(function() require(script.Parent:WaitForChild(`World`):WaitForChild(`DayCycle`)).HoldExposure(Name, false) end)
	end
	pcall(function() UI().ClearSubtitle() end)
	if Current == nil then pcall(function() UI().FadeHud(false, 0.4) end) end
end
function Shared.ReleaseHold() Local.ReleaseHold() end
function Shared.IsHeld(): boolean return HeldCut ~= nil end

---| API |---

function Shared.IsPlaying(): boolean return Current ~= nil end

function Shared.Replay(Id: string)
	if Current then return end
	send({ Kind = `Replay`; Id = Id })
end

-- Studio: a cut built against the live actors without the remote (capture and analysis helpers)
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

-- one path through a built cut as a single shot list and event list (segment times shifted to the path's clock)
function Shared.FlattenForTests(Built, Graph, Path: { string })
	if not Graph then return { shots = Built.shots; events = Built.events } end
	local Shots, Events, At = {}, {}, 0
	for _, Name in Path do
		local Seg = Built.segments[Name]
		for _, S in Seg.shots do table.insert(Shots, S) end
		for _, E in Seg.events or {} do local C = table.clone(E) C.t = (E.t or 0) + At table.insert(Events, C) end
		At += Graph.segments[Name].len
	end
	return { shots = Shots; events = Events }
end

function Shared.OnStart()
	-- (fix round 2) where the root was when the camera module last framed it (GlideIn's follow starts from there)
	RunService:BindToRenderStep(`NHCineRootMark`, Enum.RenderPriority.Camera.Value - 2, function()
		local C = Player.Character
		local R = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		Local.RootAtRender = R and R.Position
	end)
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
		elseif Message.Kind == `Branch` then
			if Current and Current.Session == Message.Session then Local.Branch(Current, Message.Seg, Message.Next, Message.StartAt) end
		elseif Message.Kind == `Segment` then
			local Cut = Current
			if Cut and Cut.Session == Message.Session and typeof(Message.Name) == `string` and Cut.Seg ~= Message.Name then
				Local.PlaySegment(Cut, Message.Name, math.max(0, workspace:GetServerTimeNow() - (Message.StartAt or 0)))
			end
		elseif Message.Kind == `Grade` then
			if Current and Current.Session == Message.Session then Current.GradeMsg = Message end
		elseif Message.Kind == `End` then
			if Current and Current.Session == Message.Session then task.spawn(Local.Finish, Current, Message.How or `Ended`, true) end
		end
	end)
	-- a respawn ends the cut here too (CameraLease drops every lease then)
	Player.CharacterAdded:Connect(function()
		if Current then task.spawn(Local.Finish, Current, `Died`, true) end
		if HeldCut then Local.ReleaseHold() end
	end)
	-- leaving Wickfield ends a title hold too (Tutorial.Leave clears NHTutorial)
	Player:GetAttributeChangedSignal(`NHTutorial`):Connect(function()
		if Player:GetAttribute(`NHTutorial`) ~= true and HeldCut then
			-- leaving Wickfield under a held title: a dip to black, the hold ends at full black (never a pop to gameplay)
			task.spawn(function() UI().Dip(0.3, function() Local.ReleaseHold() end) end)
		end
	end)
end

return Shared
