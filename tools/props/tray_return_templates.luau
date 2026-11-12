--!nocheck
-- Props batch 55 (the lunch tray return): turns the two imported FBX sheets in Workspace (TrayTrolley, TrayReturnHatch) into
-- templates, and stages one of each by the batch 54 lunch tables. PK is replaced before running with
-- "Sheet:color,normal,rough,metal;..." (asset ids in base 36) from the group's images. Safe to run again.
--   ServerStorage.NHProps.TrayReturn.<Sheet>   a Model (pivot at the bottom centre, its front -Z), tag NHPropBatch55; its
--                                              MeshPart is tagged NHTrayReturn (Services.Features.Tray gives it the
--                                              "Return tray" prompt) and holds the slot Attachments
--   workspace.NHPropsShowcase.Concessions.TrayReturn   one trolley and one hatch, next to the lunch tables
-- Slots (from art/props/nh_props_batch55.py SLOTS, Blender space, z up, front -Y): an Attachment SlotN at a tray's bottom
-- centre, its X along the tray's long side; the hatch's SlotNInto is where its conveyor takes the tray.
local PK = [==[PK]==]

local CS = game:GetService("CollectionService")
local SS = game:GetService("ServerStorage")

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

-- each sheet's bounding box in Blender (lo, hi) and its slots; the trolley's probe (a push-bar grip, on the mesh one way
-- round and in thin air the other) tells which way the importer turned the FBX, the same for both
local SHEETS = {
	TrayTrolley = {
		lo = Vector3.new(-1.9125, -1.215, 0.0), hi = Vector3.new(1.9125, 1.4945, 5.398),
		probe = Vector3.new(1.1, 1.43, 4.14),            -- a brass grip on the push bar (behind the top's edge)
		long = "Y",
		slots = {}, into = {},
	},
	TrayReturnHatch = {
		lo = Vector3.new(-3.35, -0.91, 0.0), hi = Vector3.new(3.35, 2.4, 8.546),
		long = "X",
		slots = { Vector3.new(-1.05, -0.1, 2.81), Vector3.new(1.05, -0.1, 2.81) },
		into = { Vector3.new(-1.05, 1.6, 2.81), Vector3.new(1.05, 1.6, 2.81) },
	},
}
for _, z in { 0.78, 1.56, 2.34, 3.12, 3.9 } do
	for _, x in { -0.89, 0.89 } do
		table.insert(SHEETS.TrayTrolley.slots, Vector3.new(x, 0, z))
	end
end

local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local report = {}

local function folder(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder") f.Name = name f.Parent = parent end
	return f
end
local Props = folder(SS, "NHProps")
local Lib = folder(Props, "TrayReturn")

-- Blender (x, y, z) to the part's space, either way round the importer may have put it: A keeps x (front to +Z), B turns
-- it round (front to -Z)
local function toLocal(v, c, way)
	local d = v - c
	if way == "A" then return Vector3.new(d.X, d.Z, -d.Y) end
	return Vector3.new(-d.X, d.Z, d.Y)
end

local way
for _, sheet in { "TrayTrolley", "TrayReturnHatch" } do
	local S = SHEETS[sheet]
	local imp = workspace:FindFirstChild(sheet)
	local mesh = imp and (imp:IsA("MeshPart") and imp or imp:FindFirstChildWhichIsA("MeshPart", true))
	if not mesh then
		table.insert(report, sheet .. ": not imported")
		continue
	end
	local m = Instance.new("Model")
	m.Name = sheet
	mesh = mesh:Clone()
	mesh.Name = sheet
	for _, o in mesh:GetChildren() do o:Destroy() end
	mesh.Parent = m
	-- the FBX comes in at 100x
	local want = S.hi - S.lo
	local k = want.Z / mesh.Size.Y
	if math.abs(k - 1) > 0.02 then mesh.Size *= k end
	mesh.Anchored, mesh.CanTouch = true, false
	mesh.CanCollide, mesh.CanQuery = true, true
	pcall(function() mesh.CollisionFidelity = Enum.CollisionFidelity.Box end)
	local ids = IDS[sheet]
	if ids then
		local s = Instance.new("SurfaceAppearance")
		for i, key in KEY do if ids[i] then s[key] = "rbxassetid://" .. string.format("%d", ids[i]) end end
		s.Parent = mesh
	end
	-- which way round: the probe point is on the mesh one way and in thin air the other (a ray down onto it)
	m.Parent = workspace
	mesh.CFrame = CFrame.new(0, 2000, 0) * mesh.CFrame.Rotation
	local c = (S.lo + S.hi) / 2
	local P = RaycastParams.new()
	P.FilterType = Enum.RaycastFilterType.Include
	P.FilterDescendantsInstances = { mesh }
	if S.probe then
		local hits = {}
		for _, w in { "A", "B" } do
			local at = mesh.CFrame * toLocal(S.probe, c, w)
			hits[w] = workspace:Raycast(at + Vector3.new(0, 0.25, 0), Vector3.new(0, -0.5, 0), P) ~= nil
		end
		way = if hits.A and not hits.B then "A" elseif hits.B and not hits.A then "B" else nil
		table.insert(report, string.format("probe A %s B %s", tostring(hits.A), tostring(hits.B)))
	end
	way = way or "B"
	-- the slots
	for i, v in S.slots do
		local a = Instance.new("Attachment")
		a.Name = "Slot" .. i
		local turn = if (S.long == "Y") then CFrame.Angles(0, math.rad(90), 0) else CFrame.identity
		a.CFrame = CFrame.new(toLocal(v, c, way)) * turn
		a.Parent = mesh
		if S.into[i] then
			local b = Instance.new("Attachment")
			b.Name = "Slot" .. i .. "Into"
			b.CFrame = CFrame.new(toLocal(S.into[i], c, way)) * turn
			b.Parent = mesh
		end
	end
	-- the pivot: the bottom centre (Blender x = y = 0, z = 0), its -Z the front
	local base = toLocal(Vector3.new(0, 0, 0), c, way)
	mesh.PivotOffset = CFrame.new(base) * (if way == "A" then CFrame.Angles(0, math.pi, 0) else CFrame.identity)
	m.PrimaryPart = mesh
	m:PivotTo(CFrame.new())
	CS:AddTag(mesh, "NHTrayReturn")
	CS:AddTag(m, "NHPropBatch55")
	m:SetAttribute("NHBuildKit", "TrayReturn")
	local old = Lib:FindFirstChild(sheet)
	if old then old:Destroy() end
	m.Parent = Lib
	table.insert(report, string.format("%s: way %s, size %s, %d slots", sheet, way, tostring(mesh.Size), #S.slots))
end

-- stage one of each by the lunch tables (batch 54: tables at x 186-197.6, z 197-203.4; floor top 0.9)
local Show = workspace:FindFirstChild("NHPropsShowcase")
local Con = Show and Show:FindFirstChild("Concessions")
if Con then
	local old = Con:FindFirstChild("TrayReturn")
	if old then old:Destroy() end
	local F = Instance.new("Folder")
	F.Name = "TrayReturn"
	CS:AddTag(F, "NHPropBatch55")
	local function put(sheet, cf)
		local t = Lib:FindFirstChild(sheet)
		if not t then return end
		local m = t:Clone()
		m:PivotTo(cf)
		m.Parent = F
	end
	-- the trolley at the west end of the lunch tables, front toward the tables (+X); the hatch beyond it, facing them too
	put("TrayTrolley", CFrame.new(183.2, 0.9, 200.2) * CFrame.Angles(0, math.rad(-90), 0))
	put("TrayReturnHatch", CFrame.new(178.6, 0.9, 200.2) * CFrame.Angles(0, math.rad(-90), 0))
	F.Parent = Con
end
return table.concat(report, "\n")
