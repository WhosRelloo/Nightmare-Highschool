--!nocheck
-- Props batch 40 (the garden kit): turns the imported FBX models in Workspace into templates in ServerStorage.NHProps,
-- like tools/props/kits_35_39_templates.luau. PK is replaced before running with "Name:color,normal,rough,metal;..."
-- (asset ids in base 36) from the group's images (itemconfiguration get-assets, groupId 15981569). Safe to run again.
-- Pieces (docs/School-Props.md, batch 40): Main (or one mesh named after the prop) takes the prop's own maps; _Leaves
-- takes the shared NH_GardenLeaves atlas with its alpha as a cut-out; _Path takes the tiled set its prop is paved with;
-- _Inlay takes MoonRoundelInlay; _Glass becomes glass or water; _Glow becomes neon.
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

local NAMES = [[BirdBath Birdhouse BloodRoseUrn ColdFrame CourtyardBenchTable CrowPerch CurvedStoneBench CypressPair FernCluster
GardenBench GardenObelisk GardenSteps GardenToolsLean GardenWallPier GhostOrchid GnarledCrabapple HedgeArchway HedgeBattlement
HedgeCorner HedgeEnd HedgeRaven HedgeStraight HedgeWolf IronGazebo IvyWallPanel KeepOffGrassSign KoiPond LavenderBed LilyPads
LogBench LowGardenWall MoonflowerPatch MushroomRing NightshadeShrub PathBridgeSlab PathCobble PathCobbleCurve PathCrazyPaving
PathEdgingIron PathFlagstone PathFlagstoneCross PathFlagstoneCurve PathFlagstoneJunction PathGateArch PathGravel PathGravelCurve
PathHerringbone PathMoonRoundel PathPuddleFlag PoppyBed PottingCluster PumpkinPatch RaisedFlowerBed RoseArbor RoseBushBlack
RoseBushCrimson Scarecrow SteppingStones StoneLanternPost TallGrassClump ThornBramble TrellisPanel UrnPedestal WeepingWillow
Wheelbarrow WisteriaPergola YewTree]]

-- the "Collides: no" props in the docs: you walk through them
local NOCOLLIDE = {}
for n in ([[SteppingStones PathEdgingIron IvyWallPanel FernCluster LavenderBed MushroomRing MoonflowerPatch TallGrassClump
NightshadeShrub PumpkinPatch PoppyBed LilyPads GhostOrchid Wheelbarrow GardenToolsLean PottingCluster TrellisPanel KeepOffGrassSign
Birdhouse Scarecrow CrowPerch]]):gmatch("%S+") do NOCOLLIDE[n] = true end

-- walk-through or walk-under props: their Main collides on its real shape, so the openings stay clear
local PRECISE = { HedgeArchway = true, PathGateArch = true, WisteriaPergola = true, RoseArbor = true, IronGazebo = true,
	WeepingWillow = true, GnarledCrabapple = true, GardenSteps = true, PathBridgeSlab = true, KoiPond = true, PathMoonRoundel = true }

local PATHSET = { PathCobble = "GardenCobble", PathCobbleCurve = "GardenCobble", PathGravel = "GardenGravel",
	PathGravelCurve = "GardenGravel", PathHerringbone = "HerringboneBrick" }

local MOON, AMBER = Color3.fromRGB(190, 215, 255), Color3.fromRGB(255, 190, 110)
local GLOW = { MushroomRing = MOON, MoonflowerPatch = MOON, GhostOrchid = MOON, NightshadeShrub = Color3.fromRGB(150, 90, 255),
	StoneLanternPost = AMBER, PathGateArch = AMBER, PumpkinPatch = Color3.fromRGB(255, 150, 60) }
local LANTERN = { StoneLanternPost = true, PathGateArch = true } -- a real light at the flame
local WATER = { KoiPond = true, BirdBath = true, PathPuddleFlag = true, PathBridgeSlab = true }

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise = {}, 0, 0
local function surface(part, set)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return nil end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
	return s
end
local function bare(part)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
end

local done, absent = {}, {}
for name in NAMES:gmatch("%S+") do
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then table.insert(absent, name) continue end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		p.PivotOffset = CFrame.new()
		for _, o in p:GetChildren() do if o:IsA("Light") then o:Destroy() end end
		local n = p.Name
		if n:match("_Leaves$") then
			local s = surface(p, "NH_GardenLeaves")
			if s then s.AlphaMode = Enum.AlphaMode.Transparency end
			p.DoubleSided = true
			p.CanCollide = false p.CanTouch = false p.CanQuery = false
		elseif n:match("_Path$") then
			surface(p, PATHSET[name] or name)
		elseif n:match("_Inlay$") then
			surface(p, "MoonRoundelInlay")
		elseif n:match("_Glow$") then
			bare(p)
			p.Material = Enum.Material.Neon
			p.Color = GLOW[name] or AMBER
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
			if LANTERN[name] then
				local L = Instance.new("PointLight") L.Color = AMBER L.Range = 16 L.Brightness = 1.4 L.Shadows = true L.Parent = p
			end
		elseif n:match("_Glass$") then
			bare(p)
			p.Material = Enum.Material.Glass
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
			if WATER[name] then
				p.Color = Color3.fromRGB(34, 48, 52) p.Transparency = 0.25 p.Reflectance = 0.3
			elseif name == "GhostOrchid" then
				p.Color = Color3.fromRGB(232, 238, 255) p.Transparency = 0.3 p.Reflectance = 0
			else
				p.Color = Color3.fromRGB(235, 240, 240) p.Transparency = 0.45 p.Reflectance = 0
			end
		else
			surface(p, name)
			if PRECISE[name] and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
			end
		end
		if NOCOLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	m:SetAttribute("NHBuildKit", "Garden")
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	table.insert(done, name)
end
table.sort(absent)
return string.format("templates %d, maps %d, precise collision %d, no ids: %s\nnot imported: %s",
	#done, mapsSet, precise, table.concat(missing, ","), table.concat(absent, ","))
