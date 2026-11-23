-- infirmarycheck (phase6-strafes T3, Edit): the Infirmary build and the bleacher seats. Reads only.
local Fails, Notes = {}, {}
local Room = workspace.School:FindFirstChild("Infirmary")
if not Room then return "FAIL no School.Infirmary" end
local Zone = Room:FindFirstChild("Zone")
if not (Zone and Zone:GetAttribute("RoomId") == "Infirmary") then table.insert(Fails, "Zone / RoomId") end
local Box = workspace:FindFirstChild("Regions") and workspace.Regions:FindFirstChild("Infirmary")
if not (Box and Box:GetAttribute("RegionId") == "Infirmary") then table.insert(Fails, "no Regions.Infirmary") end
local Post
for _, D in Room:GetDescendants() do if D:IsA("BasePart") and D:GetAttribute("NpcPost") == "Nurse" then Post = D end end
if not Post then table.insert(Fails, "no NpcPost = Nurse") end
for I = 1, 2 do
	local B = Room.Props:FindFirstChild("DormBed_Infirmary" .. I)
	if not (B and typeof(B:GetAttribute("SeatHeight")) == "number") then table.insert(Fails, "bed " .. I .. " / SeatHeight") end
	if not Room:FindFirstChild("NHInfirmaryBed" .. I) then table.insert(Fails, "bed marker " .. I) end
	if not Room:FindFirstChild("NHInfirmarySpot" .. I) then table.insert(Fails, "spot " .. I) end
end
-- nothing of the room overlaps R106, BoilerYard, the hallway floors or the hallway's props
local OP = OverlapParams.new()
OP.FilterType = Enum.RaycastFilterType.Exclude
OP.FilterDescendantsInstances = { Room, Box }
for _, Name in { "WallWest", "WallEast", "WallSouth", "WallNorthL", "WallNorthR", "WallNorthTop" } do
	local W = Room:FindFirstChild(Name)
	if not W then table.insert(Fails, "missing " .. Name) continue end
	for _, Hit in workspace:GetPartBoundsInBox(W.CFrame, W.Size * 0.98, OP) do
		local Top = Hit:FindFirstAncestorOfClass("Model") or Hit
		if not (Hit.Name == "Floor" and Hit.Size.Y < 1) and not Hit.Name:find("Baseplate") then table.insert(Notes, Name .. " touches " .. Top:GetFullName()) end
	end
end
-- floor under each marker
local RP = RaycastParams.new()
RP.FilterType = Enum.RaycastFilterType.Include
RP.FilterDescendantsInstances = { Room.Floor }
for _, M in Room:GetChildren() do
	if M:IsA("BasePart") and (M.Name:find("^NHInfirmary") or M.Name == "NursePost") then
		if not workspace:Raycast(M.Position + Vector3.new(0, 3, 0), Vector3.new(0, -10, 0), RP) then table.insert(Fails, M.Name .. " has no floor") end
	end
end
-- the bleacher seats
local CS = game:GetService("CollectionService")
local Seats = CS:GetTagged("NHBleacherSeat")
table.insert(Notes, #Seats .. " bleacher seats")
if #Seats < 48 then table.insert(Fails, "bleacher seats " .. #Seats) end
for _, S in Seats do if not (S:IsA("Model") and S:GetAttribute("Venue") and S:GetAttribute("SeatHeight")) then table.insert(Fails, "bad seat " .. S:GetFullName()) break end end
return (#Fails == 0 and "PASS infirmarycheck" or ("FAIL infirmarycheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
