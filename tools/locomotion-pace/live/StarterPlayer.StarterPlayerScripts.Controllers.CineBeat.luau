--!strict
--[[
	CineBeat (client). StarterPlayer.StarterPlayerScripts.Controllers.CineBeat   (2.35.0, spec 2026-11-20 §3)
	A walk-and-talk segment: the player keeps moving; the camera follows a CineRigs rig (nudgeable with the mouse or the
	right stick), lines and cues fire on time / place / proximity / idle / a prompt's result, and the beat ends on its
	trigger, returning the next segment. On Lead and Side rigs the stick is read against the beat's travel direction
	(spec delta 4): frame.travel (a mark), else toward the ends' enter: mark, else the facing at the beat's start.

	The beat camera is Scriptable under the director's "Cine" lease, but the controls stay ON (never CineActor.Begin).

	The way in (spec §2: a beat hands to and from cuts like any seamless seam): the rig's damped camera starts settled on its
	own goal, and the screen blends from the incoming camera (Entry.From: the cut's last shot as it would carry on, or the
	live gameplay camera when a seamless cut opens on a beat) onto it with CineSeam's ease and length. An exponential
	damp started at the old camera would leave with a step in velocity (a visible kick); the smootherstep blend leaves
	with the incoming camera's own velocity and lands on the rig's. NHCineSeam is Entry.Phase ("In" when the cut opens on
	this beat, "BeatIn" after shots) during that blend, then "Beat". A cut that opens on a beat eases its grade in over
	that blend (Entry.Grade), as the glide in does.

	The way out: the rig keeps running after the beat (Out.Rig), so the director's blend out (or the next shots' glide
	in) starts from a camera that is still moving with the player.

	(fix round 1) Side effects (WalkSpeed, the sprint block, crouch, the stick remap) are applied only after the setup that
	can fail, and the cleanup that undoes them exists first; an error in a frame ends the beat through that cleanup.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Player = Players.LocalPlayer
local Shared = {}
local BIND = `NHBeat`
local HALFLIFE = 0.18
local WALK = require(game:GetService(`ReplicatedStorage`).Config.Locomotion).Speeds.Walk -- (locomotion-pace, was 12) Sprint's Release
local SPRINTING = 20         -- at or above this WalkSpeed you're sprinting (sprint writes 22 / 30)
local CROUCH = 7             -- Services.Player.Crouch's CROUCH_SPEED: the speed the game's own crouch holds
local STICK_RATE = 480       -- right stick at full tilt: 480 "pixels" a second = 120 degrees a second of nudge
local DEADZONE = 0.15
local STANDING = 0.8        -- seconds standing before a held crouch is asserted again
local KINDS = { t = true; idle = true; enter = true; near = true; prompt = true; fail = true }

local function controls()
	local Ok, C = pcall(function() return require(Player.PlayerScripts:WaitForChild(`PlayerModule`)):GetControls() end)
	return if Ok then C else nil
end

local function posOf(Who: Instance?): Vector3?
	if not Who then return nil end
	if Who:IsA(`Model`) then return Who:GetPivot().Position end
	if Who:IsA(`BasePart`) then return Who.Position end
	return nil
end

local function parse(On: any): (string?, string?, string?)
	if typeof(On) ~= `string` then return nil, nil, nil end
	if On == `start` or On == `fail` then return On, nil, nil end
	local Kind, A, B = On:match(`^(%a+):([^:]+):?(.*)$`)
	return Kind, A, B
end

function Shared.ValidTrigger(On: any): boolean
	local Kind, A = parse(On)
	if Kind == `start` or Kind == `fail` then return true end
	if not (Kind and KINDS[Kind]) then return false end
	if (Kind == `t` or Kind == `idle`) and tonumber(A) == nil then return false end
	return true
end

-- (task 11) a beat's `ends` is one { on, next } table or a list of them (the first whose trigger holds wins); an entry's
-- keepCrouch = true hands the game's crouch on to whatever comes next (a beat that crouches too, a cut that carries the
-- crouch walk on) instead of standing the player up at this beat's end
local function endsOf(Spec): { any }
	local E = Spec.ends
	if typeof(E) ~= `table` then return {} end
	if E.on ~= nil then return { E } end
	return E
end
Shared.EndsOf = endsOf

local function trigger(On: string?, Ctx, Clock: number, Root: BasePart, Idle: number, Results, Cut): boolean
	local Kind, A, B = parse(On)
	if Kind == `start` then return Clock >= 0 end
	-- (task 11) `fail`: the cut's Built.Fail was set (a cue's soft failure). Only the ends loop clears it, when an end on it
	-- fires (fix round 1, M6: a line or cue asking about `fail` must not eat it)
	if Kind == `fail` then
		local Built = Cut and Cut.Built
		return Built ~= nil and Built.Fail == true
	end
	if Kind == `t` then return Clock >= (tonumber(A) or math.huge) end
	if Kind == `idle` then return Idle >= (tonumber(A) or math.huge) end
	if Kind == `enter` then
		local M = Ctx.Mark(A)
		-- (task 14) `enter:<Mark>:<radius>`: an explicit radius in studs (the mark's own size, at least 4, is the default), so a beat can end
		-- earlier and leave the last few studs to an on-foot approach
		return M ~= nil and ((M.Position - Root.Position) * Vector3.new(1, 0, 1)).Magnitude <= (tonumber(B) or math.max(M.Size.X, M.Size.Z, 4) / 2)
	end
	if Kind == `near` then
		local Pos = posOf(Ctx.Actor(A) or Ctx.Mark(A))
		return Pos ~= nil and (Pos - Root.Position).Magnitude <= (tonumber(B) or 8)
	end
	if Kind == `prompt` then return A ~= nil and Results[A] == true end
	return false
end

local function flat(V: Vector3): Vector3?
	local F = Vector3.new(V.X, 0, V.Z)
	return if F.Magnitude > 1e-3 then F.Unit else nil
end

-- the beat's travel direction (spec delta 4): frame.travel (a mark: toward it), else toward the ends' enter: zone mark,
-- else the way you face as the beat starts
function Shared.TravelOf(Spec, Ctx, Root: BasePart): Vector3
	local Frame = Spec.frame or {}
	if typeof(Frame.travel) == `string` then
		local M = Ctx.Mark(Frame.travel)
		local D = M and flat(M.Position - Root.Position)
		if D then return D end
	end
	for _, E in endsOf(Spec) do
		local Kind, A = parse(E.on)
		if Kind == `enter` and A then
			local M = Ctx.Mark(A)
			local D = M and flat(M.Position - Root.Position)
			if D then return D end
		end
	end
	return flat(Root.CFrame.LookVector) or Vector3.new(0, 0, -1)
end

-- the nudge input this frame: the mouse's delta plus the right stick (as a delta at STICK_RATE), past a dead zone
local function nudgeInput(Dt: number): Vector2
	local In = UserInputService:GetMouseDelta()
	if UserInputService:GetGamepadConnected(Enum.UserInputType.Gamepad1) then
		for _, S in UserInputService:GetGamepadState(Enum.UserInputType.Gamepad1) do
			if S.KeyCode == Enum.KeyCode.Thumbstick2 then
				local P = Vector2.new(S.Position.X, -S.Position.Y)
				if P.Magnitude > DEADZONE then In += P * STICK_RATE * Dt end
			end
		end
	end
	return In
end

-- the rig: a damped camera around the player that can be stepped on its own (Run steps it every frame, and the director
-- keeps stepping it through the blend out or the next glide in). Step uses real frame time (os.clock), so stepping twice
-- in a frame is harmless.
function Shared.Rig(Spec, Ctx, Root: BasePart, Travel: Vector3?)
	local Rigs = require(ReplicatedStorage.Functions.CineRigs)
	local Frame = Spec.frame or {}
	local Kind = Spec.rig or `Follow`
	local R = { Travel = Travel or Root.CFrame.LookVector; NudgeState = { yaw = 0, pitch = 0 }; Last = os.clock(); Idle = 0 }
	local function also(): Vector3?
		if not Frame.also then return nil end
		return posOf(Ctx.Actor(Frame.also) or Ctx.Mark(Frame.also))
	end
	local Goal, GoalFov = Rigs.Target(Kind, Root.CFrame, also(), R.Travel, Frame)
	R.Current, R.Fov = Goal, GoalFov
	R.Out, R.OutFov = Goal, GoalFov
	function R.Step(Input: Vector2?): (CFrame, number)
		local Now = os.clock()
		local Dt = math.min(Now - R.Last, 0.1)
		if Dt <= 1e-5 or not Root.Parent then return R.Out, R.OutFov end
		R.Last = Now
		local Vel = Root.AssemblyLinearVelocity * Vector3.new(1, 0, 1)
		if Vel.Magnitude > 2 then
			R.Travel = R.Travel:Lerp(Vel.Unit, math.min(1, Dt * 2))
			R.Idle = 0
		else
			R.Idle += Dt
		end
		local G, GFov = Rigs.Target(Kind, Root.CFrame, also(), R.Travel, Frame)
		R.Current = Rigs.Damp(R.Current, G, Dt, HALFLIFE)
		R.Fov += (GFov - R.Fov) * (1 - 0.5 ^ (Dt / HALFLIFE))
		local N = Rigs.Nudge(R.NudgeState, Input or Vector2.zero, Dt)
		R.Out = R.Current * CFrame.Angles(math.rad(N.Y), math.rad(N.X), 0)
		R.OutFov = R.Fov
		return R.Out, R.OutFov
	end
	return R
end

-- Entry (from the director, optional): { From = () -> (CFrame, number), Len = seconds?, Phase = "In" | "BeatIn",
--   Grade = { g = the cut's grade, base = the exposure before it }? (a cut that opens on this beat: eased in over the blend) }
-- Out (optional table): Out.Rig is set to the rig (the director keeps stepping it after the beat)
-- Look (optional): the cut's look (Handle:detachLook, or the one Entry.Grade builds: its effects are appended); a DOF in
--   it keeps focus on you
function Shared.Run(Cut, SegName: string, Spec, Ctx, Entry: any?, Out: any?, Look: any?): string?
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local UI = require(script.Parent.Gui.CineUI)
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Ends = endsOf(Spec)
	if not (Hum and Root) then return Ends[1] and Ends[1].next end
	local AnyEnd = false
	for _, E in Ends do
		if Shared.ValidTrigger(E.on) then AnyEnd = true
		else warn(`[CineBeat] {Cut.Id}.{SegName}: ends.on {tostring(E.on)} is unreadable`) end
	end
	if not AnyEnd then
		warn(`[CineBeat] {Cut.Id}.{SegName}: no readable ends.on; the beat ends only with the cut`)
	end
	local Cam = workspace.CurrentCamera
	local Move = Spec.move or {}
	local Remote = ReplicatedStorage:WaitForChild(`NHCine`) :: RemoteEvent

	-- setup that can fail, before anything is changed on the player
	local Travel0 = Shared.TravelOf(Spec, Ctx, Root)
	local Rig = Shared.Rig(Spec, Ctx, Root, Travel0)
	if Out then Out.Rig = Rig end
	local EntryLen = 0
	if Entry then
		local FromCF = Entry.From()
		EntryLen = Entry.Len or Seam.Length(FromCF, Rig.Out, false) -- as long as the glide in for the same change
	end
	local Grade = Entry and Entry.Grade
	local Lib = if Grade then require(ReplicatedStorage.Cine) else nil
	local Dof: DepthOfFieldEffect? = nil
	for _, Fx in (Look and Look.effects) or {} do if Fx:IsA(`DepthOfFieldEffect`) then Dof = Fx end end

	-- the cleanup exists before the first side effect; each side effect records what it changed
	local Applied: number? = nil      -- the WalkSpeed this beat wrote
	local SpeedBase = WALK            -- and the speed it goes back to
	local SpeedConn: RBXScriptConnection? = nil
	local NoSprint, Crouched = false, false
	local Ctl, MoveWas = nil, nil
	local Unbound = false
	local function cleanup(KeepCrouch: boolean?)
		if not Unbound then Unbound = true pcall(function() RunService:UnbindFromRenderStep(BIND) end) end
		if SpeedConn then SpeedConn:Disconnect() SpeedConn = nil end
		-- only our own speed goes back (the server, a stun or crouch may have written theirs since)
		-- (fix round 1, I1) SpeedBase is the speed the beat found for the state it hands on (crouch speed for a crouching player,
		-- so a keepCrouch end leaves the crouch speed, never the standing one)
		if Applied and Hum.Parent and math.abs(Hum.WalkSpeed - Applied) < 1e-3 then Hum.WalkSpeed = SpeedBase end
		Applied = nil
		if NoSprint then Player:SetAttribute(`NHBeatNoSprint`, nil) NoSprint = false end
		if Crouched and not KeepCrouch then Remote:FireServer({ Kind = `BeatCrouch`; On = false }) end
		Crouched = false
		if Ctl and MoveWas then (Ctl :: any).moveFunction = MoveWas end
		Ctl, MoveWas = nil, nil
	end

	-- movement limits (spec §3)
	if Move.sprint == false then
		NoSprint = true
		Player:SetAttribute(`NHBeatNoSprint`, true)                                     -- Movement.Sprint reads this
		pcall(function() require(ReplicatedStorage.Remotes.UnPackets).Sprint:Fire(`Release`) end) -- already sprinting: stop
	end
	if typeof(Move.speed) == `number` then
		-- from the walk base: a beat that starts mid-sprint scales the walk (Sprint's Release writes it), not the sprint
		local Base = Hum.WalkSpeed
		if Move.sprint == false and (Hum:GetAttribute(`Sprint`) or Base >= SPRINTING) then Base = WALK end
		-- (fix round 1, I1) a crouched player, or a beat that crouches, scales the crouch speed: the standing speed the previous
		-- beat handed back (or the sprint's) must never be what a crouching beat multiplies, and the server's own crouch write
		-- (7) doesn't replicate again when the player is already crouched
		if Hum:GetAttribute(`Crouch`) == true or Move.crouch then Base = CROUCH end
		SpeedBase = Base
		Applied = Base * Move.speed
		Hum.WalkSpeed = Applied :: number
		-- the walk base written back over ours (the server's sprint Release landing after this): scale it again
		SpeedConn = Hum:GetPropertyChangedSignal(`WalkSpeed`):Connect(function()
			if Applied and math.abs(Hum.WalkSpeed - SpeedBase) < 1e-3 then Hum.WalkSpeed = Applied :: number end
		end)
	end
	if Move.crouch then
		Crouched = true
		Remote:FireServer({ Kind = `BeatCrouch`; On = true })                         -- the game's own crouch (spec delta 5)
	end
	-- Lead and Side: the stick against the beat's travel direction, never the camera's (spec delta 4). This ControlModule
	-- turns camera-relative input into a world vector before moveFunction, so the raw stick is read from the active
	-- controller and mapped onto the beat's travel direction (fixed, so steering can't feed back into it).
	if Spec.rig == `Lead` or Spec.rig == `Side` then
		local Got = controls()
		local Was = Got and (Got :: any).moveFunction
		if Got and typeof(Was) == `function` then
			Ctl, MoveWas = Got, Was
			local Fwd, Right = Travel0, Travel0:Cross(Vector3.yAxis)
			;(Got :: any).moveFunction = function(P, Vec: Vector3, Relative: boolean)
				local Active = (Got :: any).activeController
				local Ok, Raw, CamRel = pcall(function() return Active:GetMoveVector(), Active:IsMoveVectorCameraRelative() end)
				if Ok and CamRel and typeof(Raw) == `Vector3` and Raw.Magnitude > 0 then
					Was(P, Right * Raw.X + Fwd * -Raw.Z, false)
				else
					Was(P, Vec, Relative)                                               -- click-to-move, MoveTo: as is
				end
			end
		end
	end

	local Fired, Results = {}, {}
	local Clock = 0
	local Last = os.clock()
	local Phase = if EntryLen > 0 then ((Entry :: any).Phase or `BeatIn`) else `Beat`
	if Cut.Live then Player:SetAttribute(`NHCineSeam`, Phase) end
	local Thread = coroutine.running()
	local Finished = false
	local Next: string? = nil
	local GradeDone = false
	local SawCrouch, StandSince = false, nil :: number?
	local Said = false                -- "Stay low." shows once per stand-up

	local function finish(To: string?, KeepCrouch: boolean?)
		if Finished then return end
		Finished = true
		Next = To
		cleanup(KeepCrouch)
		if coroutine.status(Thread) == `suspended` then task.spawn(Thread) end
	end

	local function say(L)
		-- (final fix round) a line's text function that errors must not take the frame (and the beat) with it
		local Got, Value = pcall(function() return if typeof(L.text) == `function` then L.text(Ctx) else tostring(L.text) end)
		if not Got then warn(`[CineBeat] {Cut.Id}.{SegName}: a line's text errored: {Value}`) return end
		local Text = tostring(Value)
		pcall(UI.Subtitle, L.who or ``, Text, L.secs or math.clamp(#Text / 14 + 0.8, 1.4, 5))
		-- the talking face (FaceTalk visemes) on whoever speaks: "You" is your own character
		pcall(function()
			local FT = require(script.Parent.Character.FaceTalk)
			local Who = if L.who == `You` then Player.Character else Ctx.Actor(L.who)
			if Who and FT.Say then FT.Say(Who, Text, L.expr) end
		end)
	end
	local function openPrompt()
		-- a doc 12 prompt inside the beat (the hedge dive): judged here for now (server judging is a later slice); its
		-- outcome feeds prompt:<Outcome> triggers
		local P = Spec.prompt
		local Judge = require(ReplicatedStorage.Functions.CineJudge)
		Player:SetAttribute(`NHCinePrompt`, P.kind)
		require(script.Parent.CinePrompt).Open(P, { Reduced = Ctx.Reduced; Touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled }, function(Input)
			Player:SetAttribute(`NHCinePrompt`, nil)
			if Finished then return end
			local Ok, Outcome = pcall(Judge.Evaluate, P, Input)
			if Ok and typeof(Outcome) == `string` then Results[Outcome] = true end
			Results.Any = true
		end)
	end
	local function grade(W: number)
		if not (Grade and Lib) then return end
		;(Lib :: any).applyGrade(Grade.g, W, Grade.base)
		if Look and not Look.Collected then
			Look.Collected = true
			for _, N in { `CineGrade`, `CineBloom` } do
				local Fx = game:GetService(`Lighting`):FindFirstChild(N)
				if Fx then table.insert(Look.effects, Fx) end
			end
		end
	end

	local function frame()
		local Now = os.clock()
		local Dt = math.min(Now - Last, 0.1)
		Last = Now
		Clock += Dt
		local RigCF, RigFov = Rig.Step(nudgeInput(Dt))
		local CF, Fov = RigCF, RigFov
		if EntryLen > 0 and Clock < EntryLen then
			local E = Seam.Ease(Clock / EntryLen)
			local FromCF, FromFov = (Entry :: any).From()
			CF = Seam.Blend(FromCF, RigCF, E)
			Fov = FromFov + (RigFov - FromFov) * E
			grade(E)
		else
			if not GradeDone then GradeDone = true grade(1) end
			if Phase ~= `Beat` then
				Phase = `Beat`
				Player:SetAttribute(`NHCineSeam`, `Beat`)
			end
		end
		Cam.CameraType = Enum.CameraType.Scriptable
		Cam.CFrame = CF
		Cam.FieldOfView = math.clamp(Fov, 1, 120)
		if Dof then
			local Head = C and C:FindFirstChild(`Head`) :: BasePart?
			if Head then Dof.FocusDistance = (CF.Position - Head.Position).Magnitude end
		end
		for I, L in Spec.lines or {} do
			if not Fired[`L` .. I] and trigger(L.on, Ctx, Clock, Root, Rig.Idle, Results, Cut) then
				Fired[`L` .. I] = true
				say(L)
			end
		end
		for I, Q in Spec.cues or {} do
			-- a cue with `every` (seconds) is asked again while its trigger holds (the cue itself decides whether it matters:
			-- standing up near a sleeping dog); otherwise it fires once
			local Last = Fired[`C` .. I]
			if (Last == nil or (Q.every and Clock - (Last :: number) >= Q.every)) and trigger(Q.on, Ctx, Clock, Root, Rig.Idle, Results, Cut) then
				Fired[`C` .. I] = Clock
				local Fn = Cut.Built and Cut.Built.cues and Cut.Built.cues[Q.run]
				if typeof(Fn) == `function` then task.spawn(Fn, Ctx) end
			end
		end
		if Spec.prompt and not Fired.Prompt and trigger(Spec.prompt.on or `start`, Ctx, Clock, Root, Rig.Idle, Results, Cut) then
			Fired.Prompt = true
			local Ok, Err = pcall(openPrompt)
			if not Ok then warn(`[CineBeat] prompt: {Err}`) end
		end
		for _, E in Ends do
			if not Finished and trigger(E.on, Ctx, Clock, Root, Rig.Idle, Results, Cut) then
				-- the camera was written this frame; the continuation (next segment, or the blend out) starts in this frame
				if parse(E.on) == `fail` and Cut.Built then Cut.Built.Fail = nil end
				finish(E.next or `__end`, E.keepCrouch == true)
			end
		end
		if Finished then return end
		-- a speed of 0 means stand still (the server's crouch writes its own walk speed over ours)
		if Applied == 0 and Hum.WalkSpeed ~= 0 then Hum.WalkSpeed = 0 end
		-- (task 11) the game's crouch is held: when it drops (and it was up) and stays down for STANDING seconds (a beat's own
		-- cues judge a stand-up first: standing near a sleeping dog is a soft fail, not something to undo), crouch again and say so
		if Crouched then
			if Hum:GetAttribute(`Crouch`) == true then
				SawCrouch, StandSince, Said = true, nil, false
			elseif SawCrouch then
				StandSince = StandSince or Clock
				if Clock - StandSince >= STANDING then
					-- (fix round 1, M5) asked again every STANDING seconds until it lands (the server refuses while you're busy)
					StandSince = Clock
					Remote:FireServer({ Kind = `BeatCrouch`; On = true })
					if not Said then Said = true pcall(UI.Subtitle, ``, `Stay low.`, 1.2) end
				end
			end
		end
	end
	local function step()
		if Finished then return end
		-- the cut ended (skip, a respawn, a newer cut) or moved on (the server's Segment): stop, and leave the camera alone
		if not Cut.Live or Cut.Seg ~= SegName then finish(nil) return end
		local Ok, Err = pcall(frame)
		if not Ok then
			warn(`[CineBeat] {Cut.Id}.{SegName}: {Err}`)
			-- (final fix round) an error is not the cut's soft failure: carry on along the first end that isn't a `fail` one
			local Carry
			for _, E in Ends do
				if parse(E.on) ~= `fail` then Carry = E break end
			end
			Carry = Carry or Ends[1]
			finish(Carry and Carry.next or `__end`) -- the beat's own cleanup; the cut carries on (or ends) from here
		end
	end

	RunService:BindToRenderStep(BIND, Enum.RenderPriority.Camera.Value + 1, step)
	step() -- this frame too: the shot player that handed over didn't write the camera on its last step
	if not Finished then coroutine.yield() end
	if Next == `__end` then return nil end
	return Next
end

function Shared.OnStart() end

return Shared
