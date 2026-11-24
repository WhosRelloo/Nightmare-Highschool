--[[
	Soccer (client): controls, the kick charge meter, the Bloodrush bar, procedural poses (or the animation in
	Config.Sports.SoccerAnims when a slot is filled), ball trails and landing marker, stun/ankle reactions, the goal moment.
	(soccer-2.0) The FIER clips through Soccer.Clips: kicks jump to Lead s before contact, the charge creeps, the dive
	and dribble follow their clip's travel curve over the 1.1 distance, falls last as long as the stun, the keeper
	catches and holds. Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md.
	Builds on Controllers.Gui.Sports (state, HUD, remotes). The server decides everything (Services.Sports.Soccer).
	UI: UI kit pieces only (Bar, Text) and Theme.Images for the touch buttons.

	Controls (in a soccer game or soccer drill):
		click hold/release   shoot (A / D at full charge = curve) · without the ball: volley / header on the next ball
		R    pass to the teammate you aim at · without the ball: call for it
		Q    dribble burst (ankle-breaker) · keeper in their box without the ball: dive
		E    tackle (without the ball) · right click: feint (with the ball) · T: Bloodrush · X: quit drill
		touch / gamepad: Kick (R2), Pass (X), Dribble/Dive (Y), Tackle (B), Feint (L2), Bloodrush (L1)
]]

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key
local ContextActionService = game:GetService(`ContextActionService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Config = require(ReplicatedStorage.Config.Sports)
local Sports = require(script.Parent:WaitForChild(`Sports`))
local Clips = require(script:WaitForChild(`Clips`))   -- (soccer-2.0) the FIER clips: ids, timing data, the travel dash
local Anim = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SoccerAnim`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local T = Config.Soccer

local Shared = {}
local Local = {}

-- the cosmetic FX toolbox (Controllers.Fx): settings-aware shakes, flashes and shared pieces
local FxMod = nil
function Local.Fx()
	if FxMod == nil then
		local Ok, M = pcall(function() return require(script.Parent.Parent:WaitForChild(`Fx`, 5)) end)
		FxMod = if Ok and M then M else false
	end
	return FxMod or nil
end
function Local.ShakeScale(): number local F = Local.Fx() return if F then F.ShakeScale() else 1 end
function Local.FlashScale(): number local F = Local.Fx() return if F then F.FlashScale() else 1 end
local Ui = nil
local ChargeAt = nil :: number?
local FullCharged = false
local Balls = {} :: { [BasePart]: boolean }

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

function Local.State() local S, At = Sports.State() return S, At end

function Local.Active(): boolean
	local S = Local.State()
	return S ~= nil and S.Sport == `Soccer` and Sports.Active()
end

function Local.Root(): BasePart? return Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart? end

function Local.Aim(): Vector3
	local Cam = workspace.CurrentCamera
	return if Cam then Cam.CFrame.LookVector else Vector3.new(0, 0, -1)
end

function Local.MouseFlat(): Vector3?
	local R = Local.Root()
	if not R then return nil end
	local Hit = Player:GetMouse().Hit.Position
	return Vector3.new(Hit.X - R.Position.X, 0, Hit.Z - R.Position.Z)
end

function Local.MoveDir(): Vector3
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	local R = Local.Root()
	if Hum and Hum.MoveDirection.Magnitude > 0.1 then return Hum.MoveDirection.Unit end
	return if R then R.CFrame.LookVector else Vector3.new(0, 0, -1)
end

---| UI: the charge bar under you, Bloodrush under the stamina bar |---

function Local.Build()
	local Gui = new(`ScreenGui`, { Name = `NHSoccer`; DisplayOrder = 4; ResetOnSpawn = false; Enabled = false }, Player:WaitForChild(`PlayerGui`))
	Kit.AutoScale(Gui)
	local Rush, RushApi = Kit.Bar({ Name = `Bloodrush`; color = C.Crimson; height = 16; caption = `BLOODRUSH`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -20, 0, 274); Parent = Gui })
	Rush.Size = UDim2.fromOffset(470, 16)
	local ChargeGui = new(`BillboardGui`, { Name = `NHKickCharge`; Size = UDim2.fromScale(4, 0.45); StudsOffset = Vector3.new(0, -3.4, 0); AlwaysOnTop = false; LightInfluence = 0; ResetOnSpawn = false; Enabled = false }, Player.PlayerGui)
	local Bar, BarApi = Kit.Bar({ Name = `Charge`; color = C.Gold; height = 18; caption = ``; Parent = ChargeGui })
	Bar.Size = UDim2.fromScale(1, 1)
	Ui = { Gui = Gui; Rush = Rush; RushApi = RushApi; ChargeGui = ChargeGui; BarApi = BarApi }
end

function Local.Draw()
	local S = Local.State()
	local On = Local.Active()
	Ui.Gui.Enabled = On and S ~= nil and S.Meter ~= nil
	if Ui.Gui.Enabled then
		local Pct = math.clamp((S.Meter or 0) / 100, 0, 1)
		Ui.RushApi:Set(Pct, if S.Rush then `BLOODRUSH!` elseif (S.Meter or 0) >= (S.MeterMin or 45) then `BLOODRUSH  ·  T` else `BLOODRUSH`)
	end
	-- charge bar while you hold the kick
	local R = Local.Root()
	if On and ChargeAt and R then
		local Held = os.clock() - ChargeAt
		local F = math.clamp(Held / T.Kick.ChargeTime, 0, 1)
		Ui.ChargeGui.Adornee = R
		Ui.ChargeGui.Enabled = true
		local Curve = Local.Curve()
		Ui.BarApi:Set(F, if F >= 1 then (if Curve == -1 then `◀ CURVE` elseif Curve == 1 then `CURVE ▶` else `FULL POWER`) else ``)
		if F >= 1 and not FullCharged then
			FullCharged = true
			Ui.BarApi:SetColor(Color3.fromRGB(255, 225, 140))
			Local.Shake(0.25, 0.35)
		end
		if Held > T.Kick.MaxHold then Local.Release() end
	else
		Ui.ChargeGui.Enabled = false
	end
end

function Local.Curve(): number
	if UserInputService:IsKeyDown(Enum.KeyCode.A) then return -1 end
	if UserInputService:IsKeyDown(Enum.KeyCode.D) then return 1 end
	-- gamepad / touch: steering left or right while charging curves too
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	local Cam = workspace.CurrentCamera
	if Hum and Cam and Hum.MoveDirection.Magnitude > 0.5 then
		local Side = Hum.MoveDirection:Dot(Cam.CFrame.RightVector)
		if Side > 0.6 then return 1 elseif Side < -0.6 then return -1 end
	end
	return 0
end

---| input |---

function Local.Release()
	if not ChargeAt then return end
	ChargeAt = nil
	FullCharged = false
	Ui.BarApi:SetColor(C.Gold)
	Sports.Send(`KickRelease`, { Aim = Local.Aim(); Curve = Local.Curve() })
end

function Local.Input(I: InputObject, Processed: boolean, Began: boolean)
	if Typing.Active() or not Local.Active() then return end
	local S = Local.State()
	local Ball = Sports.HasBall()
	local Mouse = I.UserInputType == Enum.UserInputType.MouseButton1 or I.UserInputType == Enum.UserInputType.MouseButton2
	if Mouse and Processed then return end
	if I.UserInputType == Enum.UserInputType.MouseButton1 then
		if Began then
			if Ball then
				ChargeAt = os.clock()
				FullCharged = false
				Sports.Send(`KickStart`)
			elseif not S.Drill then
				Sports.Send(`KickRelease`, { Aim = Local.Aim(); Curve = 0 })   -- a stored volley / header
			end
		else
			Local.Release()
		end
		return
	end
	if not Began then return end
	local K = I.KeyCode
	if I.UserInputType == Enum.UserInputType.MouseButton2 then
		if Ball and not S.Drill then Sports.Send(`Feint`) end
	elseif K == Enum.KeyCode.R then
		if Ball then
			ChargeAt = nil
			Sports.Send(`Pass`, { Aim = Local.MouseFlat() or Local.Aim() })
		elseif not S.Drill then
			Sports.Send(`Call`)
		end
	elseif K == Enum.KeyCode.Q and not S.Drill then
		if Ball then
			ChargeAt = nil
			Sports.Send(`Dribble`, { Dir = Local.MoveDir() })
		elseif S.Keeper and S.InZone then
			Sports.Send(`Dive`, { Dir = Local.MoveDir() })
		end
	elseif K == Enum.KeyCode.E and not Ball and not S.Drill then
		local R = Local.Root()
		Sports.Send(`Tackle`, { Dir = if R then R.CFrame.LookVector else nil })
	elseif K == Enum.KeyCode.T and not S.Drill then
		Sports.Send(`Bloodrush`)
	elseif K == Enum.KeyCode.X and S.Drill then
		Sports.Send(`DrillQuit`)
	end
end

---| movement on server approval: dashes, stuns, ankles |---

function Local.Dash(Dir: Vector3?, Speed: number, Time: number)
	local R = Local.Root()
	if not R then return end
	Clips.Cancel() -- (soccer-2.0) a new dash takes over from a clip's travel dash
	local D = Dir and Vector3.new(Dir.X, 0, Dir.Z)
	if not D or D.Magnitude < 0.1 then D = Vector3.new(R.CFrame.LookVector.X, 0, R.CFrame.LookVector.Z) end
	D = D.Unit
	local Att = Instance.new(`Attachment`) Att.Parent = R
	local LV = Instance.new(`LinearVelocity`)
	LV.Attachment0 = Att LV.RelativeTo = Enum.ActuatorRelativeTo.World LV.VelocityConstraintMode = Enum.VelocityConstraintMode.Plane
	LV.PrimaryTangentAxis = Vector3.new(1, 0, 0) LV.SecondaryTangentAxis = Vector3.new(0, 0, 1)
	LV.PlaneVelocity = Vector2.new(D.X, D.Z) * Speed
	LV.MaxForce = 60000
	LV.Parent = R
	task.delay(Time, function() LV:Destroy() Att:Destroy() end)
end

local Stunned = nil
-- out of stamina: no sprinting (both sports set SportTired); Bloodrush: +10% while it lasts
function Local.SpeedStep()
	local Ch = Player.Character
	local Hum = Ch and Ch:FindFirstChildOfClass(`Humanoid`)
	if not Hum or Stunned then return end
	local Base = game:GetService(`StarterPlayer`).CharacterWalkSpeed
	if Hum:GetAttribute(`SportTired`) and Hum.WalkSpeed > Base then Hum.WalkSpeed = Base end
	local Rush = (Ch:GetAttribute(`SportRush`) or 0) > workspace:GetServerTimeNow()
	if Rush and not Local.Rushing then
		Local.Rushing = Hum.WalkSpeed
		Hum.WalkSpeed *= 1 + T.Bloodrush.Speed
	elseif not Rush and Local.Rushing then
		Hum.WalkSpeed = math.max(Base, Hum.WalkSpeed / (1 + T.Bloodrush.Speed))
		Local.Rushing = nil
	end
end

function Local.StunStep()
	local Ch = Player.Character
	local Hum = Ch and Ch:FindFirstChildOfClass(`Humanoid`)
	if not Hum then return end
	local Until = Ch:GetAttribute(`SportStun`) or 0
	local On = Until > workspace:GetServerTimeNow()
	if On and not Stunned then
		Stunned = { Speed = Hum.WalkSpeed; Jump = Hum.JumpPower }
		Hum.WalkSpeed = 0
		Hum.JumpPower = 0
		ChargeAt = nil
	elseif On and Stunned then
		Hum.WalkSpeed = 0
	elseif not On and Stunned then
		Hum.WalkSpeed = game:GetService(`StarterPlayer`).CharacterWalkSpeed   -- the game's sprint raises it again when you sprint
		Hum.JumpPower = Stunned.Jump
		Stunned = nil
		Hum.PlatformStand = false
	end
end

-- the toolbox shake follows the Camera Shake / Reduce Motion settings (0 = none)
function Local.Shake(Strength: number, Seconds: number)
	local F = Local.Fx()
	if F then F.Shake(Strength, Seconds) end
end

---| poses (procedural) and animation slots |---

local Poses = {} :: { [Model]: { Kind: string, Start: number, Length: number, Side: number? } }
local LENGTH = { Charge = 1.6; Shot = 0.5; Pass = 0.4; Swing = 0.35; Volley = 0.5; Header = 0.4; Dribble = 0.4; Feint = 0.45; Tackle = 0.65; Dive = 0.7; Throw = 0.5; Celebrate = 2.5; Fall = 1.6 }
-- (soccer-2.0) Kind -> Config.Sports.SoccerAnims slot; a call can name its own Slot (the kick by speed, the dive by side,
-- the fall by cause)
local SLOT = { Charge = `Kick`; Shot = `Kick`; Pass = `Pass`; Swing = `Kick`; Volley = `Volley`; Header = `Header`; Dribble = `Dribble`; Feint = `Feint`; Tackle = `Tackle`; Dive = `KeeperDiveRight`; Throw = `KeeperThrow`; Celebrate = `Celebrate`; Fall = `Tackled` }
local STOP_AFTER = { Celebrate = 3.4 }   -- long clips are cut to the moment
local LEAD, MARGIN = 0.05, 0.10          -- the foot meets the ball LEAD s after the server's kick; a charge creeps from MARGIN before contact
local RUN_SPEED = 6                      -- a shot at this flat speed or more is the running shot
local R6 = CFrame.Angles
local rad = math.rad
local Tracks = {} :: { [Model]: { [string]: AnimationTrack } }

local function smooth(x: number): number x = math.clamp(x, 0, 1) return x * x * (3 - 2 * x) end

-- a filled slot plays its clip (the FIER clip, or the 1.1 one); returns the track, or nil for the procedural pose.
-- Opts: Slot (instead of SLOT[Kind]), At (TimePosition), Speed.
function Local.Play(Char: Model, Kind: string, Opts: { Slot: string?, At: number?, Speed: number? }?): AnimationTrack?
	local Slot = (Opts and Opts.Slot) or SLOT[Kind] or ``
	local Id, Fier = Clips.Id(Slot)
	if not Id then return nil end
	local Hum = Char:FindFirstChildOfClass(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return nil end
	Tracks[Char] = Tracks[Char] or {}
	local Key = Slot .. (if Fier then `` else `~`)
	local Tr = Tracks[Char][Key]
	if not Tr then
		local A = Instance.new(`Animation`)
		A.AnimationId = Id
		local Ok, Loaded = pcall(Animator.LoadAnimation, Animator, A)
		if not Ok then return nil end
		Tr = Loaded
		Tr.Priority = Enum.AnimationPriority.Action2
		local C = Fier and Clips.Clip(Slot)
		Tr.Looped = C ~= nil and C.Loop == true   -- 1.1 clips (the slide) are saved looping
		Tracks[Char][Key] = Tr
	end
	-- one soccer clip at a time per body
	for K, Other in Tracks[Char] do if K ~= Key and Other.IsPlaying then Other:Stop(0.08) end end
	Tr:Play(0.08)
	if Opts and Opts.At then Tr.TimePosition = Opts.At end
	Tr:AdjustSpeed(Opts and Opts.Speed or 1)
	-- FIER clips play out; 1.1 clips are cut to the move; long clips are cut to the moment
	local Cut = STOP_AFTER[Kind] or (if Fier then nil else LENGTH[Kind])
	if Cut then task.delay(Cut, function() if Tr.IsPlaying then Tr:Stop(0.2) end end) end
	return Tr
end

function Local.Pose(Char: Model?, Kind: string, Side: number?, Opts: { Slot: string?, At: number?, Speed: number? }?): AnimationTrack?
	if not Char then return nil end
	local Tr = Local.Play(Char, Kind, Opts)
	if Tr then return Tr end
	Poses[Char] = { Kind = Kind; Start = os.clock(); Length = LENGTH[Kind] or 0.5; Side = Side }
	return nil
end

-- (soccer-2.0) the FIER clip data behind a slot (nil when a 1.1 clip or the procedural pose plays)
function Local.Data(Slot: string): any?
	local _, Fier = Clips.Id(Slot)
	return if Fier then Clips.Clip(Slot) else nil
end

-- (soccer-2.0) the charge: 1x to MARGIN before contact, then a creep that reaches the kick point at MaxHold
local Charging = {} :: { [Model]: AnimationTrack }
function Local.Charge(Char: Model?)
	if not Char then return end
	local Tr = Local.Pose(Char, `Charge`)
	local C = Local.Data(`Kick`)
	if not (Tr and C) then return end
	Charging[Char] = Tr
	local HoldAt, Creep = Anim.Hold(C, LEAD, MARGIN, T.Kick.MaxHold)
	task.spawn(function()
		local T0 = os.clock()
		while Tr.IsPlaying and Charging[Char] == Tr and Tr.TimePosition < HoldAt and os.clock() - T0 < 2 do RunService.Heartbeat:Wait() end
		if not (Tr.IsPlaying and Charging[Char] == Tr) then return end
		Tr:AdjustSpeed(Creep)
		task.delay(T.Kick.MaxHold + 0.5, function()
			if Charging[Char] == Tr then Charging[Char] = nil if Tr.IsPlaying then Tr:Stop(0.2) end end
		end)
	end)
end

-- (soccer-2.0) a kick from the server: the clip jumps to LEAD s before contact (or keeps the charge's place if it's ahead)
function Local.Kick(Char: Model?, Kind: string)
	if not Char then return end
	local Slot = SLOT[Kind]
	if Kind == `Shot` or Kind == `Swing` then
		local R = Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local V = if R then R.AssemblyLinearVelocity else Vector3.zero
		Slot = Anim.KickSlot(Vector3.new(V.X, 0, V.Z).Magnitude, RUN_SPEED)
	end
	local C = Slot and Local.Data(Slot)
	local At = if C then Anim.StartAt(C, LEAD) else nil
	local Held = Charging[Char]
	Charging[Char] = nil
	if At and Held and Held.IsPlaying and Slot == `Kick` then
		Held.TimePosition = math.max(Held.TimePosition, At)
		Held:AdjustSpeed(1)
		return
	end
	Local.Pose(Char, Kind, nil, { Slot = Slot; At = At })
end

-- (soccer-2.0) a move with travel: every client plays the clip through its window at the fitted rate; the mover's own
-- client also runs the dash (the 1.1 distance and direction on the clip's speed curve). No clip data: the 1.1 dash.
function Local.Move(Char: Model?, Kind: string, Slot: string, Side: number?, Me: boolean, Dir: Vector3?, Dist: number, Time: number)
	if not Char then return end
	local C = Local.Data(Slot)
	local Tr = Local.Pose(Char, Kind, Side, { Slot = Slot })
	if Tr and C and C.Path then
		local Rate, DashTime, t0, t1 = Clips.Drive(Tr, C, Time, 2)
		local R = if Me then Local.Root() else nil
		if R then Clips.DashPath(R, Tr, C, Dir, Dist, Rate, t0, t1, DashTime) end
	elseif Me then
		Local.Dash(Dir, Dist / Time, Time)
	end
end

-- (soccer-2.0) a fall lasts as long as the stun: the clip stops when SportStun passes, Fallen Idle covers the rest
function Local.Fall(Char: Model?, Slot: string, Side: number?)
	if not Char then return end
	local Tr = Local.Pose(Char, `Fall`, Side, { Slot = Slot })
	if not (Tr and Local.Data(Slot)) then return end
	local function stunned(): boolean return (Char:GetAttribute(`SportStun`) or 0) > workspace:GetServerTimeNow() end
	task.spawn(function()
		local T0 = os.clock()
		task.wait(0.6) -- a fall always reads, even on a short stun
		while Char.Parent and Tr.IsPlaying and stunned() and os.clock() - T0 < 6 do RunService.Heartbeat:Wait() end
		if not Char.Parent then return end
		if Tr.IsPlaying then Tr:Stop(0.25) return end
		if not stunned() then return end
		local Lie = Local.Play(Char, `Fall`, { Slot = `Fallen` })
		while Lie and Char.Parent and stunned() and os.clock() - T0 < 6 do RunService.Heartbeat:Wait() end
		if Lie and Lie.IsPlaying then Lie:Stop(0.3) end
	end)
end

-- (soccer-2.0) the keeper's catch, then the hold while they keep the ball (the local player only: their tracks replicate)
function Local.Catch()
	local S = Local.State()
	local Char = Player.Character
	if not (Char and S and S.Keeper and S.InZone) then return end
	local Tr = Local.Play(Char, `Catch`, { Slot = `KeeperCatch` })
	if not Tr then return end
	task.spawn(function()
		local T0 = os.clock()
		while Tr.IsPlaying and Sports.HasBall() and os.clock() - T0 < 4 do RunService.Heartbeat:Wait() end
		if not Sports.HasBall() then if Tr.IsPlaying then Tr:Stop(0.2) end return end
		local Hold = Local.Play(Char, `Catch`, { Slot = `KeeperCatchIdle` })
		while Hold and Hold.IsPlaying and Sports.HasBall() and Char.Parent and os.clock() - T0 < T.Keeper.HoldMax + 4 do RunService.Heartbeat:Wait() end
		if Hold and Hold.IsPlaying then Hold:Stop(0.2) end
	end)
end

local function target(Kind: string, u: number, Side: number?)
	local a = math.sin(math.min(u, 1) * math.pi)
	local s = Side or 1
	if Kind == `Charge` then
		local w = smooth(u / 0.2)
		return { [`Right Hip`] = R6(rad(-45 * w), 0, 0); [`Left Shoulder`] = R6(rad(35 * w), 0, rad(30 * w)); [`Right Shoulder`] = R6(rad(-25 * w), 0, 0); [`RootJoint`] = R6(rad(8 * w), 0, 0) }
	elseif Kind == `Shot` or Kind == `Swing` or Kind == `Volley` then
		local f = smooth(u / 0.35)
		local Lift = if Kind == `Volley` then 30 else 0
		return { [`Right Hip`] = R6(rad(-45 + 135 * f) * (1 - smooth((u - 0.6) / 0.4)), 0, 0); [`Left Shoulder`] = R6(rad(40 * a), 0, rad(35 * a)); [`Right Shoulder`] = R6(rad(-30 * a), 0, 0); [`RootJoint`] = R6(rad((-10 - Lift) * a), 0, 0) }
	elseif Kind == `Pass` then
		return { [`Right Hip`] = R6(rad(55 * a), 0, rad(-20 * a)); [`Left Shoulder`] = R6(rad(20 * a), 0, rad(20 * a)) }
	elseif Kind == `Header` then
		return { [`Neck`] = R6(rad(-35 * a), 0, 0); [`RootJoint`] = R6(rad(15 * a), 0, 0) }
	elseif Kind == `Dribble` or Kind == `Feint` then
		return { [`RootJoint`] = R6(rad(-15 * a), rad(20 * a * s), rad(12 * a * s)); [`Right Hip`] = R6(rad(35 * a), 0, rad(-20 * a * s)); [`Left Shoulder`] = R6(rad(25 * a), 0, rad(30 * a)); [`Right Shoulder`] = R6(rad(25 * a), 0, rad(-30 * a)) }
	elseif Kind == `Tackle` then
		local f = smooth(u / 0.2) * (1 - smooth((u - 0.75) / 0.25))
		return { [`RootJoint`] = R6(rad(50 * f), 0, 0); [`Right Hip`] = R6(rad(80 * f), 0, 0); [`Left Hip`] = R6(rad(10 * f), 0, 0); [`Left Shoulder`] = R6(rad(-30 * f), 0, rad(40 * f)) }
	elseif Kind == `Dive` then
		local f = smooth(u / 0.2) * (1 - smooth((u - 0.7) / 0.3))
		return { [`RootJoint`] = R6(0, 0, rad(70 * f * s)); [`Left Shoulder`] = R6(rad(170 * f), 0, 0); [`Right Shoulder`] = R6(rad(170 * f), 0, 0) }
	elseif Kind == `Throw` then
		return { [`Right Shoulder`] = R6(rad(170 * a), 0, 0); [`Left Shoulder`] = R6(rad(150 * a), 0, 0); [`RootJoint`] = R6(rad(-12 * a), 0, 0) }
	elseif Kind == `Celebrate` then
		local w = smooth(u / 0.1) * (1 - smooth((u - 0.85) / 0.15))
		return { [`Right Shoulder`] = R6(rad(170 * w), 0, rad(-20 * w)); [`Left Shoulder`] = R6(rad(170 * w), 0, rad(20 * w)); [`Neck`] = R6(rad(-15 * w), 0, 0) }
	elseif Kind == `Fall` then
		local f = smooth(u / 0.15) * (1 - smooth((u - 0.8) / 0.2))
		return { [`RootJoint`] = R6(rad(-70 * f), 0, rad(20 * f * s)); [`Left Hip`] = R6(rad(40 * f), 0, 0); [`Right Shoulder`] = R6(0, 0, rad(-60 * f)); [`Left Shoulder`] = R6(0, 0, rad(60 * f)) }
	end
	return {}
end

function Local.PoseStep()
	local Now = os.clock()
	for Char, P in Poses do
		local u = (Now - P.Start) / P.Length
		if u >= 1 or not Char.Parent then Poses[Char] = nil continue end
		local Torso = Char:FindFirstChild(`Torso`)
		local Root = Char:FindFirstChild(`HumanoidRootPart`)
		for Joint, M in target(P.Kind, u, P.Side) do
			local Motor = (if Joint == `RootJoint` then Root and Root:FindFirstChild(`RootJoint`) else Torso and Torso:FindFirstChild(Joint)) :: Motor6D?
			if Motor then
				local Rc = Motor.C0 - Motor.C0.Position
				Motor.Transform = Rc:Inverse() * M * Rc
			end
		end
	end
end

---| ball effects: trails, landing marker, pickup ring |---

function Local.BallStep()
	for B in Balls do
		if not B.Parent then Balls[B] = nil continue end
		if B:GetAttribute(`SportBall`) ~= `Soccer` then continue end
		local V = B.AssemblyLinearVelocity
		local Tr = B:FindFirstChild(`SoccerTrail`) :: Trail?
		if not Tr then
			local A0 = Instance.new(`Attachment`) A0.Name = `TrailA` A0.Position = Vector3.new(0, 0.35, 0) A0.Parent = B
			local A1 = Instance.new(`Attachment`) A1.Name = `TrailB` A1.Position = Vector3.new(0, -0.35, 0) A1.Parent = B
			Tr = Instance.new(`Trail`)
			Tr.Name = `SoccerTrail` Tr.Attachment0 = A0 Tr.Attachment1 = A1 Tr.Lifetime = 0.25 Tr.LightEmission = 0.6
			Tr.Color = ColorSequence.new(Color3.fromRGB(240, 236, 226)) Tr.Transparency = NumberSequence.new(0.35, 1) Tr.FaceCamera = true
			Tr.Parent = B
		end
		Tr.Enabled = B:GetAttribute(`BallState`) ~= `Held` and V.Magnitude > 45
		-- landing marker for a high ball
		local Mark = Local.Marks[B]
		local High = B:GetAttribute(`BallState`) ~= `Held` and V.Y > 8 and B.Position.Y > 6
		if High then
			local g = workspace.Gravity
			local Floor = B.Position.Y - 6
			local t = (V.Y + math.sqrt(math.max(0, V.Y * V.Y + 2 * g * (B.Position.Y - 1.6)))) / g
			local Land = Vector3.new(B.Position.X + V.X * t, 1.35, B.Position.Z + V.Z * t)
			if not Mark then
				-- a soft gold ring with a faint glow inside (VFX Batch 5: no hard Neon discs)
				local F = Local.Fx()
				if F and F.SoftDisc then
					Mark = F.SoftDisc(Land, C.Gold, 3.4, nil, F.Art.Ring, 0.3)
					local Inner = F.SoftDisc(Land, C.Gold, 2.4, nil, F.Art.Glow, 0.7)
					Inner.Name = `Inner`
					Inner.Parent = Mark
				else
					Mark = Instance.new(`Part`)
					Mark.Shape = Enum.PartType.Cylinder Mark.Anchored, Mark.CanCollide, Mark.CanQuery, Mark.CanTouch = true, false, false, false
					Mark.Size = Vector3.new(0.05, 3, 3) Mark.Material = Enum.Material.Neon Mark.Color = C.Gold Mark.Transparency = 0.45 Mark.CastShadow = false
					Mark.Parent = workspace
				end
				Local.Marks[B] = Mark
			end
			if Mark.Name == `FxSoft` then
				Mark.CFrame = CFrame.new(Land)
				local Inner = Mark:FindFirstChild(`Inner`)
				if Inner then Inner.CFrame = CFrame.new(Land + Vector3.new(0, 0.01, 0)) end
			else
				Mark.CFrame = CFrame.new(Land) * CFrame.Angles(0, 0, math.rad(90))
				Mark.Transparency = 0.45
			end
			local _ = Floor
		elseif Mark then
			Mark:Destroy()
			Local.Marks[B] = nil
		end
	end
end
Local.Marks = {} :: { [BasePart]: BasePart }

-- a thin expanding disc; flat on the ground by default, or facing Axis (e.g. out of a goal mouth).
-- Drawn by the shared toolbox (Controllers.Fx); the local copy below is only a fallback.
function Local.Ring(Pos: Vector3, Color: Color3, Size: number, Axis: Vector3?)
	local F = Local.Fx()
	if F then F.Ring(Pos, Color, Size, Axis) return end
	local Ring = Instance.new(`Part`)
	Ring.Shape = Enum.PartType.Cylinder Ring.Anchored, Ring.CanCollide, Ring.CanQuery, Ring.CanTouch = true, false, false, false
	-- a cylinder's axis is its X: point X up (flat ring) or along Axis (upright ring)
	Ring.Size = Vector3.new(0.05, 1.5, 1.5)
	Ring.CFrame = if Axis and Axis.Magnitude > 0 then CFrame.lookAt(Pos, Pos + Axis) * CFrame.Angles(0, math.rad(90), 0) else CFrame.new(Pos) * CFrame.Angles(0, 0, math.rad(90))
	Ring.Material = Enum.Material.Neon Ring.Color = Color Ring.Transparency = 0.25 Ring.CastShadow = false Ring.Parent = workspace
	TweenService:Create(Ring, TweenInfo.new(0.45, Enum.EasingStyle.Quad), { Size = Vector3.new(0.05, Size, Size); Transparency = 1 }):Play()
	task.delay(0.5, function() Ring:Destroy() end)
end

---| the goal moment |---

-- VFX P2-5: re-entrant (a second goal mid-shot just takes over) and it eases back behind you instead of snapping
local GoalCamToken = 0
local GoalCamRestore: Enum.CameraType? = nil
function Local.GoalCam(Scorer: Player?)
	local Cam = workspace.CurrentCamera
	local Ch = Scorer and Scorer.Character
	local Head = Ch and Ch:FindFirstChild(`Head`) :: BasePart?
	if not (Cam and Head) then return end
	GoalCamToken += 1
	local Token = GoalCamToken
	-- camera audit 2026-11-02: one owner for the scripted camera (re-entrant: a second goal keeps the same lease)
	if not require(game:GetService(`ReplicatedStorage`):WaitForChild(`Functions`):WaitForChild(`CameraLease`)).Take(`GoalCam`, function() return Token == GoalCamToken end) then return end
	local T0 = os.clock()
	local HOLD, BACK = 2.2, 0.5
	local Conn
	Conn = RunService.RenderStepped:Connect(function()
		if Token ~= GoalCamToken then Conn:Disconnect() return end
		local t = os.clock() - T0
		local Mine = Local.Root()
		if t >= HOLD + BACK or not Head.Parent then
			Conn:Disconnect()
			require(game:GetService(`ReplicatedStorage`):WaitForChild(`Functions`):WaitForChild(`CameraLease`)).Release(`GoalCam`)
			return
		end
		if t < HOLD then
			local u = t / HOLD
			local Look = Head.CFrame.LookVector
			local From = Head.Position + Look * (6 - 2 * u) + Vector3.new(0, 1.2 - 0.6 * u, 0) + Head.CFrame.RightVector * (2 * (1 - u))
			Cam.CFrame = Cam.CFrame:Lerp(CFrame.lookAt(From, Head.Position), 0.2)
		elseif Mine then
			-- ease back to roughly where the follow camera sits, so handing it back doesn't jump
			local Behind = Mine.Position - Mine.CFrame.LookVector * 11 + Vector3.new(0, 4.5, 0)
			Cam.CFrame = Cam.CFrame:Lerp(CFrame.lookAt(Behind, Mine.Position + Vector3.new(0, 1.5, 0)), 0.18)
		end
	end)
end

-- VFX P2-5: the pitch lights pulse once for a goal
local LightBase = setmetatable({}, { __mode = `k` }) :: { [Light]: number }
function Local.PulseLights()
	local Pitch = workspace:FindFirstChild(`Sports`) and workspace.Sports:FindFirstChild(`Pitch`)
	if not Pitch then return end
	local F = Local.Fx()
	local Boost = 1 + 0.8 * (if F then F.FlashScale() else 1)
	for _, L in Pitch:GetDescendants() do
		if L:IsA(`Light`) then
			LightBase[L] = LightBase[L] or L.Brightness
			local Base = LightBase[L]
			TweenService:Create(L, TweenInfo.new(0.25, Enum.EasingStyle.Quad), { Brightness = Base * Boost }):Play()
			task.delay(0.3, function()
				if L.Parent then TweenService:Create(L, TweenInfo.new(0.7, Enum.EasingStyle.Sine), { Brightness = Base }):Play() end
			end)
		end
	end
end

---| Bloodrush aura (VFX P2-6): drawn here from the character attribute SportRush, so late joiners see it too |---
-- race-colour embers and two wisp ribbons locked to the torso (nothing trails along your path); it flickers out
-- over the last 1.5 s. Colours come from Lineage (the old Config.Sports.RaceAura disagreed with it).
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local Auras = {} :: { [Model]: { A: Attachment, Embers: ParticleEmitter, Wisps: ParticleEmitter } }
local function raceColor(P: Player?): Color3
	local Id = P and P:GetAttribute(`Race`)
	for _, R in Lineage.Races or {} do
		if R.Name == Id or R.Id == Id then return R.Color end
	end
	return C.Crimson
end
function Local.AuraStep()
	local Now = workspace:GetServerTimeNow()
	local F = Local.Fx()
	for _, P in Players:GetPlayers() do
		local Ch = P.Character
		if not Ch then continue end
		local Until = Ch:GetAttribute(`SportRush`) or 0
		local Torso = Ch:FindFirstChild(`Torso`) or Ch:FindFirstChild(`UpperTorso`)
		local Aura = Auras[Ch]
		if Until > Now and Torso then
			if not Aura then
				local Col = raceColor(P)
				local A = Instance.new(`Attachment`)
				A.Name = `NHRushAura`
				local Tex = F and F.Tex or {}
				local Embers = Instance.new(`ParticleEmitter`)
				Embers.Texture = Tex.Ember or `rbxassetid://81521204867620`
				Embers.Color = ColorSequence.new(Col:Lerp(Color3.new(1, 1, 1), 0.25), Col)
				Embers.LightEmission = 0.8
				Embers.LockedToPart = true
				Embers.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 0) })
				Embers.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.15), NumberSequenceKeypoint.new(1, 1) })
				Embers.Lifetime = NumberRange.new(0.5, 0.9)
				Embers.Rate = if F then F.Count(16) else 16
				Embers.Speed = NumberRange.new(1, 2.5)
				Embers.SpreadAngle = Vector2.new(60, 60)
				Embers.Acceleration = Vector3.new(0, 3, 0)
				Embers.Parent = A
				local Wisps = Instance.new(`ParticleEmitter`)
				Wisps.Texture = Tex.Wisp or `rbxassetid://100154618460208`
				Wisps.Color = ColorSequence.new(Col)
				Wisps.LightEmission = 0.6
				Wisps.LockedToPart = true
				Wisps.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 2.2), NumberSequenceKeypoint.new(1, 2.8) })
				Wisps.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.55), NumberSequenceKeypoint.new(1, 1) })
				Wisps.Lifetime = NumberRange.new(0.9, 1.2)
				Wisps.Rate = 2 -- two ribbons on screen at a time
				Wisps.Speed = NumberRange.new(0)
				Wisps.Rotation = NumberRange.new(0, 360)
				Wisps.RotSpeed = NumberRange.new(-120, 120)
				Wisps.Parent = A
				A.Parent = Torso
				Aura = { A = A; Embers = Embers; Wisps = Wisps }
				Auras[Ch] = Aura
			end
			-- the last 1.5 s: it gutters and flickers out
			local Left = Until - Now
			if Left < 1.5 then
				local K = math.clamp(Left / 1.5, 0, 1)
				local On = math.random() < 0.4 + 0.6 * K
				Aura.Embers.Enabled = On
				Aura.Wisps.Enabled = On and K > 0.3
				Aura.Embers.Rate = 16 * K
			end
		elseif Aura then
			Auras[Ch] = nil
			Aura.Embers.Enabled = false
			Aura.Wisps.Enabled = false
			task.delay(1.2, function() Aura.A:Destroy() end)
		end
	end
	for Ch, Aura in Auras do
		if not Ch.Parent then Auras[Ch] = nil pcall(function() Aura.A:Destroy() end) end
	end
end

---| Fx from the server |---

function Local.OnFx(Kind: string, D)
	if typeof(Kind) ~= `string` or Kind:sub(1, 2) ~= `S_` then return end
	local P = D and D.Player
	local Char = typeof(P) == `Instance` and P:IsA(`Player`) and P.Character or nil
	local Me = P == Player
	if Kind == `S_Charge` then Local.Charge(Char)
	elseif Kind == `S_Kick` then
		local K = D.Kind or `Shot`
		Local.Kick(Char, if K == `Header` then `Header` elseif K == `Volley` then `Volley` elseif K == `Throw` then `Throw` elseif K == `Swing` then `Swing` elseif K == `Pass` then `Pass` else `Shot`)
		if Me and (D.Power or 0) >= 1 then Local.Shake(0.8, 0.25) end
		if Me then ChargeAt = nil end
	elseif Kind == `S_Pass` then Local.Kick(Char, `Pass`)
	elseif Kind == `S_Dribble` then
		-- (soccer-2.0) the 1.1 distance (Dash / Time * 0.5 for Time = Dash * 0.5 studs) on the Spin clip's curve
		Local.Move(Char, `Dribble`, `Dribble`, math.random() < 0.5 and 1 or -1, Me, D.Dir, T.Dribble.Dash * 0.5, T.Dribble.Time)
	elseif Kind == `S_Feint` then Local.Pose(Char, `Feint`, -1)
	elseif Kind == `S_Tackle` then
		Local.Pose(Char, `Tackle`)
		if Me then Local.Dash(D.Dir, T.Tackle.Dash, 0.35) end
	elseif Kind == `S_Dive` then
		local R = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Dot = if R and typeof(D.Dir) == `Vector3` then R.CFrame.RightVector:Dot(D.Dir) else 1
		local Side = if Dot >= 0 then 1 else -1
		-- (soccer-2.0) the slot by the dive's own side (1.1 passed -Side, which would pick the wrong clip); the procedural
		-- fallback keeps its -Side roll. The 1.1 distance (DiveDash x DiveTime) on the dive clip's curve.
		Local.Move(Char, `Dive`, Anim.DiveSlot(Dot), -Side, Me, D.Dir, T.Keeper.DiveDash * T.Keeper.DiveTime, T.Keeper.DiveTime)
	elseif Kind == `S_Stolen` then
		local From = D.From
		if From == Player then
			Local.Shake(1.6, 0.35)
			Sports.Flash(`Tackled!`, C.Crimson)
			local R = Local.Root()
			if R and typeof(D.Push) == `Vector3` and D.Push.Magnitude > 0.01 then R.AssemblyLinearVelocity += D.Push.Unit * 28 + Vector3.new(0, 8, 0) end
		end
		local FC = typeof(From) == `Instance` and From.Character
		if FC then Local.Fall(FC, if math.random() < 0.5 then `Tackled` else `Tackled2`) end
	elseif Kind == `S_Ankles` then
		Local.Fall(Char, `Trip`, -1)
		if Me then
			Sports.Flash(if D.Kind == `Feint` then `Fooled!` else `Ankles broken!`, C.Crimson)
			Local.Shake(1.2, 0.4)
		end
		if D.By == Player then Sports.Flash(if D.Kind == `Feint` then `Feinted them!` else `Ankle breaker!`, C.Gold) end
	elseif Kind == `S_Stun` then
		if Me and D.Why == `Missed` then Sports.Flash(`Missed tackle`, C.TextDim) end
		if Me and D.Why == `Ankles` then
			local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
			if Hum then Hum.PlatformStand = true task.delay(math.min(D.Seconds or 1.9, 3), function() Hum.PlatformStand = false end) end
		end
	elseif Kind == `S_Pickup` then
		if Me then Local.Catch() end -- (soccer-2.0) the keeper's catch clip (Local.Catch checks keeper + zone)
		local R = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if R then Local.Ring(R.Position - Vector3.new(0, 2.6, 0), Color3.fromRGB(240, 236, 226), 9) end
	elseif Kind == `S_Goal` then
		local Col = Config.Teams[D.Team] and Config.Teams[D.Team].Color or C.Gold
		local Mouth
		for _, X in (workspace:FindFirstChild(`Sports`) and workspace.Sports:FindFirstChild(`Pitch`) or workspace):GetDescendants() do
			if X:IsA(`BasePart`) and X:GetAttribute(`SportGoal`) == D.Team then Mouth = X break end
		end
		local F = Local.Fx()
		local Watching = Local.Active() or (Mouth ~= nil and (not F or F.Near(Mouth.Position, 150)))
		if Mouth and Watching then
			-- upright rings bursting out of the goal mouth (they used to lie flat inside the box)
			local Sz = Mouth.Size
			local Axis = if Sz.X < Sz.Z then Mouth.CFrame.RightVector else Mouth.CFrame.LookVector
			for I = 0, 2 do task.delay(I * 0.15, function() Local.Ring(Mouth.Position, Col, 5 + I * 3, Axis) end) end
			if F then
				-- VFX P2-5: an upright team-colour flare in the goal mouth...
				F.Burst(Mouth.Position - Vector3.new(0, Sz.Y / 2 - 0.5, 0), {
					Texture = F.Tex.Wisp; Color = Col; Count = 14; Size = 2.4; Spread = 12; Direction = Enum.NormalId.Top;
					Speed = NumberRange.new(14, 22); Lifetime = NumberRange.new(0.7, 1.1); Accel = Vector3.new(0, -6, 0); LightEmission = 0.9; Drag = 1;
				})
				F.Light(Mouth.Position, Col, 2, 14, 1.2)
				-- ...and shards off both posts
				local Across = if Sz.X < Sz.Z then Mouth.CFrame.LookVector * (Sz.Z / 2) else Mouth.CFrame.RightVector * (Sz.X / 2)
				for _, Side in { -1, 1 } do
					F.Burst(Mouth.Position + Across * Side, {
						Texture = F.Tex.Shards; Flipbook = `Grid2x2`; Color = Col:Lerp(Color3.new(1, 1, 1), 0.3); Count = 10; Size = 0.5;
						Speed = NumberRange.new(6, 12); Lifetime = NumberRange.new(0.5, 0.9); Spread = 70; Accel = Vector3.new(0, -20, 0);
					})
				end
			end
			Local.PulseLights()
		end
		local Sc = D.Scorer
		if typeof(Sc) == `Instance` and Sc.Character then Local.Pose(Sc.Character, `Celebrate`) end
		if Local.Active() then Local.GoalCam(if typeof(Sc) == `Instance` then Sc else nil) end
	elseif Kind == `S_Bloodrush` then
		local R = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if R then Local.Ring(R.Position - Vector3.new(0, 2.6, 0), Config.RaceAura[P:GetAttribute(`Race`) or `Human`] or C.Crimson, 14) end
		if Me then Local.Shake(1, 0.4) end
	elseif Kind == `S_Call` then
		local S = Local.State()
		if not Me and S and P:GetAttribute(`SportTeam`) == Player:GetAttribute(`SportTeam`) then
			local Head = Char and Char:FindFirstChild(`Head`)
			if Head then
				local G = new(`BillboardGui`, { Size = UDim2.fromScale(2, 2); StudsOffset = Vector3.new(0, 2.5, 0); AlwaysOnTop = true; Adornee = Head }, Player.PlayerGui)
				Kit.Image(`Pip`, { ImageColor3 = C.Gold; Size = UDim2.fromScale(1, 1); Parent = G })
				task.delay(1.5, function() G:Destroy() end)
			end
		end
	elseif Kind == `S_Text` then
		if Me and typeof(D.Text) == `string` then Sports.Flash(D.Text, C.TextDim) end
	elseif Kind == `S_Target` then
		if Me then Sports.Flash(if D.Index == 0 then `Clean pass!` else `Target!`, C.Gold) end
	end
end

---| touch + gamepad (kit art) |---

local Bound = false
function Local.Pad(Name: string, Began: boolean)
	if not Local.Active() then return end
	local S = Local.State()
	local Ball = Sports.HasBall()
	if Name == `NHSoccerKick` then
		if Began and Ball then ChargeAt = os.clock() FullCharged = false Sports.Send(`KickStart`)
		elseif Began and not S.Drill then Sports.Send(`KickRelease`, { Aim = Local.Aim(); Curve = 0 })
		elseif not Began then Local.Release() end
	elseif not Began then return
	elseif Name == `NHSoccerPass` then
		if Ball then Sports.Send(`Pass`, { Aim = Local.Aim() }) elseif not S.Drill then Sports.Send(`Call`) end
	elseif Name == `NHSoccerMove` and not S.Drill then
		if Ball then Sports.Send(`Dribble`, { Dir = Local.MoveDir() }) elseif S.Keeper and S.InZone then Sports.Send(`Dive`, { Dir = Local.MoveDir() }) end
	elseif Name == `NHSoccerTackle` and not Ball and not S.Drill then
		local R = Local.Root()
		Sports.Send(`Tackle`, { Dir = if R then R.CFrame.LookVector else nil })
	elseif Name == `NHSoccerFeint` and Ball and not S.Drill then Sports.Send(`Feint`)
	elseif Name == `NHSoccerRush` and not S.Drill then Sports.Send(`Bloodrush`)
	end
end

function Local.BindPads(On: boolean)
	if On == Bound then return end
	Bound = On
	local List = {
		{ `NHSoccerKick`, `Kick`, Enum.KeyCode.ButtonR2, UDim2.new(1, -95, 1, -230) };
		{ `NHSoccerPass`, `Pass`, Enum.KeyCode.ButtonX, UDim2.new(1, -175, 1, -185) };
		{ `NHSoccerMove`, `Dribble`, Enum.KeyCode.ButtonY, UDim2.new(1, -175, 1, -265) };
		{ `NHSoccerTackle`, `Tackle`, Enum.KeyCode.ButtonB, UDim2.new(1, -95, 1, -310) };
		{ `NHSoccerFeint`, `Feint`, Enum.KeyCode.ButtonL2, UDim2.new(1, -255, 1, -225) };
		{ `NHSoccerRush`, `Rush`, Enum.KeyCode.ButtonL1, UDim2.new(1, -255, 1, -305) };
	}
	for _, B in List do
		if On then
			ContextActionService:BindAction(B[1], function(Name, InputState)
				if InputState == Enum.UserInputState.Begin then Local.Pad(Name, true)
				elseif InputState == Enum.UserInputState.End then Local.Pad(Name, false) end
				return Enum.ContextActionResult.Sink
			end, true, B[3])
			pcall(ContextActionService.SetImage, ContextActionService, B[1], Theme.Images[`IconSoccer{B[2]}`] or Theme.Images.Pip) -- each move's own icon (docs/Icon-Set.md)
			pcall(ContextActionService.SetTitle, ContextActionService, B[1], B[2])
			pcall(ContextActionService.SetPosition, ContextActionService, B[1], B[4])
			task.defer(function() -- the title sits in the icon's dark lower band
				local Btn = ContextActionService:GetButton(B[1])
				local T = Btn and Btn:FindFirstChild(`ActionTitle`)
				if T and T:IsA(`TextLabel`) then T.AnchorPoint = Vector2.new(0.5, 1); T.Position = UDim2.fromScale(0.5, 0.95); T.Size = UDim2.fromScale(0.84, 0.3) end
			end)
		else
			ContextActionService:UnbindAction(B[1])
		end
	end
end

function Shared.OnStart()
	RunService.Heartbeat:Connect(function() pcall(Local.AuraStep) end)
	local Folder = ReplicatedStorage:WaitForChild(`NHSports`, 60)
	if not Folder then return end
	Local.Build()
	Sports.Hints.Soccer = function(S)
		if S.Drill then return `<b>Click</b> hold/release shoot   <b>R</b> pass   <b>X</b> quit` end
		if S.HasBall then return `<b>Click</b> shoot (A/D curve)   <b>R</b> pass   <b>Q</b> dribble   <b>Right-click</b> feint   <b>T</b> Bloodrush` end
		if S.Keeper and S.InZone then return `<b>Q</b> dive   walk into the ball to catch it   <b>Click</b> throw   <b>E</b> tackle` end
		return `<b>E</b> tackle   <b>Click</b> volley / header   <b>R</b> call for it   <b>T</b> Bloodrush`
	end
	local Root = workspace:WaitForChild(`Sports`, 30)
	if Root then
		local function track(D) if D:IsA(`BasePart`) and D:GetAttribute(`SportBall`) then Balls[D] = true end end
		for _, D in Root:GetDescendants() do track(D) end
		Root.DescendantAdded:Connect(track)
		Root.DescendantRemoving:Connect(function(D)
			Balls[D] = nil
			local Mk = Local.Marks[D]
			if Mk then Mk:Destroy() Local.Marks[D] = nil end
		end)
	end
	Folder:WaitForChild(`Fx`).OnClientEvent:Connect(function(Kind, D) pcall(Local.OnFx, Kind, D) end)
	UserInputService.InputBegan:Connect(function(I, P) Local.Input(I, P, true) end)
	UserInputService.InputEnded:Connect(function(I, P) Local.Input(I, P, false) end)
	RunService.RenderStepped:Connect(function()
		local Ok, Err = pcall(Local.Draw)
		if not Ok then warn(`[Soccer HUD] {Err}`) end
		pcall(Local.StunStep)
		pcall(Local.SpeedStep)
		if not Local.Active() then ChargeAt = nil end   -- a charge never survives leaving the game or drill
		pcall(Local.BallStep)
		pcall(Local.BindPads, Local.Active())
	end)
	RunService.PreSimulation:Connect(function()
		local Ok, Err = pcall(Local.PoseStep)
		if not Ok then warn(`[Soccer poses] {Err}`) end
	end)
end

-- (soccer-2.0) Studio checks drive the server's Fx through the real handler (tools/soccer2/checks)
function Shared.FxForTests(Kind: string, D: any) if RunService:IsStudio() then Local.OnFx(Kind, D) end end
function Shared.TracksForTests(Char: Model): { [string]: AnimationTrack } return Tracks[Char] or {} end

return Shared
