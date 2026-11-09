--!nocheck
-- Props batches 35-39 (lounge, school, detention, electives, dorm house): turns the imported FBX models in
-- Workspace into templates in ServerStorage.NHProps, like the dorm kit (tools/homes/dorm_kit_templates.luau).
-- PK is replaced before running with "Name:color,normal,rough,metal;..." (asset ids in base 36), read from the
-- group's images (itemconfiguration get-assets, groupId 15981569). Safe to run again: it only takes models
-- still at import scale from Workspace, and re-applies the rest in place.
local PK = [==[PK]==]

local SS = game:GetService("ServerStorage")
local P = SS:FindFirstChild("NHProps")
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

local KIT = {}
local function kit(name, list) for _, n in list do KIT[n] = name end end
kit("Lounge", { "TeaUrn", "SpiritKettle", "TeaSet", "MugRack", "BiscuitBarrel", "KitchenetteCounter", "IceBox", "MarkingStack",
	"Gradebook", "StaffRotaBoard", "WallTelephone", "CardTable", "StaffOnlySign", "Dartboard", "StaffLockers" })
kit("School", { "Abacus", "AnatomySkeleton", "LabBench", "TestTubeRack", "SpecimenJars", "Microscope", "WallMap", "WritingSlate",
	"InkwellSet", "Satchel", "DunceStool", "UprightPiano", "MusicStand", "Metronome", "Radiator", "FireBucketRack", "DrinkingFountain", "VaultingHorse" })
kit("Detention", { "DetentionDesk", "LinesChalkboard", "LinesPaperStack", "SupervisorPodium", "DetentionLog", "ConfiscatedBox",
	"SchoolRulesBoard", "DetentionSign", "FacingWallDesk", "WindowGrille", "KeyRingHook", "WallBell",
	"StudentDeskCarved", "StudentDeskGraffiti", "StudentDeskBroken", "StudentDeskWobbly", "StudentDeskInkStained",
	"StudentDeskPrankVigil", "StudentDeskPrankCourt", "StudentDeskPrankAthletes", "StudentDeskPrankDelinquents",
	"StudentDeskPrankPack", "StudentDeskPrankOrdinary", "StudentDeskPrankChoir", "StudentDeskPrankInk" })
kit("Electives", { "PottingBench", "HerbDryingRack", "Terrarium", "CastIronRange", "PotRack", "MixingBowlSet", "TreadleSewingMachine",
	"DressForm", "FabricBolts", "BellowsCamera", "DarkroomTrays", "WoodLathe", "ToolWall", "Sawhorse", "PottersWheel", "Kiln",
	"CostumeRack", "TheatreMasks" })
kit("DormHouse", { "BunkBed", "Nightstand", "FloorMirror", "LaundryHamper", "WashingMachine", "ShowerStall", "MiniFridge", "BeanBag",
	"PingPongTable", "RADesk", "VanityTable", "MakeupSet", "JewelryBox", "PerfumeTray", "ShoeRack", "FairyLights", "WeightBench",
	"Dumbbells", "GuitarStand", "TVConsole", "SneakerPile", "DoorHoop", "Urinal", "UrinalDivider", "UrinalTrough" })

-- small, table-top or wall things you walk through rather than bump into
local NOCOLLIDE = {}
for _, n in { "TeaUrn", "SpiritKettle", "TeaSet", "MugRack", "BiscuitBarrel", "MarkingStack", "Gradebook", "StaffRotaBoard",
	"WallTelephone", "StaffOnlySign", "Dartboard", "Abacus", "TestTubeRack", "SpecimenJars", "Microscope", "WallMap", "WritingSlate",
	"InkwellSet", "Satchel", "Metronome", "FireBucketRack", "LinesPaperStack", "SchoolRulesBoard", "DetentionSign", "KeyRingHook",
	"WallBell", "MixingBowlSet", "ToolWall", "TheatreMasks", "MakeupSet", "JewelryBox", "PerfumeTray", "FairyLights", "SneakerPile",
	"DoorHoop" } do NOCOLLIDE[n] = true end

local GLOW = { -- neon colour for the light pieces (the TV screen keeps its picture instead)
	SupervisorPodium = Color3.fromRGB(255, 214, 160), VanityTable = Color3.fromRGB(255, 226, 180),
	FairyLights = Color3.fromRGB(255, 210, 140), DarkroomTrays = Color3.fromRGB(255, 40, 30) }

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet = {}, 0
local function surface(part, set)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
	local ids = IDS[set]
	if not ids then table.insert(missing, set) return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
end

local done, absent = {}, {}
for name, kitName in KIT do
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then table.insert(absent, name) continue end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		p.PivotOffset = CFrame.new()
		local n = p.Name
		for _, o in p:GetChildren() do if o:IsA("Light") then o:Destroy() end end
		if n:match("_Glow$") and name == "TVConsole" then
			surface(p, name) -- the CRYPT CRAWLER screen is in the maps
			p.CastShadow = false
			local L = Instance.new("SurfaceLight") L.Face = Enum.NormalId.Front L.Angle = 120 L.Range = 10
			L.Brightness = 1.2 L.Color = Color3.fromRGB(190, 120, 255) L.Parent = p
		elseif n:match("_Glow$") then
			for _, o in p:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
			p.Material = Enum.Material.Neon
			p.Color = GLOW[name] or Color3.fromRGB(255, 214, 160)
			p.CastShadow = false
		elseif n:match("_Glass$") then
			for _, o in p:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
			p.Material = Enum.Material.Glass
			p.Transparency = 0.45
			p.Color = Color3.fromRGB(235, 240, 240)
			p.CastShadow = false
		elseif n:match("_Mirror$") then
			for _, o in p:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
			p.Material = Enum.Material.Glass
			p.Transparency = 0
			p.Reflectance = 0.6
			p.Color = Color3.fromRGB(200, 205, 210)
		else
			surface(p, name)
		end
		if NOCOLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	m:SetAttribute("NHBuildKit", kitName)
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	table.insert(done, name)
end
table.sort(absent)
return string.format("templates %d, maps %d, no ids: %s\nnot imported: %s",
	#done, mapsSet, table.concat(missing, ","), table.concat(absent, ","))
