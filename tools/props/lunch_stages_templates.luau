--!nocheck
-- Props batch 56 (the lunch trays eaten in stages): turns the six imported FBX sheets in Workspace
-- (ConcessionLunchSets2/3/4, ConcessionLunchHouse2/3/4) into the eating stages. PK is replaced before running with
-- "Sheet:color,normal,rough,metal;..." (asset ids in base 36) from the group's images. Run after
-- tools/props/concession_kit_templates.luau. Safe to run again.
--   ReplicatedStorage.NHSnacks.<Id>.Stages.<N>         the stage MeshPart at the tray's 1.5x (N = 2 partly eaten, 3 mostly
--                                                      eaten, 4 empty); Services.Features.Tray welds it over the tray
--   ServerStorage.NHProps.ConcessionStages.<Id>_<N>    a Model per stage for the builder (pivot at the bottom centre, front
--                                                      -Z, tag NHPropBatch56, attributes ItemId, Stage)
--   workspace.NHPropsShowcase.Concessions.LunchStages  each meal full, partly eaten, mostly eaten and empty, on tables
-- A stage lines up with its tray by the bottom centre (both are the batch 54 tray, 1.97 x 1.45 at 1.5x); the report gives
-- each stage's size against the tray's, so a mismatch shows.
local PK = [==[PK]==]

local CS = game:GetService("CollectionService")
local RS = game:GetService("ReplicatedStorage")
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

local FAMILY = {
	ConcessionLunchSets = { "KatsuCurry", "ShoyuRamen", "KaraageSet", "MackerelSet", "Omurice" },
	ConcessionLunchHouse = { "WitchingStew", "ShepherdsPie", "PumpkinGratin", "RavensRoast" },
}
local TRAY_SCALE = 1.5       -- as batch 54 (the owner's bigger trays)
local KEY = { "ColorMap", "NormalMap", "RoughnessMap", "MetalnessMap" }
local report, worst = {}, 0

local function folder(parent, name)
	local f = parent:FindFirstChild(name)
	if not f then f = Instance.new("Folder") f.Name = name f.Parent = parent end
	return f
end
local Lib = folder(folder(SS, "NHProps"), "ConcessionStages")
local Snacks = RS:WaitForChild("NHSnacks")

for family, ids in FAMILY do
	for N = 2, 4 do
		local sheet = family .. N
		local imp = workspace:FindFirstChild(sheet)
		if not imp then table.insert(report, sheet .. ": not imported") continue end
		for _, id in ids do
			local src = imp:FindFirstChild(sheet .. "_" .. id, true)
			local snack = Snacks:FindFirstChild(id)
			local handle = snack and snack:FindFirstChild("Handle")
			if not (src and handle) then table.insert(report, sheet .. "_" .. id .. ": missing") continue end
			local p = src:Clone()
			for _, o in p:GetChildren() do o:Destroy() end
			p.Size *= 0.01 * TRAY_SCALE        -- the FBX comes in at 100x
			p.Name = tostring(N)
			p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.Massless = false, false, false, false, true
			local ids_ = IDS[sheet]
			if ids_ then
				local s = Instance.new("SurfaceAppearance")
				for i, key in KEY do if ids_[i] then s[key] = "rbxassetid://" .. string.format("%d", ids_[i]) end end
				s.Parent = p
			else
				table.insert(report, sheet .. ": no maps")
			end
			-- against the tray: the footprint should be the same
			local dx, dz = p.Size.X - handle.Size.X, p.Size.Z - handle.Size.Z
			worst = math.max(worst, math.abs(dx), math.abs(dz))
			-- a stage whose cutlery was moved off an overhang (the mackerel's chopsticks stick out past the tray's front, -Z,
			-- until they're laid on the plate) is that much narrower: NHAlign puts its tray back under the full one's
			local align = Vector3.zero
			if math.abs(dx) > 0.01 or math.abs(dz) > 0.01 then
				align = Vector3.new(if math.abs(dx) > 0.01 then -dx / 2 else 0, 0, if math.abs(dz) > 0.01 then -dz / 2 else 0)
				table.insert(report, string.format("%s stage %d: footprint off by %.3f x %.3f, NHAlign %s", id, N, dx, dz, tostring(align)))
			end
			p:SetAttribute("NHAlign", align)
			local stages = snack:FindFirstChild("Stages") or Instance.new("Folder")
			stages.Name = "Stages"
			stages.Parent = snack
			local old = stages:FindFirstChild(tostring(N))
			if old then old:Destroy() end
			p.CFrame = handle.CFrame * CFrame.new(align + Vector3.new(0, (p.Size.Y - handle.Size.Y) / 2, 0))
			p.Parent = stages
			-- the builder's copy, standing like ConcessionItems.<Id>
			local item = SS.NHProps.ConcessionItems:FindFirstChild(id)
			local m = Instance.new("Model")
			m.Name = id .. "_" .. N
			local a = p:Clone()
			a.Name = id .. "_" .. N
			a.Anchored, a.CanQuery = true, true
			a.Parent = m
			if item and item.PrimaryPart then
				local full = item.PrimaryPart
				a.CFrame = full.CFrame * CFrame.new(align + Vector3.new(0, (a.Size.Y - full.Size.Y) / 2, 0))
				a.PivotOffset = a.CFrame:ToObjectSpace(full:GetPivot())
				local glass = item:FindFirstChild(id .. "_Glass")
				if glass then local g = glass:Clone() g.Parent = m end
			end
			m.PrimaryPart = a
			m:SetAttribute("ItemId", id)
			m:SetAttribute("Stage", N)
			m:SetAttribute("NHBuildKit", "Concession")
			CS:AddTag(m, "NHPropBatch56")
			local oldm = Lib:FindFirstChild(m.Name)
			if oldm then oldm:Destroy() end
			m.Parent = Lib
		end
	end
end

-- the showcase: a table per meal, full to empty along X (west of the lunch tables, clear of the return hatch)
local Con = workspace:FindFirstChild("NHPropsShowcase") and workspace.NHPropsShowcase:FindFirstChild("Concessions")
if Con then
	local old = Con:FindFirstChild("LunchStages")
	if old then old:Destroy() end
	local F = Instance.new("Folder")
	F.Name = "LunchStages"
	CS:AddTag(F, "NHPropBatch56")
	local FLOOR, H = 0.9, 2.6
	local SLATE, IRON = Color3.fromRGB(38, 40, 44), Color3.fromRGB(28, 26, 30)
	local function part(parent, size, cf, color, mat)
		local q = Instance.new("Part")
		q.Anchored, q.Size, q.CFrame, q.Color, q.Material = true, size, cf, color, mat
		q.TopSurface, q.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		q.Parent = parent
	end
	local order = { "KatsuCurry", "ShoyuRamen", "KaraageSet", "MackerelSet", "Omurice", "WitchingStew", "ShepherdsPie", "PumpkinGratin",
		"RavensRoast" }
	local X0, Z0, DZ, DX = 155.0, 199.0, 2.3, 2.3
	for r, id in order do
		local z = Z0 + (r - 1) * DZ
		local t = Instance.new("Model")
		t.Name = "StageTable" .. r
		local x1 = X0 + 4 * DX
		part(t, Vector3.new(x1 - X0 + 0.2, 0.16, 1.9), CFrame.new((X0 + x1) / 2 - DX / 2, FLOOR + H - 0.08, z), SLATE, Enum.Material.Slate)
		for _, sx in { X0 - DX / 2 + 0.1, x1 - DX / 2 - 0.1 } do
			part(t, Vector3.new(0.18, H - 0.16, 1.5), CFrame.new(sx, FLOOR + (H - 0.16) / 2, z), IRON, Enum.Material.Metal)
		end
		t.Parent = F
		for k = 1, 4 do
			local src = if k == 1 then SS.NHProps.ConcessionItems:FindFirstChild(id) else Lib:FindFirstChild(id .. "_" .. k)
			if src then
				local m = src:Clone()
				m:PivotTo(CFrame.new(X0 + (k - 1) * DX, FLOOR + H, z))
				m.Parent = F
			end
		end
	end
	F.Parent = Con
end
table.insert(report, 1, string.format("worst footprint difference %.4f", worst))
return table.concat(report, "\n")
