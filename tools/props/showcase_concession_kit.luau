--!nocheck
-- Props batch 54: stages the concession kit in NH Combat Test, at the batch-14 stand (workspace.NHPropsShowcase.
-- ConcessionStand_Showcase, front facing -Z). Run after tools/props/concession_kit_templates.luau. Safe to run again (it
-- rebuilds workspace.NHPropsShowcase.Concessions).
--   Stand      a few items stocked on the glass counter's free middle, the floor stock (bottle crate, can tray, bento stack)
--              beside the stand's east post, a little litter in front.
--   Catalogue  every item on low iron-and-slate display tables on the open floor in front of the stand (snacks east, the
--              lunch trays west), fronts toward -Z, in sheet order, so the builder can pick any of them.
-- Everything is a clone of ServerStorage.NHProps.ConcessionItems.<Id> (tag NHConcessionItem, attribute ItemId).
local CS = game:GetService("CollectionService")
local Items = game:GetService("ServerStorage").NHProps.ConcessionItems
local Show = workspace:FindFirstChild("NHPropsShowcase")
assert(Show, "no workspace.NHPropsShowcase")
local old = Show:FindFirstChild("Concessions")
if old then old:Destroy() end
local F = Instance.new("Folder")
F.Name = "Concessions"
CS:AddTag(F, "NHPropBatch54")

local FLOOR = 0.9            -- the baseplate's top here
local COUNTER = 4.45         -- the stand's glass counter top
local placed, missing = 0, {}

local function put(id, x, y, z, yaw, parent)
	local t = Items:FindFirstChild(id)
	if not t then table.insert(missing, id) return nil end
	local m = t:Clone()
	m:PivotTo(CFrame.new(x, y, z) * CFrame.Angles(0, math.rad(yaw or 0), 0))
	m.Parent = parent or F
	placed += 1
	return m
end

local function width(id)
	local t = Items:FindFirstChild(id)
	if not t then return 0.6 end
	local _, s = t:GetBoundingBox()
	return s.X
end

local SLATE = Color3.fromRGB(38, 40, 44)
local IRON = Color3.fromRGB(28, 26, 30)
local function part(parent, name, size, cf, color, mat)
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.Size = size
	p.CFrame = cf
	p.Color = color
	p.Material = mat
	p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end

-- a display table: slate top 'depth' deep, iron legs, its top at FLOOR + 2.6; returns the top's height
local function table_(name, x0, x1, z, depth)
	local M = Instance.new("Model")
	M.Name = name
	local H = 2.6
	local cx = (x0 + x1) / 2
	part(M, "Top", Vector3.new(x1 - x0, 0.16, depth), CFrame.new(cx, FLOOR + H - 0.08, z), SLATE, Enum.Material.Slate)
	part(M, "Apron", Vector3.new(x1 - x0 - 0.2, 0.3, depth - 0.2), CFrame.new(cx, FLOOR + H - 0.31, z), IRON, Enum.Material.Metal)
	for _, sx in { x0 + 0.2, x1 - 0.2 } do
		for _, sz in { z - depth / 2 + 0.2, z + depth / 2 - 0.2 } do
			part(M, "Leg", Vector3.new(0.18, H - 0.16, 0.18), CFrame.new(sx, FLOOR + (H - 0.16) / 2, sz), IRON, Enum.Material.Metal)
		end
	end
	CS:AddTag(M, "NHPropBatch54")
	M.Parent = F
	return FLOOR + H, M
end

-- a row of items along X starting at x0, `gap` apart, standing on y at z
local function row(ids, x0, y, z, gap, parent)
	local x = x0
	for _, id in ids do
		local w = width(id)
		put(id, x + w / 2, y, z, 0, parent)
		x += w + gap
	end
	return x
end

-- the stand ---------------------------------------------------------------------------------------------------------------
local Stand = Instance.new("Folder")
Stand.Name = "Stand"
Stand.Parent = F
-- the glass counter's free middle (between the cake dome / pencil cup and the candy jars), back row then front row
row({ "CupStack", "Ramune", "BlackCatCola", "GreenTea", "StrawHolder" }, 202.05, COUNTER, 217.15, 0.08, Stand)
row({ "GraveCrisps", "Onigiri", "MelonBread" }, 202.1, COUNTER, 216.05, 0.1, Stand)
-- floor stock by the east post, and some litter out front
put("BottleCrate", 208.75, FLOOR, 215.0, -90, Stand)
put("CanTray", 208.75, FLOOR, 216.6, -90, Stand)
put("BentoStack", 208.7, FLOOR, 218.0, -90, Stand)
put("LitterChipBag", 199.2, FLOOR, 212.4, 25, Stand)
put("LitterCan", 200.4, FLOOR, 212.0, -40, Stand)
put("LitterWrappers", 205.6, FLOOR, 212.3, 10, Stand)

-- the catalogue ----------------------------------------------------------------------------------------------------------
local Cat = Instance.new("Folder")
Cat.Name = "Catalogue"
Cat.Parent = F
local ROWS = {
	{ z = 197.5, ids = { "Onigiri", "MelonBread", "YakisobaBun", "GarlicBread", "CurryBread", "Nikuman", "Taiyaki", "CreamPuff",
		"Bento", "MeatLoaf", "TakoyakiBoat", "CupRamen", "RoastSweetPotato", "YakitoriSkewers", "PumpkinSoup" } },
	{ z = 201.0, ids = { "Ramune", "BarleyTea", "CannedCoffee", "RedLantern", "HolyLemonade", "BlackCatCola", "GreenTea", "StrawberryMilk",
		"HotCocoa", "MelonSoda", "PuddingCup", "EctoJelly", "MoonCake", "Dango", "TombstoneCookie" } },
	{ z = 204.5, ids = { "BatGummies", "CandyApple", "GhostMints", "KonpeitoStars", "LicoriceWhips", "ChocolateBar", "Senbei", "GraveCrisps",
		"Popcorn", "PrankKit", "FruitCup", "SideSalad", "RiceBowl", "MisoSoup", "ChocolateMilk" } },
	{ z = 208.0, ids = { "CupStack", "LidStack", "StrawHolder", "NapkinDispenser", "BoatStack", "SkewerCup", "SoyBottle", "MustardBottle",
		"LitterFilm", "LitterChipBag", "LitterWrappers", "LitterCan", "JarGummies", "JarKonpeito", "JarMints" } },
}
for i, r in ROWS do
	local len = 0
	for _, id in r.ids do len += width(id) + 0.25 end
	local x0 = 206.0
	local top = table_("SnackTable" .. i, x0 - 0.3, x0 + len + 0.1, r.z, 1.6)
	row(r.ids, x0, top, r.z, 0.25, Cat)
end
-- the lunch trays, on two long tables west of the crate pile
local LUNCH = { { z = 198.5, ids = { "KatsuCurry", "ShoyuRamen", "KaraageSet", "MackerelSet", "Omurice" } },
	{ z = 202.5, ids = { "WitchingStew", "ShepherdsPie", "PumpkinGratin", "RavensRoast", "BunTray" } } }
for i, r in LUNCH do
	local len = 0
	for _, id in r.ids do len += width(id) + 0.3 end
	local x1 = 197.4
	local top = table_("LunchTable" .. i, x1 - len - 0.2, x1 + 0.2, r.z, 1.6)
	row(r.ids, x1 - len, top, r.z, 0.3, Cat)
end
-- the bigger stock stands on the floor behind the lunch tables
put("BottleCrate", 192.0, FLOOR, 206.5, 0, Cat)
put("CanTray", 194.0, FLOOR, 206.5, 0, Cat)
put("BentoStack", 196.0, FLOOR, 206.5, 0, Cat)

F.Parent = Show
return string.format("placed %d; missing: %s", placed, table.concat(missing, ","))
