--!nocheck
-- Lines up the dorm kit (batch 34) and the lounge, school, detention, electives and dorm house kits (35-39) in
-- workspace.NHPropsShowcase like the other kits: one folder per kit, "<Name>_Showcase" clones standing in a row on
-- the baseplate (top y = 0.9), wall pieces hung on a dark slate backing wall behind the row, ceiling pieces on a
-- beam. Rows run along X in the free strip at the north end of the baseplate (z -694 .. -454). Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR = 0.9
local X0 = -236
local GAP = 2.5
local KITS = {
	{ "Dorm Room", "Dorm", -682 },
	{ "Teachers Lounge", "Lounge", -646 },
	{ "School Props", "School", -610 },
	{ "Detention", "Detention", -574 },
	{ "Electives", "Electives", -538 },
	{ "Dorm House", "DormHouse", -502 },
}
-- wall pieces: the bottom of their box this far above the floor (their pivot is on their back face)
local WALL = {
	MugRack = 4, StaffRotaBoard = 3, WallTelephone = 2.5, StaffOnlySign = 6, Dartboard = 3.5, SpecimenJars = 4, WallMap = 3,
	FireBucketRack = 3, DrinkingFountain = 0, LinesChalkboard = 2.5, SchoolRulesBoard = 3, WindowGrille = 2, KeyRingHook = 3.5,
	WallBell = 6, ToolWall = 2.5, TheatreMasks = 4, FairyLights = 4, DoorHoop = 3.5, Urinal = 0, UrinalDivider = 0, UrinalTrough = 0,
	CertificateHonourRoll = 4.5, CertificateDeansList = 4.5, CertificatePerfectAttendance = 4.5, TrophyShelf = 4, OverdueNotices = 4,
	RoomNumberPlate = 5, RoomNumberPlateBlank = 5, DormShelfFull = 4, DormShelfSparse = 4, DormShelfEmpty = 4,
}
local CEILING = { PotRack = true, DormCeilingLight = true } -- hung from a beam, their top at BEAM - 0.5
-- table-top things stand on a slate plinth like the other kits' (<Name>_ShowcasePlinth, top 3.4, the prop + 0.6)
local PLINTH = {}
for _, n in { "TeaUrn", "SpiritKettle", "TeaSet", "BiscuitBarrel", "MarkingStack", "Gradebook", "Abacus", "TestTubeRack",
	"Microscope", "WritingSlate", "InkwellSet", "Metronome", "LinesPaperStack", "MixingBowlSet", "MakeupSet", "JewelryBox",
	"PerfumeTray", "DormDeskLamp", "DormBookStack", "CoffeeCup" } do PLINTH[n] = true end
local PLINTH_TOP = 3.4
local BEAM = 10.5

local function wallPart(name, size, cf, parent, mat, col)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = mat or Enum.Material.Slate
	w.Color = col or Color3.new(0.227, 0.22, 0.227)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local report = {}
for _, k in KITS do
	local folderName, kitName, Zb = k[1], k[2], k[3]
	local old = SC:FindFirstChild(folderName)
	if old then old:Destroy() end
	local F = Instance.new("Folder") F.Name = folderName

	local names = {}
	for _, m in P:GetChildren() do
		if m:IsA("Model") and m:GetAttribute("NHBuildKit") == kitName then table.insert(names, m.Name) end
	end
	table.sort(names)
	-- floor pieces first, then plinths, wall pieces and ceiling pieces, so each kind shares one stretch
	table.sort(names, function(a, b)
		local ra = CEILING[a] and 3 or (WALL[a] and 2 or (PLINTH[a] and 1 or 0))
		local rb = CEILING[b] and 3 or (WALL[b] and 2 or (PLINTH[b] and 1 or 0))
		if ra ~= rb then return ra < rb end
		return a < b
	end)

	-- the wall is on the row's north side and the props face south (+Z), toward the rest of the map. Props are
	-- built facing -Z, so each is turned 180 degrees: a box offset (rx, ry, rz) from the pivot becomes (-rx, ry, -rz).
	local face = Zb + 0.5 -- the front (south) face of the backing wall
	local TURN = CFrame.Angles(0, math.pi, 0)
	local x = X0
	local beamFrom, beamTo
	for _, n in names do
		local c = P[n]:Clone()
		c:SetAttribute("NHBuildKit", nil)
		c.Name = n .. "_Showcase"
		local pv = c:GetPivot()
		local cf, s = c:GetBoundingBox()
		local rel = pv:PointToObjectSpace(cf.Position) -- the box centre from the pivot (templates are unrotated)
		local px = x + rel.X + s.X / 2                -- the turned box's left (west) edge sits at x
		local py, pz
		local width = s.X
		if PLINTH[n] then
			local side = math.max(s.X, s.Z) + 0.6
			local cx, cz = x + side / 2, face + 0.6 + side / 2
			px = cx + rel.X
			py = PLINTH_TOP - (rel.Y - s.Y / 2)
			pz = cz + rel.Z
			local pl = wallPart(n .. "_ShowcasePlinth", Vector3.new(side, PLINTH_TOP - FLOOR, side),
				CFrame.new(cx, FLOOR + (PLINTH_TOP - FLOOR) / 2, cz), F, Enum.Material.Slate, Color3.new(0.157, 0.141, 0.173))
			width = side
		elseif CEILING[n] then
			py = (BEAM - 0.5) - (rel.Y + s.Y / 2)
			pz = face + 3 + rel.Z
			beamFrom = beamFrom or x
			beamTo = x + s.X
		elseif WALL[n] then
			py = FLOOR + WALL[n] - (rel.Y - s.Y / 2)
			pz = face -- the back face on the wall
		else
			py = FLOOR - (rel.Y - s.Y / 2)
			pz = face + 0.6 + rel.Z + s.Z / 2 -- the turned box's back just in front of the wall
		end
		c:PivotTo(CFrame.new(px, py, pz) * TURN)
		for _, d in c:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
		c.Parent = F
		x += width + GAP
	end
	local len = x - X0 + 2
	wallPart(folderName:gsub(" ", "") .. "Wall", Vector3.new(len, 15, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + 7.5, Zb), F)
	if beamFrom then
		local bl = beamTo - beamFrom + 4
		local mat, col = Enum.Material.Metal, Color3.new(0.133, 0.122, 0.141)
		wallPart("CeilingBeam", Vector3.new(bl, 1, 1), CFrame.new(beamFrom - 2 + bl / 2, BEAM, face + 3), F, mat, col)
		wallPart("CeilingBeamPost0", Vector3.new(1, BEAM - FLOOR, 1), CFrame.new(beamFrom - 2.5, FLOOR + (BEAM - FLOOR) / 2, face + 3), F, mat, col)
		wallPart("CeilingBeamPost1", Vector3.new(1, BEAM - FLOOR, 1), CFrame.new(beamTo + 2.5, FLOOR + (BEAM - FLOOR) / 2, face + 3), F, mat, col)
	end
	F.Parent = SC
	table.insert(report, string.format("%s: %d props, %.0f studs (x %.0f..%.0f, wall z %.0f)", folderName, #names, len, X0, x, Zb))
end
return table.concat(report, "\n")
