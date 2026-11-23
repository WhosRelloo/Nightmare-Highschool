-- tools/phase6-2350/stage/textures.lua (Edit mode). Dresses the Wickfield props under Workspace.Hometown with the
-- group's uploaded maps, following the prop pipeline's rules (art/props/props.json _note):
--   * <Prop>_*Glow pieces become Neon, <Prop>_*Glass pieces Glass (no SurfaceAppearance);
--   * canvas pieces (signs, plates, blinds) get their canvas set;
--   * tiled pieces (a house's Siding / Roof / Brick ...) get their tile set;
--   * every other piece gets the prop's baked atlas (one SurfaceAppearance per piece, same four maps).
-- A set whose ids aren't uploaded yet is reported as MISSING and the piece is left as it is. Idempotent.
local function set(c, n, m, r) return { Color = c, Normal = n, Metal = m, Rough = r } end
local ATLAS = {
	WFBlackBus = set(105785771552764, 102930794103326, 83558228354904, 134062780123729),
	WFBusStop = set(116947995404626, 109640021422461, 91615662434002, 108367054922071),
	WFPicketGate = set(84222340516192, 98064335371557, 120543061893612, 126247700072127),
	WFBiscuit = set(112546262860861, 136186793277403, 111360307162850, 91765761922029),
	WFWickHouse = set(78429174177737, 116158405674482, 86100793161793, 120446577334327),
	WFKennel = set(82707989702453, 135687643487219, 117170230930850, 117358596024459),
	WFPicketFence = set(128495500741626, 121191286456473, 135904678807860, 128667251269387),
}
local CANVAS_SETS = {
	BusBlind = set(112756168878675, 110905673173953, 113104884743415, 131482475033372),
	BusSide = set(132810804202172, 98828107242392, 101274540604765, 122345539887672),
	BusPlate = set(81201460479671, 127109260492071, 133933169566034, 117393760068008),
	BusSign = set(91938222268972, 93154342156751, 119492087272701, 115690778262859),
	ShelterBand = set(94161896505343, 85816461846991, 74791049067750, 122872534510742),
	PosterBand = set(73093154751740, 79632058701398, 117419975024305, 104271770143494),
	ThePlan = set(102309737570223, 123906876914059, 74424215072451, 104132500629485),
	Biscuit = set(121465001224548), -- the kennel sign has a colour map only
	Timetable = set(97779368060155, 108125980375033, nil, 123170301420529), -- WF_Timetable_canvas (2026-11-22; no metalness map)
}
local CANVAS = {
	WFBlackBus_Blind = "BusBlind", WFBlackBus_SideL = "BusSide", WFBlackBus_SideR = "BusSide",
	WFBlackBus_Plate = "BusPlate", WFBlackBus_PlateRear = "BusPlate",
	WFBusStop_SignA = "BusSign", WFBusStop_SignB = "BusSign", WFBusStop_Band = "ShelterBand",
	WFBusStop_Timetable = "Timetable", WFBusStop_AdOut = "PosterBand", WFBusStop_Flyer = "ThePlan",
	WFKennel_Sign = "Biscuit",
}
local TILES = { Siding = "WF_ClapCream", Roof = "WF_Shingle", Brick = "WF_Brick", Walk = "WF_Sidewalk",
	Asphalt = "WF_Road", Floor = "WF_FloorOak", Paper = "WF_Wallpaper" }
local TILE_SETS = {
	WF_ClapCream = set(123304236805154, 85996737149979, 138775822833363, 132726121032361),
	WF_Brick = set(117145373109688, 109095381636468, 135123052756281, 131789682702424),
	WF_Shingle = set(133994678414940, 139001006865550, nil, 107762671353016), -- no metalness map uploaded (it's all 0)
}

local out, missing = {}, {}
local function dress(part, s)
	local sa = part:FindFirstChildOfClass("SurfaceAppearance") or Instance.new("SurfaceAppearance")
	local function id(n) return if n then "rbxassetid://" .. n else "" end
	sa.ColorMap = id(s.Color)
	sa.NormalMap = id(s.Normal)
	sa.MetalnessMap = id(s.Metal)
	sa.RoughnessMap = id(s.Rough)
	sa.Parent = part
end
local counts = {}
for _, model in workspace.Hometown:GetDescendants() do
	if model:IsA("Model") and ATLAS[model.Name] ~= nil or (model:IsA("Model") and (model.Name == "WFKennel" or model.Name == "WFPicketFence")) then
		local c = { sa = 0, neon = 0, glass = 0, skipped = 0 }
		for _, p in model:GetDescendants() do
			if p:IsA("MeshPart") then
				local group = p.Name:match("^[^_]+_(.+)$") or "" -- a re-imported prop keeps its file name (WickHouse_Siding under WFWickHouse)
				if p.Name:match("Glow$") then
					p.Material = Enum.Material.Neon
					p.Color = Color3.fromRGB(255, 196, 120)
					local old = p:FindFirstChildOfClass("SurfaceAppearance") if old then old:Destroy() end
					c.neon += 1
				elseif p.Name:match("Glass$") then
					p.Material = Enum.Material.Glass
					p.Transparency = 0.45
					p.Color = Color3.fromRGB(60, 66, 72)
					local old = p:FindFirstChildOfClass("SurfaceAppearance") if old then old:Destroy() end
					c.glass += 1
				else
					local s, what
					if CANVAS[p.Name] then
						what = "canvas " .. CANVAS[p.Name]
						s = CANVAS_SETS[CANVAS[p.Name]]
					elseif TILES[group] then
						what = "tile " .. TILES[group]
						s = TILE_SETS[TILES[group]]
					else
						what = "atlas " .. model.Name
						s = ATLAS[model.Name]
					end
					if s then
						dress(p, s); c.sa += 1
					else
						local old = p:FindFirstChildOfClass("SurfaceAppearance") if old then old:Destroy() end -- never the wrong set
						c.skipped += 1; missing[what] = true
					end
				end
			end
		end
		table.insert(out, string.format("%s: %d dressed, %d neon, %d glass, %d left bare", model.Name, c.sa, c.neon, c.glass, c.skipped))
	end
end
local m = {}
for k in missing do table.insert(m, k) end
table.sort(m)
table.insert(out, "MISSING sets: " .. (if #m > 0 then table.concat(m, ", ") else "none"))
return table.concat(out, "\n")
