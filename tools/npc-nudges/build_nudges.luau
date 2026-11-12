--[[
	build_nudges.luau  (1.86.3)  run in Studio's command bar or through MCP execute_luau, Edit mode.

	Builds ServerStorage.NHNudges with three KeyframeSequences for the students' bump reactions, keyed from the
	design canvas "NPC Nudge Animations" (https://claude.ai/artifact/H8o9KQqcyvtqSrpThZfVhq):
	  Nudge_Left     bumped on the left shoulder: twist, not lean. Upper body only (Hips unkeyed, the walk keeps the legs)
	  Nudge_Right    the mirror
	  Shove_Forward  a hard shove from behind: fold, low stagger, rise. Full body, Action2

	R6 joint directions (checked numerically on Services.AI.AI.Rig):
	  Root Joint  X+ lean forward, Y+ lean left, Z+ turn left; translate (0,-d,0) forward, (0,0,-d) down
	  Neck        X+ chin down, Y+ tilt left, Z+ turn left
	  Shoulders   Right Z+ swings forward, Left Z+ swings back; X- lifts either arm out
	  Hips        Right Z+ leg forward, Left Z+ leg back
	Pose easing is reversed from TweenService: PoseEasingDirection.In is the fast start ("snap in").

	The head turn toward the passer mostly comes from NpcLook (NHLookAt, which the brain sets before the hook), so the
	neck yaw here is a third of the design's: the two add up.
]]

local ServerStorage = game:GetService(`ServerStorage`)
local rad = math.rad
local FPS = 30
local SNAP = Enum.PoseEasingDirection.In -- fast start
local SMOOTH = Enum.PoseEasingDirection.InOut

local function pose(Parent: Instance, Name: string, CF: CFrame?, Dir: Enum.PoseEasingDirection, Weight: number?): Pose
	local P = Instance.new(`Pose`)
	P.Name = Name
	P.CFrame = CF or CFrame.identity
	P.Weight = Weight or 1
	P.EasingStyle = Enum.PoseEasingStyle.Cubic
	P.EasingDirection = Dir
	P.Parent = Parent
	return P
end

-- Frames: { [i] = { F = frame, Dir = easing out of this key, Root = CFrame, Neck = CFrame, RS, LS, RH?, LH? } }
local function build(Name: string, Priority: Enum.AnimationPriority, Frames): KeyframeSequence
	local KS = Instance.new(`KeyframeSequence`)
	KS.Name = Name
	KS.Loop = false
	KS.Priority = Priority
	for _, K in Frames do
		local Key = Instance.new(`Keyframe`)
		Key.Time = K.F / FPS
		Key.Name = K.Name or `F{K.F}`
		local HRP = pose(Key, `HumanoidRootPart`, nil, K.Dir, 0)
		local Torso = pose(HRP, `Torso`, K.Root, K.Dir)
		pose(Torso, `Head`, K.Neck, K.Dir)
		pose(Torso, `Right Arm`, K.RS, K.Dir)
		pose(Torso, `Left Arm`, K.LS, K.Dir)
		if K.RH then pose(Torso, `Right Leg`, K.RH, K.Dir) end
		if K.LH then pose(Torso, `Left Leg`, K.LH, K.Dir) end
		Key.Parent = KS
	end
	return KS
end

---| Nudge_Left / Nudge_Right (0.7 s) |---
-- columns: frame, root yaw (bumped shoulder back +), root roll (away from the hit +), neck yaw (toward the passer +),
-- neck roll (away from the hit +), hit-side shoulder back, hit-side shoulder out, far shoulder forward
local SIDE = {
	{ 0, 0, 0, 0, 0, 0, 0, 0 },
	{ 2, 5, 2, -1, -3, 10, 6, 6 },
	{ 5, 12, 4, 6, -2, 30, 10, 22 },
	{ 10, 9, 2, 10, 0, 22, 6, 16 },
	{ 16, -2, -1, 4, 0, 4, 0, 2 },
	{ 21, 0, 0, 0, 0, 0, 0, 0 },
}

local function side(Left: boolean): KeyframeSequence
	local S = if Left then 1 else -1 -- hit on the left: turn left (Z+), lean right (Y-)
	local Frames = {}
	for _, R in SIDE do
		local F, Yaw, Roll, NYaw, NRoll, Back, Out, Fwd = table.unpack(R)
		local HitArm = CFrame.Angles(rad(-Out), 0, rad(Back * S)) -- Left Z+ is back; Right Z- is back
		local FarArm = CFrame.Angles(0, 0, rad(Fwd * S)) -- Right Z+ is forward; Left Z- is forward
		table.insert(Frames, {
			F = F;
			Dir = if F < 5 then SNAP else SMOOTH;
			Root = CFrame.Angles(0, rad(-Roll * S), rad(Yaw * S));
			Neck = CFrame.Angles(0, rad(-NRoll * S), rad(NYaw * S));
			LS = if Left then HitArm else FarArm;
			RS = if Left then FarArm else HitArm;
		})
	end
	return build(if Left then `Nudge_Left` else `Nudge_Right`, Enum.AnimationPriority.Action, Frames)
end

---| Shove_Forward (1.8 s) |---
-- the canvas's side view (facing right, 40 px a stud): x forward, y down (px), t torso pitch about the hips, h neck
-- pitch, an/af near/far arm (negative = forward, relative to the torso), ln/lf near/far leg (negative = forward, world)
local SHOVE = {
	{ f = 0, n = `Rest`, x = 0, y = 0, t = 0, h = 0, an = 0, af = 0, ln = 0, lf = 0 },
	{ f = 2, n = `Impact`, x = 8, y = 2, t = -8, h = -15, an = 30, af = 25, ln = 4, lf = 3 },
	{ f = 6, n = `Fold`, x = 14, y = 10, t = 38, h = 10, an = -50, af = -35, ln = -25, lf = 20 },
	{ f = 12, n = `Stagger1`, x = 12, y = 12, t = 34, h = 6, an = -70, af = -20, ln = 15, lf = -30 },
	{ f = 18, n = `Stagger2`, x = 10, y = 10, t = 30, h = 4, an = -40, af = -75, ln = -28, lf = 18 },
	{ f = 26, n = `LowCatch`, x = 8, y = 12, t = 22, h = 0, an = -35, af = -30, ln = -22, lf = 20 },
	{ f = 38, n = `Rise`, x = 3, y = 3, t = 8, h = -4, an = -10, af = -8, ln = -6, lf = 5 },
	{ f = 46, n = `LookBack`, x = -1, y = 0, t = -3, h = -6, an = 0, af = 0, ln = 0, lf = 0 },
	{ f = 54, n = `Settle`, x = 0, y = 0, t = 0, h = 0, an = 0, af = 0, ln = 0, lf = 0 },
}

local HIP = CFrame.new(0, 0, -1) -- the hip line in the Root Joint's frame: the canvas folds about the hips, not the chest

-- the lowest foot corner (height in the root part's space) for a root and hip pose, from the student rig's joints
local Rig = game:GetService(`ServerScriptService`).Services.AI.AI.Rig
local RJ, RHip, LHip = Rig.HumanoidRootPart.RootJoint, Rig.Torso[`Right Hip`], Rig.Torso[`Left Hip`]
local function lowestFoot(Root: CFrame, RH: CFrame, LH: CFrame): number
	local Torso = RJ.C0 * Root * RJ.C1:Inverse()
	local Low = math.huge
	for _, Leg in { Torso * RHip.C0 * RH * RHip.C1:Inverse(), Torso * LHip.C0 * LH * LHip.C1:Inverse() } do
		for _, X in { -0.5, 0.5 } do
			for _, Z in { -0.5, 0.5 } do
				Low = math.min(Low, Leg:PointToWorldSpace(Vector3.new(X, -1, Z)).Y)
			end
		end
	end
	return Low
end
local REST = lowestFoot(CFrame.identity, CFrame.identity, CFrame.identity)

local function shove(): KeyframeSequence
	local Frames = {}
	for _, K in SHOVE do
		local Fold = HIP * CFrame.Angles(rad(K.t), 0, 0) * HIP:Inverse()
		local Root = CFrame.new(0, -K.x / 40, -K.y / 40) * Fold
		-- legs hang from the torso, so a world angle needs the fold added back
		local RH = CFrame.Angles(0, 0, rad(-K.ln + K.t))
		local LH = CFrame.Angles(0, 0, rad(K.lf - K.t))
		-- plant the lowest foot on the floor: the drop is whatever keeps it there, never through it
		Root = CFrame.new(0, 0, REST - lowestFoot(Root, RH, LH)) * Root
		table.insert(Frames, {
			F = K.f;
			Name = K.n;
			Dir = if K.f < 6 then SNAP else SMOOTH;
			Root = Root;
			Neck = CFrame.Angles(rad(K.h), 0, 0);
			RS = CFrame.Angles(0, 0, rad(-K.an)); -- near arm forward = -an
			LS = CFrame.Angles(0, 0, rad(K.af)); -- far arm: Left Z+ is back
			RH = RH;
			LH = LH;
		})
	end
	return build(`Shove_Forward`, Enum.AnimationPriority.Action2, Frames)
end

local Folder = ServerStorage:FindFirstChild(`NHNudges`)
if Folder then Folder:Destroy() end
Folder = Instance.new(`Folder`)
Folder.Name = `NHNudges`
side(true).Parent = Folder
side(false).Parent = Folder
shove().Parent = Folder
Folder.Parent = ServerStorage

local Out = {}
for _, KS in Folder:GetChildren() do
	table.insert(Out, `{KS.Name}: {#KS:GetKeyframes()} keys, {KS.Priority.Name}`)
end
return table.concat(Out, ` | `)
