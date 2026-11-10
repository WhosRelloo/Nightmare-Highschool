--!nocheck
-- Props batches 45 (the shop, bookshop and cafe interiors, NHBuildKit "Interiors") and 46 (the armory and the spell shop,
-- NHBuildKits "Armory" and "SpellShop"): turns the imported FBX models in Workspace into templates in ServerStorage.NHProps,
-- like tools/props/art_showpiece_templates.luau. PK is replaced before running with "Name:color,normal,rough,metal;..."
-- (asset ids in base 36) from the group's images. Safe to run again. Every piece takes its own prop's four maps.
--   Glow / Glow2: Neon in the docs' colours, with the lights and particles docs/School-Props.md lists (batches 45, 46);
--   candle flames and the scrying orb's breathing light are tagged NHCandle (Controllers.World.Ambient flickers them).
--   Glass: see-through.  Mirror (CafeBackShelf): dark reflective glass.
--   Doors and the till drawer run on the locker system (tag NHLockerProp, Controllers.World.LockerDoors): the gate and
--   the tall cabinet's door swing out on their hinges (the FBX origin, kept as the part's PivotOffset; the cabinet's
--   pane swings with its door), the till drawer slides out 0.7 to the front.
local PK = [==[PK]==]

local CS = game:GetService("CollectionService")
local P = game:GetService("ServerStorage"):FindFirstChild("NHProps")
assert(P, "no ServerStorage.NHProps")

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
local rgb = Color3.fromRGB

local KITS = {
	Interiors = [[ShopCounter ShopCounterCorner ShopCounterEnd CashRegister ShopScales CounterBell WrapStand DisplayCase
GlassCabinetTall WallShelfStocked IslandShelf ApothecaryDrawers SweetJarShelf PostcardSpinner StockSacks StockCrates
BookshopCounter NewReleasesTable BookStandAngled BargainBinCart StaffPicksEasel CafeBarCounter BarStool CafeBackShelf
OpenClosedSign ShopSignInterior PriceTagRail DoorBellBracket ShopStool HatUmbrellaStand]],
	Armory = [[KatanaStand PolearmRack PlateArmourStand MailHauberkStand ShieldWall Grindstone ArmoryCounter SilverDaggerCase
HelmShelf BoltBarrel BeastPell CrossbowRack HuntersReliquary ArmorySign ClawGauntletDisplay]],
	SpellShop = [[TetheredGrimoires PotionHoneycomb ScryingOrbStand WandCoffin RuneStoneTable ScrollCarousel WaxfallAltar
OrreryCounter StarChartBanner HangingCrystals FamiliarPerch RuneCircleRug OddmentsEtagere SpellShopSign]],
}

-- "Collides: no" in the docs; everything else collides on its precise shape
local NOCOLLIDE = {}
for n in ([[ShopScales CounterBell OpenClosedSign ShopSignInterior PriceTagRail DoorBellBracket CrossbowRack
ClawGauntletDisplay HelmShelf ShieldWall ArmorySign RuneCircleRug StarChartBanner PotionHoneycomb HangingCrystals
SpellShopSign]]):gmatch("%S+") do NOCOLLIDE[n] = true end

local GLOW = {
	ShopCounterCorner = { Glow = rgb(255, 170, 90) }, CafeBarCounter = { Glow = rgb(255, 160, 80) },
	TetheredGrimoires = { Glow = rgb(180, 120, 255) },
	PotionHoneycomb = { Glow = rgb(190, 110, 255), Glow2 = rgb(120, 255, 150) },
	ScryingOrbStand = { Glow = rgb(160, 205, 255) }, WandCoffin = { Glow = rgb(210, 180, 255) },
	RuneStoneTable = { Glow = rgb(90, 230, 220) }, ScrollCarousel = { Glow = rgb(220, 230, 255) },
	WaxfallAltar = { Glow = rgb(190, 140, 255) }, OrreryCounter = { Glow = rgb(255, 190, 90) },
	StarChartBanner = { Glow = rgb(200, 220, 255) },
	HangingCrystals = { Glow = rgb(180, 120, 255), Glow2 = rgb(100, 230, 230) },
	FamiliarPerch = { Glow = rgb(255, 180, 60) }, RuneCircleRug = { Glow = rgb(90, 230, 220) },
	OddmentsEtagere = { Glow = rgb(170, 255, 120), Glow2 = rgb(190, 215, 255) }, SpellShopSign = { Glow = rgb(220, 200, 255) },
}
local GLASS = { ShopCounterCorner = 0.7, ApothecaryDrawers = 0.5, SweetJarShelf = 0.55, ScryingOrbStand = 0.3 }
local function glassT(name, kit) return GLASS[name] or (kit == "Interiors" and 0.6 or 0.5) end

local TEX = { star = "rbxassetid://8030760338", dust = "rbxassetid://7216851093", ember = "rbxassetid://8114157061" }
-- e: { tex, colour, rate, speed, life {min,max}, size {a,b}, spread?, accel?, locked? }
local function emit(part, e)
	local p = Instance.new("ParticleEmitter")
	p.Name = "NHFX_" .. e[1]
	p.Texture = TEX[e[1]]
	p.Color = ColorSequence.new(e[2])
	p.Rate = e[3]
	p.Speed = NumberRange.new(e[4])
	p.Lifetime = NumberRange.new(e[5][1], e[5][2])
	p.Size = NumberSequence.new(e[6][1], e[6][2])
	p.Transparency = NumberSequence.new(0.2, 1)
	p.SpreadAngle = Vector2.new(e.spread or 180, e.spread or 180)
	p.Rotation = NumberRange.new(0, 360)
	p.Acceleration = e.accel or Vector3.zero
	p.LightEmission = 1
	p.LockedToPart = e.locked or false
	p.Shape = Enum.ParticleEmitterShape.Box
	p.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	p.Parent = part
end
local function light(part, color, brightness, range, flicker, shadows)
	local L = Instance.new("PointLight")
	L.Name = "NHFX_Light"
	L.Color = color L.Brightness = brightness L.Range = range L.Shadows = shadows or false
	L.Parent = part
	if flicker then CS:AddTag(part, "NHCandle") end
end

-- the docs' "Lights and particles" (batch 45: two flames; batch 46: the spell shop; the grindstone's sparks are left out)
local FX = {
	ShopCounterCorner = function(g) light(g.Glow, rgb(255, 170, 95), 1.2, 14, false, true) end,
	CafeBarCounter = function(g) light(g.Glow, rgb(255, 160, 85), 0.9, 12, true) end,
	TetheredGrimoires = function(g)
		light(g.Glow, rgb(180, 120, 255), 0.8, 10)
		emit(g.Glow, { "star", rgb(190, 140, 255), 4, 0.3, { 3, 5 }, { 0.15, 0.08 } })
	end,
	PotionHoneycomb = function(g) light(g.Glow, rgb(190, 110, 255), 0.6, 9) if g.Glow2 then light(g.Glow2, rgb(120, 255, 150), 0.6, 9) end end,
	ScryingOrbStand = function(g)
		light(g.Glow, rgb(160, 205, 255), 0.7, 9, true)
		if g.Glass then emit(g.Glass, { "dust", rgb(170, 210, 255), 6, 0.1, { 2, 2 }, { 0.1, 0.05 }, locked = true }) end
	end,
	WandCoffin = function(g) light(g.Glow, rgb(210, 180, 255), 0.4, 5) end,
	RuneStoneTable = function(g) light(g.Glow, rgb(90, 230, 220), 0.7, 9) end,
	ScrollCarousel = function(g) light(g.Glow, rgb(220, 230, 255), 0.4, 6) end,
	WaxfallAltar = function(g) light(g.Glow, rgb(190, 140, 255), 1.4, 12, true) end,
	OrreryCounter = function(g) light(g.Glow, rgb(255, 190, 90), 0.9, 10) end,
	HangingCrystals = function(g)
		light(g.Glow, rgb(180, 120, 255), 1.0, 14)
		if g.Glow2 then light(g.Glow2, rgb(100, 230, 230), 0.5, 10) end
		emit(g.Glow, { "star", rgb(200, 180, 255), 3, 0.5, { 2, 2 }, { 0.05, 0.02 }, spread = 20, accel = Vector3.new(0, -2, 0) })
	end,
	FamiliarPerch = function(g) light(g.Glow, rgb(255, 180, 60), 0.2, 3) end,
	RuneCircleRug = function(g) light(g.Glow, rgb(90, 230, 220), 0.5, 10) end,
	OddmentsEtagere = function(g)
		light(g.Glow, rgb(170, 255, 120), 0.4, 5)
		emit(g.Glow, { "ember", rgb(170, 255, 120), 3, 0.2, { 2, 2 }, { 0.03, 0.03 }, locked = true })
	end,
	SpellShopSign = function(g) light(g.Glow, rgb(220, 200, 255), 0.6, 8) end,
}

-- the locker-system rig (as the gym's SaunaDoor): prompt attributes and an invisible NHPropSpot linked by a Placeholder
local DOORS = {
	ShopCounterEnd = { "Gate", 6 }, GlassCabinetTall = { "Cabinet", 8 }, CashRegister = { "Till", 6 },
}
local function swingOut(pv, door)
	-- out = toward the front (-Z); try both ways round the hinge and keep the one whose middle ends up in front
	local hinge = door.CFrame * door.PivotOffset
	local best, bestZ = 100, math.huge
	for _, deg in { 100, -100 } do
		local moved = hinge * CFrame.Angles(0, math.rad(deg), 0) * hinge:Inverse() * door.CFrame
		local z = pv:PointToObjectSpace(moved.Position).Z
		if z < bestZ then best, bestZ = deg, z end
	end
	return best
end
local function rig(m, leaves, kind)
	local pv = m:GetPivot()
	local main = leaves[1]
	local swing
	for _, leaf in leaves do
		leaf:SetAttribute("Door", true)
		if kind == "slide" then
			leaf:SetAttribute("SwingDeg", 1)
			leaf:SetAttribute("SlideBy", leaf.CFrame:VectorToObjectSpace(pv.LookVector * 0.7))
		else
			swing = swing or swingOut(pv, main) -- the pane follows its door
			leaf:SetAttribute("SwingDeg", swing)
		end
	end
	local spot = m:FindFirstChild("NHPropSpot") or Instance.new("Part")
	spot.Name = "NHPropSpot" spot.Size = Vector3.new(0.2, 0.2, 0.2) spot.Transparency = 1
	spot.Anchored = true spot.CanCollide = false spot.CanTouch = false spot.CanQuery = false
	local rel = pv:PointToObjectSpace(main.Position)
	spot.CFrame = pv * CFrame.new(rel.X, rel.Y, rel.Z - main.Size.Z / 2 - 1)
	spot.Parent = m
	local ph = m:FindFirstChild("Placeholder") or Instance.new("ObjectValue")
	ph.Name = "Placeholder" ph.Value = spot ph.Parent = m
	local d = DOORS[m.Name]
	m:SetAttribute("PromptObject", d[1]) m:SetAttribute("PromptOpen", "Open")
	m:SetAttribute("PromptClose", "Close") m:SetAttribute("AutoClose", d[2])
	CS:AddTag(m, "NHLockerProp")
	return swing or "slide"
end

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise, fx, rigs = {}, 0, 0, 0, {}
local function clear(part)
	for _, o in part:GetChildren() do
		if o:IsA("SurfaceAppearance") or o:IsA("Light") or o:IsA("ParticleEmitter") then o:Destroy() end
	end
	CS:RemoveTag(part, "NHCandle")
end
local function surface(part, set)
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
end

local function build(name, kit)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	local glow = GLOW[name] or {}
	local pieces, leaves = {}, {}
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		clear(p)
		local suf = p.Name:sub(#name + 2)
		pieces[suf] = p
		local leaf = suf == "Door0" or suf == "Drawer0" or (suf == "Glass" and name == "GlassCabinetTall")
		if not leaf then p.PivotOffset = CFrame.new() end -- a leaf keeps its PivotOffset: that is the hinge
		if suf == "Glow" or suf == "Glow2" then
			p.Material = Enum.Material.Neon
			p.Color = glow[suf] or glow.Glow or rgb(255, 200, 140)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
		elseif suf == "Glass" then
			p.Material = Enum.Material.Glass
			p.Transparency = glassT(name, kit)
			p.Color = rgb(225, 232, 238)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		elseif suf == "Mirror" then
			p.Material = Enum.Material.Glass
			p.Transparency = 0 p.Reflectance = 0.35
			p.Color = rgb(40, 40, 46)
		else
			surface(p, name)
			if not NOCOLLIDE[name] and not leaf and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
			end
		end
		if leaf then
			table.insert(leaves, p)
			p.CanCollide = false p.CanTouch = false -- the locker system's doors don't collide
		end
		if NOCOLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	if FX[name] and pieces.Glow then FX[name](pieces) fx += 1 end
	if DOORS[name] and #leaves > 0 then
		table.sort(leaves, function(a, b) return a.Name < b.Name end) -- Door0 before Glass
		table.insert(rigs, name .. " " .. tostring(rig(m, leaves, pieces.Drawer0 and "slide" or "swing")))
	end
	m:SetAttribute("NHBuildKit", kit)
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	return true
end

local done, absent = 0, {}
for _, kit in { "Interiors", "Armory", "SpellShop" } do
	for name in KITS[kit]:gmatch("%S+") do
		if build(name, kit) then done += 1 else table.insert(absent, name) end
		task.wait()
	end
end
return string.format("templates %d, maps %d, precise collision %d, effects on %d, rigs: %s\nno ids: %s\nnot imported: %s",
	done, mapsSet, precise, fx, table.concat(rigs, ", "), table.concat(missing, ","), table.concat(absent, ","))
