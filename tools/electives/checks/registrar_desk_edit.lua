-- registrar_desk_edit (Task 4 step 3): clone the Enrollment desk as the Registrar desk, beside it, clear of everything.
local CS = game:GetService("CollectionService")
if workspace:FindFirstChild("NHRegistrarDesk", true) then return "PASS registrar_desk_edit (already placed)" end
local Src = CS:GetTagged("NHEnrollDesk")[1]
assert(Src and Src:IsA("Model"), "FAIL no enrollment desk model")
local D = Src:Clone()
D.Name = "NHRegistrarDesk"
for _, T in CS:GetTags(D) do CS:RemoveTag(D, T) end
for _, X in D:GetDescendants() do
	for _, T in CS:GetTags(X) do CS:RemoveTag(X, T) end
	if X:IsA("ProximityPrompt") or X:IsA("SurfaceGui") or X:IsA("BillboardGui") then X:Destroy() end
end
local CF, Size = Src:GetBoundingBox()
local Params = OverlapParams.new()
Params.FilterType = Enum.RaycastFilterType.Exclude
Params.FilterDescendantsInstances = { Src, D }
local Placed = nil
for _, Side in { 1, -1 } do
	for _, Gap in { 2, 3, 4, 6 } do
		local Off = CF.RightVector * Side * (Size.X + Gap)
		local Box = CF + Off
		local Hits = workspace:GetPartBoundsInBox(Box + Vector3.new(0, 0.3, 0), Size - Vector3.new(0.2, 0.6, 0.2), Params)
		local Solid = {}
		for _, H in Hits do if H.CanCollide and H.Transparency < 1 then table.insert(Solid, H:GetFullName()) end end
		if #Solid == 0 then Placed = Off break end
	end
	if Placed then break end
end
if not Placed then D:Destroy() return "FAIL no clear spot beside the enrollment desk" end
D:PivotTo(Src:GetPivot() + Placed)
D.Parent = Src.Parent
CS:AddTag(D, "NHRegistrarDesk")
-- the sign
local Host = D.PrimaryPart or D:FindFirstChildWhichIsA("BasePart", true)
local G = Instance.new("SurfaceGui")
G.Name = "RegistrarSign"
G.Face = Enum.NormalId.Front
G.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
G.PixelsPerStud = 40
G.Parent = Host
local L = Instance.new("TextLabel")
L.BackgroundTransparency = 1
L.Size = UDim2.fromScale(1, 0.5)
L.Text = "THE REGISTRAR"
L.TextScaled = true
L.Font = require(game.ReplicatedStorage.UI.Components).Theme.Fonts.Title
L.TextColor3 = Color3.fromRGB(235, 205, 120)
L.Parent = G
return "PASS registrar_desk_edit at " .. tostring(D:GetPivot().Position) .. " host " .. Host.Name
