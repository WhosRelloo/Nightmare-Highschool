--!nocheck
-- Props batches 41 (the art kit, NHBuildKit "Art") and 44 (the showpiece kit, NHBuildKit "Showpiece"): turns the imported
-- FBX models in Workspace into templates in ServerStorage.NHProps, like tools/props/gym_kit_templates.luau. PK is replaced
-- before running with "Set:color,normal,rough,metal;..." (asset ids in base 36) from the group's images; a painting's
-- canvas set is "<Prop>Canvas:canvas,canvasnormal,canvasrough,". Safe to run again.
--   Main / Figure / Figure2 / Costume / Cloth: the prop's own maps.  Weave: "<Prop>Weave".  Canvas: "<Prop>Canvas"
--   (IconTriptych_Canvas2 / _Canvas3: IconTriptychL / IconTriptychR); batch 41's canvases take the shared canvas
--   roughness map.  Glow / Glow2: Neon in the prop's colours (docs/School-Props.md), with the lights and particles the
--   docs list; candle flames and strobing lights are tagged NHCandle (Controllers.World.Ambient flickers them).
--   Glass: see-through.  Cloth (the banners): NHSwing about the FBX origin on its rod.
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

local CANVAS_ROUGH = 109250550085797 -- batch 21's shared canvas roughness (art/props/props.json)
local rgb = Color3.fromRGB

local ART = [[BannerChoir BannerInk BannerPack BustHeadmistress BustVampireCount BustVeiledStudent CliqueHeraldry DeathMaskCase
EaselCovered GonfalonStand IconTriptych MosaicRaven PaintingAcademyPanorama PaintingClassOf1887 PaintingVampireBall
PaintingWolfHuntSnow PlaqueMemorial PortraitCountessOval PortraitCursedStudent PortraitHeadmasterGallery PortraitHeadmistress
PortraitMiniatures ReliefDanseMacabre ReliefFounding SculptureClaspedHands StainedGlassRoundel StatueChoirChild StatueCourtDuchess
StatueInkScribe TapestryCliques TapestryProcession TondoMoonCloister]]
local SHOW = [[VampireLordRising WerewolfTurning VigilCaptainLantern ChoirConductor InkScribeTendrils DelinquentGlare AthleteSpinKick
CourtDuchessThrone ReaperGuard PackAlphaLanding FounderRavens ExorcistSigil GhoulUppercut CourtIaiDraw TwinRivalsDuel
BackToBackStandoff PaintingBellTowerStorm PaintingFloodedCrypt PaintingBurningLibrary PaintingMoonlitRooftop PaintingChoirLoft
PaintingDormCorridor PaintingFrozenLake PaintingHeadmasterStudy PaintingGymMidnight PaintingInkArchive MuralBloodMoonCourtyard]]

-- floor pieces collide (their Main precisely); wall pieces, banners and tapestries don't
local FLOOR = {}
for n in ([[BustHeadmistress BustVampireCount BustVeiledStudent DeathMaskCase EaselCovered GonfalonStand IconTriptych
SculptureClaspedHands StatueChoirChild StatueCourtDuchess StatueInkScribe VampireLordRising WerewolfTurning VigilCaptainLantern
ChoirConductor InkScribeTendrils DelinquentGlare AthleteSpinKick CourtDuchessThrone ReaperGuard PackAlphaLanding FounderRavens
ExorcistSigil GhoulUppercut CourtIaiDraw TwinRivalsDuel BackToBackStandoff]]):gmatch("%S+") do FLOOR[n] = true end

-- Neon / glass colours (batch 44: glow44.json; batch 41: its template notes)
local CANDLE = rgb(255, 170, 90)
local GLOW = {
	VampireLordRising = { Glow = rgb(255, 30, 40), Glass = rgb(200, 20, 35) },
	WerewolfTurning = { Glow = rgb(255, 70, 40), Glow2 = rgb(255, 190, 70) },
	VigilCaptainLantern = { Glow = rgb(150, 210, 255), Glow2 = rgb(255, 170, 70), Glass = rgb(190, 225, 255) },
	ChoirConductor = { Glow = rgb(255, 236, 190), Glow2 = rgb(170, 200, 255) },
	InkScribeTendrils = { Glow = rgb(185, 90, 255), Glow2 = rgb(120, 230, 255) },
	DelinquentGlare = { Glow = rgb(120, 255, 90), Glow2 = rgb(255, 60, 200), Glass = rgb(150, 255, 120) },
	AthleteSpinKick = { Glow = rgb(255, 200, 70), Glow2 = rgb(255, 90, 50) },
	CourtDuchessThrone = { Glow = rgb(255, 40, 50), Glow2 = rgb(255, 120, 90) },
	ReaperGuard = { Glow = rgb(200, 160, 255), Glow2 = rgb(120, 255, 230), Glass = rgb(190, 230, 255) },
	PackAlphaLanding = { Glow = rgb(255, 120, 40), Glow2 = rgb(255, 200, 80), Glass = rgb(160, 210, 255) },
	FounderRavens = { Glow = rgb(255, 60, 60), Glow2 = rgb(190, 210, 255) },
	ExorcistSigil = { Glow = rgb(255, 210, 120), Glow2 = rgb(170, 210, 255) },
	GhoulUppercut = { Glow = rgb(150, 255, 110), Glow2 = rgb(220, 255, 160), Glass = rgb(170, 255, 170) },
	CourtIaiDraw = { Glow = rgb(255, 40, 70), Glow2 = rgb(255, 170, 190) },
	TwinRivalsDuel = { Glow = rgb(120, 190, 255), Glow2 = rgb(255, 50, 70) },
	BackToBackStandoff = { Glow = rgb(255, 200, 110), Glow2 = rgb(150, 255, 120) },
	-- batch 41
	PaintingVampireBall = { Glow = CANDLE }, PlaqueMemorial = { Glow = CANDLE }, IconTriptych = { Glow = CANDLE },
	PaintingAcademyPanorama = { Glow = rgb(255, 214, 160) },
	StatueChoirChild = { Glow = rgb(255, 230, 160) },
	DeathMaskCase = { Glass = rgb(235, 240, 240) },
}
local PAINT_GLOW = { Glow = rgb(255, 200, 120), Glow2 = rgb(255, 170, 80) } -- batch 44's frames: sconces, gems, picture lights

-- particle textures already used in the game
local TEX = {
	smoke = "rbxassetid://8527116276", ember = "rbxassetid://8114157061", flame = "rbxassetid://13209151224",
	star = "rbxassetid://8030760338", dust = "rbxassetid://7216851093",
}
local function seq(a, b) return ColorSequence.new(a, b or a) end
local function nseq(a, b) return NumberSequence.new(a, b or a) end
-- e: { tex, c1, c2?, rate, speed {min,max}, life {min,max}, size {a,b}, trans {a,b}?, spread?, rot?, accel?, light? }
local function emit(part, e)
	local p = Instance.new("ParticleEmitter")
	p.Name = "NHFX_" .. e[1]
	p.Texture = TEX[e[1]]
	p.Color = seq(e[2], e[3])
	p.Rate = e[4]
	p.Speed = NumberRange.new(e[5][1], e[5][2])
	p.Lifetime = NumberRange.new(e[6][1], e[6][2])
	p.Size = nseq(e[7][1], e[7][2])
	p.Transparency = nseq((e.trans or { 0.2, 1 })[1], (e.trans or { 0.2, 1 })[2])
	p.SpreadAngle = Vector2.new(e.spread or 30, e.spread or 30)
	p.RotSpeed = NumberRange.new(-(e.rot or 0), e.rot or 0)
	p.Rotation = NumberRange.new(0, 360)
	p.Acceleration = e.accel or Vector3.zero
	p.LightEmission = e.light or 0.6
	p.EmissionDirection = Enum.NormalId.Top
	p.Shape = Enum.ParticleEmitterShape.Box
	p.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	p.Parent = part
end
local function light(part, color, brightness, range, flicker, spot)
	local L = Instance.new(spot and "SpotLight" or "PointLight")
	L.Name = "NHFX_Light"
	L.Color = color L.Brightness = brightness L.Range = range L.Shadows = false
	if spot then L.Angle = 70 L.Face = Enum.NormalId.Front end
	L.Parent = part
	if flicker then CS:AddTag(part, "NHCandle") end
end

-- batch 44's effects (docs/School-Props.md, batch 44, "Effects for the template script"); batch 41's lights
local FX = {
	VampireLordRising = function(g)
		if g.Glass then emit(g.Glass, { "smoke", rgb(140, 10, 20), rgb(60, 0, 10), 12, { 0.5, 1.2 }, { 3, 5 }, { 2, 4 }, trans = { 0.6, 1 } }) end
		if g.Glow then emit(g.Glow, { "ember", rgb(255, 40, 50), nil, 6, { 1, 2 }, { 2, 2 }, { 0.15, 0.05 } }) light(g.Glow, rgb(255, 40, 50), 2, 14) end
	end,
	WerewolfTurning = function(g)
		if g.Glow then emit(g.Glow, { "ember", rgb(255, 90, 50), nil, 4, { 0.5, 0.5 }, { 4, 4 }, { 0.2, 0.05 }, spread = 180 }) light(g.Glow, rgb(255, 70, 40), 3, 18) end
		if g.Glow2 then light(g.Glow2, rgb(255, 190, 70), 1, 4) end
	end,
	VigilCaptainLantern = function(g)
		if g.Glow then
			emit(g.Glow, { "flame", rgb(150, 210, 255), rgb(220, 240, 255), 18, { 0.4, 0.8 }, { 1, 1.6 }, { 0.4, 0 }, light = 1 })
			emit(g.Glow, { "ember", rgb(200, 230, 255), nil, 5, { 1, 2 }, { 3, 3 }, { 0.12, 0.04 } })
			light(g.Glow, rgb(150, 210, 255), 3, 16, true)
		end
		if g.Glow2 then light(g.Glow2, rgb(255, 170, 70), 0.8, 6, true) end
	end,
	ChoirConductor = function(g)
		if g.Glow then emit(g.Glow, { "star", rgb(255, 236, 190), nil, 3, { 0.6, 0.6 }, { 5, 5 }, { 0.5, 0.3 }, spread = 60, rot = 20 }) end
		if g.Glow2 then light(g.Glow2, rgb(170, 200, 255), 1.5, 10) end
	end,
	InkScribeTendrils = function(g)
		if g.Glow then emit(g.Glow, { "ember", rgb(185, 90, 255), rgb(40, 0, 80), 8, { 0.5, 1 }, { 2, 2 }, { 0.25, 0.1 }, accel = Vector3.new(0, -3, 0) }) light(g.Glow, rgb(185, 90, 255), 2.5, 12) end
	end,
	DelinquentGlare = function(g)
		if g.Glass then emit(g.Glass, { "smoke", rgb(150, 255, 120), nil, 25, { 3, 5 }, { 0.6, 0.6 }, { 0.3, 1.2 }, trans = { 0.4, 1 } }) end
		if g.Glow then emit(g.Glow, { "ember", rgb(120, 255, 90), nil, 2, { 0, 0 }, { 1, 1 }, { 0.15, 0.1 }, accel = Vector3.new(0, -4, 0) }) light(g.Glow, rgb(120, 255, 90), 3, 14, false, true) end
	end,
	AthleteSpinKick = function(g)
		if g.Glow then
			emit(g.Glow, { "star", rgb(255, 200, 70), nil, 30, { 4, 6 }, { 0.6, 0.6 }, { 0.2, 0.05 }, spread = 180, rot = 200 })
			emit(g.Glow, { "dust", rgb(140, 120, 90), nil, 6, { 1, 2 }, { 1.5, 1.5 }, { 0.6, 1.5 }, trans = { 0.6, 1 } })
			light(g.Glow, rgb(255, 200, 70), 2, 12)
		end
	end,
	CourtDuchessThrone = function(g)
		if g.Glow then emit(g.Glow, { "ember", rgb(160, 10, 25), nil, 2, { 0.4, 0.4 }, { 6, 6 }, { 0.25, 0.25 }, rot = 60, accel = Vector3.new(0, -0.6, 0) }) light(g.Glow, rgb(255, 40, 50), 3, 16) end
	end,
	ReaperGuard = function(g)
		if g.Glow then emit(g.Glow, { "ember", rgb(200, 160, 255), nil, 14, { 2, 4 }, { 0.3, 0.3 }, { 0.15, 0.05 } }) light(g.Glow, rgb(200, 160, 255), 2.5, 14, true) end
		if g.Glass then emit(g.Glass, { "smoke", rgb(190, 230, 255), nil, 3, { 0.5, 0.5 }, { 4, 4 }, { 0.6, 0 }, trans = { 0.5, 1 } }) end
	end,
	PackAlphaLanding = function(g)
		if g.Glow then
			emit(g.Glow, { "ember", rgb(255, 120, 40), nil, 10, { 1, 2 }, { 1.5, 1.5 }, { 0.15, 0.05 } })
			emit(g.Glow, { "dust", rgb(150, 140, 130), nil, 4, { 2, 2 }, { 1.5, 1.5 }, { 1, 2 }, trans = { 0.6, 1 }, spread = 90 })
			light(g.Glow, rgb(255, 120, 40), 2, 10)
		end
		if g.Glass then light(g.Glass, rgb(160, 210, 255), 1.5, 12) end
	end,
	FounderRavens = function(g)
		if g.Glow2 then emit(g.Glow2, { "smoke", rgb(20, 20, 30), nil, 1, { 0.5, 0.5 }, { 6, 6 }, { 0.4, 0.4 }, rot = 40, trans = { 0.3, 1 } }) light(g.Glow2, rgb(190, 210, 255), 1.5, 12) end
	end,
	ExorcistSigil = function(g)
		if g.Glow then emit(g.Glow, { "star", rgb(255, 210, 120), nil, 6, { 1, 2 }, { 2, 2 }, { 0.3, 0.1 }, light = 1 }) light(g.Glow, rgb(255, 210, 120), 3, 16) end
		if g.Glow2 then emit(g.Glow2, { "star", rgb(170, 210, 255), nil, 8, { 0.5, 1 }, { 1.5, 1.5 }, { 0.15, 0.05 } }) end
	end,
	GhoulUppercut = function(g)
		if g.Glow then emit(g.Glow, { "flame", rgb(150, 255, 110), rgb(20, 80, 20), 20, { 1, 3 }, { 1, 1 }, { 0.5, 0 }, light = 1 }) light(g.Glow, rgb(150, 255, 110), 3, 14) end
		if g.Glass then emit(g.Glass, { "smoke", rgb(170, 255, 170), nil, 3, { 0.5, 0.5 }, { 3, 3 }, { 0.6, 0 }, trans = { 0.5, 1 } }) end
	end,
	CourtIaiDraw = function(g)
		if g.Glow then emit(g.Glow, { "ember", rgb(170, 10, 30), nil, 6, { 1, 2 }, { 3, 3 }, { 0.25, 0.2 }, rot = 90 }) light(g.Glow, rgb(255, 40, 70), 2, 12) end
	end,
	TwinRivalsDuel = function(g)
		if g.Glow then
			emit(g.Glow, { "ember", rgb(200, 220, 255), nil, 15, { 4, 8 }, { 0.25, 0.25 }, { 0.12, 0.04 }, spread = 180 })
			emit(g.Glow, { "ember", rgb(255, 80, 90), nil, 15, { 4, 8 }, { 0.25, 0.25 }, { 0.12, 0.04 }, spread = 180 })
			light(g.Glow, rgb(220, 200, 255), 4, 14, true)
		end
	end,
	BackToBackStandoff = function(g)
		if g.Glow then emit(g.Glow, { "flame", rgb(255, 200, 110), nil, 20, { 1, 2 }, { 1, 1 }, { 0.4, 0 }, light = 1 }) light(g.Glow, rgb(255, 200, 110), 3, 16) end
	end,
	-- batch 41
	PaintingVampireBall = function(g) if g.Glow then light(g.Glow, CANDLE, 0.8, 8, true) end end,
	PlaqueMemorial = function(g) if g.Glow then light(g.Glow, CANDLE, 0.8, 6, true) end end,
	IconTriptych = function(g) if g.Glow then light(g.Glow, CANDLE, 0.8, 6, true) end end,
	PaintingAcademyPanorama = function(g) if g.Glow then light(g.Glow, rgb(255, 214, 160), 1.5, 8, false, true) end end,
	StatueChoirChild = function(g) if g.Glow then light(g.Glow, rgb(255, 230, 160), 2, 14) end end,
}
local function paintingFX(g) -- batch 44's paintings: the sconce flames flicker
	if g.Glow then
		emit(g.Glow, { "flame", rgb(255, 200, 120), nil, 6, { 0.3, 0.3 }, { 0.8, 0.8 }, { 0.3, 0 }, light = 1 })
		light(g.Glow, rgb(255, 190, 110), 0.7, 7, true)
	end
end

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise, fx = {}, 0, 0, 0
local function clear(part)
	for _, o in part:GetChildren() do
		if o:IsA("SurfaceAppearance") or o:IsA("Light") or o:IsA("ParticleEmitter") then o:Destroy() end
	end
	CS:RemoveTag(part, "NHCandle") CS:RemoveTag(part, "NHSwing")
end
local function surface(part, set, roughOverride)
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	if roughOverride then s.RoughnessMap = "rbxassetid://" .. roughOverride end
	s.Parent = part
end

local function build(name, kit)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 120 then m:ScaleTo(0.01) end
	local glow = GLOW[name] or (name:match("^Painting") or name:match("^Mural")) and kit == "Showpiece" and PAINT_GLOW or {}
	local pieces = {}
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		clear(p)
		local suf = p.Name:sub(#name + 2)
		pieces[suf] = p
		local hinge = p.PivotOffset.Position
		p.PivotOffset = CFrame.new()
		if suf == "Glow" or suf == "Glow2" then
			p.Material = Enum.Material.Neon
			p.Color = glow[suf] or glow.Glow or CANDLE
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
		elseif suf == "Glass" then
			p.Material = Enum.Material.Glass
			p.Transparency = name == "DeathMaskCase" and 0.6 or 0.45
			p.Color = glow.Glass or rgb(200, 220, 255)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		elseif suf:match("^Canvas") then
			local set = name .. "Canvas"
			if name == "IconTriptych" and suf == "Canvas2" then set = "IconTriptychLCanvas" end
			if name == "IconTriptych" and suf == "Canvas3" then set = "IconTriptychRCanvas" end
			surface(p, set, kit == "Art" and CANVAS_ROUGH or nil)
		elseif suf == "Weave" then
			surface(p, name .. "Weave")
		else
			surface(p, name)
			if suf == "Cloth" then
				p:SetAttribute("SwingHinge", hinge) p:SetAttribute("SwingAxis", Vector3.new(1, 0, 0))
				p:SetAttribute("SwingAngle", 1.6) p:SetAttribute("SwingPeriod", 5.5)
				CS:AddTag(p, "NHSwing")
			end
			if suf == "Main" and FLOOR[name] and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
			end
		end
		if not FLOOR[name] then p.CanCollide = false p.CanTouch = false end
	end
	local f = FX[name] or (kit == "Showpiece" and (name:match("^Painting") or name:match("^Mural")) and paintingFX)
	if f then f(pieces) fx += 1 end
	m:SetAttribute("NHBuildKit", kit)
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	return true
end

local done, absent = 0, {}
for _, pair in { { ART, "Art" }, { SHOW, "Showpiece" } } do
	for name in pair[1]:gmatch("%S+") do
		if build(name, pair[2]) then done += 1 else table.insert(absent, name) end
	end
end
return string.format("templates %d, maps %d, precise collision %d, effects on %d\nno ids: %s\nnot imported: %s",
	done, mapsSet, precise, fx, table.concat(missing, ","), table.concat(absent, ","))
