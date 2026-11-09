--!nocheck
-- Lines up the garden kit (batch 40) in workspace.NHPropsShowcase like the other kits: one "Garden" folder, three rows
-- (paths, plants, features) of "<Name>_Showcase" clones on the baseplate (top y = 0.9), each row in front of a dark slate
-- backing wall on its north side with the props facing south (+Z). The rows sit east of the dorm/lounge/school rows in
-- the free strip at the north end of the baseplate (x 20 .. 376, z -694 .. -454), 40 apart because the willow, gazebo
-- and roundel are deep. Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR = 0.9
local X0 = 24
local XMAX = 376
local GAP = 2.5
local ROWS = { -- docs/School-Props.md order
	{ "Paths", -690, [[PathFlagstone PathFlagstoneCurve PathFlagstoneJunction PathFlagstoneCross PathCobble PathCobbleCurve PathGravel
		PathGravelCurve PathHerringbone PathCrazyPaving PathPuddleFlag PathMoonRoundel SteppingStones GardenSteps PathEdgingIron
		PathBridgeSlab PathGateArch]] },
	{ "Plants", -650, [[RoseBushCrimson RoseBushBlack HedgeStraight HedgeBattlement HedgeCorner HedgeEnd HedgeArchway HedgeWolf
		HedgeRaven WeepingWillow YewTree GnarledCrabapple CypressPair IvyWallPanel WisteriaPergola FernCluster LavenderBed
		RaisedFlowerBed MushroomRing MoonflowerPatch TallGrassClump ThornBramble NightshadeShrub PumpkinPatch PoppyBed LilyPads
		BloodRoseUrn GhostOrchid]] },
	{ "Features", -610, [[KoiPond BirdBath GardenBench CurvedStoneBench LogBench IronGazebo RoseArbor GardenObelisk UrnPedestal
		LowGardenWall GardenWallPier StoneLanternPost Wheelbarrow GardenToolsLean PottingCluster ColdFrame TrellisPanel
		KeepOffGrassSign Birdhouse Scarecrow CourtyardBenchTable CrowPerch]] },
}
local WALL = { IvyWallPanel = 0 } -- hung on the backing wall: the bottom of its box this far above the floor
local WALL_H = 22 -- taller than the other kits' 15: the cypresses and the gazebo reach 17-20

local function wallPart(name, size, cf, parent)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = Enum.Material.Slate
	w.Color = Color3.new(0.227, 0.22, 0.227)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local old = SC:FindFirstChild("Garden")
if old then old:Destroy() end
local F = Instance.new("Folder") F.Name = "Garden"
local TURN = CFrame.Angles(0, math.pi, 0) -- props are built facing -Z; turned to face south
local report, missing = {}, {}
for _, row in ROWS do
	local rowName, Zb, list = row[1], row[2], row[3]
	local face = Zb + 0.5
	local x, n, deepest = X0, 0, 0
	for name in list:gmatch("%S+") do
		local t = P:FindFirstChild(name)
		if not t then table.insert(missing, name) continue end
		local c = t:Clone()
		c:SetAttribute("NHBuildKit", nil)
		c.Name = name .. "_Showcase"
		local pv = c:GetPivot()
		local cf, s = c:GetBoundingBox()
		local rel = pv:PointToObjectSpace(cf.Position)
		local px = x + rel.X + s.X / 2
		local py, pz
		if WALL[name] then
			py = FLOOR + WALL[name] - (rel.Y - s.Y / 2)
			pz = face
		else
			py = FLOOR - (rel.Y - s.Y / 2)
			pz = face + 0.6 + rel.Z + s.Z / 2
		end
		c:PivotTo(CFrame.new(px, py, pz) * TURN)
		c.Parent = F
		x += s.X + GAP
		n += 1
		deepest = math.max(deepest, s.Z)
	end
	local len = x - X0 + 2
	wallPart("Garden" .. rowName .. "Wall", Vector3.new(len, WALL_H, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + WALL_H / 2, Zb), F)
	table.insert(report, string.format("%s: %d props, x %.0f..%.0f%s, wall z %.0f, deepest %.1f", rowName, n, X0, x,
		x > XMAX and " (PAST THE STRIP)" or "", Zb, deepest))
end
F.Parent = SC
return table.concat(report, "\n") .. (#missing > 0 and ("\nno template: " .. table.concat(missing, ",")) or "")
