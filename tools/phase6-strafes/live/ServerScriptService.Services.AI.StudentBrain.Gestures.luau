--[[
	Gestures (server). Services.AI.StudentBrain.Gestures  (phase6-strafes)
	Spec: docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §3, §5. Clips and casting: Config.Gestures;
	picking: Functions.Gestures.

	The FIER ANIMATIONS gestures on the school's NPCs (students, staff, the Nurse), the same way Nudges plays its clips:
	the published id (Config.Gestures.Clips[Base].Id / .Ids[bucket], group 15981569) or, in Studio with an id of 0, the
	local KeyframeSequence ServerStorage.NHGestures["NHG_" .. Name] through RegisterKeyframeSequence. Live servers skip a
	gesture until it is published.

	S is any record with Model, Hum, Root (and Tracks): a scheduled student (Features.Schedules), or a staff record made by
	Gestures.Record(Model). Tracks load into S.Tracks[Name], so Schedules' Local.Pose(S, nil) (every WalkTo) ends them.
	  Gestures.Play(S, Name, Opts?) -> AnimationTrack?    Name = a Clips base (bucketed by the leg length) or an NHG name
	      Opts: Seconds, Fade (0.25), Speed, Weight, Carry (play the baked root-motion curve), Force (ignore the cap,
	      cooldown, the near-player rule and S.Reacting: reactions and scenes)
	  Gestures.Stop(S, Fade?)   Gestures.Busy(S)   Gestures.Active() -> number
	  Gestures.PickFor(S, Hook, Ctx?) -> Name?   (Ctx is filled with Clique / Npc / Temper from the record)
	  Gestures.Carry(S, Curve)   Gestures.Record(Model) -> S   Gestures.Init(Host)
	Downed.OnRecovered: a student or staff NPC that gets back up plays Dizzy or InjuredHurt for 5-8 s (never a player or
	combat AI), and a student is sent to the infirmary later (S.SickUntil).
	Studio only: ServerStorage.NHGestureProbe (BindableFunction) for tools/phase6-strafes/checks/*.lua.
]]

local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

local Config = require(ReplicatedStorage.Config.Gestures)
local F = require(ReplicatedStorage.Functions.Gestures)
local Space = require(script.Parent:WaitForChild(`Space`))

local Gestures = {}
local Host = nil
local Studio = RunService:IsStudio()
local Ids = {} :: { [string]: string }
local Playing = {} :: { [any]: { Track: AnimationTrack, Name: string, Token: number } }
local ActiveCount = 0
local Token = 0
local Rng = Random.new()

local function roll() return Rng:NextNumber() end

local function baseOf(Name: string): (string, number?)
	local B, Bucket = Name:match(`^(.-)_(%d+)$`)
	if B and Config.Clips[B] and Config.Clips[B].Buckets then return B, tonumber(Bucket) end
	return Name, nil
end

local function legLen(S): number
	local Leg = S.Model and S.Model:FindFirstChild(`Left Leg`)
	return if Leg and Leg:IsA(`BasePart`) then Leg.Size.Y else 2
end

-- the full piece name for S (a bucketed clip gets the student's leg-length bucket)
function Gestures.Name(S, Name: string): string
	local Base, Bucket = baseOf(Name)
	if Bucket then return Name end
	return F.Name(Base, Config.Clips[Base], legLen(S))
end

local function idOf(Full: string): string?
	if Ids[Full] then return Ids[Full] end
	local Base, Bucket = baseOf(Full)
	local Clip = Config.Clips[Base]
	if not Clip then return nil end
	local Id = if Bucket and Clip.Ids then Clip.Ids[Bucket] else Clip.Id
	if Id and Id ~= 0 then
		Ids[Full] = `rbxassetid://{Id}`
	elseif Studio then
		local Folder = ServerStorage:FindFirstChild(`NHGestures`)
		local KS = Folder and Folder:FindFirstChild(`NHG_{Full}`)
		if not KS then return nil end
		local Ok, Temp = pcall(function() return KeyframeSequenceProvider:RegisterKeyframeSequence(KS) end)
		if not Ok then return nil end
		Ids[Full] = Temp
	else
		return nil
	end
	return Ids[Full]
end
Gestures.IdOf = idOf

local function track(S, Full: string): AnimationTrack?
	S.Tracks = S.Tracks or {}
	local Key = `G:{Full}`
	if S.Tracks[Key] then return S.Tracks[Key] end
	local Id = idOf(Full)
	local Animator = Id and S.Hum and (S.Hum:FindFirstChildOfClass(`Animator`) or Instance.new(`Animator`, S.Hum))
	if not Animator then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = Id
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	local Clip = Config.Clips[(baseOf(Full))]
	T.Looped = Clip and Clip.Loop == true
	T.Priority = Enum.AnimationPriority[Clip and Clip.Priority or `Action`]
	S.Tracks[Key] = T
	return T
end

local function playerNear(P: Vector3, R: number): boolean
	for _, Pl in Players:GetPlayers() do
		local Root = Pl.Character and Pl.Character:FindFirstChild(`HumanoidRootPart`)
		if Root and (Root.Position - P).Magnitude <= R then return true end
	end
	return false
end

local function posture(S, Standing: boolean)
	pcall(function() require(ReplicatedStorage.Config.NpcBuilds).SetPosture(S.Model, Standing) end)
end

function Gestures.Busy(S): boolean
	return Playing[S] ~= nil
end

function Gestures.Active(): number
	return ActiveCount
end

function Gestures.Stop(S, Fade: number?)
	local P = Playing[S]
	if not P then return end
	Playing[S] = nil
	ActiveCount = math.max(0, ActiveCount - 1)
	if P.Track.IsPlaying then P.Track:Stop(Fade or 0.3) end
	S.Gesture = nil
	if S.Model and S.Model.Parent and not S.Seated then posture(S, true) end
end

function Gestures.Play(S, Name: string?, Opts: { [string]: any }?): AnimationTrack?
	if not (Name and S and S.Model and S.Hum and S.Root and S.Model.Parent) then return nil end
	local O = Opts or {}
	local Full = Gestures.Name(S, Name)
	local Clip = Config.Clips[(baseOf(Full))]
	if not Clip then return nil end
	if not O.Force then
		if S.Reacting or S.Leaning or (S.Agent and S.Agent.Moving and not Clip.Walking) then return nil end
		if ActiveCount >= Config.Caps.MaxActive then return nil end
		if os.clock() < (S.GestureReady or 0) then return nil end
		if not playerNear(S.Root.Position, Config.Caps.NearRange) then return nil end
	end
	if S.Seated and not (Clip.Seated or Clip.Upper) then return nil end
	local T = track(S, Full)
	if not T then return nil end
	if Playing[S] then Gestures.Stop(S, 0.2) end
	Token += 1
	local Me = Token
	Playing[S] = { Track = T; Name = Full; Token = Me }
	ActiveCount += 1
	S.Gesture = Full
	S.GestureReady = os.clock() + Config.Caps.Cooldown
	if not (Clip.Upper or S.Seated) then posture(S, false) end
	T:Play(O.Fade or 0.25, O.Weight or 1, O.Speed or 1)
	T.Stopped:Once(function()
		local P = Playing[S]
		if P and P.Token == Me then Gestures.Stop(S, 0) end
	end)
	if O.Seconds then
		task.delay(O.Seconds, function()
			local P = Playing[S]
			if P and P.Token == Me then Gestures.Stop(S, 0.3) end
		end)
	end
	if O.Carry and Clip.Carry then task.spawn(Gestures.Carry, S, Clip.Carry, O.Speed or 1) end
	return T
end

-- the baked root motion: the curve is { t, dx, dz, dyaw } in the root's space at the start (studs, degrees)
function Gestures.Carry(S, Curve: { { number } }, Speed: number?)
	local Root = S.Root
	if not (Root and Root.Parent and Curve and #Curve > 1) then return end
	local Start = Root.CFrame
	local Rate = Speed or 1
	local T0 = os.clock()
	local Done = Vector3.zero
	for I = 2, #Curve do
		local Row = Curve[I]
		while (os.clock() - T0) * Rate < Row[1] do
			RunService.Heartbeat:Wait()
			if not Root.Parent or S.Root ~= Root then return end
		end
		local Want = Start:VectorToWorldSpace(Vector3.new(Row[2], 0, Row[3]))
		local Step = Want - Done
		if Step.Magnitude > 1e-3 then
			if not Space.Clear(S, Step.Unit, Step.Magnitude) then return end -- short of a wall: the clip plays on, the body stops
			Done = Want
		end
		local Yaw = math.rad(Row[4] or 0)
		local Pos = Start.Position + Done
		Root.CFrame = CFrame.new(Pos) * (Start - Start.Position) * CFrame.Angles(0, Yaw, 0)
	end
end

function Gestures.PickFor(S, Hook: string, Ctx: { [string]: any }?): string?
	local C = table.clone(Ctx or {})
	local M = S and S.Model
	if M then
		C.Clique = C.Clique or M:GetAttribute(`Clique`)
		C.Npc = C.Npc or M:GetAttribute(`NpcId`)
	end
	C.Temper = C.Temper or (S and S.Temper)
	C.Moon = if C.Moon ~= nil then C.Moon else workspace:GetAttribute(`NHMoonEvent`) ~= nil
	return F.Pick(Config.Cast, Hook, C, roll)
end

-- a gesture record for a staff model (Social.Npcs): the same shape Schedules' students have
local Records = setmetatable({}, { __mode = `k` }) :: { [Model]: any }
function Gestures.Record(Model: Model)
	local R = Records[Model]
	if R then return R end
	R = { Model = Model; Hum = Model:FindFirstChildOfClass(`Humanoid`); Root = Model:FindFirstChild(`HumanoidRootPart`); Tracks = {}; Up = 3 }
	Records[Model] = R
	return R
end

---| the get-up after being downed (spec §5) |---

local function recordOf(Model: Model): any?
	if Players:GetPlayerFromCharacter(Model) then return nil end
	if Model:GetAttribute(`NHScheduled`) and Host and Host.Students then
		for _, S in Host.Students() do if S.Model == Model then return S end end
		return nil
	end
	if Model:GetAttribute(`NpcId`) then return Gestures.Record(Model) end
	return nil -- combat AI, beasts: untouched
end

function Gestures.GetUp(Model: Model): string?
	local S = recordOf(Model)
	if not S then return nil end
	local Name = Gestures.PickFor(S, `GetUp`) or `Dizzy`
	local Lo, Hi = Config.GetUp.Seconds[1], Config.GetUp.Seconds[2]
	local Seconds = Lo + roll() * (Hi - Lo)
	if S.Agent then pcall(function() S.Agent:Stop() end) end
	S.Reacting = true
	local T = Gestures.Play(S, Name, { Force = true; Seconds = Seconds })
	task.delay(Seconds, function() if S.Model == Model then S.Reacting = false end end)
	if Model:GetAttribute(`NHScheduled`) then
		S.SickUntil = os.clock() + Config.Infirmary.VisitAfter
		S.Replan = true
	end
	return if T then Gestures.Name(S, Name) else nil
end

---| the far stop |---

local Sweep = 0
RunService.Heartbeat:Connect(function(Dt)
	Sweep += Dt
	if Sweep < 1 then return end
	Sweep = 0
	for S, P in Playing do
		if not (S.Model and S.Model.Parent and S.Root) then
			Playing[S] = nil
			ActiveCount = math.max(0, ActiveCount - 1)
		elseif P.Track.Looped and not playerNear(S.Root.Position, Config.Caps.StopFar) then
			Gestures.Stop(S, 0.5)
		end
	end
end)

---| the Studio probe |---

local function probe()
	if not Studio then return end
	local B = ServerStorage:FindFirstChild(`NHGestureProbe`) or Instance.new(`BindableFunction`)
	B.Name = `NHGestureProbe`
	B.Parent = ServerStorage
	local function student(I)
		local L = Host and Host.Students and Host.Students() or {}
		return L[tonumber(I) or 1]
	end
	B.OnInvoke = function(Cmd: string, A: any, Bv: any, Cv: any)
		local Ok, R = pcall(function()
			if Cmd == `Play` then
				local S = student(A)
				local T = Gestures.Play(S, Bv, { Force = Cv == true; Carry = true })
				return { Ok = T ~= nil; Gesture = S and S.Gesture; Active = ActiveCount }
			elseif Cmd == `Stop` then
				Gestures.Stop(student(A)) return { Active = ActiveCount }
			elseif Cmd == `State` then
				local S = student(A)
				local Tracks = {}
				if S and S.Hum then
					local An = S.Hum:FindFirstChildOfClass(`Animator`)
					for _, T in (An and An:GetPlayingAnimationTracks() or {}) do table.insert(Tracks, { Id = T.Animation and T.Animation.AnimationId; W = T.WeightCurrent; P = T.Priority.Name; Speed = T.Speed }) end
				end
				return { Gesture = S and S.Gesture; Reacting = S and S.Reacting; Sick = S and S.SickUntil ~= nil; Seated = S and S.Seated ~= nil; Model = S and S.Model and S.Model:GetFullName(); Pos = S and S.Root and S.Root.Position; Tracks = Tracks }
			elseif Cmd == `Active` then
				return { Active = ActiveCount }
			elseif Cmd == `GetUp` then
				local S = student(A)
				return { Name = S and S.Model and Gestures.GetUp(S.Model) }
			elseif Cmd == `Students` then
				local L = {}
				for I, S in (Host and Host.Students and Host.Students() or {}) do
					table.insert(L, { I = I; Clique = S.Clique; Alive = S.Model ~= nil and S.Model.Parent ~= nil; Pos = S.Root and S.Root.Position })
				end
				return L
			elseif Cmd == `Id` then
				return { Id = idOf(A) }
			elseif Cmd == `DownRecover` then -- the real Downed path, in the game VM
				local S = student(A)
				local Downed = require(ServerScriptService.Services.Features.Downed)
				local Can = Downed.CanBeDowned(S.Model)
				if Can then Downed.Down(S.Model, nil) task.wait(0.5) Downed.Recover(S.Model) task.wait(0.6) end
				return { CanBeDowned = Can; Gesture = S.Gesture; Reacting = S.Reacting; Sick = S.SickUntil ~= nil }
			elseif Cmd == `Near` then -- move the first player next to student A (Studio checks)
				local S = student(A)
				local P = Players:GetPlayers()[1]
				local R = P and P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
				if R and S and S.Root then R.CFrame = S.Root.CFrame * CFrame.new(0, 0, -(tonumber(Bv) or 6)) * CFrame.Angles(0, math.pi, 0) end
				return { Ok = R ~= nil }
			elseif Cmd == `Away` then
				local P = Players:GetPlayers()[1]
				local R = P and P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
				if R then R.CFrame = R.CFrame + Vector3.new(0, 0, tonumber(A) or 200) end
				return { Ok = R ~= nil }
			elseif Cmd == `StartMatch` then
				local M = require(ServerScriptService.Services.Sports.Matches)
				local P = Players:GetPlayers()[1]
				return { Live = M.ForceStart(A or `Gymnasium`, { P }, {}, true) }
			elseif Cmd == `Score` then
				local M = require(ServerScriptService.Services.Sports.Matches).Get(A or `Gymnasium`)
				if M then M:Scored(`A`, 2, nil) end
				return { Ok = M ~= nil }
			elseif Cmd == `EndMatch` then
				local M = require(ServerScriptService.Services.Sports.Matches).Get(A or `Gymnasium`)
				if M then M:End(nil, `Test`) end
				return { Ok = M ~= nil }
			elseif Cmd == `Watchers` then
				local L = {}
				for I, S in (Host and Host.Students and Host.Students() or {}) do
					if S.Seated and S.Seated.Name:find(`BleacherSeat`) then table.insert(L, { I = I; Seat = S.Seated.Name; Gesture = S.Gesture; Clique = S.Clique }) end
				end
				return L
			elseif Cmd == `SitBleacher` then
				local CS = game:GetService(`CollectionService`)
				local P = Players:GetPlayers()[1]
				local H = P and P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
				local Seat = nil
				for _, M in CS:GetTagged(`NHBleacherSeat`) do local St = M:FindFirstChild(`NHPlayerSeat`) if St and not St.Occupant then Seat = St break end end
				if not (Seat and H) then return { Ok = false; Seats = #CS:GetTagged(`NHBleacherSeat`) } end
				P.Character:PivotTo(Seat.CFrame + Vector3.new(0, 3, 0))
				task.wait(0.2)
				Seat:Sit(H)
				task.wait(0.5)
				return { Ok = H.SeatPart == Seat; Seat = Seat.Parent.Name; Prompt = Seat:FindFirstChild(`SitPrompt`) ~= nil }
			elseif Cmd == `Stand` then
				local P = Players:GetPlayers()[1]
				local H = P and P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
				if H then H.Sit = false H.Jump = true end
				task.wait(0.5)
				return { Seated = H and H.SeatPart ~= nil }
			end
			local Inf = ServerScriptService.Services.Features:FindFirstChild(`Infirmary`)
			if Inf then
				local M = require(Inf)
				if M.Probe then return M.Probe(Cmd, A, Bv, Cv) end
			end
			return { Error = `unknown command {Cmd}` }
		end)
		return if Ok then R else { Error = tostring(R) }
	end
end

function Gestures.Init(H)
	Host = H
end

task.defer(function()
	probe()
	local Ok, Downed = pcall(function() return require(ServerScriptService.Services.Features.Downed) end)
	if Ok and Downed and Downed.OnRecovered then
		Downed.OnRecovered:Connect(function(Target)
			if typeof(Target) == `Instance` and Target:IsA(`Model`) then task.spawn(Gestures.GetUp, Target) end
		end)
	end
end)

return Gestures
