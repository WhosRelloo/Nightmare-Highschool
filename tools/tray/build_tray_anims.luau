--!nocheck
-- Lunch tray clips (props batch 54): eight R6 KeyframeSequences in ServerStorage.NHTrayAnims for the owner to publish
-- (Animation Editor > Publish to Roblox, under the group), then their ids go in ReplicatedStorage.Config.Tray.Anims.
-- Until then Services.Features.Tray plays them in Studio straight from here (KeyframeSequenceProvider).
--
-- Each pose is a Motor6D Transform on top of the carry the server sets through the shoulders' C0 (Config.Tray.Hold,
-- pitch 56 and yaw 20 degrees). Measured on a 0.9-scale R6 rig (2026-11-12), all in radians, CFrame.Angles(x, y, z):
--   right shoulder  +Z raises the arm forward and up, +Y swings it inward; the left shoulder mirrors (-Z, -Y)
--   neck            +X looks down, -X looks up, +Z turns the head to its left
--   root (Torso)    +X leans forward, -X back, +Y rolls to its left, Z turns
-- Keys used below: the bite (the hand just in front of the mouth) R {0, 0.7, 1.3}; the scoop (over the tray) R {0, 0.4,
-- 0.12}; the arms back at the sides (exactly undoing the carry) R {-0.293, -0.192, -1.006} / L {-0.293, 0.192, 1.006};
-- from rest, the hand to the nose R {0, 1.15, 2.2}.
local SS = game:GetService("ServerStorage")
local Old = SS:FindFirstChild("NHTrayAnims")
if Old then Old:Destroy() end
local Folder = Instance.new("Folder")
Folder.Name = "NHTrayAnims"
Folder:SetAttribute("Note", "Lunch tray clips: publish each under the group, then put the ids in ReplicatedStorage.Config.Tray.Anims")

local JOINTS = { r = "Right Arm", l = "Left Arm", h = "Head" }
local Z = { 0, 0, 0 }

local function seq(Name, Loop, Priority, Frames)
	local K = Instance.new("KeyframeSequence")
	K.Name = Name
	K.Loop = Loop
	K.Priority = Priority
	-- a joint keyed anywhere in the clip is keyed in every frame (a gap would let it blend back to the walk)
	local keyed = {}
	for _, F in Frames do for k in pairs(F) do if k ~= "t" then keyed[k] = true end end end
	for _, F in Frames do
		local Kf = Instance.new("Keyframe")
		Kf.Time = F.t
		local Root = Instance.new("Pose") Root.Name = "HumanoidRootPart" Root.Weight = 0 Root.Parent = Kf
		local Torso = Instance.new("Pose")
		Torso.Name = "Torso"
		Torso.Weight = if keyed.tor then 1 else 0
		local tor = F.tor or Z
		Torso.CFrame = if keyed.tor then CFrame.Angles(tor[1], tor[2], tor[3]) else CFrame.identity
		Torso.EasingStyle = Enum.PoseEasingStyle.Cubic
		Torso.EasingDirection = Enum.PoseEasingDirection.InOut
		Torso.Parent = Root
		for key, Part in JOINTS do
			local P = Instance.new("Pose")
			P.Name = Part
			P.Weight = if keyed[key] then 1 else 0
			local A = F[key] or Z
			P.CFrame = if keyed[key] then CFrame.Angles(A[1], A[2], A[3]) else CFrame.identity
			P.EasingStyle = Enum.PoseEasingStyle.Cubic
			P.EasingDirection = Enum.PoseEasingDirection.InOut
			P.Parent = Torso
		end
		Kf.Parent = K
	end
	K.Parent = Folder
	return K
end

local BITE, SCOOP = { 0, 0.7, 1.3 }, { 0, 0.4, 0.12 }
local R_DOWN, L_DOWN = { -0.293, -0.192, -1.006 }, { -0.293, 0.192, 1.006 }
local A2, A3 = Enum.AnimationPriority.Action2, Enum.AnimationPriority.Action3

-- 1. eating standing: the left hand keeps the tray, the right scoops, bites and chews
seq("EatStand", true, A2, {
	{ t = 0; r = Z; l = Z; h = Z };
	{ t = 0.35; r = SCOOP; l = Z; h = { 0.22, 0, 0 } };
	{ t = 0.8; r = BITE; l = Z; h = { 0.04, 0, 0 } };
	{ t = 1.05; r = BITE; l = Z; h = { 0.14, 0, 0 } };
	{ t = 1.3; r = BITE; l = Z; h = { 0.03, 0, 0 } };
	{ t = 1.55; r = { 0, 0.62, 1.15 }; l = Z; h = { 0.13, 0, 0 } };
	{ t = 1.95; r = SCOOP; l = Z; h = { 0.2, 0, 0 } };
	{ t = 2.4; r = Z; l = Z; h = Z };
})

-- 2. eating sitting: the tray on the table, the left forearm on its edge; scoop, bite, chew, a glance round the room
seq("EatSit", true, A2, {
	{ t = 0; r = Z; l = { 0, 0, 0.12 }; h = { 0.15, 0, 0 } };
	{ t = 0.4; r = SCOOP; l = { 0, 0, 0.12 }; h = { 0.25, 0, 0 } };
	{ t = 0.85; r = BITE; l = { 0, 0, 0.12 }; h = { 0.05, 0, 0 } };
	{ t = 1.1; r = BITE; l = { 0, 0, 0.12 }; h = { 0.15, 0, 0 } };
	{ t = 1.35; r = BITE; l = { 0, 0, 0.12 }; h = { 0.04, 0, 0 } };
	{ t = 1.8; r = SCOOP; l = { 0, 0, 0.12 }; h = { 0.2, 0, 0 } };
	{ t = 2.3; r = Z; l = { 0, 0, 0.12 }; h = { 0.1, 0, 0.32 } };
	{ t = 2.8; r = Z; l = { 0, 0, 0.12 }; h = { 0.05, 0, -0.26 } };
	{ t = 3.4; r = Z; l = { 0, 0, 0.12 }; h = { 0.15, 0, 0 } };
})

-- 3. sitting down: the tray is lowered to the table, the head follows it; standing up: lifted back to the carry
seq("SitDown", false, A2, {
	{ t = 0; r = Z; l = Z; h = Z };
	{ t = 0.35; r = { 0, 0, -0.3 }; l = { 0, 0, 0.3 }; h = { 0.18, 0, 0 } };
	{ t = 0.7; r = Z; l = Z; h = { 0.1, 0, 0 } };
})
seq("StandUp", false, A2, {
	{ t = 0; r = { 0, 0, -0.3 }; l = { 0, 0, 0.3 }; h = { 0.12, 0, 0 } };
	{ t = 0.6; r = Z; l = Z; h = Z };
})

-- 4. waiting in the queue with a tray (looped while standing still): a look up at the menu board, a glance down the
-- line each way, a small weight shift. The arms stay on the tray (TrayFx keeps them), so only the head and torso move.
seq("QueueIdle", true, Enum.AnimationPriority.Action, {
	{ t = 0; h = Z; tor = Z };
	{ t = 1.0; h = { -0.22, 0, 0 }; tor = { 0, 0.035, 0 } };
	{ t = 2.0; h = { -0.18, 0, 0.22 }; tor = { 0, 0.035, 0 } };
	{ t = 2.9; h = { 0.02, 0, -0.32 }; tor = Z };
	{ t = 3.9; h = { 0.05, 0, 0 }; tor = { 0, -0.03, 0 } };
	{ t = 5.0; h = Z; tor = Z };
})

-- 5. spill: arms thrown up as the tray goes, head back, a recoil; a look down at the mess; the arms drop to the sides
seq("Spill", false, A3, {
	{ t = 0; r = Z; l = Z; h = Z; tor = Z };
	{ t = 0.12; r = { 0, -0.4, 1.4 }; l = { 0, 0.4, -1.4 }; h = { -0.3, 0, 0 }; tor = { -0.14, 0, 0 } };
	{ t = 0.45; r = { 0, -0.5, 1.15 }; l = { 0, 0.5, -1.15 }; h = { 0.38, 0, 0.1 }; tor = { 0.1, 0, 0 } };
	{ t = 0.85; r = R_DOWN; l = L_DOWN; h = { 0.32, 0, 0 }; tor = { 0.06, 0, 0 } };
	{ t = 1.25; r = R_DOWN; l = L_DOWN; h = { 0.15, 0, 0 }; tor = Z };
})

-- 6. returning the tray: push it onto the rack, let go, arms back to the sides
seq("Return", false, A2, {
	{ t = 0; r = Z; l = Z; h = Z; tor = Z };
	{ t = 0.4; r = { 0, 0, 0.15 }; l = { 0, 0, -0.15 }; h = { 0.18, 0, 0 }; tor = { 0.12, 0, 0 } };
	{ t = 0.55; r = { 0, 0, 0.12 }; l = { 0, 0, -0.12 }; h = { 0.15, 0, 0 }; tor = { 0.12, 0, 0 } };
	{ t = 1.0; r = R_DOWN; l = L_DOWN; h = Z; tor = Z };
})

-- 7. the mystery meat: up to the nose, a sniff, a recoil and a turn away, a shake of the head, then a resigned bite
-- (from rest: no tray; it plays over the usual eating clip)
seq("Grimace", false, A3, {
	{ t = 0; r = Z; h = Z; tor = Z };
	{ t = 0.25; r = { 0, 1.15, 2.2 }; h = { 0.18, 0, 0 }; tor = { 0.05, 0, 0 } };
	{ t = 0.55; r = { 0, 0.7, 1.4 }; h = { -0.25, 0, 0.3 }; tor = { -0.12, 0, 0 } };
	{ t = 0.85; r = { 0, 0.7, 1.4 }; h = { 0.05, 0, -0.28 }; tor = { -0.06, 0, 0 } };
	{ t = 1.05; r = { 0, 0.7, 1.4 }; h = { 0.05, 0, 0.24 }; tor = { -0.04, 0, 0 } };
	{ t = 1.3; r = { 0, 1.15, 2.2 }; h = { 0.12, 0, 0 }; tor = Z };
	{ t = 1.6; r = Z; h = Z; tor = Z };
})

Folder.Parent = SS
local names = {}
for _, k in Folder:GetChildren() do table.insert(names, k.Name) end
table.sort(names)
return #names .. " clips: " .. table.concat(names, ", ")
