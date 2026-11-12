local src = [==[--[[
	BodyFollow (client): Kit C's skinned clothes (coats, long hems) bend with the R6 body. R6 has no layered clothing:
	a piece welded to the Torso would stay rigid while the arms and legs swing through it, so a piece that crosses a
	joint is one skinned mesh with a follow bone per limb, and this controller turns those bones every frame to match
	the limb (part of the turn, about the joint, when the factor is below 1). Vertices weighted to a follow bone move
	exactly with that limb (a sleeve rides its arm, a skirt panel its leg); vertices blended between the torso and a
	follow bone bend across the joint.

	A piece takes part when it carries NHFollow, "LA=1;RA=1;LL=0.5;RL=0.5": which follow bones it has (LA, RA = the
	arms at the shoulders, LL, RL = the legs at the hips) and how much of the limb's turn each one takes (1 = all of it.
	Kit C's skirts take all of it: cloth turned less than an R6 leg, in front of it, gets pushed through by the leg's
	face; art/characters/accessories/nh_acc_batchc1.py). The bones are named F_LA, F_RA, F_LL, F_RL and
	hang off the piece's Root bone (depth 1, so AccessorySway never moves them; sway chains may hang below them and
	swing on top of the follow).

	The maths: the limb's rigid motion in the torso's space since rest is M = rel * C1 * C0^-1 (rel = the limb's pose
	in the torso's space, C0 / C1 its Motor6D's offsets; at rest rel = C0 * C1^-1). A bone whose rest frame is B in the
	torso's space (the weld's offset times the bone's rest frame in the piece) moves a skinned vertex by M when its
	Transform is B^-1 * M * B. Reading the parts' own CFrames covers animation tracks and the old joint angles alike.

	Every character within MAX_DIST of the camera. Reduce Motion doesn't apply: the cloth has to stay on the limbs.
]]
local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)

local MAX_DIST = 150
local Shared = {}

local LIMBS = {
	LA = { Part = `Left Arm`; Motor = `Left Shoulder` };
	RA = { Part = `Right Arm`; Motor = `Right Shoulder` };
	LL = { Part = `Left Leg`; Motor = `Left Hip` };
	RL = { Part = `Right Leg`; Motor = `Right Hip` };
}

local States = {} :: { [BasePart]: any }

local function parseFollow(S: any): { [string]: number }
	local Out = {}
	if type(S) ~= `string` then return Out end
	for Key, F in S:gmatch(`(%u%u)=([%d%.]+)`) do
		if LIMBS[Key] then Out[Key] = math.clamp(tonumber(F) or 1, 0, 1) end
	end
	return Out
end

-- a bone's rest frame in its piece (the chain of parent bones at rest)
local function restInPiece(B: Bone): CFrame
	local CF = B.CFrame
	local P = B.Parent
	while P and P:IsA(`Bone`) do
		CF = P.CFrame * CF
		P = P.Parent
	end
	return CF
end

local function stateFor(Piece: BasePart)
	local S = States[Piece]
	if S then return S end
	local Follow = parseFollow(Piece:GetAttribute(`NHFollow`))
	local Bones = {}
	for Key, F in Follow do
		local B = Piece:FindFirstChild(`F_{Key}`, true)
		if B and B:IsA(`Bone`) then table.insert(Bones, { Key = Key; F = F; Bone = B; Rest = restInPiece(B) }) end
	end
	S = { Bones = Bones }
	States[Piece] = S
	return S
end

local function followPiece(Char: Model, Torso: BasePart, Piece: BasePart)
	local S = stateFor(Piece)
	if #S.Bones == 0 then return end
	local Weld = Piece:FindFirstChild(`NHAccWeld`) :: Weld?
	if not (Weld and Weld.Part0 == Torso) then return end
	local TorsoInv = Torso.CFrame:Inverse()
	for _, E in S.Bones do
		local L = LIMBS[E.Key]
		local Limb = Char:FindFirstChild(L.Part) :: BasePart?
		local Motor = Torso:FindFirstChild(L.Motor) :: Motor6D?
		if not (Limb and Motor and Motor:IsA(`Motor6D`)) then
			E.Bone.Transform = CFrame.identity
			continue
		end
		local Rel = TorsoInv * Limb.CFrame
		local M = Rel * Motor.C1 * Motor.C0:Inverse()
		if E.F < 0.999 then -- part of the limb's turn, about the joint (the motor's pivot), as the checker tests it
			local Piv = Motor.C0.Position
			M = CFrame.new(Piv) * CFrame.identity:Lerp(M.Rotation, E.F) * CFrame.new(-Piv)
		end
		local B = Weld.C0 * Weld.C1:Inverse() * E.Rest
		E.Bone.Transform = B:Inverse() * M * B
	end
end

local function step()
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local Seen = {}
	for _, Pl in Players:GetPlayers() do
		local Char = Pl.Character
		local Torso = Char and Char:FindFirstChild(`Torso`) :: BasePart?
		if not (Torso and Torso:IsA(`BasePart`)) then continue end
		if (Torso.Position - Cam.CFrame.Position).Magnitude > MAX_DIST then continue end
		for _, M in Char:GetChildren() do
			if not (M:IsA(`Model`) and M:GetAttribute(`NHAcc`) ~= nil) then continue end
			for _, P in M:GetChildren() do
				if P:IsA(`BasePart`) and P:GetAttribute(`NHFollow`) then
					Seen[P] = true
					followPiece(Char, Torso, P)
				end
			end
		end
	end
	for P in States do
		if not Seen[P] then
			-- out of range: leave the limbs' last pose rather than snapping (the piece is far away); forget removed ones
			if not P.Parent then States[P] = nil end
		end
	end
end

function Shared.OnStart()
	-- after the frame's animation and physics, before it's drawn: the limbs' CFrames are this frame's pose
	RunService.PreRender:Connect(function()
		local Ok, Err = pcall(step)
		if not Ok then warn(`[BodyFollow] {Err}`) end
	end)
end

return Shared
]==]
local Ch = game.StarterPlayer.StarterPlayerScripts.Controllers.Character
local M = Ch:FindFirstChild("BodyFollow")
if not M then M = Instance.new("ModuleScript") M.Name = "BodyFollow" M.Parent = Ch end
M.Source = src
return "BodyFollow installed, " .. #M.Source .. " bytes"
