-- phase6-infirmary: dresses workspace.School.Infirmary (built by tools/phase6-strafes/build/infirmary.luau) in NH Combat
-- Test, Edit mode. Re-runnable: everything it adds lives in Infirmary.Dressing and Infirmary.Props.Dress_*, both rebuilt.
-- Room: x 199-225, z 13.5-39.5 (wall centres), floor top y 1.1, walls to y 12.9; door in the north wall at x 215-219.
-- Beds along the west wall (x 202.6, z 19 and z 31, heads to +z). The Nurse's side is the east wall.
-- Gothic house style: dark oak wainscot, dado and cornice; a coffered plaster ceiling on oak beams; iron curtain rails with
-- bone-linen bed curtains; apothecary drawers, a jar shelf and the first-aid case for the medicine wall.
if game.PlaceId ~= 98950102230473 then return "REFUSED: not NH Combat Test (" .. game.PlaceId .. ")" end
local Room = workspace.School:FindFirstChild("Infirmary")
if not Room then return "FAIL no School.Infirmary (run the phase6-strafes builder first)" end
local Props = Room:FindFirstChild("Props")
local NP = game:GetService("ServerStorage"):FindFirstChild("NHProps")
if not (Props and NP) then return "FAIL no Props / NHProps" end

local Old = Room:FindFirstChild("Dressing")
if Old then Old:Destroy() end
for _, P in Props:GetChildren() do if P.Name:match("^Dress_") then P:Destroy() end end

local D = Instance.new("Folder")
D.Name = "Dressing"
local Report = {}

local X0, X1, Z0, Z1 = 199.5, 224.5, 14, 39 -- inner wall faces
local FLOOR, TOP = 1.1, 12.9
local OAK = Color3.fromRGB(58, 38, 28)
local OAK_DARK = Color3.fromRGB(40, 26, 20)
local IRON = Color3.fromRGB(34, 32, 34)
local LINEN = Color3.fromRGB(206, 196, 176)
local PLASTER = Color3.fromRGB(196, 190, 178)

local function part(Name: string, Size: Vector3, CF: CFrame, Color: Color3, Mat: Enum.Material, Parent: Instance?): Part
	local P = Instance.new("Part")
	P.Name = Name
	P.Size = Size
	P.CFrame = CF
	P.Color = Color
	P.Material = Mat
	P.Anchored = true
	P.CanCollide, P.CanTouch = false, false
	P.CastShadow = true
	P.TopSurface, P.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	P.Parent = Parent or D
	return P
end

---| walls: wainscot, dado rail, cornice (skipping the door gap) |---
local Trim = Instance.new("Folder") Trim.Name = "Trim" Trim.Parent = D
local Runs = { -- { from, to } along each wall: the north wall stops at the door (x 215-219)
	{ "W", Vector3.new(X0, 0, Z0), Vector3.new(X0, 0, Z1) },
	{ "E", Vector3.new(X1, 0, Z0), Vector3.new(X1, 0, Z1) },
	{ "S", Vector3.new(X0, 0, Z0), Vector3.new(X1, 0, Z0) },
	{ "NL", Vector3.new(X0, 0, Z1), Vector3.new(215, 0, Z1) },
	{ "NR", Vector3.new(219, 0, Z1), Vector3.new(X1, 0, Z1) },
}
local function inward(Name: string): Vector3
	return if Name == "W" then Vector3.new(1, 0, 0) elseif Name == "E" then Vector3.new(-1, 0, 0)
		elseif Name == "S" then Vector3.new(0, 0, 1) else Vector3.new(0, 0, -1)
end
for _, R in Runs do
	local Name, A, B = R[1], R[2], R[3]
	local Len = (B - A).Magnitude
	local Mid = (A + B) / 2
	local In = inward(Name)
	local Along = (B - A).Unit
	local function band(Label: string, H: number, Y: number, T: number, Color: Color3, Mat: Enum.Material)
		local C = Mid + In * (T / 2)
		local CF = CFrame.fromMatrix(Vector3.new(C.X, Y, C.Z), Along, Vector3.yAxis)
		part(Label .. Name, Vector3.new(Len, H, T), CF, Color, Mat, Trim)
	end
	band("Wainscot", 3.6, FLOOR + 1.8, 0.16, OAK, Enum.Material.Wood)
	band("Skirting", 0.5, FLOOR + 0.25, 0.26, OAK_DARK, Enum.Material.Wood)
	band("DadoRail", 0.22, FLOOR + 3.7, 0.3, OAK_DARK, Enum.Material.Wood)
	band("Cornice", 0.6, TOP - 0.3, 0.42, OAK_DARK, Enum.Material.Wood)
	band("CorniceBead", 0.16, TOP - 0.72, 0.28, OAK, Enum.Material.Wood)
	-- raised panels on the wainscot, every ~2.6 studs
	local N = math.max(1, math.floor(Len / 2.6))
	local Step = Len / N
	for I = 1, N do
		local At = A + Along * (Step * (I - 0.5)) + In * 0.2
		local CF = CFrame.fromMatrix(Vector3.new(At.X, FLOOR + 1.95, At.Z), Along, Vector3.yAxis)
		part("Panel" .. Name, Vector3.new(Step - 0.6, 2.5, 0.08), CF, OAK_DARK, Enum.Material.Wood, Trim)
	end
end
-- the door casing (inside face)
for _, X in { 214.75, 219.25 } do
	part("DoorCasing", Vector3.new(0.5, 8.8, 0.3), CFrame.new(X, FLOOR + 4.4, Z1 - 0.15), OAK_DARK, Enum.Material.Wood, Trim)
end
part("DoorHead", Vector3.new(5, 0.6, 0.3), CFrame.new(217, FLOOR + 8.95, Z1 - 0.15), OAK_DARK, Enum.Material.Wood, Trim)

---| the ceiling: plaster on oak beams, coffered |---
local Ceil = Instance.new("Folder") Ceil.Name = "Ceiling" Ceil.Parent = D
local Slab = part("CeilingSlab", Vector3.new(26, 0.4, 26), CFrame.new(212, TOP + 0.2, 26.5), PLASTER, Enum.Material.Plaster, Ceil)
Slab.CanCollide = true
for _, Z in { 20.25, 26.5, 32.75 } do
	part("BeamX", Vector3.new(25, 0.9, 0.8), CFrame.new(212, TOP - 0.45, Z), OAK_DARK, Enum.Material.Wood, Ceil)
end
for _, X in { 205.75, 212, 218.25 } do
	part("BeamZ", Vector3.new(0.6, 0.6, 25), CFrame.new(X, TOP - 0.3, 26.5), OAK, Enum.Material.Wood, Ceil)
end

---| bed curtains: iron rails hung from the beams, bone linen gathered open at the ends |---
local Curt = Instance.new("Folder") Curt.Name = "Curtains" Curt.Parent = D
local RAIL_Y = 10.6
local function rail(A: Vector3, B: Vector3)
	local Len = (B - A).Magnitude
	part("Rail", Vector3.new(0.14, 0.14, Len), CFrame.lookAt((A + B) / 2, B), IRON, Enum.Material.Metal, Curt)
	for _, P in { A, B } do -- drop rods to the ceiling
		part("RailRod", Vector3.new(0.08, TOP - RAIL_Y, 0.08), CFrame.new(P.X, (TOP + RAIL_Y) / 2, P.Z), IRON, Enum.Material.Metal, Curt)
		part("RailFinial", Vector3.new(0.3, 0.3, 0.3), CFrame.new(P), Color3.fromRGB(150, 118, 60), Enum.Material.Metal, Curt)
	end
end
-- a gathered curtain from A to B (pleats alternate in and out so it reads as cloth)
local function curtain(A: Vector3, B: Vector3, Normal: Vector3)
	local Len = (B - A).Magnitude
	local Along = (B - A).Unit
	local N = math.max(2, math.floor(Len / 0.45))
	local W = Len / N
	local Drop = RAIL_Y - 0.15 - (FLOOR + 0.6)
	for I = 1, N do
		local C = A + Along * (W * (I - 0.5)) + Normal * (if I % 2 == 0 then 0.05 else -0.05)
		local CF = CFrame.fromMatrix(Vector3.new(C.X, RAIL_Y - 0.15 - Drop / 2, C.Z), Along, Vector3.yAxis)
		part("Pleat", Vector3.new(W * 1.9, Drop, 0.1), CF, if I % 2 == 0 then LINEN else LINEN:Lerp(Color3.new(0, 0, 0), 0.12), Enum.Material.Plastic, Curt)
	end
	for _, P in { A, B } do -- rings
		part("Ring", Vector3.new(0.2, 0.2, 0.2), CFrame.new(P.X, RAIL_Y, P.Z), Color3.fromRGB(150, 118, 60), Enum.Material.Metal, Curt)
	end
end
local RX = 207.2 -- the open side of the beds (beds span x 200.5-204.7)
for _, Bed in { { 14.3, 24.6 }, { 26.4, 38.7 } } do
	local ZA, ZB = Bed[1], Bed[2]
	rail(Vector3.new(RX, RAIL_Y, ZA), Vector3.new(RX, RAIL_Y, ZB))
	-- drawn back: a short bunch at each end, the middle open
	curtain(Vector3.new(RX, RAIL_Y, ZA), Vector3.new(RX, RAIL_Y, ZA + 2.2), Vector3.new(1, 0, 0))
	curtain(Vector3.new(RX, RAIL_Y, ZB - 2.2), Vector3.new(RX, RAIL_Y, ZB), Vector3.new(1, 0, 0))
end
-- the divider between the beds, drawn closed
rail(Vector3.new(X0 + 0.2, RAIL_Y, 25.5), Vector3.new(RX, RAIL_Y, 25.5))
curtain(Vector3.new(X0 + 0.3, RAIL_Y, 25.5), Vector3.new(RX - 0.4, RAIL_Y, 25.5), Vector3.new(0, 0, 1))

---| props from ServerStorage.NHProps |---
local function prop(Name: string, Pos: Vector3, YawDeg: number, Label: string?): Model?
	local Src = NP:FindFirstChild(Name)
	if not Src then table.insert(Report, "missing prop " .. Name) return nil end
	local C = Src:Clone()
	C.Name = "Dress_" .. (Label or Name)
	C:PivotTo(CFrame.new(Pos) * CFrame.Angles(0, math.rad(YawDeg), 0))
	C.Parent = Props
	return C
end
-- yaw: 0 faces -z (north wall props, facing into the room), 180 faces +z (south wall), 90 faces -x (east wall), -90 faces +x (west wall)
-- the medicine wall (east, behind the Nurse's desk) and the south wall
prop("ApothecaryDrawers", Vector3.new(X1 - 0.85, FLOOR, 34.4), 90)
prop("TeacherDesk", Vector3.new(218.4, FLOOR, 30), 90, "NurseDesk")
prop("WitchJarShelf", Vector3.new(213.2, FLOOR + 3.2, Z0 + 0.65), 180, "MedicineShelf")
prop("FirstAidStation", Vector3.new(218.4, FLOOR + 1.6, Z0 + 0.5), 180)
prop("Sink", Vector3.new(208.2, FLOOR, Z0 + 0.95), 180)
prop("BathroomMirror", Vector3.new(208.2, FLOOR + 5.4, Z0 + 0.25), 180)
prop("TowelRail", Vector3.new(210.4, FLOOR + 3.9, Z0 + 0.25), 180)
-- on the desk (top at FLOOR + 3.01): a lamp, the hourglass, a microscope, jars and tubes
local DeskTop = FLOOR + 3.01
prop("DeskLamp", Vector3.new(218.2, DeskTop, 27.6), 90)
prop("Microscope", Vector3.new(218.4, DeskTop, 32.2), 120)
prop("Hourglass", Vector3.new(217.9, DeskTop, 29.2), 0)
prop("TestTubeRack", Vector3.new(219.0, DeskTop, 30.6), 90)
prop("SpecimenJars", Vector3.new(218.9, DeskTop, 28.4), 90)
-- by the beds: a nightstand with a candle lamp at bed 1's head, a nightstand with an oil lamp at bed 2's head
prop("Nightstand", Vector3.new(205.7, FLOOR, 24.1), -90, "Nightstand1")
prop("CandleLamp", Vector3.new(205.7, FLOOR + 2.92, 24.1), -90, "BedLamp1")
prop("Nightstand", Vector3.new(200.5, FLOOR, 37.6), -90)
prop("OilLamp", Vector3.new(200.5, FLOOR + 2.92, 37.6), -90)
prop("StepStool", Vector3.new(206.0, FLOOR, 34.4), -90)
-- the rest of the room
prop("CarpetDamask", Vector3.new(212.6, FLOOR, 26.5), 0)
prop("AnatomySkeleton", Vector3.new(222.6, FLOOR, 37.6), 200)
prop("PottedPlant", Vector3.new(212.0, FLOOR, 37.6), 0)
prop("Radiator", Vector3.new(209.0, FLOOR, Z1 - 0.4), 0)
prop("WallClock", Vector3.new(217, FLOOR + 9.0, Z1 - 0.25), 0)
prop("PortraitHeadmistress", Vector3.new(205.2, FLOOR + 4.2, Z1 - 0.3), 0)
prop("SchoolRulesBoard", Vector3.new(X1 - 0.1, FLOOR + 4.6, 26.0), 90, "InfirmaryRules")
prop("WallSconce", Vector3.new(X0 + 0.3, FLOOR + 7.0, 25.5), -90, "SconceW")
prop("WallSconce", Vector3.new(X1 - 0.3, FLOOR + 7.0, 21.2), 90, "SconceE")
prop("WallSconce", Vector3.new(214.0, FLOOR + 7.0, Z0 + 0.3), 180, "SconceS")
-- two pendant lamps over the aisle, hanging from the middle beam line
prop("PendantLamp", Vector3.new(212, TOP - 0.9 - 4.07, 20.25), 0, "PendantN")
prop("PendantLamp", Vector3.new(212, TOP - 0.9 - 4.07, 32.75), 0, "PendantS")

-- light: the ceiling closes the room, so the pendants and sconces carry real lights (warm, gas-lamp)
local function light(Where: Instance?, Range: number, Bright: number)
	if not Where then return end
	local Bulb = nil
	for _, P in Where:GetDescendants() do
		if P:IsA("BasePart") and (P.Name:find("Glow") or P.Name:find("Shade") or P.Name:find("Globe") or P.Name:find("Bulb")) then Bulb = P break end
	end
	Bulb = Bulb or Where:FindFirstChildWhichIsA("BasePart", true)
	if Bulb and not Bulb:FindFirstChildWhichIsA("Light") then
		local L = Instance.new("PointLight")
		L.Color = Color3.fromRGB(255, 206, 150)
		L.Range, L.Brightness, L.Shadows = Range, Bright, true
		L.Parent = Bulb
	end
end
light(Props:FindFirstChild("Dress_PendantN"), 22, 1.4)
light(Props:FindFirstChild("Dress_PendantS"), 22, 1.4)
light(Props:FindFirstChild("Dress_SconceW"), 12, 0.9)
light(Props:FindFirstChild("Dress_SconceE"), 12, 0.9)
light(Props:FindFirstChild("Dress_SconceS"), 12, 0.9)
light(Props:FindFirstChild("Dress_OilLamp"), 8, 0.7)

-- nothing in the dressing blocks queries or touches; the curtains and trim never collide (patients walk through the
-- open curtain gap, and nav ignores non-colliding parts)
for _, P in D:GetDescendants() do
	if P:IsA("BasePart") and P.Name ~= "CeilingSlab" then P.CanCollide, P.CanQuery = false, false end
end
D.Parent = Room
local N = 0
for _, P in Props:GetChildren() do if P.Name:match("^Dress_") then N += 1 end end
return string.format("dressed: %d parts, %d props · %s", #D:GetDescendants(), N, table.concat(Report, " · "))
