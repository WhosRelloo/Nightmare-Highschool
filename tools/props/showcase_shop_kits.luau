--!nocheck
-- Lines up the interiors kit (batch 45) and the armory and spell shop kits (batch 46) in workspace.NHPropsShowcase like the
-- other kits: rows in front of dark slate backing walls, props facing south (+Z), from x -235, in the next slots south of
-- the Showpiece Paintings row (-790): "Interiors" at z -826, "Armory" at z -862, "Spell Shop" at z -898. They stand on
-- their own floor slab (ShowcaseFloorShops, in the Interiors folder) south of ShowcaseFloorSouth (which ends at z -797).
-- Wall pieces hang on the wall (their pivot is on their back face) with their bottoms at the docs' heights (0 for the
-- tall shelves that stand on the floor against a wall); the till, scales, bell and claw gauntlets sit on slate plinths.
-- Run again to rebuild.
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
		-- some wall-backed pieces have their pivot short of their back face: push them out to sit on the wall
		local bcf, bs = c:GetBoundingBox()
		local back = bcf.Position.Z - bs.Z / 2
		if back < face then c:PivotTo(c:GetPivot() + Vector3.new(0, 0, face - back)) end
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

-- batch 45 (names45.py order; WALL and PLINTH from the docs' showcase notes)
local INTERIORS = [[ShopCounterEnd ShopCounter ShopCounterCorner CashRegister ShopScales CounterBell WrapStand DisplayCase
GlassCabinetTall WallShelfStocked IslandShelf ApothecaryDrawers SweetJarShelf PostcardSpinner StockSacks StockCrates
BookshopCounter NewReleasesTable BookStandAngled BargainBinCart StaffPicksEasel CafeBarCounter BarStool CafeBackShelf
ShopStool HatUmbrellaStand OpenClosedSign PriceTagRail DoorBellBracket ShopSignInterior]]
local INT_WALL = { WallShelfStocked = 0, ApothecaryDrawers = 0, SweetJarShelf = 0, CafeBackShelf = 0, HatUmbrellaStand = 0,
	OpenClosedSign = 4.0, PriceTagRail = 2.0, DoorBellBracket = 7.0, ShopSignInterior = 3.0 }
local INT_PLINTH = { CashRegister = true, ShopScales = true, CounterBell = true }

-- batch 46
local ARMORY = [[ArmorySign KatanaStand PolearmRack PlateArmourStand MailHauberkStand ShieldWall Grindstone ArmoryCounter
ClawGauntletDisplay SilverDaggerCase HelmShelf BoltBarrel BeastPell CrossbowRack HuntersReliquary]]
local ARM_WALL = { ShieldWall = 1.6, HelmShelf = 2.2, CrossbowRack = 1.2, ArmorySign = 4.6, PolearmRack = 0, HuntersReliquary = 0 }
local ARM_PLINTH = { ClawGauntletDisplay = true }
local SPELL = [[SpellShopSign TetheredGrimoires PotionHoneycomb ScryingOrbStand WandCoffin RuneCircleRug RuneStoneTable
ScrollCarousel WaxfallAltar OrreryCounter StarChartBanner HangingCrystals FamiliarPerch OddmentsEtagere]]
local SPELL_WALL = { PotionHoneycomb = 1.2, StarChartBanner = 0.8, SpellShopSign = 4.8, WandCoffin = 0, WaxfallAltar = 0,
	OddmentsEtagere = 0 }

local out = {
	row("Interiors", -826, INTERIORS, INT_WALL, INT_PLINTH, 14),
	row("Armory", -862, ARMORY, ARM_WALL, ARM_PLINTH, 13),
	row("Spell Shop", -898, SPELL, SPELL_WALL, {}, 12),
}

-- the rune-stone table stands on its rug (rug top 0.09): move it onto the rug's centre
local S = SC:FindFirstChild("Spell Shop")
local rug, tab = S:FindFirstChild("RuneCircleRug_Showcase"), S:FindFirstChild("RuneStoneTable_Showcase")
if rug and tab then
	local rcf = rug:GetBoundingBox()
	local tcf, ts = tab:GetBoundingBox()
	local tp = tab:GetPivot()
	tab:PivotTo(tp + Vector3.new(rcf.Position.X - tcf.Position.X, FLOOR + 0.09 - (tcf.Position.Y - ts.Y / 2), rcf.Position.Z - tcf.Position.Z))
end

-- the floor south of ShowcaseFloorSouth (z -797), under all three rows
local I = SC:FindFirstChild("Interiors")
local north, south = -797, -905
part("ShowcaseFloorShops", Vector3.new(300, 2, north - south), CFrame.new(X0 - 10 + 150, FLOOR - 1, (north + south) / 2), I,
	Enum.Material.Plaster, Color3.new(0.357, 0.357, 0.357))
return table.concat(out, "\n")
