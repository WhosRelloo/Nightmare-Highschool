-- roomcheck (phase6-infirmary, Edit or Server): the Infirmary's dressing. Reads only.
local Fails, Notes = {}, {}
local function Ok(C, W) if not C then table.insert(Fails, W) end end
local Room = workspace.School:FindFirstChild("Infirmary")
if not Room then return "FAIL no School.Infirmary" end
local D = Room:FindFirstChild("Dressing")
Ok(D, "no Dressing")
if not D then return "FAIL " .. table.concat(Fails, "; ") end
local Slab = D:FindFirstChild("Ceiling") and D.Ceiling:FindFirstChild("CeilingSlab")
Ok(Slab and Slab.Position.Y > 12.9 and Slab.Size.X >= 26 and Slab.Size.Z >= 26, "ceiling slab")
local Pleats, Rails, Colliders = 0, 0, 0
for _, P in D:GetDescendants() do
	if P:IsA("BasePart") then
		if P.Name == "Pleat" then Pleats += 1 end
		if P.Name == "Rail" then Rails += 1 end
		if P.CanCollide and P ~= Slab then Colliders += 1 end
	end
end
Ok(Pleats >= 30, "curtain pleats " .. Pleats)
Ok(Rails == 3, "curtain rails " .. Rails)
Ok(Colliders == 0, Colliders .. " dressing parts collide")
local Want = { "ApothecaryDrawers", "NurseDesk", "MedicineShelf", "FirstAidStation", "Sink", "Nightstand", "Nightstand1", "CarpetDamask", "PendantN", "PendantS", "AnatomySkeleton", "WallClock" }
for _, N in Want do Ok(Room.Props:FindFirstChild("Dress_" .. N), "missing Dress_" .. N) end
local Lights = 0
for _, L in Room:GetDescendants() do if L:IsA("PointLight") then Lights += 1 end end
Ok(Lights >= 4, "lights " .. Lights)
-- every dressing prop sits inside the room (x 199-225, z 13.5-39.5)
for _, M in Room.Props:GetChildren() do
	local CF, Sz = M:GetBoundingBox() -- oriented: the world box from its corners; wall-hung props may sit 0.35 into a wall
	local XL, XH, ZL, ZH = math.huge, -math.huge, math.huge, -math.huge
	for _, X in { -1, 1 } do for _, Z in { -1, 1 } do for _, Y in { -1, 1 } do
		local C = CF * Vector3.new(X * Sz.X / 2, Y * Sz.Y / 2, Z * Sz.Z / 2)
		XL, XH, ZL, ZH = math.min(XL, C.X), math.max(XH, C.X), math.min(ZL, C.Z), math.max(ZH, C.Z)
	end end end
	if XL < 199.15 or XH > 224.85 or ZL < 13.65 or ZH > 39.35 then
		table.insert(Fails, M.Name .. " pokes out of the room")
	end
end
-- the floor is clear at the markers and the approach to each bed's edge (x +2.6 from the bed): nothing solid there
local OP = OverlapParams.new()
OP.FilterType = Enum.RaycastFilterType.Include
OP.FilterDescendantsInstances = { Room.Props, D }
OP.RespectCanCollide = false
local Spots = {}
for _, N in { "NHInfirmarySpot1", "NHInfirmarySpot2", "NursePost" } do local P = Room:FindFirstChild(N) if P then Spots[N] = P.Position end end
for I = 1, 2 do local B = Room.Props:FindFirstChild("DormBed_Infirmary" .. I) Spots["Bed" .. I .. "Edge"] = (B:GetPivot() * CFrame.new(2.6, 0, 0)).Position end
for N, P in Spots do
	local Box = CFrame.new(P.X, 3.6, P.Z)
	for _, Hit in workspace:GetPartBoundsInBox(Box, Vector3.new(1.6, 4, 1.6), OP) do
		local Top = Hit:FindFirstAncestorOfClass("Model") or Hit
		if not (Top.Name:find("DormBed") or Top.Name == "Dress_CarpetDamask" or Hit.Name == "Pleat" or Hit.Name == "Rail") then
			table.insert(Fails, N .. " blocked by " .. Top.Name .. "." .. Hit.Name)
		end
	end
end
table.insert(Notes, string.format("pleats %d, rails %d, lights %d, props %d", Pleats, Rails, Lights, #Room.Props:GetChildren()))
if #Fails > 0 then return "FAIL " .. table.concat(Fails, "; ") .. " | " .. table.concat(Notes, "; ") end
return "PASS roomcheck: " .. table.concat(Notes, "; ")
