--!nocheck
-- Props batch 51 (the school gate kit, NHBuildKit "Gates"): turns the imported FBX models in Workspace into templates in
-- ServerStorage.NHProps, like tools/props/secret_kit_templates.luau. PK is replaced before running with
-- "Name:color,normal,rough,metal;..." (asset ids in base 36) from the group's images, including batch 40's shared
-- NH_GardenLeaves set. Safe to run again.
--   Main: its own maps, precise collision.  Leaves: NH_GardenLeaves, alpha cut-out, double-sided, no collision.
--   Glow: the lantern flames, candle-amber Neon with a PointLight (shadows on), tagged NHCandle.  Glass: warm lantern panes.
--   Gate leaves and the wicket door run on the door kit system (tag NHDoor, OneWay, swinging OUT to the front, AutoClose 8;
--   prompts "Gate" / "Door"): they collide while shut and stop colliding while open. Hinges come from
--   art/props/gates_batch51.json (Blender x, y, z -> Roblox -x, z, y). GateChained starts Locked (its Chain comes off later).
--   The portcullis stays raised (tag NHPortcullis with its SlideBy, for the winch lever), and the boards and loose bars stay
--   in place (tags NHBoard / NHLooseBar), until that gameplay is designed.
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

local NAMES = [[GateGrand GatePedestrian GateWicket GatehouseArch GateLych GateService GateChained GateBroken GateMoon
GatePierLantern Railing8 RailingPost RailingCorner RailingEnd RailingGatePier StoneWall8 StoneWallPier BrickWallIron
BrickWallPier HedgeRailing SneakBentBars SneakMissingBars SneakWallHole SneakCulvert SneakHedgeGap SneakLooseBars]]

-- gates_batch51.json (Blender coordinates): { hinge }
local LEAVES = {
	GateGrand = { Leaf0 = { -6.33, 0, 0.25 }, Leaf1 = { 6.33, 0, 0.25 } },
	GatePedestrian = { Leaf0 = { -2.78, 0, 0.25 } },
	GateWicket = { Door0 = { -1.75, -0.64, 0.12 } },
	GateService = { Leaf0 = { -6.53, 0, 0.25 }, Leaf1 = { 6.53, 0, 0.25 } },
	GateChained = { Leaf0 = { -2.88, 0, 0.25 }, Leaf1 = { 2.88, 0, 0.25 } },
	GateBroken = { Leaf0 = { -2.83, 0, 0.25 } },
	GateMoon = { Leaf0 = { -4.12, -1.02, 0.15 }, Leaf1 = { 4.12, -1.02, 0.15 } },
	GateLych = { Leaf0 = { -3.055, -2.7, 0.2 }, Leaf1 = { 3.055, -2.7, 0.2 } },
}
local SWING = 90
local PORTCULLIS_SLIDE = { 0, 0, -9.0 }
local function rb(v) return Vector3.new(-v[1], v[3], v[2]) end -- Blender (x, y, z) -> Roblox model space (-x, z, y): the front (Blender -Y) is Roblox -Z, so X mirrors

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
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return nil end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
	return s
end

-- the swing sign that sends a leaf's middle toward the front (-Z of the model), as Controllers.World.Doors turns it
local function frontSign(pv, part)
	local hinge = (part.CFrame * part.PivotOffset).Position
	local function mid(deg)
		return ((CFrame.new(hinge) * CFrame.fromAxisAngle(Vector3.yAxis, math.rad(deg)) * CFrame.new(-hinge)) * part.CFrame).Position
	end
	local front = pv.LookVector -- the model's -Z
	return (mid(SWING) - part.Position):Dot(front) >= (mid(-SWING) - part.Position):Dot(front) and 1 or -1
end

local function rig(m, spec)
	local pv = m:GetPivot()
	local first
	for suf, hingeB in spec do
		local part = m:FindFirstChild(m.Name .. "_" .. suf)
		if not part then table.insert(missing, "leaf " .. m.Name .. "_" .. suf) continue end
		part.PivotOffset = CFrame.new(part.CFrame:PointToObjectSpace(pv:PointToWorldSpace(rb(hingeB))))
		part:SetAttribute("DoorLeaf", true)
		part:SetAttribute("DoorKind", "swing")
		part:SetAttribute("SwingTime", 1.1)
		local deg = SWING * frontSign(pv, part)
		part:SetAttribute("SwingDeg", deg)
		table.insert(rigs, m.Name .. "_" .. suf .. " " .. deg)
		first = first or part
	end
	local cf, size = m:GetBoundingBox()
	m:SetAttribute("PromptObject", m.Name == "GateWicket" and "Door" or "Gate")
	m:SetAttribute("OneWay", true)
	m:SetAttribute("AutoClose", 8)
	m:SetAttribute("DoorwaySize", Vector3.new(size.X, size.Y, math.max(4, size.Z)))
	if m.Name == "GateChained" then m:SetAttribute("Locked", true) end
	local at = m:FindFirstChild("DoorPrompt", true) or Instance.new("Attachment")
	at.Name = "DoorPrompt"
	at.Parent = m:FindFirstChild(m.Name .. "_Main") or first
	at.WorldPosition = pv.Position + Vector3.new(0, 4, 0) + pv.LookVector * 1.5
	CS:AddTag(m, "NHDoor")
end

local function build(name)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	local spec = LEAVES[name]
	local pv = m:GetPivot()
	for _, p in m:GetChildren() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		clear(p)
		local suf = p.Name == name and "Main" or p.Name:sub(#name + 2)
		local leaf = spec and spec[suf] ~= nil
		if not leaf then p.PivotOffset = CFrame.new() end
		if suf == "Glow" then
			p.Material = Enum.Material.Neon p.Color = AMBER
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
			local L = Instance.new("PointLight") L.Name = "NHFX_Light" L.Color = AMBER
			L.Brightness = 1.2 L.Range = name == "GatePierLantern" and 18 or 14 L.Shadows = true L.Parent = p
			CS:AddTag(p, "NHCandle")
		elseif suf == "Glass" then
			p.Material = Enum.Material.Glass p.Transparency = 0.55 p.Color = rgb(220, 205, 170)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		elseif suf == "Leaves" then
			local s = surface(p, "NH_GardenLeaves")
			if s then s.AlphaMode = Enum.AlphaMode.Transparency end
			pcall(function() p.DoubleSided = true end)
			p.CanCollide = false p.CanTouch = false p.CanQuery = false
		else
			surface(p, name)
			if suf:match("^Board%d") then
				CS:AddTag(p, "NHBoard")
			elseif suf:match("^Bar%d") then
				CS:AddTag(p, "NHLooseBar")
			elseif suf == "Portcullis" then
				CS:AddTag(p, "NHPortcullis")
				p:SetAttribute("SlideBy", p.CFrame:VectorToObjectSpace(pv:VectorToWorldSpace(rb(PORTCULLIS_SLIDE))))
			elseif suf == "Chain" then
				CS:AddTag(p, "NHGateChain")
			elseif not leaf and p.CollisionFidelity ~= Enum.CollisionFidelity.PreciseConvexDecomposition then
				if pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.PreciseConvexDecomposition end) then precise += 1 end
			end
		end
	end
	if spec then rig(m, spec) end
	m:SetAttribute("NHBuildKit", "Gates")
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
