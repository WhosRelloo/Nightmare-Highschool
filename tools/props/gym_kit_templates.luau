--!nocheck
-- Props batch 43 (the gym kit): turns the imported FBX models in Workspace into templates in ServerStorage.NHProps
-- (NHBuildKit "Gym"), like tools/props/garden_kit_templates.luau. PK is replaced before running with
-- "Name:color,normal,rough,metal;..." (asset ids in base 36) from the group's images. Safe to run again.
-- Every piece takes its own prop's maps (docs/School-Props.md, batch 43). CursedTrophy_Glow is violet neon with a small
-- light; StopwatchStand_Glass is the clear crystal; SaunaDoor_Door0 is rigged on the locker system like the Safe
-- ("Sweatbox / Open", swings out on its hinge, which the FBX origin carries as the part's PivotOffset).
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

local NAMES = [[ArcheryTarget BalanceBeam BasketballHoop BowRack BoxingGloves BoxingRingCorner ClimbingRopes CursedTrophy
EquipmentCage FencingMaskRack FencingPiste FirstAidStation GymRings HighJumpStands HousePointsBoard IndianClubRack KitHamper
LockerBench MatTrolley MedicineBallRack Megaphone ParallelBars PommelHorse PunchingBag RefereeChair RowingMachine SaunaDoor
Springboard StopwatchStand VaultingBox WallBars WallPulley WhistleBoard]]

-- "Collides: no" in the docs, plus the ropes and rings: they collide on the beam only, and the beam is overhead
local NOCOLLIDE = {}
for n in ([[FencingPiste BoxingGloves Megaphone IndianClubRack FencingMaskRack WhistleBoard HousePointsBoard ClimbingRopes
GymRings]]):gmatch("%S+") do NOCOLLIDE[n] = true end

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise = {}, 0, 0
local function surface(part, set)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
end
local function bare(part)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
end

-- the locker-system rig (as the Safe): tag, prompt attributes, an invisible NHPropSpot linked by a Placeholder value
local function rigDoor(m, door)
	local pv = m:GetPivot()
	door:SetAttribute("Door", true)
	-- out = toward the front (-Z); try both ways round the hinge and keep the one whose middle ends up in front
	local hinge = door.CFrame * door.PivotOffset
	local best, bestZ = 95, math.huge
	for _, deg in { 95, -95 } do
		local moved = hinge * CFrame.Angles(0, math.rad(deg), 0) * hinge:Inverse() * door.CFrame
		local z = pv:PointToObjectSpace(moved.Position).Z
		if z < bestZ then best, bestZ = deg, z end
	end
	door:SetAttribute("SwingDeg", best)
	local spot = m:FindFirstChild("NHPropSpot") or Instance.new("Part")
	spot.Name = "NHPropSpot" spot.Size = Vector3.new(0.2, 0.2, 0.2) spot.Transparency = 1
	spot.Anchored = true spot.CanCollide = false spot.CanTouch = false spot.CanQuery = false
	local rel = pv:PointToObjectSpace(door.Position)
	spot.CFrame = pv * CFrame.new(rel.X, rel.Y, rel.Z - door.Size.Z / 2 - 1)
	spot.Parent = m
	local ph = m:FindFirstChild("Placeholder") or Instance.new("ObjectValue")
	ph.Name = "Placeholder" ph.Value = spot ph.Parent = m
	m:SetAttribute("PromptObject", "Sweatbox") m:SetAttribute("PromptOpen", "Open")
	m:SetAttribute("PromptClose", "Close") m:SetAttribute("AutoClose", 8)
	CS:AddTag(m, "NHLockerProp")
	return best
end

local done, absent, swing = {}, {}, "?"
for name in NAMES:gmatch("%S+") do
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then table.insert(absent, name) continue end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	-- Roblox's importer caps a mesh at 2048 studs (20.48 at the FBX's 100x): the ropes are 22.08 tall (from the FBX)
	if name == "ClimbingRopes" and math.abs(m:GetExtentsSize().Y - 22.08) > 0.05 then
		m:ScaleTo(m:GetScale() * 22.08 / m:GetExtentsSize().Y)
	end
	local door
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		for _, o in p:GetChildren() do if o:IsA("Light") then o:Destroy() end end
		local n = p.Name
		if n:match("_Door0$") then
			surface(p, name) -- keeps its PivotOffset: that is the hinge
			door = p
		else
			p.PivotOffset = CFrame.new()
			if n:match("_Glow$") then
				bare(p)
				p.Material = Enum.Material.Neon p.Color = Color3.fromRGB(150, 70, 255)
				p.CastShadow = false p.CanCollide = false p.CanTouch = false
				local L = Instance.new("PointLight") L.Color = Color3.fromRGB(150, 70, 255) L.Range = 6 L.Brightness = 0.6 L.Parent = p
			elseif n:match("_Glass$") then
				bare(p)
				p.Material = Enum.Material.Glass p.Transparency = 0.6 p.Color = Color3.fromRGB(235, 240, 240)
				p.CastShadow = false p.CanCollide = false p.CanTouch = false
			else
				surface(p, name)
				if not NOCOLLIDE[name] and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
					if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
				end
			end
		end
		if NOCOLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	if door then swing = tostring(rigDoor(m, door)) end
	m:SetAttribute("NHBuildKit", "Gym")
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	table.insert(done, name)
end
table.sort(absent)
return string.format("templates %d, maps %d, precise collision %d, sweatbox door swings %s\nno ids: %s\nnot imported: %s",
	#done, mapsSet, precise, swing, table.concat(missing, ","), table.concat(absent, ","))
