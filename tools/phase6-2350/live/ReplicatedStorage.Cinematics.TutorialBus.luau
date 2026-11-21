--[[
	TutorialBus (doc 15 §5 beat 10, the ending). Seamless: you're waiting at the stop (the TheBus chain's loop), the camera
	glides in over your shoulder, the black bus pulls in out of the fog (BrakeStop), the doors hiss open (DoorsOpen), the
	driver turns his head (DriverTurn), you step on (the chain's TheBus2), the doors close, it pulls away, and the frame
	freezes on the title card (Def.EndHold: no glide out; the title stays until the Prologue starts). Set BusStop
	(tools/phase6-2350/stage/hometown.lua).

	The bus is the player's own copy (Controllers.Hometown.Cast): Wickfield is private, so each player moves their own bus
	and the shared model never moves. Its AnimationController gets an Animator if it has none. Every bus clip authors the
	whole rig (all bones), so they play one after another, each held on its last frame until the next one starts (a clip
	that ends falls back to the rest pose, which is not an assembled bus); every track loaded is stopped and destroyed when
	the cut ends (Ctx.OnEnd).

	Timing: the TheBus chain's loop leaves on its exit phase (5.133 s into a 10.667 s loop, so 16.15 s after the cut's
	first frame with the 0.35 s turn onto the mark); the cue below holds the loop until 15.0 so TheBus2 (the step on) starts at
	~16.15 s, on the "You step on" shot. Everything after it is set from that.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local Config = require(ReplicatedStorage.Config.Cine)
local Def = { Set = `BusStop`; Seamless = true; EndHold = true }

local function controllers()
	local Player = Players.LocalPlayer
	return if Player then Player.PlayerScripts:FindFirstChild(`Controllers`) else nil
end

function Def.Build(Ctx)
	local Me = Ctx.Self
	local Ctl = controllers()
	local Actor = Ctl and require(Ctl.CineActor) or nil
	local Hometown = Ctl and require(Ctl.Hometown) or nil
	-- the player's own copy of the bus (a Studio lint, outside the tutorial, borrows the shared one and leaves it where it is)
	local Own = Hometown and Hometown.Cast(`WFBlackBus`) or nil
	local Bus: Model = Own or workspace.Hometown.BlackBus:FindFirstChild(`WFBlackBus`)
	if Own then
		for _, D in Own:GetDescendants() do
			if D:IsA(`BasePart`) then D.CanCollide = false; D.CanQuery = false; D.CanTouch = false end
		end
		Own:PivotTo(Ctx.CF(`BusStart`)) -- out in the fog before the first frame (the copy starts where the source stands)
	end
	local Controller = Bus:FindFirstChildWhichIsA(`AnimationController`, true)
	local BusAnimator: Animator? = Bus:FindFirstChildWhichIsA(`Animator`, true)
	if not BusAnimator and Controller then
		BusAnimator = Instance.new(`Animator`)
		BusAnimator.Parent = Controller
	end

	-- The bus clips' pose translations are not animation: every bone but Root and Body carries a constant offset (DoorA
	-- (-1.69, -1.70, 0.44) in all of them, the wheels 3.3 studs down), the rig's bind offset written into the pose, so
	-- unmodified the wheels sink through the road and the doors drop. Their rotations are the animation (doors 88 deg, the
	-- head 33 deg). So after the Animator's step, each frame, those bones keep their rotation and lose the translation.
	local Bones: { Bone } = {}
	for _, B in Bus:GetDescendants() do
		if B:IsA(`Bone`) and B.Name ~= `Root` and B.Name ~= `Body` then table.insert(Bones, B) end
	end
	local Strip = RunService.PreRender:Connect(function()
		for _, B in Bones do
			local X = B.Transform
			if X.Position.Magnitude > 1e-4 then B.Transform = X - X.Position end
		end
	end)

	-- the bus clips: one at a time, the last frame held until the next starts; all stopped at the cut's end
	local Tracks: { AnimationTrack } = {}
	local Anims: { Animation } = {}
	local Current: AnimationTrack? = nil
	local function play(Clip: string, Loop: boolean?)
		local Id = Ctx.Clip(Clip)
		if not (BusAnimator and Id and Ctx.Alive()) then return end
		local A = Instance.new(`Animation`)
		A.AnimationId = Id
		local T = BusAnimator:LoadAnimation(A)
		table.insert(Anims, A)
		table.insert(Tracks, T)
		T.Priority = Enum.AnimationPriority.Action
		T.Looped = Loop == true
		T:Play(0.12)
		local Prev = Current
		Current = T
		if Prev then Prev:Stop(0.12) end
		if not Loop then
			-- hold the last frame: stopped, a finished clip would fall back to the unassembled rest pose
			local Conn: RBXScriptConnection
			Conn = RunService.PreAnimation:Connect(function(Dt: number)
				if not T.IsPlaying or Current ~= T then Conn:Disconnect() return end
				if T.TimePosition + 1.25 * Dt >= T.Length then
					Conn:Disconnect()
					T:AdjustSpeed(0)
					T.TimePosition = math.max(0, T.Length - 1 / 60)
				end
			end)
		end
	end
	Ctx.OnEnd(function()
		Strip:Disconnect()
		for _, T in Tracks do pcall(function() T:Stop(0) T:Destroy() end) end
		for _, A in Anims do pcall(function() A:Destroy() end) end
		table.clear(Tracks)
		table.clear(Anims)
		Current = nil
	end)

	-- a slide along a line, ending on its own or when the cut does
	local function slide(From: CFrame, To: CFrame, Seconds: number, Curve: (number) -> number)
		local T0 = os.clock()
		while Ctx.Alive() and os.clock() - T0 < Seconds do
			Bus:PivotTo(From:Lerp(To, Curve((os.clock() - T0) / Seconds)))
			RunService.PreRender:Wait()
		end
		if Ctx.Alive() then Bus:PivotTo(To) end
	end

	local Go = false -- the loop may end now (its exit phase then lands on the step on)
	local Taken = false
	local TA = require(ReplicatedStorage.Config.TutorialAnim)
	local Away = CFrame.lookAt(Ctx.Pos(`CamAway`), Ctx.Pos(`CamLookAway`))
	return {
		grade = Config.Looks.BusStop;
		cues = {};
		events = {
			{ t = 0; call = function()
				play(`BusEngineIdle`, true)
				if not Actor then return end
				Actor.WalkTo(Ctx.CF(`Stand`), 4)
				Actor.Chain(`TheBus`, Ctx.Clip, { [1] = function() while not Go and Ctx.Alive() do task.wait() end end })
				if Ctx.Alive() then Actor.Reseat(`TheBus2`, TA.Chains.TheBus[2].EndOffset, Ctx.Clip) end
			end };
			-- the last 58 studs to the stop over 5.5 s, decelerating; BrakeStop plays through its arrival
			{ t = 1.0; call = function()
				slide(Ctx.CF(`BusStart`), Ctx.CF(`BusStop`), 5.5, function(U) return 1 - (1 - U) ^ 3 end)
			end };
			{ t = 3.6; call = function() play(`BusBrakeStop`) end };
			{ t = 7.4; call = function() play(`BusDoorsOpen`) end };
			{ t = 10.0; call = function() play(`BusDriverTurn`) end };
			{ t = 15.0; call = function() Go = true end };
			-- you're on: the doors close behind you, your own copy of you is out of sight for the rest of the cut
			{ t = 19.6; call = function() play(`BusDoorsClose`) end };
			{ t = 19.75; call = function()
				if Hometown and Me and not Taken then
					Taken = true
					Hometown.HideCharacter(Me, true)
					Ctx.OnRelease(function() Hometown.HideCharacter(Me, false) end)
				end
			end };
			{ t = 20.6; call = function()
				play(`BusPullAway`)
				slide(Ctx.CF(`BusStop`), Ctx.CF(`BusAway`), 6, function(U) return U * U * U end)
			end };
			-- the title stays (Def.EndHold) until the Prologue starts
			{ t = 26.4; card = { title = `NIGHTMARE HIGHSCHOOL`; sub = ``; dur = 3; hold = true } };
		};
		shots = {
			{ name = `Waiting`; dur = 4.0; subject = Me; noise = `calm`; dof = true;
			  camera = { frame = { size = `MS`; yaw = 155; pitch = 6; lens = 35 }; to = { size = `MCU` }; ease = "inout" } };
			{ name = `Out of the fog`; dur = 3.4; subject = Bus; noise = `tense`; dof = true;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamWide`), Ctx.Pos(`CamLookWide`)); lens = 24 } };
			{ name = `The doors`; dur = 2.6; subject = Ctx.Mark(`Door`); noise = `calm`; dof = true;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamDoor`), Ctx.Pos(`Door`)); lens = 50 } };
			{ name = `The driver`; dur = 5.8; subject = Ctx.Mark(`Driver`); noise = `calm`; dof = true;
			  camera = { cframe = CFrame.lookAt(Ctx.Pos(`CamDriver`), Ctx.Pos(`Driver`)); lens = 85 } };
			{ name = `You step on`; dur = 4.0; subject = Me; noise = `calm`; dof = true;
			  camera = { frame = { size = `MS`; yaw = 200; pitch = 4; lens = 35 } } };
			{ name = `Away`; dur = 6.6; subject = Bus; noise = `calm`;
			  camera = { cframe = Away; lens = 28 } };
			{ name = `Title`; dur = 3.0; role = `card`; card = { text = `NIGHTMARE HIGHSCHOOL`; style = `title` }; fadeIn = 0.15;
			  camera = { cframe = Away; lens = 28 } };
		};
	}
end

return Def
