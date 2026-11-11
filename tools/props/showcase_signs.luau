--!nocheck
-- Builds the misc signs kit's showcase (props batch 50) in workspace.NHPropsShowcase.Signs on its own floor slab
-- (ShowcaseFloorSigns, x -245..55, z -970..-1030, south of the Witch Hut), from the Signs templates and SignKit:
--   North wall (z -990): one of every base on its template preset, at a sensible height, a ceiling beam for the
--     CorridorSign and the FloorStand on the floor in front.
--   South wall (z -1012): the class doors (a LintelTablet and a BrassPlaque over each of six doorways, R101 to R106),
--     the restroom plates, and rows of the rules and wayfinding presets on plaques, arrows and roundels.
--   The icon board: every icon with its name, on a tall slate board at the west end.
-- Every sign faces south (+Z, toward the viewer). Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")
local tmp = P.SignKit:Clone() tmp.Name = "SignKitRun" tmp.Parent = game:GetService("ServerStorage")
local K = require(tmp)
tmp:Destroy()

local GROUND = 0.9
local old = SC:FindFirstChild("Signs")
if old then old:Destroy() end
local F = Instance.new("Folder") F.Name = "Signs"
local missing, placed = {}, 0
local SOUTH = math.pi -- a piece's front (local -Z) turned to face +Z

local function part(name, size, cf, color, mat)
	local p = Instance.new("Part")
	p.Name = name p.Anchored = true p.Size = size p.CFrame = cf
	p.Color = color p.Material = mat or Enum.Material.Slate
	p.TopSurface = Enum.SurfaceType.Smooth p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = F
	return p
end

local floor = SC:FindFirstChild("ShowcaseFloorSigns") or workspace:FindFirstChild("ShowcaseFloorSigns", true)
if not floor then
	floor = Instance.new("Part")
	floor.Name = "ShowcaseFloorSigns" floor.Anchored = true
	floor.Size = Vector3.new(300, 2, 60) floor.CFrame = CFrame.new(-95, -0.1, -1000)
	floor.Material = Enum.Material.Slate floor.Color = Color3.fromRGB(58, 56, 62)
	floor.Parent = SC
end

-- put(name, x, y, z, attrs): a template copy, its pivot at (x, y, z), facing south; attrs set before SignKit draws it
local function put(name, x, y, z, attrs, tag)
	local t = P:FindFirstChild(name)
	if not t then table.insert(missing, name) return nil end
	local c = t:Clone()
	c.Name = name .. "_Showcase" .. (tag or "")
	for k, v in attrs or {} do c:SetAttribute(k, v) end
	c:PivotTo(CFrame.new(x, y, z) * CFrame.Angles(0, SOUTH, 0))
	c.Parent = F
	K.ApplyOne(c)
	placed += 1
	return c
end

local WALL = Color3.fromRGB(150, 142, 128) -- limestone
-- north wall: one of every base (wall pieces on the wall, the ceiling ones under beams)
local zN = -990
part("SignsWallNorth", Vector3.new(150, 14, 2), CFrame.new(-160, GROUND + 7, zN - 1), WALL, Enum.Material.Limestone)
local x = -228
put("LintelTablet", x + 4, GROUND + 9, zN) put("BrassPlaque", x + 4, GROUND + 5.2, zN)
x += 12
put("EnamelPlate", x, GROUND + 4.5, zN) put("EnamelPlate", x + 3, GROUND + 4.5, zN, { Preset = "Boys", Field = "InkBlue" }, "Boys")
x += 9
put("Roundel", x, GROUND + 5, zN) put("Roundel", x + 3, GROUND + 5, zN, { Preset = "Floor3" }, "3")
x += 10
put("ArrowBoard", x, GROUND + 6.5, zN) put("ArrowBoardLeft", x, GROUND + 4.6, zN)
x += 9
put("BracketSign", x, GROUND + 5, zN)
x += 7
put("ExitLantern", x, GROUND + 8.5, zN)
-- a ceiling beam for the corridor sign
x += 9
part("SignsBeam", Vector3.new(8, 0.8, 1.2), CFrame.new(x, GROUND + 12.4, zN + 4), Color3.fromRGB(40, 38, 42), Enum.Material.Slate)
put("CorridorSign", x, GROUND + 12 - 3.0, zN + 4)
-- wing directories under a second beam (their roses are 5.4 above the pivot)
x += 9
part("SignsBeamWings", Vector3.new(14, 0.8, 1.2), CFrame.new(x + 3, GROUND + 13.4, zN + 4), Color3.fromRGB(40, 38, 42), Enum.Material.Slate)
put("WingDirectory", x, GROUND + 13 - 5.4, zN + 4)
put("WingDirectory", x + 6, GROUND + 13 - 5.4, zN + 4, { Preset = "MainHall", Field = "Crimson" }, "MainHall")
x += 15
put("FloorStand", x, GROUND, zN + 3)
put("FloorStand", x + 4, GROUND, zN + 3, { Preset = "WetFloor", Field = "Bone", Ink = "Ink" }, "Wet")

-- south wall: the class doors and the rows of presets
local zS = -1012
part("SignsWallSouth", Vector3.new(290, 16, 2), CFrame.new(-95, GROUND + 8, zS - 1), WALL, Enum.Material.Limestone)
local classes = { "Homeroom", "Mathematics", "Chemistry", "English", "History", "Detention" }
for i, pre in classes do
	local cx = -232 + (i - 1) * 9
	part("Doorway" .. i, Vector3.new(4.5, 8, 0.4), CFrame.new(cx, GROUND + 4, zS + 0.2), Color3.fromRGB(34, 26, 24), Enum.Material.Wood)
	put("LintelTablet", cx, GROUND + 8.6, zS, { Preset = pre }, pre)
	put("BrassPlaque", cx + 3.9, GROUND + 4.6, zS, { Preset = pre }, pre)
end
-- the restrooms
local rx = -172
for i, pre in { "Boys", "Girls", "Restroom", "Accessible" } do
	put("EnamelPlate", rx + (i - 1) * 2.4, GROUND + 4.5, zS, { Preset = pre, Field = i == 1 and "InkBlue" or nil }, pre)
end
-- every other preset on a plaque, in rows, alphabetically
local skip = { Homeroom = 1, Mathematics = 1, Chemistry = 1, English = 1, History = 1, Detention = 1, Boys = 1, Girls = 1,
	Restroom = 1, Accessible = 1, ArrowRight = 1, ArrowLeft = 1, ArrowUp = 1, ArrowDown = 1, Floor1 = 1, Floor2 = 1, Floor3 = 1,
	Ground = 1, EastWing = 1, WestWing = 1, NorthWing = 1, SouthWing = 1, MainHall = 1, StaffWing = 1 }
local list = {}
for k in K.PRESETS do if not skip[k] then table.insert(list, k) end end
table.sort(list)
local fields = { "Black", "Crimson", "InkBlue", "Verdigris", "Slate" }
local col, row = 0, 0
for i, pre in list do
	local px = -158 + col * 3.0
	local py = GROUND + 12.6 - row * 1.25
	put("BrassPlaque", px, py, zS, { Preset = pre, Field = fields[(i - 1) % #fields + 1] }, pre)
	col += 1
	if col >= 30 then col = 0 row += 1 end
end
-- arrows and floor numbers along the bottom
local ax = -150
for i, pre in { "ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown" } do
	put(i == 2 and "ArrowBoardLeft" or "ArrowBoard", ax + (i - 1) * 4, GROUND + 2.2, zS, { Preset = pre, Subtitle = "-", Icon = "Arrow",
		IconRotation = ({ 0, 180, 270, 90 })[i] }, pre)
end
for i, pre in { "Ground", "Floor1", "Floor2", "Floor3" } do
	put("Roundel", -132 + (i - 1) * 2.2, GROUND + 2.2, zS, { Preset = pre }, pre)
end

-- the icon board: every icon with its name, 10 to a row
local names = {}
for n in K.ICONS do table.insert(names, n) end
table.sort(names)
local cols = 10
local rows = math.ceil(#names / cols)
local cell = 1.6
local bw, bh = cols * cell + 0.6, rows * cell + 1.6
local board = part("SignIconBoard", Vector3.new(bw, bh, 0.3), CFrame.new(-60 + bw / 2, GROUND + 0.5 + bh / 2, zS + 0.15),
	Color3.fromRGB(28, 26, 30), Enum.Material.Slate)
local g = Instance.new("SurfaceGui")
g.Face = Enum.NormalId.Back -- the board's +Z face, toward the viewer
g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud g.PixelsPerStud = 100
g.LightInfluence = 1 g.Parent = board
local title = Instance.new("TextLabel")
title.BackgroundTransparency = 1 title.Size = UDim2.new(1, 0, 0, 100) title.Text = "SIGN ICONS  ·  Icon attribute names"
title.FontFace = Font.new(K.FONTS.Garamond, Enum.FontWeight.Bold) title.TextScaled = true
title.TextColor3 = K.INK.Gilt title.Parent = g
for i, n in names do
	local cx, cy = (i - 1) % cols, (i - 1) // cols
	local im = Instance.new("ImageLabel")
	im.BackgroundTransparency = 1 im.Image = "rbxassetid://" .. K.ICONS[n] im.ImageColor3 = K.INK.Gilt
	im.Size = UDim2.fromOffset(110, 110) im.Position = UDim2.fromOffset(30 + cx * 160 + 25, 130 + cy * 160)
	im.Parent = g
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1 t.Text = n t.TextScaled = true t.FontFace = Font.new(K.FONTS.Garamond)
	t.TextColor3 = K.INK.Bone t.Size = UDim2.fromOffset(156, 30) t.Position = UDim2.fromOffset(30 + cx * 160 + 2, 130 + cy * 160 + 114)
	t.Parent = g
end

F.Parent = SC
return string.format("signs showcase: %d placed, %d icons on the board; missing: %s", placed, #names, table.concat(missing, ","))
