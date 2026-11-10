--!nocheck
-- Builds one standard witch hut (props batch 47) in workspace.NHPropsShowcase["Witch Hut"], south of the Spell Shop row,
-- from the WitchHut templates and the kit's snap grid (docs/School-Props.md, batch 47): 24 x 16 between post centres,
-- posts every 8, footings and walls on the wall lines (a window either side of the door at the front, the door facing
-- the viewer, +Z), gables on the 16-wide ends, three roof slopes a side, three ridge pieces, the chimney on the east end
-- with the hearth inside it, the porch under the door. Inside: rug, cauldron, work table, lectern, bed, shelves, broom
-- corner, hat stand, cat basket, hanging herbs. Outside: wisp lantern, toadstool ring, gourds, chimes on the porch.
-- Stands on its own floor slab (ShowcaseFloorHut, z -905 to -965). Run again to rebuild.
local P = game:GetService("ServerStorage").NHProps
local SC = workspace:FindFirstChild("NHPropsShowcase")
assert(SC, "no NHPropsShowcase")

local GROUND = 0.9
local FLOORY = GROUND + 1.6 -- the hut's floor
local PLATE = GROUND + 12.6 -- the wall plates' top
local O = Vector3.new(-200, 0, -935) -- the hut's centre on the ground plane
-- facings: a piece's front (its local -Z) points this way
local FACE = { N = 0, S = math.pi, E = -math.pi / 2, W = math.pi / 2 } -- N = -Z, S = +Z (toward the viewer), E = +X, W = -X

local old = SC:FindFirstChild("Witch Hut")
if old then old:Destroy() end
local F = Instance.new("Folder") F.Name = "Witch Hut"
local missing, placed = {}, 0

local function put(name, x, y, z, face, tag)
	local t = P:FindFirstChild(name)
	if not t then table.insert(missing, name) return nil end
	local c = t:Clone()
	c:SetAttribute("NHBuildKit", nil)
	c.Name = name .. "_Showcase" .. (tag or "")
	c:PivotTo(CFrame.new(O.X + x, y, O.Z + z) * CFrame.Angles(0, FACE[face] or face, 0))
	c.Parent = F
	placed += 1
	return c
end

-- posts at every corner and wall joint (10)
for _, x in { -12, -4, 4, 12 } do
	put("HutPost", x, GROUND, -8, "N", "N" .. x)
	put("HutPost", x, GROUND, 8, "S", "S" .. x)
end
put("HutPost", -12, GROUND, 0, "W", "W0") put("HutPost", 12, GROUND, 0, "E", "E0")

-- footings and walls: front (south, +Z) window / door / window; back (north) wall / window / wall; ends plain
local WALLS = {
	{ -8, 8, "S", "HutWallWindow" }, { 0, 8, "S", "HutWallDoor" }, { 8, 8, "S", "HutWallWindow" },
	{ -8, -8, "N", "HutWall" }, { 0, -8, "N", "HutWallWindow" }, { 8, -8, "N", "HutWall" },
	{ -12, -4, "W", "HutWall" }, { -12, 4, "W", "HutWall" }, { 12, -4, "E", "HutWall" }, { 12, 4, "E", "HutWall" },
}
for i, w in WALLS do
	put("HutFooting", w[1], GROUND, w[2], w[3], i)
	put(w[4], w[1], FLOORY, w[2], w[3], i)
end

-- the floor inside (the docs: a Part floor at 1.6)
local fl = Instance.new("Part")
fl.Name = "HutFloor_Showcase" fl.Anchored = true
fl.Size = Vector3.new(23.2, 0.3, 15.2)
fl.CFrame = CFrame.new(O.X, FLOORY - 0.15, O.Z)
fl.Material = Enum.Material.WoodPlanks fl.Color = Color3.fromRGB(70, 52, 40)
fl.Parent = F

-- gables, roof slopes, ridge
put("HutGable", -12, PLATE, 0, "W", "W") put("HutGable", 12, PLATE, 0, "E", "E")
for _, x in { -8, 0, 8 } do
	put("HutRoof", x, PLATE, 8, "S", "S" .. x)
	put("HutRoof", x, PLATE, -8, "N", "N" .. x)
	put("HutRidge", x, PLATE, 0, "N", x)
end

-- the chimney on the east end (its back on the end wall's outside face) with the hearth inside on the same spot
put("HutChimney", 12.45, GROUND, 0, "E")
put("HearthKettle", 11.55, FLOORY, 0, "W")
-- the porch under the door
put("HutPorch", 0, GROUND, 8, "S")

-- inside (the walls' inner faces are at x = +-11.55 and z = +-7.55; the hearth takes the east end's middle)
put("BraidedRug", 0.5, FLOORY, 0, "S")
put("WitchCauldron", 0.5, FLOORY + 0.2, 0, "S") -- on the rug
put("WitchWorkTable", -1.4, FLOORY, -5.8, "S") -- against the back wall
put("HerbBeamRack", -1.4, PLATE - 4.4, -5.8, "S") -- hung from the plate over the table
put("WitchJarShelf", -7.8, FLOORY + 2.4, -7.55, "S")
put("SpellNoteShelf", 5.2, FLOORY, -7.55, "S")
put("BroomCorner", 11.55, FLOORY, 7.55, "N") -- the south-east inside corner, beside the hearth
put("StrawBed", -7.4, FLOORY, 3.55, "E") -- head to the west wall
put("SpellLectern", 4.5, FLOORY, 5.6, "S")

-- outside
put("WispLanternPost", -15, GROUND, 13, "S")
put("WitchHatStand", -15, GROUND, 3, "W") -- under the west eaves
put("GourdPile", -8.6, GROUND, 11.5, "S")
put("CatBasket", 8, GROUND, 10.5, "S")
put("ToadstoolRing", 12, GROUND, 17, "S")
put("BoneChimes", 4.2, GROUND + 3.6, 15.4, "S")

-- the hut's own ground: a slab south of ShowcaseFloorShops (which ends at z -905)
local slab = Instance.new("Part")
slab.Name = "ShowcaseFloorHut" slab.Anchored = true
slab.Size = Vector3.new(300, 2, 60)
slab.CFrame = CFrame.new(-245 + 150, GROUND - 1, -935)
slab.Material = Enum.Material.Plaster slab.Color = Color3.new(0.357, 0.357, 0.357)
slab.Parent = F

F.Parent = SC
return string.format("Witch Hut: %d pieces placed%s", placed, #missing > 0 and ("; no template: " .. table.concat(missing, ",")) or "")
