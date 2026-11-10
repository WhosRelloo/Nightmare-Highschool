--!nocheck
-- Lines up the indoor lighting kit (batch 42) in workspace.NHPropsShowcase.Lighting like the other kits: one row in
-- front of a dark slate backing wall, props facing south (+Z), wall at z -560 from x 40 (south of the garden rows, east
-- of the dorm wing). Ceiling pieces hang with their top under an iron beam at 13.5 (their drop is their height); wall
-- pieces hang on the wall at the mount heights in the docs (their pivot is the bottom of their back face); the floor
-- pieces stand on the floor and the table lamps on slate plinths. Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local FLOOR, X0, GAP, ZB = 0.9, 40, 2.5, -560
local BEAM, PLINTH_TOP = 13.5, 3.4
local CEILING = [[ChandelierGreatWheel ChandelierShipHull ChandelierAntler ChandelierCage ChandelierCascade ChandelierRavenWing
ChandelierThornCrown LanternCluster PendantSpire PendantBellCage ClassroomPendant ClassroomTriPendant MoonOrb TraceryCeilingRose
VaultBossLight CorridorStripLight]]
local WALL = { SconceIronHand = 4.5, SconceBatWing = 4.5, SconceGasBracket = 5.0, SconceMirror = 4.0, SconceGargoyle = 5.0,
	SconceWitchlight = 4.5, CorridorUplighter = 8.0, StainedLightbox = 3.5 }
local WALL_ORDER = "SconceIronHand SconceBatWing SconceGasBracket SconceMirror SconceGargoyle SconceWitchlight CorridorUplighter StainedLightbox"
local FLOOR_ORDER = "TorchereWolves CandelabraDeadTree TorchereAlabaster CandleHearse"
local PLINTH_ORDER = "PianoLamp ReadingLampSwing DeskLampChapel MantelLampBat"

local function part(name, size, cf, parent, mat, col)
	local w = Instance.new("Part")
	w.Name = name w.Anchored = true w.Size = size w.CFrame = cf
	w.Material = mat or Enum.Material.Slate
	w.Color = col or Color3.new(0.227, 0.22, 0.227)
	w.TopSurface = Enum.SurfaceType.Smooth w.BottomSurface = Enum.SurfaceType.Smooth
	w.Parent = parent
	return w
end

local old = SC:FindFirstChild("Lighting")
if old then old:Destroy() end
local F = Instance.new("Folder") F.Name = "Lighting"
local TURN = CFrame.Angles(0, math.pi, 0)
local face = ZB + 0.5
local IRON = Color3.new(0.133, 0.122, 0.141)
local x, n, missing = X0, 0, {}

local function place(name, mode)
	local t = P:FindFirstChild(name)
	if not t then table.insert(missing, name) return end
	local c = t:Clone()
	c:SetAttribute("NHBuildKit", nil)
	c.Name = name .. "_Showcase"
	local pv = c:GetPivot()
	local cf, s = c:GetBoundingBox()
	local rel = pv:PointToObjectSpace(cf.Position)
	local px, py, pz, width = x + rel.X + s.X / 2, nil, nil, s.X
	if mode == "ceiling" then
		py = (BEAM - 0.5) - (rel.Y + s.Y / 2)
		pz = face + 4 + rel.Z
	elseif mode == "wall" then
		py, pz = FLOOR + WALL[name] - (rel.Y - s.Y / 2), face
	elseif mode == "plinth" then
		local side = math.max(s.X, s.Z) + 0.6
		local cx, cz = x + side / 2, face + 0.6 + side / 2
		px, py, pz = cx + rel.X, PLINTH_TOP - (rel.Y - s.Y / 2), cz + rel.Z
		part(name .. "_ShowcasePlinth", Vector3.new(side, PLINTH_TOP - FLOOR, side), CFrame.new(cx, FLOOR + (PLINTH_TOP - FLOOR) / 2, cz),
			F, Enum.Material.Slate, Color3.new(0.157, 0.141, 0.173))
		width = side
	else
		py, pz = FLOOR - (rel.Y - s.Y / 2), face + 0.6 + rel.Z + s.Z / 2
	end
	c:PivotTo(CFrame.new(px, py, pz) * TURN)
	c.Parent = F
	x += width + GAP
	n += 1
end

-- the ceiling run under one beam on two posts
local beamFrom = x
for name in CEILING:gmatch("%S+") do place(name, "ceiling") end
local beamTo = x - GAP
local bl = beamTo - beamFrom + 4
part("CeilingBeam", Vector3.new(bl, 1, 1), CFrame.new(beamFrom - 2 + bl / 2, BEAM, face + 4), F, Enum.Material.Metal, IRON)
part("CeilingBeamPost0", Vector3.new(1, BEAM - FLOOR, 1), CFrame.new(beamFrom - 2.5, FLOOR + (BEAM - FLOOR) / 2, face + 4), F, Enum.Material.Metal, IRON)
part("CeilingBeamPost1", Vector3.new(1, BEAM - FLOOR, 1), CFrame.new(beamTo + 2.5, FLOOR + (BEAM - FLOOR) / 2, face + 4), F, Enum.Material.Metal, IRON)
x += 4
for name in WALL_ORDER:gmatch("%S+") do place(name, "wall") end
for name in FLOOR_ORDER:gmatch("%S+") do place(name, "floor") end
for name in PLINTH_ORDER:gmatch("%S+") do place(name, "plinth") end

local len = x - X0 + 2
part("LightingWall", Vector3.new(len, 15, 1), CFrame.new(X0 - 2 + len / 2, FLOOR + 7.5, ZB), F)
F.Parent = SC
return string.format("Lighting: %d props, x %.0f..%.0f, wall z %d, beam %.0f..%.0f%s", n, X0, x, ZB, beamFrom, beamTo,
	#missing > 0 and ("\nno template: " .. table.concat(missing, ",")) or "")
