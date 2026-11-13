--[[
	HandGear (server): combat concept 16 (2.14.0). Hand gear for fists, bought at the armory (Config.Armory.Gear), one
	worn at a time. The worn piece is the character attribute NHGear (Features.Armory keeps it in step with the save),
	which the game reads for the effects:
	  Hand Wraps       you take 10% less guard (posture) damage while blocking           DamageLogic.Processed
	  Weighted Gloves  +20% guard damage dealt; fist swings 5% slower                     DamageLogic / Combat.M1 / Predict
	  Brass Knuckles   +15% fist damage, +10% guard damage; contraband                   DamageLogic / HallMonitor
	The effects only count with fists out (the character's Weapon attribute is Fist).
	Looks: each piece's mesh (Config.Armory.Gear[...].Mesh with its textures, group uploads) is welded to both arms'
	bottom ends. While a mesh id is empty nothing is drawn.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Armory = require(ReplicatedStorage.Config.Armory)

local HandGear = {}

HandGear.Effects = {
	HandWraps = { GuardTaken = 0.9 };
	WeightedGloves = { GuardDealt = 1.2; SwingSpeed = 0.95 };
	BrassKnuckles = { GuardDealt = 1.1; Damage = 1.15 };
}

-- the effects of what Character wears, if its fists are out
function HandGear.Of(Character: Instance?): { [string]: number }?
	if not (Character and Character:IsA(`Model`)) then return nil end
	if Character:GetAttribute(`Weapon`) ~= `Fist` then return nil end
	local Id = Character:GetAttribute(`NHGear`)
	return if typeof(Id) == `string` then HandGear.Effects[Id] else nil
end

function HandGear.Mult(Character: Instance?, Key: string): number
	local E = HandGear.Of(Character)
	return E and E[Key] or 1
end

-- weld the worn piece's mesh to both arms (or clear it)
function HandGear.Dress(Character: Model, Id: string?)
	for _, Old in Character:GetChildren() do
		if Old:GetAttribute(`NHGearPiece`) then Old:Destroy() end
	end
	local G = Id and Armory.GearById[Id]
	if not (G and typeof(G.Mesh) == `string` and G.Mesh ~= ``) then return end
	for _, ArmName in { `Right Arm`, `Left Arm` } do
		local Arm = Character:FindFirstChild(ArmName)
		if not (Arm and Arm:IsA(`BasePart`)) then continue end
		local Ok, Part = pcall(function()
			local M = Instance.new(`MeshPart`)
			M:ApplyMesh(game:GetService(`AssetService`):CreateMeshPartAsync(Content.fromUri(G.Mesh)))
			return M
		end)
		if not (Ok and Part) then
			local P = Instance.new(`MeshPart`)
			pcall(function() P.MeshId = G.Mesh end)
			Part = P
		end
		Part.Name = `NHGear_` .. Id
		Part.Massless = true
		Part.CanCollide = false
		Part.CanQuery = false
		Part.CanTouch = false
		Part.CastShadow = false
		Part:SetAttribute(`NHGearPiece`, true)
		if G.Textures then
			local SA = Instance.new(`SurfaceAppearance`)
			SA.ColorMap = G.Textures.Color or ``
			SA.NormalMap = G.Textures.Normal or ``
			SA.RoughnessMap = G.Textures.Roughness or ``
			SA.MetalnessMap = G.Textures.Metalness or ``
			SA.Parent = Part
		end
		-- the left hand is the mirror of the right (the mesh is a right hand)
		local Mirror = if ArmName == `Left Arm` then CFrame.Angles(0, math.pi, 0) else CFrame.identity
		Part.CFrame = Arm.CFrame * (G.Offset or CFrame.new(0, -1, 0)) * Mirror
		local W = Instance.new(`WeldConstraint`)
		W.Part0 = Arm
		W.Part1 = Part
		W.Parent = Part
		Part.Parent = Character
	end
end

return HandGear
