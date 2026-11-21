--!strict
--[[
	CineBeat (client). StarterPlayer.StarterPlayerScripts.Controllers.CineBeat   (2.35.0, spec 2026-11-20 §3)
	A walk-and-talk segment: the player keeps moving; the camera follows a CineRigs rig (nudgeable), lines and cues fire
	on time / place / proximity / idle / a prompt's result, and the beat ends on its trigger, returning the next segment.
	On Lead and Side rigs the stick is read against the beat's travel direction (spec delta 4).

	The beat camera is Scriptable under the director's "Cine" lease, but the controls stay ON (never CineActor.Begin).

	The way in (spec §2: a beat hands to and from cuts like any seamless seam): the rig's damped camera starts settled on its
	own goal, and the screen blends from the incoming camera (Entry.From: the cut's last shot as it would carry on, or the
	live gameplay camera when a seamless cut opens on a beat) onto it with CineSeam's ease and length. An exponential
	damp started at the old camera would leave with a step in velocity (a visible kick); the smootherstep blend leaves
	with the incoming camera's own velocity and lands on the rig's. NHCineSeam is Entry.Phase ("In" when the cut opens on
	this beat, "BeatIn" after shots) during that blend, then "Beat".

	The way out: the rig keeps running after the beat (Shared.Run hands back Rig.Step through Out.Rig), so the director's
	blend out (or the next cut's glide in) starts from a camera that is still moving with the player.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Player = Players.LocalPlayer
local Shared = {}
local BIND = `NHBeat`
local HALFLIFE = 0.18

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

local function trigger(On: string?, Ctx, Clock: number, Root: BasePart, Idle: number, Results): boolean
	if typeof(On) ~= `string` then return false end
	if On == `start` then return Clock >= 0 end
	local Kind, A, B = On:match(`^(%a+):([^:]+):?(.*)$`)
	if Kind == `t` then return Clock >= (tonumber(A) or math.huge) end
	if Kind == `idle` then return Idle >= (tonumber(A) or math.huge) end
	if Kind == `enter` then
		local M = Ctx.Mark(A)
		return M ~= nil and ((M.Position - Root.Position) * Vector3.new(1, 0, 1)).Magnitude <= math.max(M.Size.X, M.Size.Z, 4) / 2
	end
	if Kind == `near` then
		local Pos = posOf(Ctx.Actor(A) or Ctx.Mark(A))
		return Pos ~= nil and (Pos - Root.Position).Magnitude <= (tonumber(B) or 8)
	end
	if Kind == `prompt` then return Results[A] == true end
	return false
end

-- the rig: a damped camera around the player that can be stepped on its own (Run steps it every frame, and the director
-- keeps stepping it through the blend out). Step uses real frame time (os.clock), so stepping twice in a frame is harmless.
function Shared.Rig(Spec, Ctx, Root: BasePart)
	local Rigs = require(ReplicatedStorage.Functions.CineRigs)
	local Frame = Spec.frame or {}
	local Kind = Spec.rig or `Follow`
	local R = { Travel = Root.CFrame.LookVector; NudgeState = { yaw = 0, pitch = 0 }; Last = os.clock(); Idle = 0 }
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

-- Entry (from the director, optional): { From = () -> (CFrame, number), Len = seconds, Phase = "In" | "BeatIn" }
-- Out (optional table): Out.Rig is set to the rig (the director keeps stepping it for the blend out)
-- Look (optional): the cut's look carried over from the shots before (Handle:detachLook); its DOF keeps focus on you
function Shared.Run(Cut, SegName: string, Spec, Ctx, Entry: any?, Out: any?, Look: any?): string?
	local Seam = require(ReplicatedStorage.Functions.CineSeam)
	local UI = require(script.Parent.Gui.CineUI)
	local C = Player.Character
	local Hum = C and C:FindFirstChildOfClass(`Humanoid`)
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not (Hum and Root) then return Spec.ends and Spec.ends.next end
	local Cam = workspace.CurrentCamera
	local Move = Spec.move or {}
	-- movement limits (spec §3)
	local SpeedWas = Hum.WalkSpeed
	if typeof(Move.speed) == `number` then Hum.WalkSpeed = SpeedWas * Move.speed end
	if Move.sprint == false then
		Player:SetAttribute(`NHBeatNoSprint`, true)                                     -- Movement.Sprint reads this
		pcall(function() require(ReplicatedStorage.Remotes.UnPackets).Sprint:Fire(`Release`) end) -- already sprinting: stop
	end
	local Remote = ReplicatedStorage:WaitForChild(`NHCine`)
	if Move.crouch then (Remote :: RemoteEvent):FireServer({ Kind = `BeatCrouch`; On = true }) end -- the game's own crouch (spec delta 5)
	-- Lead and Side: the stick against the beat's travel direction, never the camera's (spec delta 4). This ControlModule
	-- turns camera-relative input into a world vector before moveFunction, so the raw stick is read from the active
	-- controller and mapped onto the travel direction the beat started with (fixed, so steering can't feed back into it).
	local Ctl = controls()
	local MoveWas = Ctl and (Ctl :: any).moveFunction
	local Travel0 = Vector3.new(Root.CFrame.LookVector.X, 0, Root.CFrame.LookVector.Z)
	Travel0 = if Travel0.Magnitude > 1e-3 then Travel0.Unit else Vector3.new(0, 0, -1)
	if Ctl and (Spec.rig == `Lead` or Spec.rig == `Side`) and typeof(MoveWas) == `function` then
		local Fwd, Right = Travel0, Travel0:Cross(Vector3.yAxis)
		;(Ctl :: any).moveFunction = function(P, Vec: Vector3, Relative: boolean)
			local Active = (Ctl :: any).activeController
			local Ok, Raw, CamRel = pcall(function() return Active:GetMoveVector(), Active:IsMoveVectorCameraRelative() end)
			if Ok and CamRel and typeof(Raw) == `Vector3` and Raw.Magnitude > 0 then
				MoveWas(P, Right * Raw.X + Fwd * -Raw.Z, false)
			else
				MoveWas(P, Vec, Relative)                                               -- click-to-move, MoveTo: as is
			end
		end
	end
	local Rig = Shared.Rig(Spec, Ctx, Root)
	if Out then Out.Rig = Rig end
	local Dof: DepthOfFieldEffect? = nil
	for _, Fx in (Look and Look.effects) or {} do if Fx:IsA(`DepthOfFieldEffect`) then Dof = Fx end end
	local Fired, Results = {}, {}
	local Clock = 0
	local Last = os.clock()
	local EntryLen = 0
	if Entry then
		-- as long as the glide in would take for the same change (CineSeam: 0.6-1.0 s)
		local FromCF = Entry.From()
		EntryLen = Entry.Len or Seam.Length(FromCF, Rig.Out, false)
	end
	local Phase = if EntryLen > 0 then (Entry.Phase or `BeatIn`) else `Beat`
	if Cut.Live then Player:SetAttribute(`NHCineSeam`, Phase) end
	local Thread = coroutine.running()
	local Finished = false
	local Next: string? = nil

	local function cleanup()
		pcall(function() RunService:UnbindFromRenderStep(BIND) end)
		if typeof(Move.speed) == `number` and Hum.Parent then Hum.WalkSpeed = SpeedWas end
		Player:SetAttribute(`NHBeatNoSprint`, nil)
		if Move.crouch then (Remote :: RemoteEvent):FireServer({ Kind = `BeatCrouch`; On = false }) end
		if Ctl and MoveWas then (Ctl :: any).moveFunction = MoveWas end
	end
	local function finish(To: string?)
		if Finished then return end
		Finished = true
		Next = To
		cleanup()
		if coroutine.status(Thread) == `suspended` then task.spawn(Thread) end
	end

	local function say(L)
		local Text = if typeof(L.text) == `function` then L.text(Ctx) else tostring(L.text)
		pcall(UI.Subtitle, L.who or ``, Text, L.secs or math.clamp(#Text / 14 + 0.8, 1.4, 5))
		-- the talking face (FaceTalk visemes) on whoever speaks: "You" is your own character
		pcall(function()
			local FT = require(script.Parent.Character.FaceTalk)
			local Who = if L.who == `You` then Player.Character else Ctx.Actor(L.who)
			if Who and FT.Say then FT.Say(Who, Text, L.expr) end
		end)
	end
	local function openPrompt()
		-- a doc 12 prompt inside the beat (the hedge dive): judged here; its outcome feeds prompt:<Outcome> triggers
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

	local function step()
		if Finished then return end
		-- the cut ended (skip, a respawn, a newer cut) or moved on (the server's Segment): stop, and leave the camera alone
		if not Cut.Live or Cut.Seg ~= SegName then finish(nil) return end
		local Now = os.clock()
		local Dt = math.min(Now - Last, 0.1)
		Last = Now
		Clock += Dt
		local RigCF, RigFov = Rig.Step(UserInputService:GetMouseDelta())
		local CF, Fov = RigCF, RigFov
		if EntryLen > 0 and Clock < EntryLen then
			local E = Seam.Ease(Clock / EntryLen)
			local FromCF, FromFov = Entry.From()
			CF = Seam.Blend(FromCF, RigCF, E)
			Fov = FromFov + (RigFov - FromFov) * E
		elseif Phase ~= `Beat` then
			Phase = `Beat`
			Player:SetAttribute(`NHCineSeam`, `Beat`)
		end
		Cam.CameraType = Enum.CameraType.Scriptable
		Cam.CFrame = CF
		Cam.FieldOfView = math.clamp(Fov, 1, 120)
		if Dof then
			local Head = C and C:FindFirstChild(`Head`) :: BasePart?
			if Head then Dof.FocusDistance = (CF.Position - Head.Position).Magnitude end
		end
		for I, L in Spec.lines or {} do
			if not Fired[`L` .. I] and trigger(L.on, Ctx, Clock, Root, Rig.Idle, Results) then
				Fired[`L` .. I] = true
				say(L)
			end
		end
		for I, Q in Spec.cues or {} do
			if not Fired[`C` .. I] and trigger(Q.on, Ctx, Clock, Root, Rig.Idle, Results) then
				Fired[`C` .. I] = true
				local Fn = Cut.Built and Cut.Built.cues and Cut.Built.cues[Q.run]
				if typeof(Fn) == `function` then task.spawn(Fn, Ctx) end
			end
		end
		if Spec.prompt and not Fired.Prompt and trigger(Spec.prompt.on or `start`, Ctx, Clock, Root, Rig.Idle, Results) then
			Fired.Prompt = true
			local Ok, Err = pcall(openPrompt)
			if not Ok then warn(`[CineBeat] prompt: {Err}`) end
		end
		if Spec.ends and trigger(Spec.ends.on, Ctx, Clock, Root, Rig.Idle, Results) then
			-- the camera was written this frame; the continuation (next segment, or the blend out) starts in this frame
			finish(Spec.ends.next or `__end`)
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
