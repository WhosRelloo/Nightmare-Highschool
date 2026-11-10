--!nocheck
-- Props batch 42 (the indoor lighting kit): turns the imported FBX models in Workspace into templates in
-- ServerStorage.NHProps (NHBuildKit "Lighting"), like tools/props/gym_kit_templates.luau. PK is replaced before running
-- with "Name:color,normal,rough,metal;...;StainedLightboxStained:canvas,emissive" (asset ids in base 36). Safe to run again.
-- The lights are the table in docs/School-Props.md ("Lights for the template"): each _Glow piece becomes Neon in its glow
-- colour with CastShadow off, and gets its light (plus a dimmer fill PointLight where listed) and its flicker tags.
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

local function c(r, g, b) return Color3.fromRGB(r, g, b) end
local WARM, WARMG = c(255, 185, 115), c(255, 170, 90)
local FIRE, FIREG = c(255, 150, 75), c(255, 130, 55)
local CANDLE, EMBERS = { "NHCandle" }, { "NHCandle", "NHAmbient:Embers" }
-- name = { kind, on (piece suffix), colour, brightness, range, shadows, glow colour, tags, face, angle, fill {colour, b, range} }
local L = {
	ChandelierGreatWheel = { "Point", "Glow", c(255, 190, 120), 3.0, 30, true, WARMG, CANDLE },
	ChandelierAntler = { "Point", "Glow", WARM, 2.5, 26, true, WARMG, CANDLE },
	ChandelierCage = { "Point", "Glow", WARM, 2.2, 22, true, WARMG, CANDLE },
	ChandelierCascade = { "Point", "Glow", c(200, 220, 255), 2.5, 26, true, c(185, 210, 255), {} },
	ChandelierRavenWing = { "Point", "Glow", WARM, 2.5, 26, true, WARMG, CANDLE },
	ChandelierShipHull = { "Point", "Glow", WARM, 2.8, 28, true, WARMG, CANDLE },
	ChandelierThornCrown = { "Point", "Glow", c(255, 150, 120), 2.2, 22, true, c(255, 120, 105), {} },
	LanternCluster = { "Point", "Glow", WARM, 2.0, 20, false, WARMG, CANDLE },
	PendantSpire = { "Point", "Glow", c(175, 120, 255), 1.8, 18, false, c(170, 110, 255), CANDLE },
	PendantBellCage = { "Point", "Glow", c(255, 205, 150), 2.0, 20, false, c(255, 214, 160), {} },
	ClassroomPendant = { "Point", "Glow", c(255, 232, 200), 2.0, 20, false, c(255, 236, 205), {} },
	ClassroomTriPendant = { "Spot", "Glow", c(255, 225, 185), 2.5, 24, false, c(255, 222, 175), {}, "Bottom", 120, { c(255, 225, 185), 1.0, 16 } },
	MoonOrb = { "Point", "Glow", c(185, 210, 255), 2.0, 22, false, c(185, 210, 255), {} },
	TraceryCeilingRose = { "Surface", "Glow", c(255, 225, 185), 2.0, 22, false, c(255, 228, 190), {}, "Bottom", 160 },
	VaultBossLight = { "Point", "Glow", c(255, 180, 100), 2.2, 22, false, c(255, 165, 70), {} },
	CorridorStripLight = { "Surface", "Glow", c(255, 228, 195), 1.8, 18, false, c(255, 230, 195), {}, "Bottom", 150 },
	SconceIronHand = { "Point", "Glow", FIRE, 1.8, 18, false, FIREG, EMBERS },
	SconceBatWing = { "Point", "Glow", WARM, 1.5, 16, false, WARMG, CANDLE },
	SconceGasBracket = { "Point", "Glow", c(255, 225, 185), 1.6, 16, false, c(255, 232, 200), {} },
	SconceMirror = { "Point", "Glow", c(255, 190, 125), 1.6, 16, false, WARMG, CANDLE },
	SconceGargoyle = { "Point", "Glow", FIRE, 2.0, 20, false, FIREG, EMBERS },
	SconceWitchlight = { "Point", "Glow", c(175, 120, 255), 1.4, 14, false, c(170, 110, 255), CANDLE },
	CorridorUplighter = { "Surface", "Glow", c(255, 222, 180), 2.0, 18, false, c(255, 225, 185), {}, "Top", 150 },
	StainedLightbox = { "Surface", "Stained", c(255, 185, 140), 1.5, 14, false, c(255, 180, 110), {}, "Front", 120, { c(255, 180, 110), 0.8, 10 } },
	TorchereWolves = { "Point", "Glow", FIRE, 2.5, 24, true, FIREG, EMBERS },
	CandelabraDeadTree = { "Point", "Glow", WARM, 1.8, 18, false, WARMG, CANDLE },
	TorchereAlabaster = { "Spot", "Glow", c(255, 215, 165), 2.5, 24, false, c(255, 218, 170), {}, "Top", 120, { c(255, 215, 165), 1.0, 14 } },
	CandleHearse = { "Point", "Glow", WARM, 2.0, 20, false, WARMG, CANDLE },
	PianoLamp = { "Spot", "Glow", c(255, 222, 175), 1.5, 12, false, c(255, 222, 175), {}, "Bottom", 90, { c(255, 222, 175), 0.6, 8 } },
	ReadingLampSwing = { "Spot", "Glow", c(255, 222, 175), 1.5, 12, false, c(255, 222, 175), {}, "Bottom", 80, { c(255, 222, 175), 0.6, 8 } },
	DeskLampChapel = { "Point", "Glow", c(255, 175, 95), 1.2, 12, false, c(255, 165, 70), {} },
	MantelLampBat = { "Point", "Glow", c(255, 140, 90), 1.2, 12, false, c(255, 120, 75), {} },
}
local COLLIDE = { TorchereWolves = true, CandelabraDeadTree = true, TorchereAlabaster = true, CandleHearse = true }
local VIOLET_GLASS = { PendantSpire = true, SconceWitchlight = true }

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, lights = {}, 0, 0
local function surface(part, set)
	for _, o in part:GetChildren() do if o:IsA("SurfaceAppearance") then o:Destroy() end end
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return end
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
local function addLight(part, kind, col, b, r, shadows, face, angle)
	local l = Instance.new(kind .. "Light")
	l.Color = col l.Brightness = b l.Range = r l.Shadows = shadows
	if face then l.Face = Enum.NormalId[face] l.Angle = angle end
	l.Parent = part
	lights += 1
end

local done, absent, emissive = {}, {}, "not set"
for name, spec in L do
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then table.insert(absent, name) continue end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	local kind, on, col, b, r, shadows, glowCol, tags, face, angle, fill = table.unpack(spec)
	local lightPart, glowPart
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		p.PivotOffset = CFrame.new()
		for _, o in p:GetChildren() do if o:IsA("Light") then o:Destroy() end end
		for _, t in CS:GetTags(p) do CS:RemoveTag(p, t) end
		local n = p.Name
		if n:match("_Glow$") then
			bare(p)
			p.Material = Enum.Material.Neon p.Color = glowCol
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
			glowPart = p
			for _, t in tags do CS:AddTag(p, t) end
		elseif n:match("_Glass$") then
			bare(p)
			p.Material = Enum.Material.Glass p.Transparency = 0.4
			p.Color = VIOLET_GLASS[name] and c(120, 70, 180) or c(235, 238, 240)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		elseif n:match("_Mirror$") then
			bare(p)
			p.Material = Enum.Material.Glass p.Transparency = 0 p.Reflectance = 0.6 p.Color = c(200, 205, 210)
			p.CanCollide = false p.CanTouch = false
		elseif n:match("_Stained$") then
			-- the window kit's way: the painted canvas as its colour, the emissive mask lit at strength 2
			bare(p)
			local ids = IDS.StainedLightboxStained
			local s = Instance.new("SurfaceAppearance")
			if ids and ids[1] then s.ColorMap = "rbxassetid://" .. string.format("%d", ids[1]) mapsSet += 1 end
			if ids and ids[2] then
				local uri = "rbxassetid://" .. string.format("%d", ids[2])
				local ok = pcall(function() s.EmissiveMaskContent = Content.fromUri(uri) end)
				if not ok then ok = pcall(function() s.EmissiveMaskContent = uri end) end
				if ok then pcall(function() s.EmissiveStrength = 2 end) emissive = "set" mapsSet += 1 end
			end
			s.Parent = p
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		else
			surface(p, name)
		end
		if n:match("_" .. on .. "$") then lightPart = p end
		if not COLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	lightPart = lightPart or glowPart
	if lightPart then
		addLight(lightPart, kind, col, b, r, shadows, face, angle)
		if fill then addLight(glowPart or lightPart, "Point", fill[1], fill[2], fill[3], false) end
	else
		table.insert(missing, "light piece(" .. name .. ")")
	end
	m:SetAttribute("NHBuildKit", "Lighting")
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	table.insert(done, name)
end
table.sort(absent)
return string.format("templates %d, maps %d, lights %d, lightbox emissive %s\nno ids: %s\nnot imported: %s",
	#done, mapsSet, lights, emissive, table.concat(missing, ","), table.concat(absent, ","))
