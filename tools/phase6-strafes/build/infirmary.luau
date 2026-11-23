-- phase6-strafes T3: builds workspace.School.Infirmary (spec §6.2) in NH Combat Test, Edit mode. Idempotent.
-- The lot south of the hallway extension, opposite R106: x 199-225, z 13.5-39.5, floor y 1.1; the door in the north
-- wall at x 215-219 (between the hallway's potted plant at x 211 and the vase at x 225). Walls and floor are cloned
-- from School.R106 (same greybox, same PBR attributes); props are cloned from ServerStorage.NHProps.
if game.PlaceId ~= 98950102230473 then return "REFUSED: not NH Combat Test (" .. game.PlaceId .. ")" end
local School = workspace:FindFirstChild("School")
local R106 = School and School:FindFirstChild("R106")
if not R106 then return "FAIL no School.R106 template" end
if School:FindFirstChild("Infirmary") then return "exists" end

local CX, CZ = 212, 26.5          -- room centre (R106's x)
local X0, X1, Z0, Z1 = 199, 225, 13.5, 39.5
local DoorX, DoorW = 217, 4
local M = Instance.new("Model")
M.Name = "Infirmary"
M:SetAttribute("RoomId", "Infirmary")
M:SetAttribute("Label", "Infirmary")

local function part(Template: string, Name: string, Size: Vector3, Pos: Vector3): BasePart
	local P = R106[Template]:Clone()
	for _, K in P:GetChildren() do K:Destroy() end
	P.Name = Name
	P.Size = Size
	P.CFrame = CFrame.new(Pos)
	P.Parent = M
	return P
end

local Floor = part("Floor", "Floor", Vector3.new(26, 0.2, 26), Vector3.new(CX, 1.0, CZ))
Floor.BrickColor = BrickColor.new("Institutional white")
part("WallWest", "WallWest", Vector3.new(1, 12, 26), Vector3.new(X0, 6.9, CZ))
part("WallEast", "WallEast", Vector3.new(1, 12, 26), Vector3.new(X1, 6.9, CZ))
part("WallNorth", "WallSouth", Vector3.new(26, 12, 1), Vector3.new(CX, 6.9, Z0))
-- the north wall (onto the hallway) with the door gap
local LeftW = (DoorX - DoorW / 2) - X0
local RightW = X1 - (DoorX + DoorW / 2)
part("WallSouthL", "WallNorthL", Vector3.new(LeftW, 12, 1), Vector3.new(X0 + LeftW / 2, 6.9, Z1))
part("WallSouthR", "WallNorthR", Vector3.new(RightW, 12, 1), Vector3.new(X1 - RightW / 2, 6.9, Z1))
part("WallSouthTop", "WallNorthTop", Vector3.new(DoorW, 3, 1), Vector3.new(DoorX, 11.4, Z1))
local Door = R106.Door:Clone()
Door.CFrame = CFrame.new(DoorX, 4.9, Z1)
Door.Parent = M
-- the sign over the door, facing the hallway (R106's sign, relabelled)
local Sign = R106.Sign:Clone()
Sign.CFrame = CFrame.lookAt(Vector3.new(DoorX, 11.4, Z1 + 0.7), Vector3.new(DoorX, 11.4, Z1 + 10))
for _, D in Sign:GetDescendants() do
	if D:IsA("TextLabel") or D:IsA("TextBox") then D.Text = "Infirmary" end
end
Sign.Parent = M

local Zone = part("Zone", "Zone", Vector3.new(24, 12, 24), Vector3.new(CX, 6.9, CZ))
Zone:SetAttribute("RoomId", "Infirmary")

local function marker(Name: string, Pos: Vector3, Look: Vector3, Attrs: { [string]: any }?): BasePart
	local P = Instance.new("Part")
	P.Name = Name
	P.Size = Vector3.new(2, 1, 1)
	P.Anchored, P.CanCollide, P.CanQuery, P.CanTouch = true, false, false, false
	P.Transparency = 1
	P.CFrame = CFrame.lookAt(Pos, Pos + Look)
	for K, V in Attrs or {} do P:SetAttribute(K, V) end
	P.Parent = M
	return P
end
-- the Nurse stands by her cabinet facing the beds; posts sit half a stud over the floor like the other NpcPost parts
marker("NursePost", Vector3.new(219, 1.6, 21), Vector3.new(-1, 0, 0), { NpcPost = "Nurse" })
marker("NHInfirmarySpot1", Vector3.new(208.5, 1.6, 22), Vector3.new(-1, 0, 0), { Kind = "Stand" })
marker("NHInfirmarySpot2", Vector3.new(208.5, 1.6, 32), Vector3.new(-1, 0, 0), { Kind = "Stand" })

-- props (ServerStorage.NHProps)
local NP = game:GetService("ServerStorage"):FindFirstChild("NHProps")
local Props = Instance.new("Folder")
Props.Name = "Props"
Props.Parent = M
local Report = {}
local function prop(Name: string, Pos: Vector3, YawDeg: number, NewName: string?): Model?
	local Src = NP and NP:FindFirstChild(Name, true)
	if not Src then table.insert(Report, "missing prop " .. Name) return nil end
	local C = Src:Clone()
	C.Name = NewName or Name
	C:PivotTo(CFrame.new(Pos) * CFrame.Angles(0, math.rad(YawDeg), 0))
	C.Parent = Props
	return C
end
local Bed1 = prop("DormBed", Vector3.new(202.6, 1.1, 19), 0, "DormBed_Infirmary1")
local Bed2 = prop("DormBed", Vector3.new(202.6, 1.1, 31), 0, "DormBed_Infirmary2")
prop("GlassCabinetTall", Vector3.new(223.2, 1.1, 18), 90)
prop("FilingCabinet", Vector3.new(223.6, 1.1, 24), 90)
prop("TeacherChair", Vector3.new(221, 1.1, 30), 90)
-- the bed markers: where a patient lies (the mattress top, measured, else 2.1 studs)
for I, Bed in { Bed1, Bed2 } do
	if Bed then
		local Cf, Sz = Bed:GetBoundingBox()
		local RP = RaycastParams.new()
		RP.FilterType = Enum.RaycastFilterType.Include
		RP.FilterDescendantsInstances = { Bed }
		local Hit = workspace:Raycast(Cf.Position + Vector3.new(0, 10, 0), Vector3.new(0, -20, 0), RP)
		local Top = if Hit then Hit.Position.Y else 1.1 + 2.1
		marker("NHInfirmaryBed" .. I, Vector3.new(Cf.Position.X, Top, Cf.Position.Z), Vector3.new(0, 0, -1), { SeatHeight = Top - 1.1; Kind = "Bed" })
		table.insert(Report, string.format("bed %d top %.2f (%s)", I, Top, if Hit then "raycast" else "default"))
	end
end
M.Parent = School

-- the region box (Config.Regions.Defs.Infirmary), on the room itself
local Regions = workspace:FindFirstChild("Regions")
if Regions and not Regions:FindFirstChild("Infirmary") then
	local Tpl = Regions:FindFirstChild("R106", true)
	local B = if Tpl then Tpl:Clone() else Instance.new("Part")
	for _, K in B:GetChildren() do K:Destroy() end
	B.Name = "Infirmary"
	B.Size = Vector3.new(26, 14, 26)
	B.CFrame = CFrame.new(CX, 7.5, CZ)
	B.Anchored, B.CanCollide, B.CanQuery, B.CanTouch = true, false, false, false
	B:SetAttribute("RegionId", "Infirmary")
	B.Parent = Regions
	table.insert(Report, "region box added")
end
return "built " .. M:GetFullName() .. " · " .. table.concat(Report, " · ")
