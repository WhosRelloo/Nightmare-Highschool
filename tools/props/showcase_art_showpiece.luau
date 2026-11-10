--!nocheck
-- Lines up the art kit (batch 41) and the showpiece kit (batch 44) in workspace.NHPropsShowcase like the other kits: rows in
-- front of dark slate backing walls, props facing south (+Z), from x -235, in the next slots south of the Dorm Room row
-- (-682): "Art" at z -718, "Showpiece Statues" at z -760 (the statues are up to 14 deep), "Showpiece Paintings" at z -790.
-- The baseplate ends at z -694, so the rows stand on their own floor slab (ShowcaseFloorSouth, in the Art folder).
-- Wall pieces hang on the wall (their pivot is on their back face) with their bottoms at the docs' heights; busts and the
-- icon triptych sit on slate plinths. Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR, X0, GAP = 0.9, -235, 2.5
local PLINTH_TOP = 3.4
local TURN = CFrame.Angles(0, math.pi, 0)

local function part(name, size, cf, parent, mat, col)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = mat or Enum.Material.Slate
	w.Color = col or Color3.new(0.224, 0.22, 0.224)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local function row(folderName, ZB, order, WALL, PLINTH, wallH)
	local old = SC:FindFirstChild(folderName)
	if old then old:Destroy() end
	local F = Instance.new("Folder") F.Name = folderName
	local face = ZB + 0.5
	local x, n, missing, deepest = X0, 0, {}, 0
	for name in order:gmatch("%S+") do
		local t = P:FindFirstChild(name)
		if not t then table.insert(missing, name) continue end
		local c = t:Clone()
		c:SetAttribute("NHBuildKit", nil)
		c.Name = name .. "_Showcase"
		local pv = c:GetPivot()
		local cf, s = c:GetBoundingBox()
		local rel = pv:PointToObjectSpace(cf.Position)
		local px = x + rel.X + s.X / 2
		local py, pz, width = nil, nil, s.X
		if PLINTH[name] then
			local side = math.max(s.X, s.Z) + 0.6
			local cx, cz = x + side / 2, face + 0.6 + side / 2
			px, py, pz = cx + rel.X, PLINTH_TOP - (rel.Y - s.Y / 2), cz + rel.Z
			part(name .. "_ShowcasePlinth", Vector3.new(side, PLINTH_TOP - FLOOR, side), CFrame.new(cx, FLOOR + (PLINTH_TOP - FLOOR) / 2, cz),
				F, Enum.Material.Slate, Color3.new(0.157, 0.141, 0.173))
			width = side
		elseif WALL[name] then
			py, pz = FLOOR + WALL[name] - (rel.Y - s.Y / 2), face
		else
			py, pz = FLOOR - (rel.Y - s.Y / 2), face + 0.6 + rel.Z + s.Z / 2
		end
		c:PivotTo(CFrame.new(px, py, pz) * TURN)
		c.Parent = F
		x += width + GAP
		n += 1
		deepest = math.max(deepest, s.Z)
	end
	local len = x - X0 + 2
	part(folderName:gsub(" ", "") .. "Wall", Vector3.new(len, wallH, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + wallH / 2, ZB), F)
	F.Parent = SC
	return string.format("%s: %d props, x %.0f..%.0f, wall z %d, deepest %.1f%s", folderName, n, X0, x, ZB, deepest,
		#missing > 0 and ("; no template: " .. table.concat(missing, ",")) or "")
end

-- batch 41 (names41.py: PAINT, CLOTH, SCULPT, GALLERY; WALL and PLINTH from the docs)
local ART = [[PortraitHeadmasterGallery PortraitHeadmistress PortraitCursedStudent PortraitCountessOval PaintingVampireBall
PaintingWolfHuntSnow TondoMoonCloister PaintingAcademyPanorama PaintingClassOf1887 CliqueHeraldry PortraitMiniatures
TapestryCliques TapestryProcession BannerPack BannerChoir BannerInk GonfalonStand BustHeadmistress BustVampireCount
BustVeiledStudent StatueChoirChild StatueInkScribe StatueCourtDuchess SculptureClaspedHands ReliefFounding ReliefDanseMacabre
PlaqueMemorial EaselCovered StainedGlassRoundel MosaicRaven IconTriptych DeathMaskCase]]
local ART_WALL = { PortraitHeadmasterGallery = 1.0, PortraitHeadmistress = 4.0, PortraitCursedStudent = 4.0, PortraitCountessOval = 4.0,
	PaintingVampireBall = 3.5, PaintingWolfHuntSnow = 3.0, TondoMoonCloister = 4.0, PaintingAcademyPanorama = 5.5,
	PaintingClassOf1887 = 4.0, CliqueHeraldry = 4.0, PortraitMiniatures = 4.0, TapestryCliques = 1.5, TapestryProcession = 2.5,
	BannerPack = 3.0, BannerChoir = 2.5, BannerInk = 3.0, ReliefFounding = 3.0, ReliefDanseMacabre = 5.0, PlaqueMemorial = 4.5,
	StainedGlassRoundel = 4.5, MosaicRaven = 3.0 }
local ART_PLINTH = { BustHeadmistress = true, BustVampireCount = true, BustVeiledStudent = true, IconTriptych = true }

-- batch 44 (names44.py: STATUES + the two set-pieces; PAINT + the mural)
local STATUES = [[VampireLordRising WerewolfTurning VigilCaptainLantern ChoirConductor InkScribeTendrils DelinquentGlare
AthleteSpinKick CourtDuchessThrone ReaperGuard PackAlphaLanding FounderRavens ExorcistSigil GhoulUppercut CourtIaiDraw
TwinRivalsDuel BackToBackStandoff]]
local PAINTINGS = [[PaintingBellTowerStorm PaintingFloodedCrypt PaintingBurningLibrary PaintingMoonlitRooftop PaintingChoirLoft
PaintingDormCorridor PaintingFrozenLake PaintingHeadmasterStudy PaintingGymMidnight PaintingInkArchive MuralBloodMoonCourtyard]]
local PAINT_WALL = {}
for n in PAINTINGS:gmatch("%S+") do PAINT_WALL[n] = 2.5 end
PAINT_WALL.MuralBloodMoonCourtyard = 1.5

local out = {
	row("Art", -718, ART, ART_WALL, ART_PLINTH, 15),
	row("Showpiece Statues", -760, STATUES, {}, {}, 18),
	row("Showpiece Paintings", -790, PAINTINGS, PAINT_WALL, {}, 17),
}
-- the floor south of the baseplate's edge (z -694), under all three rows
local A = SC:FindFirstChild("Art")
local edge, south = -694, -797
part("ShowcaseFloorSouth", Vector3.new(300, 2, edge - south), CFrame.new(X0 - 10 + 150, FLOOR - 1, (edge + south) / 2), A,
	Enum.Material.Plaster, Color3.new(0.357, 0.357, 0.357))
return table.concat(out, "\n")
