--!nocheck
-- Props batch 47 (the witch hut kit, NHBuildKit "WitchHut"): turns the imported FBX models in Workspace into templates in
-- ServerStorage.NHProps, like tools/props/shop_kits_templates.luau. PK is replaced before running with
-- "Name:color,normal,rough,metal;..." (asset ids in base 36) from the group's images, including batch 40's shared
-- NH_GardenLeaves set. Safe to run again.
--   Main (or the prop's only piece): its own four maps.  Leaves: NH_GardenLeaves, alpha cut-out, double-sided.
--   Glow (green or violet) / Glow2 (fire and candle flames): Neon, with the lights and particles in docs/School-Props.md
--   (batch 47); flames are tagged NHCandle (Controllers.World.Ambient flickers them).  Glass: see-through in its tint.
--   HutWallDoor_Door0 swings out toward the porch on the locker system (NHLockerProp, "Door / Open").
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

local NAMES = [[HutFooting HutPost HutWall HutWallWindow HutWallDoor HutGable HutRoof HutRidge HutChimney HutPorch
WitchCauldron HerbBeamRack WitchJarShelf BroomCorner SpellLectern BoneChimes HearthKettle StrawBed WitchWorkTable
WitchHatStand CatBasket GourdPile BraidedRug SpellNoteShelf ToadstoolRing WispLanternPost]]

local NOCOLLIDE = { BraidedRug = true, ToadstoolRing = true, HerbBeamRack = true, BoneChimes = true }
-- props taller than Roblox's import cap (the whole model's height, from the FBX)
local TRUE_HEIGHT = { HutChimney = 30.09 }

local GREEN, VIOLET, FIRE, CANDLE = rgb(120, 255, 90), rgb(170, 90, 255), rgb(255, 150, 60), rgb(255, 180, 110)
local GLOW = {
	WitchCauldron = { Glow = GREEN, Glow2 = FIRE }, HearthKettle = { Glow2 = FIRE },
	SpellLectern = { Glow = VIOLET, Glow2 = FIRE }, WitchWorkTable = { Glow2 = FIRE }, WitchJarShelf = { Glow = GREEN },
	WispLanternPost = { Glow = GREEN }, ToadstoolRing = { Glow = VIOLET }, CatBasket = { Glow = rgb(190, 255, 80) },
	HutPorch = { Glow = VIOLET },
}
local GLASS = {
	HutWallWindow = { 0.4, rgb(150, 190, 140) }, WitchJarShelf = { 0.5, rgb(230, 236, 232) },
	BoneChimes = { 0.3, rgb(120, 200, 170) }, WispLanternPost = { 0.4, rgb(110, 150, 110) },
}

local TEX = {
	smoke = "rbxassetid://8527116276", ember = "rbxassetid://8114157061", star = "rbxassetid://8030760338",
	dust = "rbxassetid://7216851093",
}
-- e: { tex, colour, rate, speed {min,max}, life {min,max}, size {a,b}, trans?, spread?, light?, accel? }
local function emit(parent, e)
	local p = Instance.new("ParticleEmitter")
	p.Name = "NHFX_" .. e[1]
	p.Texture = TEX[e[1]]
	p.Color = ColorSequence.new(e[2])
	p.Rate = e[3]
	p.Speed = NumberRange.new(e[4][1], e[4][2])
	p.Lifetime = NumberRange.new(e[5][1], e[5][2])
	p.Size = NumberSequence.new(e[6][1], e[6][2])
	p.Transparency = NumberSequence.new(e.trans or 0.2, 1)
	p.SpreadAngle = Vector2.new(e.spread or 15, e.spread or 15)
	p.Rotation = NumberRange.new(0, 360)
	p.RotSpeed = NumberRange.new(-30, 30)
	p.LightEmission = e.light or 0
	p.Acceleration = e.accel or Vector3.zero
	p.EmissionDirection = Enum.NormalId.Top
	if parent:IsA("BasePart") then
		p.Shape = Enum.ParticleEmitterShape.Box
		p.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	end
	p.Parent = parent
end
local function light(parent, color, brightness, range)
	local L = Instance.new("PointLight")
	L.Name = "NHFX_Light"
	L.Color = color L.Brightness = brightness L.Range = range L.Shadows = false
	L.Parent = parent
end
-- an attachment on the prop's main piece at (right, up, forward) from the model's pivot; forward is the prop's front (-Z)
local function at(m, main, name, x, y, f)
	local a = Instance.new("Attachment")
	a.Name = "NHFX_" .. name
	a.Parent = main
	a.WorldPosition = (m:GetPivot() * CFrame.new(x, y, -f)).Position
	return a
end
local function flicker(part) CS:AddTag(part, "NHCandle") end

-- the docs' lights and particles (batch 47, "Lights for the template script" and "ParticleEmitters")
local FX = {
	WitchCauldron = function(m, g)
		light(at(m, g.Main, "Brew", 0, 3.4, 0), GREEN, 1.2, 14)
		if g.Glow2 then light(g.Glow2, FIRE, 1.5, 16) flicker(g.Glow2) end
		if g.Glow then
			emit(g.Glow, { "dust", GREEN, 6, { 1, 2 }, { 1, 1.6 }, { 0.15, 0.35 }, light = 1 })
			emit(g.Glow, { "smoke", rgb(90, 200, 80), 4, { 0.5, 1 }, { 3, 4 }, { 1, 3 }, trans = 0.7, spread = 25 })
		end
		if g.Glow2 then emit(g.Glow2, { "ember", FIRE, 12, { 2, 4 }, { 1, 2 }, { 0.08, 0.04 }, light = 1, spread = 30 }) end
		emit(at(m, g.Main, "Smoke", 0, 1.8, 0), { "smoke", rgb(60, 60, 60), 3, { 2, 2 }, { 4, 6 }, { 1, 4 }, trans = 0.8, spread = 35 })
	end,
	HearthKettle = function(m, g)
		if g.Glow2 then
			light(g.Glow2, FIRE, 1.6, 18) flicker(g.Glow2)
			emit(g.Glow2, { "ember", FIRE, 8, { 2, 4 }, { 1, 2 }, { 0.08, 0.04 }, light = 1, spread = 30 })
		end
		emit(at(m, g.Main, "Steam", 2.3, 2.6, 0.8), { "smoke", rgb(220, 220, 220), 3, { 1, 1 }, { 1.5, 1.5 }, { 0.2, 0.8 }, trans = 0.6 })
	end,
	SpellLectern = function(m, g)
		if g.Glow2 then light(g.Glow2, CANDLE, 0.8, 8) flicker(g.Glow2) end
		if g.Glow then
			light(g.Glow, VIOLET, 0.3, 5)
			emit(g.Glow, { "star", VIOLET, 2, { 0.3, 0.6 }, { 2, 3 }, { 0.06, 0.03 }, light = 1, spread = 40 })
		end
	end,
	WitchWorkTable = function(m, g) if g.Glow2 then light(g.Glow2, CANDLE, 0.7, 8) flicker(g.Glow2) end end,
	WitchJarShelf = function(m, g) if g.Glow then light(g.Glow, GREEN, 0.35, 5) end end,
	WispLanternPost = function(m, g)
		if g.Glow then
			light(g.Glow, GREEN, 1.0, 14) flicker(g.Glow)
			emit(g.Glow, { "star", GREEN, 2, { 0.3, 0.3 }, { 1.5, 1.5 }, { 0.06, 0.03 }, light = 1, spread = 180 })
		end
	end,
	ToadstoolRing = function(m, g)
		light(at(m, g.Main, "Ring", 0, 0.8, 0), VIOLET, 0.4, 8)
		if g.Glow then emit(g.Glow, { "star", VIOLET, 3, { 0.2, 0.5 }, { 3, 5 }, { 0.08, 0.04 }, light = 1, spread = 60 }) end
	end,
	HutPorch = function(m, g) if g.Glow then light(g.Glow, VIOLET, 0.2, 4) end end,
	HutChimney = function(m, g)
		-- smoke from the tall pot's mouth: the top of the chimney's bounding box, over the pot
		local cf, s = m:GetBoundingBox()
		local top = m:GetPivot():PointToObjectSpace(cf.Position + Vector3.new(0, s.Y / 2, 0))
		emit(at(m, g.Main, "Smoke", -0.14, top.Y, 1.95), { "smoke", rgb(70, 70, 72), 2, { 2, 3 }, { 6, 8 }, { 1.5, 5 },
			trans = 0.75, spread = 10, accel = Vector3.new(0.6, 0.2, 0) })
	end,
}

local function swingOut(pv, door)
	local hinge = door.CFrame * door.PivotOffset
	local best, bestZ = 100, math.huge
	for _, deg in { 100, -100 } do
		local moved = hinge * CFrame.Angles(0, math.rad(deg), 0) * hinge:Inverse() * door.CFrame
		local z = pv:PointToObjectSpace(moved.Position).Z
		if z < bestZ then best, bestZ = deg, z end
	end
	return best
end
local function rigDoor(m, door)
	local pv = m:GetPivot()
	door:SetAttribute("Door", true)
	local deg = swingOut(pv, door)
	door:SetAttribute("SwingDeg", deg)
	local spot = m:FindFirstChild("NHPropSpot") or Instance.new("Part")
	spot.Name = "NHPropSpot" spot.Size = Vector3.new(0.2, 0.2, 0.2) spot.Transparency = 1
	spot.Anchored = true spot.CanCollide = false spot.CanTouch = false spot.CanQuery = false
	local rel = pv:PointToObjectSpace(door.Position)
	spot.CFrame = pv * CFrame.new(rel.X, rel.Y, rel.Z - door.Size.Z / 2 - 1)
	spot.Parent = m
	local ph = m:FindFirstChild("Placeholder") or Instance.new("ObjectValue")
	ph.Name = "Placeholder" ph.Value = spot ph.Parent = m
	m:SetAttribute("PromptObject", "Door") m:SetAttribute("PromptOpen", "Open")
	m:SetAttribute("PromptClose", "Close") m:SetAttribute("AutoClose", 8)
	CS:AddTag(m, "NHLockerProp")
	return deg
end

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise, fx, swing = {}, 0, 0, 0, "?"
local function clear(part)
	for _, o in part:GetChildren() do
		if o:IsA("SurfaceAppearance") or o:IsA("Light") or o:IsA("ParticleEmitter") or (o:IsA("Attachment") and o.Name:match("^NHFX_")) then o:Destroy() end
	end
	CS:RemoveTag(part, "NHCandle")
end
local function surface(part, set)
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return nil end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
	return s
end

local function build(name)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	-- Roblox's importer caps a mesh at 2048 studs; at the FBX's 100x that is 20.48, so a taller prop comes in shrunk
	-- (the whole model, evenly). Scale it back to its true height (read from the FBX in Blender).
	local trueH = TRUE_HEIGHT[name]
	if trueH then
		local h = m:GetExtentsSize().Y
		if math.abs(h - trueH) > 0.05 then m:ScaleTo(m:GetScale() * trueH / h) end
	end
	local glow = GLOW[name] or {}
	local pieces, door = {}, nil
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		clear(p)
		local suf = p.Name == name and "Main" or p.Name:sub(#name + 2)
		pieces[suf] = p
		if suf ~= "Door0" then p.PivotOffset = CFrame.new() end -- the door keeps its PivotOffset: that is the hinge
		if suf == "Glow" or suf == "Glow2" then
			p.Material = Enum.Material.Neon
			p.Color = glow[suf] or (suf == "Glow2" and FIRE or GREEN)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
		elseif suf == "Glass" then
			local g = GLASS[name] or { 0.5, rgb(225, 232, 238) }
			p.Material = Enum.Material.Glass
			p.Transparency = g[1] p.Color = g[2]
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		elseif suf == "Leaves" then
			local s = surface(p, "NH_GardenLeaves")
			if s then s.AlphaMode = Enum.AlphaMode.Transparency end
			pcall(function() p.DoubleSided = true end)
			p.CanCollide = false p.CanTouch = false p.CanQuery = false
		else
			surface(p, name)
			if suf == "Door0" then
				door = p
				p.CanCollide = false p.CanTouch = false -- the locker system's doors don't collide
			elseif not NOCOLLIDE[name] and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
			end
		end
		if NOCOLLIDE[name] then p.CanCollide = false p.CanTouch = false end
	end
	if FX[name] and pieces.Main then FX[name](m, pieces) fx += 1 end
	if door then swing = tostring(rigDoor(m, door)) end
	m:SetAttribute("NHBuildKit", "WitchHut")
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	return true
end

local done, absent = 0, {}
for name in NAMES:gmatch("%S+") do
	if build(name) then done += 1 else table.insert(absent, name) end
	task.wait()
end
return string.format("templates %d, maps %d, precise collision %d, effects on %d, door swings %s\nno ids: %s\nnot imported: %s",
	done, mapsSet, precise, fx, swing, table.concat(missing, ","), table.concat(absent, ","))
