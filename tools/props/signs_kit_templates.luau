--!nocheck
-- Props batch 50 (the misc signs kit, NHBuildKit "Signs"): turns the imported FBX models in Workspace into templates in
-- ServerStorage.NHProps, like tools/props/shop_kits_templates.luau, and installs the chooser module
-- ServerStorage.NHProps.SignKit (tools/props/signs_kit_module.luau). PK is replaced before running with
-- "Name:color,normal,rough,metal;..." (asset ids in base 36) from the group's images. Safe to run again.
--   Main and Field take the prop's four maps; the Field's SurfaceAppearance is tinted (SignKit sets its Color).
--   ExitLantern: Glow is warm Neon with a PointLight, Glass is a frosted pane (the words sit on it).
--   Nothing collides except FloorStand (a box). Each template gets the chooser attributes and a default face.
local PK = [==[PK]==]
local SIGNKIT = [==[SIGNKIT]==]

local CS = game:GetService("CollectionService")
local P = game:GetService("ServerStorage"):FindFirstChild("NHProps")
assert(P, "no ServerStorage.NHProps")

local mod = P:FindFirstChild("SignKit") or Instance.new("ModuleScript")
mod.Name = "SignKit"
mod.Source = SIGNKIT
mod.Parent = P

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

local NAMES = [[BrassPlaque EnamelPlate LintelTablet Roundel CorridorSign BracketSign ArrowBoard ArrowBoardLeft FloorStand ExitLantern WingDirectory]]
local PRESET = {
	BrassPlaque = "Mathematics", EnamelPlate = "Girls", LintelTablet = "Chemistry", Roundel = "Floor2",
	CorridorSign = "Library", BracketSign = "Infirmary", ArrowBoard = "DiningHall", ArrowBoardLeft = "Dormitories",
	FloorStand = "Quiet", ExitLantern = "WayOut", WingDirectory = "EastWing",
}
local COLLIDE = { FloorStand = true }
local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }

local missing, mapsSet, absent, done = {}, 0, {}, 0
local function surface(part, set)
	for _, o in part:GetChildren() do
		if o:IsA("SurfaceAppearance") then o:Destroy() end
	end
	local ids = IDS[set]
	if not ids then table.insert(missing, set .. "(" .. part.Name .. ")") return end
	local s = Instance.new("SurfaceAppearance")
	for i, k in KEY do
		if ids[i] then s[k] = "rbxassetid://" .. string.format("%d", ids[i]) mapsSet += 1 end
	end
	s.Parent = part
end

local function build(name)
	local m = workspace:FindFirstChild(name)
	local fresh = m ~= nil and m:IsA("Model")
	if not fresh then m = P:FindFirstChild(name) end
	if not m then return false end
	if m:GetScale() == 1 and m:GetExtentsSize().Magnitude > 60 then m:ScaleTo(0.01) end
	for _, p in m:GetDescendants() do
		if not p:IsA("MeshPart") then continue end
		p.Anchored = true
		p.PivotOffset = CFrame.new()
		for _, o in p:GetChildren() do
			if o:IsA("Light") then o:Destroy() end
		end
		local suf = p.Name:sub(#name + 2)
		if suf == "Glow" then
			p.Material = Enum.Material.Neon
			p.Color = rgb(255, 196, 120)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false p.CanQuery = false
			local L = Instance.new("PointLight")
			L.Name = "NHFX_Light" L.Color = rgb(255, 190, 120) L.Brightness = 0.8 L.Range = 9 L.Parent = p
		elseif suf == "Glass" then
			p.Material = Enum.Material.Glass
			p.Transparency = 0.35
			p.Color = rgb(255, 236, 205)
			p.CastShadow = false p.CanCollide = false p.CanTouch = false
		else
			surface(p, name)
			p.CanCollide = COLLIDE[name] == true and suf == "Main"
			p.CanTouch = p.CanCollide
			if suf == "Field" then p.CastShadow = false end
			if COLLIDE[name] and suf == "Main" then pcall(function() p.CollisionFidelity = Enum.CollisionFidelity.Box end) end
		end
	end
	m:SetAttribute("NHBuildKit", "Signs")
	m:SetAttribute("SignBase", name)
	if m:GetAttribute("Preset") == nil then m:SetAttribute("Preset", PRESET[name]) end
	for _, a in { "Icon", "Icon2", "Title", "Subtitle", "Field", "Ink", "Font" } do
		if m:GetAttribute(a) == nil then m:SetAttribute(a, "") end
	end
	if m:GetAttribute("IconRotation") == nil then m:SetAttribute("IconRotation", 0) end
	if name == "WingDirectory" then
		for i = 1, 5 do
			if m:GetAttribute("Row" .. i) == nil then m:SetAttribute("Row" .. i, "") end
		end
	end
	CS:AddTag(m, "NHSign")
	if fresh then
		local old = P:FindFirstChild(name)
		if old and old ~= m then old:Destroy() end
		m.Parent = P
	end
	return true
end

for name in NAMES:gmatch("%S+") do
	if build(name) then done += 1 else table.insert(absent, name) end
	task.wait()
end
local tmp = mod:Clone() -- a fresh copy, so an edited Source is the one that runs
tmp.Name = "SignKitRun" tmp.Parent = game:GetService("ServerStorage")
local K = require(tmp)
tmp:Destroy()
local faces = {}
for name in NAMES:gmatch("%S+") do
	local m = P:FindFirstChild(name)
	if m then
		local ok, why = K.ApplyOne(m)
		if not ok then table.insert(faces, name .. ": " .. tostring(why)) end
	end
end
return string.format("templates %d, maps %d\nno ids: %s\nnot imported: %s\nface problems: %s", done, mapsSet,
	table.concat(missing, ","), table.concat(absent, ","), table.concat(faces, "; "))
