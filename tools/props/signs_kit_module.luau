--!nocheck
-- SignKit (ServerStorage.NHProps.SignKit): the misc signs kit's chooser (props batch 50, NHBuildKit "Signs").
-- Every sign base has a blank enamel Field; this draws the icon and words on it (SurfaceGuis on the Field's faces) and
-- tints the Field. A sign is set by its attributes:
--   Preset        one word that fills the rest (see PRESETS), e.g. "Mathematics", "Girls", "Library", "WayOut"
--   Icon, Icon2   icon names (see ICONS). Icon2 is the second slot (LintelTablet repeats Icon there unless Icon2 is set;
--                 CorridorSign and WingDirectory leave it empty unless set)
--   IconRotation  degrees, for the Arrow icon (0 points right, 90 down, 180 left, 270 up)
--   Title         the big line (written in capitals);  Subtitle  the small line, or "" for none
--   Field         enamel: Black, Crimson, InkBlue, Verdigris, Bone, Slate, or a Color3
--   Ink           lettering and icon: Gilt, Ink, Bone, Silver, or a Color3
--   Font          Garamond (the default, the game's font), Merriweather, Gothic, Script or Antique
--   Row1..Row5    WingDirectory only: one destination per row, written the way it reads, the arrow where it points:
--                 "Library >", "< Chapel", "^ Infirmary" (up), "v Crypt" (down), or no arrow. The row's icon comes
--                 from its name (a preset or icon name), or name it first: "Crypt: The Vaults >"
-- Set the attributes in Properties, then in the command bar:
--   require(game.ServerStorage.NHProps.SignKit).Apply()          -- the selected signs (or every sign if none selected)
--   require(game.ServerStorage.NHProps.SignKit).Apply(model)     -- one sign
-- The result is saved in the sign, so nothing has to run in game and the signs work in any place.
-- Explicit attributes win over the Preset's ("-" or "None" blanks a line or icon); an empty one takes the Preset's.
local SignKit = {}

-- icon name -> image asset id (group 15981569); filled from the upload, read by name
SignKit.ICONS = {--[[ICONS]]}

local rgb = Color3.fromRGB
SignKit.INK = { Gilt = rgb(255, 214, 128), Ink = rgb(32, 26, 30), Bone = rgb(234, 224, 200), Silver = rgb(212, 214, 222) }
SignKit.FIELD = {
	Black = rgb(26, 24, 28), Crimson = rgb(96, 14, 26), InkBlue = rgb(22, 30, 66), Verdigris = rgb(46, 92, 80),
	Bone = rgb(214, 202, 176), Slate = rgb(52, 56, 60),
}

-- base -> faces (NormalIds of the Field's bounding box), default enamel and ink, layout boxes {x0, y0, x1, y1} as
-- fractions of the face from its top left (art/props/signs_batch50.json)
SignKit.BASES = {--[[BASES]]}

-- Preset -> { Icon, Title, Subtitle, Icon2?, IconRotation? }
SignKit.PRESETS = {
	-- classes (Config.Classes)
	Homeroom = { "Homeroom", "Homeroom", "Room 101" },
	Mathematics = { "Mathematics", "Mathematics", "Room 102" },
	Chemistry = { "Chemistry", "Chemistry", "Room 103" },
	English = { "English", "English", "Room 104" },
	History = { "History", "History", "Room 105" },
	Detention = { "Detention", "Detention", "Room 106" },
	-- electives and the arts
	Herbology = { "Herbology", "Herbology", "" }, HomeEconomics = { "HomeEconomics", "Home Economics", "" },
	Sewing = { "Sewing", "Sewing Room", "" }, Photography = { "Photography", "Photography", "Darkroom" },
	Woodshop = { "Woodshop", "Woodshop", "" }, Ceramics = { "Ceramics", "Ceramics", "Kiln room" },
	Drama = { "Drama", "Drama", "The stage" }, Art = { "Art", "Art Room", "" }, Music = { "Music", "Music Room", "" },
	Choir = { "Choir", "Choir", "Rehearsal room" }, Alchemy = { "Alchemy", "Alchemy", "" },
	Astronomy = { "Astronomy", "Astronomy", "" }, Seance = { "Seance", "Seance Room", "Knock thrice" },
	Gymnasium = { "Gym", "Gymnasium", "" }, PE = { "Gym", "Physical Education", "" },
	Football = { "Football", "The West Pitch", "" },
	-- rooms
	Library = { "Library", "Library", "" }, Archive = { "Archive", "The Archive", "" },
	RecordsOffice = { "RecordsOffice", "Records Office", "Staff only" }, Infirmary = { "Infirmary", "Infirmary", "Matron" },
	Headmaster = { "Headmaster", "Headmaster", "Knock and wait" }, StaffRoom = { "StaffRoom", "Staff Room", "" },
	Lounge = { "Lounge", "Teachers' Lounge", "" }, DiningHall = { "Cafeteria", "Dining Hall", "" },
	Cafeteria = { "Cafeteria", "Cafeteria", "" }, Chapel = { "Chapel", "Chapel", "" },
	Dormitories = { "Dormitory", "Dormitories", "Lights out at ten" }, CommonRoom = { "CommonRoom", "Common Room", "" },
	LockerRoom = { "LockerRoom", "Locker Room", "" }, BoilerRoom = { "BoilerRoom", "Boiler Room", "Keep out" },
	BellTower = { "BellTower", "Bell Tower", "" }, Crypt = { "Crypt", "The Crypt", "" },
	InkStudio = { "InkStudio", "Ink Studio", "" }, Courtyard = { "Courtyard", "Courtyard", "" },
	Reception = { "Reception", "Reception", "" }, Office = { "Reception", "School Office", "" },
	LostFound = { "LostFound", "Lost & Found", "" }, Post = { "Post", "Post Room", "" },
	Crest = { "Crest", "Nightmare High", "" },
	-- restrooms
	Boys = { "Boys", "Boys", "" }, Girls = { "Girls", "Girls", "" }, Men = { "Boys", "Men", "" },
	Women = { "Girls", "Women", "" }, Restroom = { "Restroom", "Restroom", "" }, Accessible = { "Accessible", "Accessible", "" },
	-- wayfinding and rules
	ArrowRight = { "Arrow", "This Way", "", IconRotation = 0 }, ArrowLeft = { "Arrow", "This Way", "", IconRotation = 180 },
	ArrowUp = { "Arrow", "Upstairs", "", IconRotation = 270 }, ArrowDown = { "Arrow", "Downstairs", "", IconRotation = 90 },
	Stairs = { "Stairs", "Stairs", "" }, Floor1 = { "Stairs", "I", "" }, Floor2 = { "Stairs", "II", "" },
	Floor3 = { "Stairs", "III", "" }, Ground = { "Stairs", "G", "" },
	WayOut = { "Exit", "Way Out", "" }, Exit = { "Exit", "Exit", "" },
	Quiet = { "Quiet", "Quiet Please", "" }, NoRunning = { "NoRunning", "No Running", "In the halls" },
	NoMagic = { "NoMagic", "No Magic", "Beyond this point" }, NoEntry = { "NoEntry", "No Entry", "" },
	KeepOut = { "KeepOut", "Keep Out", "" }, StaffOnly = { "StaffOnly", "Staff Only", "" },
	Danger = { "Danger", "Danger", "" }, Information = { "Information", "Information", "" },
	Curfew = { "Curfew", "Curfew", "Halls close at ten" }, WetFloor = { "WetFloor", "Wet Floor", "" },
	-- wing directories (WingDirectory): the header, the crest either side, and the rows
	EastWing = { "Crest", "East Wing", "", Icon2 = "Crest",
		Rows = { "Homeroom >", "Mathematics >", "Chemistry >", "< English", "< History" } },
	WestWing = { "Crest", "West Wing", "", Icon2 = "Crest", Rows = { "Library >", "< Archive", "< Chapel", "Ink Studio >" } },
	NorthWing = { "Crest", "North Wing", "", Icon2 = "Crest", Rows = { "Gymnasium >", "< Locker Room", "^ Bell Tower", "v Boiler Room" } },
	SouthWing = { "Crest", "South Wing", "", Icon2 = "Crest", Rows = { "Dining Hall >", "< Common Room", "^ Dormitories", "Infirmary >" } },
	MainHall = { "Crest", "Main Hall", "", Icon2 = "Crest", Rows = { "< East Wing", "West Wing >", "^ Headmaster", "Staff Room >", "v Crypt" } },
	StaffWing = { "StaffOnly", "Staff Wing", "", Icon2 = "StaffOnly", Rows = { "Staff Room >", "< Records Office", "Headmaster >", "< Reception" } },
}

-- Font attribute -> family (Garamond is the game's UI body font, Roblox's Guru family)
SignKit.FONTS = {
	Garamond = "rbxasset://fonts/families/Guru.json", Merriweather = "rbxasset://fonts/families/Merriweather.json",
	Gothic = "rbxasset://fonts/families/GrenzeGotisch.json", Script = "rbxasset://fonts/families/Fondamento.json",
	Antique = "rbxasset://fonts/families/AccanthisADFStd.json",
}
local function fonts(name)
	local fam = SignKit.FONTS[name or ""] or SignKit.FONTS.Garamond
	return Font.new(fam, Enum.FontWeight.Bold, Enum.FontStyle.Normal), Font.new(fam, Enum.FontWeight.Regular, Enum.FontStyle.Italic)
end
local PPS = 160 -- SurfaceGui pixels per stud

local function color(v, tbl, fallback)
	if typeof(v) == "Color3" then return v end
	return tbl[v] or fallback
end

local function baseOf(m)
	local b = m:GetAttribute("SignBase")
	if b and SignKit.BASES[b] then return b end
	if SignKit.BASES[m.Name] then return m.Name end
	return nil
end

local function fieldOf(m, base)
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") and (p.Name == base .. "_Field" or p.Name == "Field") then return p end
	end
	for _, p in m:GetDescendants() do
		if p:IsA("BasePart") and p.Name:sub(-6) == "_Glass" then return p end
	end
	return nil
end

local function box(parent, name, b, z)
	local f = Instance.new("Frame")
	f.Name = name
	f.BackgroundTransparency = 1
	f.Position = UDim2.fromScale(b[1], b[2])
	f.Size = UDim2.fromScale(b[3] - b[1], b[4] - b[2])
	f.ZIndex = z or 1
	f.Parent = parent
	return f
end

local function icon(parent, name, b, id, ink, rot)
	local f = box(parent, name, b)
	local ar = Instance.new("UIAspectRatioConstraint")
	ar.AspectRatio = 1
	ar.Parent = f
	f.AnchorPoint = Vector2.new(0.5, 0.5)
	f.Position = UDim2.fromScale((b[1] + b[3]) / 2, (b[2] + b[4]) / 2)
	local function img(n, col, tr, off, z)
		local i = Instance.new("ImageLabel")
		i.Name = n
		i.BackgroundTransparency = 1
		i.Image = id
		i.ImageColor3 = col
		i.ImageTransparency = tr
		i.Size = UDim2.fromScale(1, 1)
		i.Position = UDim2.fromScale(off, off * 1.2)
		i.Rotation = rot
		i.ScaleType = Enum.ScaleType.Fit
		i.ZIndex = z
		i.Parent = f
	end
	img("Shadow", Color3.new(0, 0, 0), 0.45, 0.025, 1)
	img("Icon", ink, 0, 0, 2)
end

-- the largest text size (up to Roblox's 100) at which `s` fits w x h pixels on one line, measured with TextService
-- (TextScaled is not used: in Studio it wraps "II" into two lines, and with wrapping off it doesn't scale at all)
local TS = game:GetService("TextService")
local function fit(s, font, w, h)
	local size = math.clamp(math.floor(h * 0.92), 6, 100)
	for _ = 1, 3 do
		local params = Instance.new("GetTextBoundsParams")
		params.Text = s params.Font = font params.Size = size params.Width = 100000
		local ok, b = pcall(TS.GetTextBoundsAsync, TS, params)
		if not ok or b.X <= w then break end
		size = math.max(6, math.floor(size * w / b.X))
	end
	return size
end

-- words in box b (fractions of the parent, whose size in pixels is px), one line, with a soft drop shadow
local function text(parent, name, b, s, font, ink, shadow, px, align)
	-- the game's Garamond (Guru) joins "II" into one barred glyph: a hair space keeps the I's apart
	while s:find("II", 1, true) do s = s:gsub("II", "I\u{200A}I") end
	local f = box(parent, name, b)
	local size = fit(s, font, (b[3] - b[1]) * px.X, (b[4] - b[2]) * px.Y)
	local function lbl(n, col, tr, dx, z)
		local t = Instance.new("TextLabel")
		t.Name = n
		t.BackgroundTransparency = 1
		t.Text = s
		t.FontFace = font
		t.TextColor3 = col
		t.TextTransparency = tr
		t.TextScaled = false
		t.TextWrapped = false
		t.TextSize = size
		t.TextXAlignment = align or Enum.TextXAlignment.Center
		t.Size = UDim2.fromScale(1, 1)
		t.Position = UDim2.new(0, dx, 0, dx)
		t.ZIndex = z
		t.Parent = f
	end
	if shadow then lbl("Shadow", Color3.new(0, 0, 0), 0.5, math.max(1, math.floor(size / 24 + 0.5)) * shadow / 2, 1) end
	lbl("Text", ink, 0, 0, 2)
end

-- a row's words -> name, arrow rotation (or nil) and icon id (or nil)
local ARROWS = { [">"] = 0, ["<"] = 180, ["^"] = 270, ["v"] = 90, ["V"] = 90 }
local function key(s) return (s:lower():gsub("[^%w]", "")) end
local function iconFor(name)
	local k = key(name)
	for pn, p in SignKit.PRESETS do
		if key(pn) == k or key(p[2] or "") == k then return SignKit.ICONS[p[1]] end
	end
	for n, id in SignKit.ICONS do
		if key(n) == k then return id end
	end
	return nil
end
function SignKit.ParseRow(row)
	local s = row:match("^%s*(.-)%s*$")
	local deg
	local a = s:sub(-1)
	if ARROWS[a] and (#s == 1 or s:sub(-2, -2) == " ") then deg = ARROWS[a] s = s:sub(1, -2) end
	local b = s:sub(1, 1)
	if not deg and ARROWS[b] and s:sub(2, 2) == " " then deg = ARROWS[b] s = s:sub(3) end
	s = s:match("^%s*(.-)%s*$")
	local named, rest = s:match("^([%w]+):%s*(.+)$")
	local id
	if named and SignKit.ICONS[named] then id = SignKit.ICONS[named] s = rest else id = iconFor(s) end
	return s, deg, id
end

-- the sign's resolved settings: explicit attributes over the preset
local function settings(m)
	local p = SignKit.PRESETS[m:GetAttribute("Preset") or ""] or {}
	local function pick(attr, i)
		local v = m:GetAttribute(attr)
		if v == "-" or v == "None" then return "" end -- an explicit blank, over the preset
		if v ~= nil and v ~= "" then return v end
		if i then return p[i] end
		return p[attr]
	end
	return {
		Icon = pick("Icon", 1) or "", Title = pick("Title", 2) or "", Subtitle = pick("Subtitle", 3) or "",
		Icon2 = pick("Icon2") or "", IconRotation = m:GetAttribute("IconRotation") or p.IconRotation or 0,
		Field = m:GetAttribute("Field"), Ink = m:GetAttribute("Ink"), Font = m:GetAttribute("Font"),
		Rows = (function()
			local own, any = {}, false
			for i = 1, 5 do
				local v = m:GetAttribute("Row" .. i)
				if v ~= nil and v ~= "" then any = true if v ~= "-" and v ~= "None" then table.insert(own, v) end end
			end
			if any then return own end
			return p.Rows or {}
		end)(),
	}
end

function SignKit.ApplyOne(m)
	local base = baseOf(m)
	if not base then return false, "not a sign" end
	local B = SignKit.BASES[base]
	local field = fieldOf(m, base)
	if not field then return false, "no Field" end
	local s = settings(m)
	-- a symmetric base (LintelTablet) repeats its icon in the second slot unless Icon2 is set ("-" leaves it empty)
	local i2 = m:GetAttribute("Icon2")
	if B.mirror and s.Icon2 == "" and i2 ~= "-" and i2 ~= "None" then s.Icon2 = s.Icon end
	local ink = color(s.Ink, SignKit.INK, SignKit.INK[B.ink])
	local tint = color(s.Field, SignKit.FIELD, B.tint and SignKit.FIELD[B.tint])
	local sa = field:FindFirstChildOfClass("SurfaceAppearance")
	if sa and tint then sa.Color = tint end
	for _, g in field:GetChildren() do
		if g:IsA("SurfaceGui") and g.Name:sub(1, 8) == "SignFace" then g:Destroy() end
	end
	local L = B.layout
	local FONT_T, FONT_S = fonts(s.Font)
	for _, face in B.faces do
		local fs = field.Size
		local px = (face == "Left" or face == "Right") and Vector2.new(fs.Z, fs.Y) * PPS or Vector2.new(fs.X, fs.Y) * PPS
		local g = Instance.new("SurfaceGui")
		g.Name = "SignFace_" .. face
		g.Face = Enum.NormalId[face]
		g.SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud
		g.PixelsPerStud = PPS
		g.LightInfluence = B.glass and 0.2 or 1
		g.Brightness = B.glass and 1 or 1.15
		g.ClipsDescendants = true
		g.MaxDistance = 220
		g.ResetOnSpawn = false
		local id1 = SignKit.ICONS[s.Icon]
		local id2 = SignKit.ICONS[s.Icon2]
		if id1 and L.Icon then icon(g, "Icon", L.Icon, "rbxassetid://" .. id1, ink, s.IconRotation) end
		if id2 and L.Icon2 then icon(g, "Icon2", L.Icon2, "rbxassetid://" .. id2, ink, s.IconRotation) end
		local tb = L.Title
		if s.Subtitle == "" and L.Subtitle then tb = { tb[1], tb[2], tb[3], L.Subtitle[4] } end
		-- no icon in a slot: let the words use the room it leaves (keep them centred)
		if not id1 and not id2 and L.Icon then
			local l = math.min(tb[1], L.Icon[1]) local r = math.max(tb[3], (L.Icon2 or L.Icon)[3])
			if L.Icon[1] < tb[1] and not L.Icon2 then tb = { L.Icon[1], tb[2], tb[3], tb[4] } end
			if L.Icon2 then tb = { l, tb[2], r, tb[4] } end
		end
		if s.Title ~= "" then
			local pad = (tb[4] - tb[2]) * ((s.Subtitle == "" and L.Subtitle) and 0.16 or 0.06)
			text(g, "Title", { tb[1], tb[2] + pad, tb[3], tb[4] - pad }, string.upper(s.Title), FONT_T, ink, 2, px)
		end
		if s.Subtitle ~= "" and L.Subtitle then
			local sb = L.Subtitle
			local pad = (sb[4] - sb[2]) * 0.1
			text(g, "Subtitle", { sb[1], sb[2] + pad, sb[3], sb[4] - pad }, s.Subtitle, FONT_S, ink, 1, px)
		end
		if L.Rows and #s.Rows > 0 then
			local R = L.Rows
			local n = #s.Rows
			local slot = (R[4] - R[2]) / math.max(n, 4) -- never bigger than a four-row board, so the header stays the largest
			for i, row in s.Rows do
				local name, deg, id = SignKit.ParseRow(row)
				local y0 = R[2] + (i - 1) * slot
				local rf = box(g, "Row" .. i, { R[1], y0, R[3], y0 + slot })
				if id then icon(rf, "Icon", { 0, 0.04, 0.12, 0.96 }, "rbxassetid://" .. id, ink, 0) end
				if deg and SignKit.ICONS.Arrow then
					icon(rf, "Arrow", { 0.88, 0.04, 1, 0.96 }, "rbxassetid://" .. SignKit.ICONS.Arrow, ink, deg)
				end
				text(rf, "Name", { 0.14, 0.14, 0.86, 0.86 }, string.upper(name), FONT_T, ink, 2,
					Vector2.new((R[3] - R[1]) * px.X, slot * px.Y), Enum.TextXAlignment.Left)
			end
		end
		g.Parent = field
	end
	m:SetAttribute("SignBase", base)
	return true
end

function SignKit.Apply(target)
	local list = {}
	if typeof(target) == "Instance" then
		list = { target }
	else
		local ok, sel = pcall(function() return game:GetService("Selection"):Get() end)
		if ok and #sel > 0 then
			for _, o in sel do
				local m = o:IsA("Model") and o or o:FindFirstAncestorWhichIsA("Model")
				while m and not baseOf(m) and m.Parent and m.Parent:IsA("Model") do m = m.Parent end
				if m then table.insert(list, m) end
			end
		else
			for _, o in workspace:GetDescendants() do
				if o:IsA("Model") and o:GetAttribute("NHBuildKit") == "Signs" then table.insert(list, o) end
			end
		end
	end
	local n, bad = 0, {}
	for _, m in list do
		local ok, why = SignKit.ApplyOne(m)
		if ok then n += 1 elseif why ~= "not a sign" then table.insert(bad, m:GetFullName() .. ": " .. why) end
	end
	local msg = string.format("SignKit: %d sign(s) updated%s", n, #bad > 0 and ("; " .. table.concat(bad, "; ")) or "")
	print(msg)
	return msg
end

return SignKit
