--!nocheck
-- Lines up the gym kit (batch 43) in workspace.NHPropsShowcase.Gym like the kits in showcase_kits_34_39.luau: one row
-- in front of a dark slate backing wall, props facing south (+Z), at z -466 (the next slot south of the Dorm House row,
-- from x -236). Wall pieces stand or hang on the wall (their pivot is on their back face) at the heights in the docs;
-- the climbing ropes and rings stand on the floor by their pivot (their own beam is at 22.4 / 21.3) with two iron posts
-- under each beam; the gloves and megaphone sit on slate plinths. Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR, X0, GAP, ZB = 0.9, -236, 2.5, -466
local PLINTH_TOP = 3.4
local WALL = { WallBars = 0, WallPulley = 0, LockerBench = 0, SaunaDoor = 0, FirstAidStation = 0, BasketballHoop = 0,
	PunchingBag = 0, IndianClubRack = 3.0, FencingMaskRack = 3.2, WhistleBoard = 3.0, HousePointsBoard = 3.2 }
local HANG = { ClimbingRopes = true, GymRings = true } -- pivot at the floor, under their own beam
local PLINTH = { BoxingGloves = true, Megaphone = true }
local ORDER = [[PommelHorse ParallelBars BalanceBeam VaultingBox Springboard HighJumpStands MatTrolley MedicineBallRack
RowingMachine BoxingRingCorner FencingPiste ArcheryTarget BowRack KitHamper CursedTrophy EquipmentCage StopwatchStand
RefereeChair ClimbingRopes GymRings BoxingGloves Megaphone WallBars WallPulley PunchingBag LockerBench SaunaDoor
FirstAidStation BasketballHoop IndianClubRack FencingMaskRack WhistleBoard HousePointsBoard]]

local function part(name, size, cf, parent, mat, col)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = mat or Enum.Material.Slate
	w.Color = col or Color3.new(0.227, 0.22, 0.227)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local old = SC:FindFirstChild("Gym")
if old then old:Destroy() end
local F = Instance.new("Folder") F.Name = "Gym"
local TURN = CFrame.Angles(0, math.pi, 0)
local face = ZB + 0.5
local x, n, missing, deepest = X0, 0, {}, 0
for name in ORDER:gmatch("%S+") do
	local t = P:FindFirstChild(name)
	if not t then table.insert(missing, name) continue end
	local c = t:Clone()
	c:SetAttribute("NHBuildKit", nil)
	c.Name = name .. "_Showcase"
	local pv = c:GetPivot()
	local cf, s = c:GetBoundingBox()
	local rel = pv:PointToObjectSpace(cf.Position)
	local px = x + rel.X + s.X / 2
	local py, pz, width = nil, nil, s.X
	if PLINTH[name] then
		local side = math.max(s.X, s.Z) + 0.6
		local cx, cz = x + side / 2, face + 0.6 + side / 2
		px, py, pz = cx + rel.X, PLINTH_TOP - (rel.Y - s.Y / 2), cz + rel.Z
		part(name .. "_ShowcasePlinth", Vector3.new(side, PLINTH_TOP - FLOOR, side), CFrame.new(cx, FLOOR + (PLINTH_TOP - FLOOR) / 2, cz),
			F, Enum.Material.Slate, Color3.new(0.157, 0.141, 0.173))
		width = side
	elseif WALL[name] then
		py, pz = FLOOR + WALL[name] - (rel.Y - s.Y / 2), face
	elseif HANG[name] then
		py, pz = FLOOR, face + 0.6 + rel.Z + s.Z / 2
		local top = FLOOR + rel.Y + s.Y / 2
		for i, ex in { x + 0.4, x + 1.2 + s.X } do
			part(name .. "_ShowcasePost" .. i, Vector3.new(0.8, top - FLOOR, 0.8), CFrame.new(ex, FLOOR + (top - FLOOR) / 2, pz - rel.Z),
				F, Enum.Material.Metal, Color3.new(0.133, 0.122, 0.141))
		end
		width = s.X + 1.6
		px = x + 0.8 + rel.X + s.X / 2
	else
		py, pz = FLOOR - (rel.Y - s.Y / 2), face + 0.6 + rel.Z + s.Z / 2
	end
	c:PivotTo(CFrame.new(px, py, pz) * TURN)
	c.Parent = F
	x += width + GAP
	n += 1
	deepest = math.max(deepest, s.Z)
end
local len = x - X0 + 2
part("GymWall", Vector3.new(len, 15, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + 7.5, ZB), F)
F.Parent = SC
return string.format("Gym: %d props, x %.0f..%.0f, wall z %d, deepest %.1f%s", n, X0, x, ZB, deepest,
	#missing > 0 and ("\nno template: " .. table.concat(missing, ",")) or "")
