--!nocheck
-- Props batch 53 (the secret passages kit, NHBuildKit "Secret"): turns the imported FBX models in Workspace into templates
-- in ServerStorage.NHProps, like tools/props/witchhut_templates.luau. PK is replaced before running with
-- "Name:color,normal,rough,metal;..." (asset ids in base 36) from the group's images, including the shared tiled sets
-- NH_CastleStone (the *_Wall shells) and NH_MossyPaving (the tunnels' *_Floor; in the group as "MossyPaving_*").
-- Safe to run again.
--   Glow: candle-amber Neon with its PointLight, tagged NHCandle (Controllers.World.Ambient flickers it).
--   Every grate, door, hatch, slide, lever and bust runs on the door kit system (tag NHDoor; Services.Features.Doors makes
--   the prompt on the DoorPrompt attachment, Controllers.World.Doors moves the leaves): its leaves collide while shut and stop
--   colliding while open. Hinges come from art/props/secret_batch53.json (Blender x, y, z -> Roblox x, z, y), and each
--   leaf's swing sign is picked so it opens the way the kit means (outward, up, down). The boards of BoardedPassage stay put
--   (tag NHBoard, each with its fall-away SlideBy) until the board-prying gameplay is designed.
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
local AMBER = rgb(255, 170, 90)

local NAMES = [[VentWallLow VentWallHigh VentCeiling VentFloor DuctStraight DuctCorner DuctTee DuctRiser DuctEndCap DuctDamaged
BookcaseSecretDoor FireplacePassage TapestryPassage SlidingWallPanel TrapdoorLadder SecretSpiralStair TunnelStraight TunnelCurve
TunnelJunction TunnelSteps TunnelDeadEnd StageCrawlspace BoardedPassage SconceLever LooseBrick TiltingBust]]

-- the docs' lights: { brightness, range }
local LIGHT = {
	TunnelStraight = { 1.2, 18 }, TunnelCurve = { 0.8, 12 }, SecretSpiralStair = { 0.8, 12 }, SconceLever = { 0.6, 10 },
}

-- the openings (secret_batch53.json, in Blender coordinates). kind: swing (about world up), hatch (about axis), slide.
-- want: where the leaf's middle should end up from where it starts (model space): F front (-Z), U up, D down.
local FRONT, UP, DOWN = Vector3.new(0, 0, -1), Vector3.new(0, 1, 0), Vector3.new(0, -1, 0)
local RIG = {
	VentWallLow = { obj = "Vent", leaves = { Grate0 = { "slide", { 0, -0.32, 0.18 }, nil, { 0, -1.4, -0.18 } } } },
	VentWallHigh = { obj = "Vent", leaves = { Grate0 = { "swing", { -3, -0.43, 0 }, nil, nil, 110, FRONT } } },
	VentCeiling = { obj = "Vent", leaves = { Grate0 = { "hatch", { 0, -3.82, -0.36 }, { 1, 0, 0 }, nil, 100, DOWN } } },
	VentFloor = { obj = "Vent", leaves = { Grate0 = { "slide", { 0, 0, -0.27 }, nil, { 0, -6.4, 0.27 } } } },
	DuctEndCap = { obj = "Hatch", leaves = { Door0 = { "hatch", { 0, 1.52, 4.06 }, { 1, 0, 0 }, nil, 95, FRONT } } },
	BookcaseSecretDoor = { obj = "Bookcase", leaves = { Door0 = { "swing", { 1.98, -0.6, 0.02 }, nil, nil, 80, FRONT } } },
	TapestryPassage = { obj = "Tapestry", leaves = { Cloth0 = { "hatch", { 0, -1.05, 9.1 }, { 1, 0, 0 }, nil, 55, FRONT } } },
	SlidingWallPanel = { obj = "Panel", leaves = {
		Boss0 = { "slide", { -4.1, -0.82, 4.3 }, nil, { 0, 0.1, 0 } },
		Slide0 = { "slide", { 0, -0.5, 0.06 }, nil, { 4.1, 0, 0 } },
	} },
	TrapdoorLadder = { obj = "Trapdoor", leaves = { Door0 = { "hatch", { 0, 2.72, 0 }, { 1, 0, 0 }, nil, 100, UP } } },
	TunnelDeadEnd = { obj = "Gate", leaves = { Grate0 = { "swing", { -2.8, 3.28, 0.05 }, nil, nil, 100, FRONT } } },
	StageCrawlspace = { obj = "Hatch", leaves = { Door0 = { "hatch", { -2.8, 0.9, 3.2 }, { 0, 1, 0 }, nil, 100, UP } } },
	SconceLever = { obj = "Sconce", leaves = {
		Lever0 = { "hatch", { 0, -0.1, 0.8 }, { 1, 0, 0 }, nil, 35, DOWN },
		Lever0Glow = { "hatch", { 0, -0.1, 0.8 }, { 1, 0, 0 }, nil, 35, DOWN },
	} },
	LooseBrick = { obj = "Brick", leaves = { Brick0 = { "slide", { 0, -0.23, 1.775 }, nil, { 0, 0.45, 0 } } } },
	TiltingBust = { obj = "Bust", leaves = { Bust0 = { "hatch", { 0, 0.55, 3.62 }, { 1, 0, 0 }, nil, 22, FRONT } } },
	FireplacePassage = { obj = "Fireplace", leaves = { Slide0 = { "slide", { 0, 2, 0 }, nil, { 0, 0, -6.3 } } } },
}
local BOARD_SLIDE = { 0, -1.5, -0.5 }
local function rb(v) return Vector3.new(v[1], v[3], v[2]) end -- Blender (x, y, z) -> Roblox model space (x, z, y)

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local missing, mapsSet, precise, rigs = {}, 0, 0, {}
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

-- where a leaf's middle goes when it opens (as Controllers.World.Doors does it, OpenDir = 1)
local function openMid(part, kind, swing, axisPart, slidePart)
	local hinge = (part.CFrame * part.PivotOffset).Position
	if kind == "slide" then return part.Position + part.CFrame:VectorToWorldSpace(slidePart) end
	local axis = kind == "hatch" and part.CFrame:VectorToWorldSpace(axisPart).Unit or Vector3.yAxis
	local rot = CFrame.new(hinge) * CFrame.fromAxisAngle(axis, math.rad(swing)) * CFrame.new(-hinge)
	return (rot * part.CFrame).Position
end

local function rig(m, spec)
	local pv = m:GetPivot()
	local first
	for suf, l in spec.leaves do
		local part = m:FindFirstChild(m.Name .. "_" .. suf)
		if not part then table.insert(missing, "leaf " .. m.Name .. "_" .. suf) continue end
		local kind, hingeB, axisB, slideB, deg, want = l[1], l[2], l[3], l[4], l[5], l[6]
		local hingeW = pv:PointToWorldSpace(rb(hingeB))
		part.PivotOffset = CFrame.new(part.CFrame:PointToObjectSpace(hingeW))
		part:SetAttribute("DoorLeaf", true)
		part:SetAttribute("DoorKind", kind)
		part:SetAttribute("SwingTime", kind == "slide" and 1.1 or 0.9)
		local axisPart, slidePart
		if axisB then axisPart = part.CFrame:VectorToObjectSpace(pv:VectorToWorldSpace(rb(axisB))) part:SetAttribute("DoorAxis", axisPart) end
		if slideB then slidePart = part.CFrame:VectorToObjectSpace(pv:VectorToWorldSpace(rb(slideB))) part:SetAttribute("SlideBy", slidePart) end
		local sign = 1
		if kind ~= "slide" then
			local wantW = pv:VectorToWorldSpace(want)
			local a = (openMid(part, kind, deg, axisPart) - part.Position):Dot(wantW)
			local b = (openMid(part, kind, -deg, axisPart) - part.Position):Dot(wantW)
			sign = a >= b and 1 or -1
			part:SetAttribute("SwingDeg", deg * sign)
		end
		table.insert(rigs, string.format("%s_%s %s %s", m.Name, suf, kind, kind == "slide" and tostring(slidePart) or tostring(deg * sign)))
		first = first or part
	end
	if not first then return end
	local cf, size = m:GetBoundingBox()
	m:SetAttribute("PromptObject", spec.obj)
	m:SetAttribute("OneWay", true)
	m:SetAttribute("AutoClose", 8)
	m:SetAttribute("DoorwaySize", Vector3.new(size.X, size.Y, math.max(4, size.Z)))
	local at = m:FindFirstChild("DoorPrompt", true) or Instance.new("Attachment")
	at.Name = "DoorPrompt"
	at.Parent = first.Name:match("Glow$") and m:FindFirstChildWhichIsA("MeshPart") or first
	at.WorldPosition = first.Position + pv:VectorToWorldSpace(FRONT) * 1.2
	CS:AddTag(m, "NHDoor")
end

local function build(name)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	local spec = RIG[name]
	for _, p in m:GetChildren() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		clear(p)
		local suf = p.Name == name and "Main" or p.Name:sub(#name + 2)
		local leaf = spec and spec.leaves[suf] ~= nil
		if not leaf and not suf:match("^Board%d") then p.PivotOffset = CFrame.new() end
		if suf:match("Glow$") then
			p.Material = Enum.Material.Neon p.Color = AMBER
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
			local l = LIGHT[name]
			if l then
				local L = Instance.new("PointLight") L.Name = "NHFX_Light" L.Color = AMBER
				L.Brightness = l[1] L.Range = l[2] L.Shadows = false L.Parent = p
				CS:AddTag(p, "NHCandle")
			end
		elseif suf:match("Wall$") then
			surface(p, "NH_CastleStone")
		elseif suf == "Floor" then
			surface(p, "NH_MossyPaving")
		else
			surface(p, name)
		end
		if suf:match("^Board%d") then
			CS:AddTag(p, "NHBoard")
			p:SetAttribute("SlideBy", p.CFrame:VectorToObjectSpace(m:GetPivot():VectorToWorldSpace(rb(BOARD_SLIDE))))
		end
		-- collisions: the passage pieces precisely; the tapestry cloth, the sconce and the glows don't collide
		local noCollide = suf:match("Glow$") or suf == "Cloth0" or name == "SconceLever"
		if noCollide then
			p.CanCollide = false p.CanTouch = false
		elseif not leaf and not suf:match("^Board%d") and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
			if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
		end
	end
	if spec then rig(m, spec) end
	m:SetAttribute("NHBuildKit", "Secret")
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
return string.format("templates %d, maps %d, precise collision %d\nrigs: %s\nno ids: %s\nnot imported: %s",
	done, mapsSet, precise, table.concat(rigs, "; "), table.concat(missing, ","), table.concat(absent, ","))
