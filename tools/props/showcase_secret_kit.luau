--!nocheck
-- Lines up the secret passages kit (batch 53) in workspace.NHPropsShowcase like the other kits: two rows in front of dark
-- slate backing walls, props facing south (+Z), from x -235, south of the Witch Hut (its slab ends at z -965):
-- "Secret Doors and Vents" at z -1050 and "Secret Tunnels" at z -1090 (the Signs showcase
-- stands at z -986 to -1013), on their own floor slab (ShowcaseFloorSecret, in the
-- first folder). The kit's pivots are at ground level and the floor vent, the trapdoor and the stage's pit go below it, so
-- every prop stands on its pivot (not its bounding box); wall pieces sit on the wall with their bottoms at the docs' heights.
-- Run again to rebuild.
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

local DOORS = [[SconceLever LooseBrick TiltingBust BookcaseSecretDoor SlidingWallPanel TapestryPassage FireplacePassage BoardedPassage
VentWallLow VentWallHigh VentFloor TrapdoorLadder StageCrawlspace]]
-- wall pieces: bottom height on the wall (0 = it stands on the floor against the wall)
local DOOR_WALL = { SconceLever = 4.0, LooseBrick = 0, BookcaseSecretDoor = 0, SlidingWallPanel = 0, TapestryPassage = 0,
	FireplacePassage = 0, BoardedPassage = 0, VentWallLow = 0, VentWallHigh = 0 }
local TUNNELS = [[TunnelStraight TunnelCurve TunnelJunction TunnelSteps TunnelDeadEnd SecretSpiralStair DuctStraight DuctCorner
DuctTee DuctRiser DuctEndCap DuctDamaged VentCeiling]]

local out = {
	row("Secret Doors and Vents", -1050, DOORS, DOOR_WALL, 20),
	row("Secret Tunnels", -1090, TUNNELS, {}, 28),
}
-- the floor south of the Witch Hut's slab (z -965), under the Signs showcase and both rows
local F = SC:FindFirstChild("Secret Doors and Vents")
local north, south = -965, -1112
part("ShowcaseFloorSecret", Vector3.new(300, 2, north - south), CFrame.new(-245 + 150, FLOOR - 1, (north + south) / 2), F,
	Enum.Material.Plaster, Color3.new(0.357, 0.357, 0.357))
return table.concat(out, "\n")
