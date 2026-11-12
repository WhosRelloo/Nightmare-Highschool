--!nocheck
-- Props batch 54 (the concession consumables kit, NHBuildKit "Concession"): turns the ten imported FBX sheets in Workspace into
-- templates. PK is replaced before running with "Sheet:color,normal,rough,metal;..." (asset ids in base 36) from the group's
-- images. Safe to run again.
--   ServerStorage.NHProps.Concession.<Sheet>    the sheet as imported (scaled to studs), each piece with its sheet's maps
--   ServerStorage.NHProps.ConcessionItems.<Id>  one Model per item (its piece, plus its see-through _Glass piece), pivot at the
--                                               bottom centre, tag NHConcessionItem, attributes ItemId, Sold, Lunch, Sheet
--   ReplicatedStorage.NHSnacks.<Id>             the hand prop of every item Config.Items sells: a Model holding `Handle` (the
--                                               piece; any glass welded under it) with an NHGrip CFrame attribute, which
--                                               Services.Features.Inventory and Controllers.Gui.Locker use in place of the
--                                               generated part (patched by tools/props/concession_kit_code.luau)
-- Pieces: <Sheet>_<Id> takes the sheet's four maps; <Sheet>_<Id>_Glass is Glass (Transparency 0.5, no maps, no shadow).
-- Nothing collides except the floor stock (crate, can tray, bento stack, bun tray: box collision).
local PK = [==[PK]==]

local CS = game:GetService("CollectionService")
local RS = game:GetService("ReplicatedStorage")
local SS = game:GetService("ServerStorage")
local P = SS:FindFirstChild("NHProps") or Instance.new("Folder")
P.Name = "NHProps"
P.Parent = SS

local IDS = {}
for entry in PK:gmatch("[^;]+") do
	local name, rest = entry:match("^([^:]+):(.*)$")
	local t, i = {}, 0
	for v in (rest .. ","):gmatch("([^,]*),") do
		i += 1
		t[i] = v ~= "" and tonumber(v, 36) or nil
	end
	IDS[name] = t
end

local SHEETS = {
	ConcessionBakery = "Onigiri MelonBread YakisobaBun GarlicBread CurryBread Nikuman Taiyaki CreamPuff",
	ConcessionHotFood = "Bento MeatLoaf TakoyakiBoat CupRamen RoastSweetPotato YakitoriSkewers PumpkinSoup",
	ConcessionDrinks = "Ramune BarleyTea CannedCoffee RedLantern HolyLemonade BlackCatCola GreenTea StrawberryMilk",
	ConcessionSweets = "HotCocoa MelonSoda PuddingCup EctoJelly MoonCake Dango TombstoneCookie",
	ConcessionCandy = "BatGummies CandyApple GhostMints KonpeitoStars LicoriceWhips ChocolateBar Senbei GraveCrisps Popcorn PrankKit",
	ConcessionLunchSets = "KatsuCurry ShoyuRamen KaraageSet MackerelSet Omurice",
	ConcessionLunchHouse = "WitchingStew ShepherdsPie PumpkinGratin RavensRoast",
	ConcessionLunchExtras = "FruitCup SideSalad RiceBowl MisoSoup ChocolateMilk",
	ConcessionCounterware = "CupStack LidStack StrawHolder NapkinDispenser BoatStack SkewerCup SoyBottle MustardBottle LitterFilm LitterChipBag LitterWrappers LitterCan",
	ConcessionStock = "JarGummies JarKonpeito JarMints BottleCrate CanTray BentoStack BunTray",
}
local ORDER = { "ConcessionBakery", "ConcessionHotFood", "ConcessionDrinks", "ConcessionSweets", "ConcessionCandy", "ConcessionLunchSets",
	"ConcessionLunchHouse", "ConcessionLunchExtras", "ConcessionCounterware", "ConcessionStock" }
local DRESSING = { ConcessionCounterware = true, ConcessionStock = true }
local LUNCH = { ConcessionLunchSets = true, ConcessionLunchHouse = true, ConcessionLunchExtras = true }
local COLLIDE = { BottleCrate = true, CanTray = true, BentoStack = true, BunTray = true }
local GLASS_TINT = { Ramune = Color3.fromRGB(150, 210, 214), GreenTea = Color3.fromRGB(214, 228, 206), BlackCatCola = Color3.fromRGB(200, 186, 170) }
-- where the hand closes on the prop, in the Handle's space (from the play test): a lunch tray is held by its near rim
local GRIP = {}
-- round items with a printed wrap: the wrap's front panel (the region's u = 0.25) lands on the mesh's -X, so these turn -90
-- degrees about Y to bring their front round to -Z (in the catalogue, on the counter, in the Locker and in the hand)
local FRONT_YAW = {}
for id in ([[BarleyTea CannedCoffee RedLantern Ramune HolyLemonade BlackCatCola GreenTea HotCocoa MelonSoda PumpkinSoup MisoSoup
	CupRamen GhostMints SoyBottle MustardBottle CupStack]]):gmatch("%S+") do FRONT_YAW[id] = math.rad(-90) end
local TRAYS = { KatsuCurry = true, ShoyuRamen = true, KaraageSet = true, MackerelSet = true, Omurice = true, WitchingStew = true,
	ShepherdsPie = true, PumpkinGratin = true, RavensRoast = true }

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, absent, items, snacks = {}, 0, {}, 0, 0

local function folder(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder") f.Name = name f.Parent = parent end
	return f
end
local Lib = folder(P, "Concession")
local ItemLib = folder(P, "ConcessionItems")
local Snacks = folder(RS, "NHSnacks")

local function surface(part, sheet)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
	local ids = IDS[sheet]
	if not ids then table.insert(missing, sheet) return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
end

local function dress(part, sheet, item, glass)
	part.Anchored = true
	part.CanCollide = COLLIDE[item] == true and not glass
	part.CanTouch = false
	part.CanQuery = not glass
	part.PivotOffset = CFrame.new()
	if glass then
		for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
		part.Material = Enum.Material.Glass
		part.Transparency = 0.5
		part.Color = GLASS_TINT[item] or Color3.fromRGB(225, 232, 236)
		part.CastShadow = false
	else
		surface(part, sheet)
		if COLLIDE[item] then pcall(function() part.CollisionFidelity = Enum.CollisionFidelity.Box end) end
	end
end

-- an item's Model: its piece and its glass, pivot at the bottom centre
local function itemModel(sheet, item, main, glass)
	local m = Instance.new("Model")
	m.Name = item
	local a = main:Clone()
	a.Name = item
	a.Parent = m
	if glass then
		local g = glass:Clone()
		g.Name = item .. "_Glass"
		g.Parent = m
	end
	if FRONT_YAW[item] then
		local turn = CFrame.new(a.Position) * CFrame.Angles(0, FRONT_YAW[item], 0) * CFrame.new(-a.Position)
		for _, p in m:GetChildren() do p.CFrame = turn * p.CFrame end
	end
	-- the pivot at the bottom centre of the item (glass included): with a PrimaryPart, that is the part's PivotOffset
	-- (setting WorldPivot on such a model doesn't stick)
	local cf, size = m:GetBoundingBox()
	a.PivotOffset = a.CFrame:ToObjectSpace(CFrame.new(cf.Position - Vector3.new(0, size.Y / 2, 0)))
	m.PrimaryPart = a
	m:SetAttribute("ItemId", item)
	m:SetAttribute("Sheet", sheet)
	m:SetAttribute("Sold", not DRESSING[sheet])
	m:SetAttribute("Lunch", LUNCH[sheet] == true)
	m:SetAttribute("NHBuildKit", "Concession")
	CS:AddTag(m, "NHConcessionItem")
	CS:AddTag(m, "NHPropBatch54")
	return m
end

-- the hand prop: Handle (the piece, unanchored at use), the glass welded under it, a grip at the handle's centre (or its rim)
local function snack(item, main, glass)
	local m = Instance.new("Model")
	m.Name = item
	local h = main:Clone()
	h.Name = "Handle"
	h.CanCollide, h.CanTouch, h.CanQuery, h.Massless = false, false, false, true
	h.Parent = m
	if glass then
		local g = glass:Clone()
		g.Name = "Glass"
		g.CanCollide, g.CanTouch, g.CanQuery, g.Massless = false, false, false, true
		g.Parent = h
		local w = Instance.new("WeldConstraint")
		w.Part0, w.Part1 = h, g
		w.Parent = g
	end
	-- the grip, measured in a play test (slot 4 Testy, R6): Rx(-90) stands an item upright in the right hand with its front (-Z)
	-- facing forward; the turned items (front on -X) need Rz(90) * Ry(90). The hand closes on the item's back face, a little
	-- above its middle, so the item sits in front of the fist rather than inside it; a lunch tray is held flat by its near rim.
	local grip = GRIP[item]
	if not grip then
		local s = h.Size
		if TRAYS[item] then
			grip = CFrame.new(0, 0.04, s.Z / 2 - 0.1) * CFrame.Angles(math.rad(-90), 0, 0)
		elseif FRONT_YAW[item] then
			grip = CFrame.new(s.X / 2 + 0.05, s.Y * 0.1, 0) * CFrame.Angles(0, 0, math.rad(90)) * CFrame.Angles(0, math.rad(90), 0)
		else
			grip = CFrame.new(0, s.Y * 0.1, s.Z / 2 + 0.05) * CFrame.Angles(math.rad(-90), 0, 0)
		end
	end
	if FRONT_YAW[item] then
		-- the Locker's view places the handle by its pivot, so the mesh turns with it there
		h.PivotOffset = CFrame.Angles(0, -FRONT_YAW[item], 0)
	end
	h:SetAttribute("NHGrip", grip)
	m.PrimaryPart = h
	m:SetAttribute("NHBuildKit", "Concession")
	return m
end

for _, sheet in ORDER do
	local m = workspace:FindFirstChild(sheet)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = Lib:FindFirstChild(sheet) end
	if not m then table.insert(absent, sheet) continue end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	local parts = {}
	for _, p in m:GetChildren() do
		if p:IsA("MeshPart") then parts[p.Name] = p end
	end
	for item in SHEETS[sheet]:gmatch("%S+") do
		local main = parts[sheet .. "_" .. item]
		local glass = parts[sheet .. "_" .. item .. "_Glass"]
		if not main then table.insert(absent, sheet .. "_" .. item) continue end
		dress(main, sheet, item, false)
		if glass then dress(glass, sheet, item, true) end
		local old = ItemLib:FindFirstChild(item)
		if old then old:Destroy() end
		itemModel(sheet, item, main, glass).Parent = ItemLib
		items += 1
		if not DRESSING[sheet] then
			local s = Snacks:FindFirstChild(item)
			if s then s:Destroy() end
			snack(item, main, glass).Parent = Snacks
			snacks += 1
		end
	end
	m:SetAttribute("NHBuildKit", "Concession")
	CS:AddTag(m, "NHPropBatch54")
	if fresh then
		local old = Lib:FindFirstChild(sheet)
		if old and old ~= m then old:Destroy() end
		m.Parent = Lib
	end
	task.wait()
end
return string.format("item templates %d, hand props %d, maps %d\nno ids: %s\nnot imported: %s", items, snacks, mapsSet,
	table.concat(missing, ","), table.concat(absent, ","))
