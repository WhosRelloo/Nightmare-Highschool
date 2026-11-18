--!nonstrict
-- (2.26.0) The Unwritten for the Chapter One finale: a faded student from the 1893 roll. Built from the AI rig (R6) with
-- existing clothing (UI.Appearance: the Victorian Waistcoat shirt, the Pinstripes + Riding Boots pants) and the game's
-- smoke texture (the down-smoke / combat dust puff) only. Re-run safe. Run in Edit.
local RS = game:GetService("ReplicatedStorage")
local Cast = RS:FindFirstChild("NHCineCast") or Instance.new("Folder")
Cast.Name = "NHCineCast"
Cast.Parent = RS
local Old = Cast:FindFirstChild("Strikethrough")
if Old then Old:Destroy() end
local M = game.ServerScriptService.Services.AI.AI.Rig:Clone()
M.Name = "Strikethrough"
for _, D in M:GetDescendants() do
	if D:IsA("Script") or D:IsA("LocalScript") or D:IsA("BillboardGui") then D:Destroy() end
end
local SHIRT, PANTS = "rbxassetid://92860287023765", "rbxassetid://121154909777878"
local SMOKE = "rbxassetid://8527116276"
local Shirt = M:FindFirstChildOfClass("Shirt") or Instance.new("Shirt", M)
local Pants = M:FindFirstChildOfClass("Pants") or Instance.new("Pants", M)
Shirt.ShirtTemplate, Pants.PantsTemplate = SHIRT, PANTS
Shirt.Color3 = Color3.fromRGB(118, 116, 130) -- washes the crimson waistcoat out to a faded grey-plum
Pants.Color3 = Color3.fromRGB(105, 104, 118)
-- faded: ash-grey skin, slightly see-through limbs, the head an ink smudge (no face)
local INK = Color3.fromRGB(18, 14, 22)
for _, P in M:GetChildren() do
	if P:IsA("BasePart") and P.Name ~= "HumanoidRootPart" then
		P.Color = Color3.fromRGB(150, 148, 156)
		P.Transparency = if P.Name == "Torso" or P.Name == "Head" then 0.05 else 0.25
		P.Material = Enum.Material.SmoothPlastic
	end
end
local BC = M:FindFirstChildOfClass("BodyColors")
if BC then BC:Destroy() end
local Head = M.Head
for _, D in Head:GetDescendants() do
	if D:IsA("Decal") then D.Transparency = 1 elseif D:IsA("SurfaceGui") then D.Enabled = false end
end
Head.Color = INK
Head.Transparency = 0.4 -- half there: the ink smoke reads as the head
for _, D in M:GetChildren() do if D:IsA("Accessory") then D:Destroy() end end -- no hair: the head is ink
M:SetAttribute("NHFaceless", true)
M:SetAttribute("NpcId", "Strikethrough")
local Hum = M:FindFirstChildOfClass("Humanoid")
Hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
if not Hum:FindFirstChildOfClass("Animator") then Instance.new("Animator", Hum) end
-- ink bleeding off the edges (the game's smoke, tinted ink) and torn pages circling it (the kit's paper colour)
local function emitter(Part, Name, Props)
	local A = Instance.new("Attachment") A.Name = Name .. "Att" A.Parent = Part
	local E = Instance.new("ParticleEmitter") E.Name = Name
	for K, V in Props do E[K] = V end
	E.Parent = A
	return E
end
for _, P in { M.Torso, M["Left Arm"], M["Right Arm"], M["Left Leg"], M["Right Leg"] } do
	emitter(P, "Ink", { Texture = SMOKE; Color = ColorSequence.new(INK); LightEmission = 0; Rate = 14;
		Lifetime = NumberRange.new(0.6, 1.2); Speed = NumberRange.new(0.3, 0.9); Acceleration = Vector3.new(0, -2.5, 0);
		Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 1.4) });
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }); SpreadAngle = Vector2.new(25, 25) })
end
emitter(Head, "InkHead", { Texture = SMOKE; Color = ColorSequence.new(INK); Rate = 16; Lifetime = NumberRange.new(0.5, 0.9);
	Speed = NumberRange.new(0.1, 0.4); Size = NumberSequence.new(0.9, 1.6); Transparency = NumberSequence.new(0.2, 1) })
emitter(M.Torso, "Pages", { Texture = SMOKE; Color = ColorSequence.new(Color3.fromRGB(214, 200, 168)); Rate = 3;
	Lifetime = NumberRange.new(1.8, 2.6); Speed = NumberRange.new(1.5, 2.5); RotSpeed = NumberRange.new(-120, 120);
	Size = NumberSequence.new(0.35); Shape = Enum.ParticleEmitterShape.Cylinder; ShapeStyle = Enum.ParticleEmitterShapeStyle.Surface;
	Orientation = Enum.ParticleOrientation.VelocityPerpendicular; Transparency = NumberSequence.new(0.1, 1) })
M.Parent = Cast
local parts = 0
for _, P in M:GetChildren() do if P:IsA("BasePart") then parts += 1 end end
return "built " .. M:GetFullName() .. ", " .. parts .. " parts, rig " .. Hum.RigType.Name
