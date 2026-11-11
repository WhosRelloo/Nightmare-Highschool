--!nocheck
-- Lines up the school gate kit (batch 51) in workspace.NHPropsShowcase like the other kits: two rows in front of dark slate
-- backing walls, props facing south (+Z), from x -235, south of the Secret Tunnels row (z -1090): "Gates" at z -1130 and
-- "Gate Runs" (railings, walls, piers, hedges and the sneak gaps) at z -1170, on their own floor slab (ShowcaseFloorGates,
-- in the Gates folder). Every prop stands on its ground pivot. Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR, X0, GAP = 0.9, -235, 3
local TURN = CFrame.Angles(0, math.pi, 0)

local function part(name, size, cf, parent, mat, col)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = mat or Enum.Material.Slate
	w.Color = col or Color3.new(0.224, 0.22, 0.224)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local function row(folderName, ZB, order, WALL, wallH)
	local old = SC:FindFirstChild(folderName)
	if old then old:Destroy() end
	local F = Instance.new("Folder") F.Name = folderName
	local face = ZB + 0.5
	local x, n, missing = X0, 0, {}
	for name in order:gmatch("%S+") do
		local t = P:FindFirstChild(name)
		if not t then table.insert(missing, name) continue end
		local c = t:Clone()
		c:SetAttribute("NHBuildKit", nil)
		c.Name = name .. "_Showcase"
		-- stand it on its pivot, turned to face +Z, then shift it so its box starts at x and its back clears the wall
		c:PivotTo(CFrame.new(0, FLOOR + (WALL[name] or 0), 0) * TURN)
		local cf, s = c:GetBoundingBox()
		local lo = cf.Position - s / 2
		c:PivotTo(c:GetPivot() + Vector3.new(x - lo.X, 0, (WALL[name] and face or face + 0.6) - lo.Z))
		c.Parent = F
		x += s.X + GAP
		n += 1
	end
	local len = x - X0 + 2
	part(folderName:gsub(" ", "") .. "Wall", Vector3.new(len, wallH, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + wallH / 2, ZB), F)
	F.Parent = SC
	return string.format("%s: %d props, x %.0f..%.0f, wall z %d%s", folderName, n, X0, x, ZB,
		#missing > 0 and ("; no template: " .. table.concat(missing, ",")) or "")
end

local GATES = [[GateGrand GatePedestrian GateWicket GatehouseArch GateLych GateService GateChained GateBroken GateMoon
GatePierLantern]]
local RUNS = [[RailingEnd Railing8 RailingPost RailingCorner RailingGatePier SneakBentBars SneakMissingBars SneakLooseBars
StoneWallPier StoneWall8 SneakWallHole SneakCulvert BrickWallPier BrickWallIron HedgeRailing SneakHedgeGap]]

local out = {
	row("Gates", -1130, GATES, {}, 22),
	row("Gate Runs", -1170, RUNS, {}, 15),
}
-- the floor south of ShowcaseFloorSecret (z -1112)
local F = SC:FindFirstChild("Gates")
local north, south = -1112, -1192
part("ShowcaseFloorGates", Vector3.new(300, 2, north - south), CFrame.new(-245 + 150, FLOOR - 1, (north + south) / 2), F,
	Enum.Material.Plaster, Color3.new(0.357, 0.357, 0.357))
return table.concat(out, "\n")
