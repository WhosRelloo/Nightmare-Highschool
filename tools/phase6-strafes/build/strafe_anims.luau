-- phase6-strafes T4: the shared strafe Animation instances (ReplicatedStorage.Assets.Animations.Movement.StrafeLeft/Right).
-- AnimationController loads the square-chest bake when Config.Locomotion.Ids.*Square is set (or in Studio from
-- ReplicatedStorage.NHLocoClips), else these. Idempotent.
if game.PlaceId ~= 98950102230473 then return "REFUSED: not NH Combat Test" end
local M = game.ReplicatedStorage.Assets.Animations.Movement
local Out = {}
for Name, Id in { StrafeLeft = 126969213208550, StrafeRight = 84541589738848 } do
	local A = M:FindFirstChild(Name) or Instance.new("Animation")
	A.Name = Name
	A.AnimationId = "rbxassetid://" .. Id
	A.Parent = M
	table.insert(Out, A:GetFullName() .. " = " .. A.AnimationId)
end
return table.concat(Out, " · ")
