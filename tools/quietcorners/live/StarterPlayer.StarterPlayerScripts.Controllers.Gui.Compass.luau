--[[
	Compass (client): a slim strip across the top of the screen that helps you find places of interest.
	Only existing UI kit art: the kit's fonts, colours and icon images (Theme.Images).

	North is -Z. N / E / S / W in the title font (N in crimson), ticks every 15 degrees, ends fade out.
	Markers (each only within its own range, so the strip never clutters):
		Classrooms      parts with RoomId + Subject        quill (IconNib)       90 studs
		Faction bases   models with Faction = <id>         candle / blood drop   400 studs
		Duel ring       the model holding DuelPad parts     seal                  300 studs
		Quest NPCs      parts with NpcPost = <npc id>       pip                   120 studs
		Anything else   Compass = "Label" (+ CompassIcon = <Theme image>, CompassRange = studs)
	When you face nothing, the readout names the place you are in (SetRegion, from Controllers.World.Regions).
		Your quest      the tracked objective (Controllers.Gui.QuestTracker's marker): gold, always shown,
		                pinned to the strip's edge when it's behind you
	Whatever you face (within a few degrees) is named under the strip with its distance.
	Places are read from attributes (the map contract), so the builder's real map lights up on its own.
	The main menu hides it with the rest of the HUD. API: Toggle(on?)
	(2.38) Quiet Corners (spec §5, plan R7): new art only. The strip is CompassStrip<Race> (560 x 52 design), the ticks a
	tiled CompassTicks (30 degrees a tile, tinted bone) in a clip over the strip's channel, the centre pointer
	CompassLubber<Race>; each falls back to today's ink strip, tick lines and knob while its id is 0 (Config.QuietCornersArt).
	Letters 24 px (N/E/S/W, bold) and 20 px (intercardinals), hidden within 16 px of a shown icon or the objective;
	readout 20 px, hidden in combat (spec §2). The strip is the Compass cluster of Controllers.Gui.HudState; a new
	readout subject wakes it. The Race attribute re-skins it.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local NpcConfig = require(ReplicatedStorage.Config.Npcs)
-- (2.38) Quiet Corners art; a missing module only means today's look
local QcOk, QuietCorners = pcall(function() return require((ReplicatedStorage :: any).Functions.QuietCorners) end)
local ArtOk, QuietCornersArt = pcall(function() return require((ReplicatedStorage :: any).Config.QuietCornersArt) end)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local MAX_WIDTH, HEIGHT = 560, 52 -- (2.38) was 32: CompassStrip's design height
local READOUT_Y, READOUT_H = 58, 24 -- (2.38) under the strip
local CHANNEL_X, CHANNEL_TOP, CHANNEL_BOTTOM = 24, 8.4, 43.6 -- (2.38) the strip art's channel (Config.QuietCornersArt Boxes.CompassStrip)
local LETTER_CLEAR = 16 -- (2.38) a letter never draws within this many px of a shown icon or the objective
local TICKS_BONE = Color3.fromRGB(236, 226, 206) -- (2.38)
local TICK_PHASE = 0 -- (2.38) degrees from the tile's left edge to its first major tick (tune against the uploaded art)
local WIDTH = MAX_WIDTH -- shrinks on narrow screens so it never runs into the top bar
local FOV = 160               -- degrees of view across the strip
local FACING = 7              -- degrees: "you're facing it" for the readout
local FACTION_THEME = { Vigil = `Vigil`; CrimsonCourt = `Court` }
local CARDINALS = { [0] = `N`; [45] = `NE`; [90] = `E`; [135] = `SE`; [180] = `S`; [225] = `SW`; [270] = `W`; [315] = `NW` }

local Local = {}
local Shared = {}
local Ui = nil
local Places = {} :: { any }
local On = true
local Region = nil :: { Name: string, Color: Color3 }?
local Subject = nil :: string? -- (2.38) what the readout names (not its distance): a new one wakes the Compass cluster

---| Helpers |---

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function bearing(V: Vector3): number
	return math.deg(math.atan2(V.X, -V.Z)) % 360
end

-- (2.38) the race's art for a piece, or nil (today's look)
local function art(Piece: string): string?
	if not (QcOk and ArtOk) then return nil end
	local Ok, Image = pcall(QuietCorners.Image, QuietCornersArt, Piece, Player:GetAttribute(`Race`))
	return if Ok then Image else nil
end

-- (2.38) the title font, bold
local function bold(Label: TextLabel, Face: any)
	local Ok = pcall(function()
		local F = if typeof(Face) == `EnumItem` then Font.fromEnum(Face) else Face
		Label.FontFace = Font.new(F.Family, Enum.FontWeight.Bold, F.Style)
	end)
	if not Ok then pcall(function() Label.Font = Face end) end
end

-- (2.38) Controllers.Gui.HudState, required lazily; never breaks the compass
local function hudState(): any?
	local Ok, Mod = pcall(function() return require(script.Parent:FindFirstChild(`HudState`) :: ModuleScript) end)
	return if Ok then Mod else nil
end

local function wrap(A: number): number
	return (A + 180) % 360 - 180
end

local function edgeFade()
	return NumberSequence.new({
		NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.14, 0),
		NumberSequenceKeypoint.new(0.86, 0), NumberSequenceKeypoint.new(1, 1),
	})
end

---| Places (from map attributes) |---

function Local.Position(Thing: Instance): Vector3?
	if Thing:IsA(`BasePart`) then return Thing.Position end
	if Thing:IsA(`Model`) then return Thing:GetPivot().Position end
	return nil
end

function Local.Scan()
	local Found = {}
	local Seen = {}
	local Menu = workspace:FindFirstChild(`MenuScene`)
	local function add(Thing: Instance, Label: string, Icon: string, Color: Color3, Range: number)
		if Seen[Thing] then return end
		Seen[Thing] = true
		table.insert(Found, { Thing = Thing; Label = Label; Icon = Icon; Color = Color; Range = Range })
	end
	for _, D in workspace:GetDescendants() do
		if Menu and D:IsDescendantOf(Menu) then continue end
		if not (D:IsA(`BasePart`) or D:IsA(`Model`)) then continue end
		local Custom = D:GetAttribute(`Compass`)
		if typeof(Custom) == `string` then
			local Icon = D:GetAttribute(`CompassIcon`)
			add(D, Custom, if typeof(Icon) == `string` and Theme.Images[Icon] then Icon else `Pip`, C.Text, D:GetAttribute(`CompassRange`) or 200)
		elseif D:GetAttribute(`RoomId`) and D:GetAttribute(`Subject`) then
			add(D, `Room {D:GetAttribute(`RoomId`)} · {D:GetAttribute(`Subject`)}`, `IconNib`, C.Chalk, 90)
		elseif typeof(D:GetAttribute(`Faction`)) == `string` and D:IsA(`Model`) then
			local Id = D:GetAttribute(`Faction`)
			local F = Theme.Faction(FACTION_THEME[Id] or Id)
			local Def = FactionConfig.Factions[Id]
			add(D, `{Def and Def.Name or Id} · {D.Name}`, F.Icon, F.Accent, 400)
		elseif D:GetAttribute(`DuelPad`) and D.Parent then
			add(D.Parent, `Duel Ring`, `IconDuelRing`, C.Crimson, 300)
		elseif typeof(D:GetAttribute(`NpcPost`)) == `string` then
			local Id = D:GetAttribute(`NpcPost`)
			local Def = NpcConfig and (NpcConfig[Id] or (NpcConfig.Npcs and NpcConfig.Npcs[Id]))
			add(D, if typeof(Def) == `table` and Def.Name then Def.Name else Id, `Pip`, C.Gold, 120)
		end
	end
	-- only rebuild the markers when the set of places actually changed
	local Same = #Found == #Places
	if Same then
		for I, P in Found do
			if Places[I].Thing ~= P.Thing or Places[I].Label ~= P.Label then Same = false break end
		end
	end
	if not Same or not (Ui and Ui.Quest) then
		Places = Found
		Local.Markers()
	end
end

---| Build |---

function Local.Build()
	local Gui = new(`ScreenGui`, {
		Name = `NHCompass`; DisplayOrder = 18; ResetOnSpawn = false; IgnoreGuiInset = true;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling;
	}, Player:WaitForChild(`PlayerGui`))
	local Scale = new(`UIScale`, {}, Gui)
	local Root = new(`Frame`, {
		Name = `Compass`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 0, 10); Size = UDim2.fromOffset(WIDTH, HEIGHT + 30); -- (2.38) the readout's room under the strip
	}, Gui)
	-- (2.38) Back is CompassStrip<Race>, or (no id yet) today's ink strip: an empty image with the ink fill and faded ends (Skin)
	local Back = new(`ImageLabel`, {
		Name = `Back`; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.12; BorderSizePixel = 0; Image = ``;
		ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromOffset(WIDTH, HEIGHT);
	}, Root)
	local BackFade = new(`UIGradient`, { Transparency = edgeFade() }, Back)
	local Lines = {}
	for _, Y in { 0, HEIGHT - 1 } do
		local Line = new(`Frame`, { BackgroundColor3 = C.GoldDeep; BorderSizePixel = 0; Position = UDim2.fromOffset(0, Y); Size = UDim2.fromOffset(WIDTH, 1) }, Root)
		new(`UIGradient`, { Transparency = edgeFade() }, Line)
		table.insert(Lines, Line)
	end
	local Strip = new(`CanvasGroup`, { Name = `Strip`; BackgroundTransparency = 1; Size = UDim2.fromOffset(WIDTH, HEIGHT) }, Root)
	new(`UIGradient`, { Transparency = edgeFade() }, Strip)

	-- (2.38) the engraved ticks: CompassTicks tiled in a clip over the channel, scrolled with the heading (Step)
	local Clip = new(`Frame`, {
		Name = `Ticks`; BackgroundTransparency = 1; ClipsDescendants = true; ZIndex = 1; Visible = false;
		Position = UDim2.fromOffset(CHANNEL_X, CHANNEL_TOP); Size = UDim2.fromOffset(WIDTH - CHANNEL_X * 2, CHANNEL_BOTTOM - CHANNEL_TOP);
	}, Strip)
	local Tile = new(`ImageLabel`, {
		Name = `Tile`; BackgroundTransparency = 1; Image = ``; ImageColor3 = TICKS_BONE; ScaleType = Enum.ScaleType.Tile; ZIndex = 1;
	}, Clip)

	-- ticks and letters
	local Ticks = {}
	for D = 0, 345, 15 do
		local Letter = CARDINALS[D]
		local Item
		if Letter and #Letter == 1 then
			Item = new(`TextLabel`, {
				BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextSize = 24; Text = Letter; ZIndex = 2; -- (2.38) was 18
				TextColor3 = if Letter == `N` then C.Crimson else C.Text; AnchorPoint = Vector2.new(0.5, 0.5);
				Size = UDim2.fromOffset(36, 30); Position = UDim2.fromOffset(0, HEIGHT / 2);
			}, Strip)
			bold(Item, Theme.Fonts.Title) -- (2.38)
		elseif Letter then
			Item = new(`TextLabel`, {
				BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 20; Text = Letter; ZIndex = 2; -- (2.38) was 15
				TextColor3 = C.TextDim; AnchorPoint = Vector2.new(0.5, 0.5);
				Size = UDim2.fromOffset(36, 26); Position = UDim2.fromOffset(0, HEIGHT / 2);
			}, Strip)
		else
			-- today's tick line: only while CompassTicks has no id (Skin, Step)
			Item = new(`Frame`, {
				BackgroundColor3 = C.IronDim; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 1); ZIndex = 1;
				Size = UDim2.fromOffset(1, 6); Position = UDim2.fromOffset(0, CHANNEL_BOTTOM - 2); -- (2.38) in the channel
			}, Strip)
		end
		table.insert(Ticks, { Item = Item; Deg = D; Letter = Letter }) -- (2.38) Letter: kept clear of icons
	end
	-- centre notch: CompassLubber<Race>, or the kit's diamond knob (Skin)
	local Notch = new(`ImageLabel`, {
		Name = `Notch`; BackgroundTransparency = 1; Image = Theme.Images.Knob; ImageColor3 = C.Gold; ZIndex = 5;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0, HEIGHT); Size = UDim2.fromOffset(12, 12);
	}, Root)
	local Readout = new(`TextLabel`, {
		Name = `Readout`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 20; RichText = true; -- (2.38) was 15
		TextColor3 = C.Text; TextStrokeColor3 = C.Ink; TextStrokeTransparency = 0.4; Text = ``; TextTruncate = Enum.TextTruncate.AtEnd;
		Position = UDim2.fromOffset(0, READOUT_Y); Size = UDim2.fromOffset(WIDTH, READOUT_H); -- (2.38) was HEIGHT + 3, 18 tall
	}, Root)
	Ui = {
		Gui = Gui; Scale = Scale; Root = Root; Strip = Strip; Ticks = Ticks; Readout = Readout; Markers = {}; Back = Back; Lines = Lines; Notch = Notch;
		BackFade = BackFade; Clip = Clip; Tile = Tile; TileArt = false; -- (2.38)
	}
	Local.Skin() -- (2.38)
	Local.Place()
end

-- (2.38) Quiet Corners: the race's strip and lubber, and the ticks, each falling back to today's piece while its id is 0
function Local.Skin()
	if not Ui then return end
	local StripArt = art(`CompassStrip`)
	Ui.Back.Image = StripArt or ``
	Ui.Back.BackgroundTransparency = if StripArt then 1 else 0.12
	Ui.BackFade.Enabled = StripArt == nil -- the strip art fades its own ends
	for _, Line in Ui.Lines do Line.Visible = StripArt == nil end
	local Lubber = art(`CompassLubber`)
	if Lubber then
		Ui.Notch.Image = Lubber
		Ui.Notch.ImageColor3 = Color3.new(1, 1, 1)
		Ui.Notch.AnchorPoint = Vector2.new(0.5, 0)
		Ui.Notch.Position = UDim2.new(0.5, 0, 0, -8)
		Ui.Notch.Size = UDim2.fromOffset(48, 60)
	else
		Ui.Notch.Image = Theme.Images.Knob
		Ui.Notch.ImageColor3 = C.Gold
		Ui.Notch.AnchorPoint = Vector2.new(0.5, 0.5)
		Ui.Notch.Position = UDim2.new(0.5, 0, 0, HEIGHT)
		Ui.Notch.Size = UDim2.fromOffset(12, 12)
	end
	local TicksArt = art(`CompassTicks`)
	Ui.TileArt = TicksArt ~= nil
	Ui.Tile.Image = TicksArt or ``
	Ui.Clip.Visible = Ui.TileArt
	for _, T in Ui.Ticks do
		if not T.Letter and Ui.TileArt then T.Item.Visible = false end -- Step shows today's lines only without the tile
	end
end

function Local.Place()
	if not Ui then return end
	local View = if Kit.Viewport then Kit.Viewport() else (workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1920, 1080))
	local Phone = Kit.Phone ~= nil and Kit.Phone()
	local S = if Phone then Kit.Theme.Scale.PhoneTouchMin or 0.62 else math.clamp(View.Y / 1080, 0.8, 1.4)
	Ui.Scale.Scale = S
	-- keep clear of the top bar plate on the left (and the same margin on the right)
	local Bar = Player.PlayerGui:FindFirstChild(`NHTopBar`)
	local Plate = Bar and Bar:FindFirstChild(`Plate`, true)
	local Left = if Plate and Plate.AbsoluteSize.X > 0 then Plate.AbsolutePosition.X + Plate.AbsoluteSize.X + 16 else 180
	local Room = (View.X / 2 - Left) * 2 / S
	WIDTH = math.floor(math.clamp(Room, 240, MAX_WIDTH))
	-- no room beside the top bar (phones: Roblox's own buttons push the bar right): under the top strip, on the left
	local Top = 10 -- (2.38) the strip's top in design px, for the fade's height below
	if Room < 240 then
		local Inset = (game:GetService(`GuiService`):GetGuiInset()).Y
		Ui.Root.AnchorPoint = Vector2.new(0, 0)
		Ui.Root.Position = UDim2.fromOffset(12 / S, (Inset + 4) / S)
		Top = (Inset + 4) / S
	else
		Ui.Root.AnchorPoint = Vector2.new(0.5, 0)
		Ui.Root.Position = UDim2.new(0.5, 0, 0, 10)
	end
	Ui.Root.Size = UDim2.fromOffset(WIDTH, HEIGHT + 30) -- (2.38)
	Ui.Back.Size = UDim2.fromOffset(WIDTH, HEIGHT)
	Ui.Strip.Size = UDim2.fromOffset(WIDTH, HEIGHT)
	for _, Line in Ui.Lines do Line.Size = UDim2.fromOffset(WIDTH, 1) end
	Ui.Readout.Size = UDim2.fromOffset(WIDTH, READOUT_H) -- (2.38) the notch is placed by scale now (Skin)
	-- (2.38) the tick clip over the channel, and its tile: 30 degrees a tile
	local ChannelW, ChannelH = WIDTH - CHANNEL_X * 2, CHANNEL_BOTTOM - CHANNEL_TOP
	local TileW = WIDTH / FOV * 30
	Ui.Clip.Size = UDim2.fromOffset(ChannelW, ChannelH)
	Ui.Tile.TileSize = UDim2.fromOffset(TileW, ChannelH)
	Ui.Tile.Size = UDim2.fromOffset(ChannelW + TileW * 2, ChannelH)
	-- (2.38) HudState's fade is 130 design px; when the strip drops under the phone inset, grow it so the readout isn't clipped
	local Fade = Ui.Gui:FindFirstChild(`QcFade`)
	if Fade and Fade:IsA(`CanvasGroup`) then
		Fade.Size = UDim2.new(1, 0, 0, math.max(130, math.ceil(Top + HEIGHT + 30 + 8)))
	end
end

function Local.Marker(Icon: string, Color: Color3)
	local M = new(`ImageLabel`, {
		Name = `Marker`; BackgroundTransparency = 1; Image = Theme.Images[Icon] or Theme.Images.Pip; ImageColor3 = if Theme.Baked and Theme.Baked[Icon] then Color3.new(1, 1, 1) else Color;
		AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(18, 18); Visible = false; ZIndex = 3;
	}, Ui.Strip)
	return M
end

function Local.Markers()
	if not Ui then return end
	for _, M in Ui.Markers do M:Destroy() end
	Ui.Markers = {}
	for I, P in Places do Ui.Markers[I] = Local.Marker(P.Icon, P.Color) end
	if not Ui.Quest then
		Ui.Quest = Local.Marker(`Knob`, C.Gold)
		Ui.Quest.Size = UDim2.fromOffset(20, 20)
		Ui.Quest.ZIndex = 4
	end
end

---| Update |---

function Local.QuestTarget(): (Vector3?, string?)
	local Tracker = Player.PlayerGui:FindFirstChild(`QuestTracker`)
	local Marker = Tracker and Tracker:FindFirstChild(`QuestMarker`, true)
	if not (Marker and Marker:IsA(`BillboardGui`) and Marker.Enabled and Marker.Adornee) then return nil end
	local Pos = Local.Position(Marker.Adornee)
	local Label = Marker:FindFirstChildWhichIsA(`TextLabel`, true)
	local Text = Label and Label.ContentText:match(`^[^\n]+`) or `Objective`
	return Pos, (Text:gsub(`^◆%s*`, ``))
end

function Local.Step()
	if not (Ui and On) then return end
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local Look = Cam.CFrame.LookVector
	local Heading = bearing(Vector3.new(Look.X, 0, Look.Z))
	local From = Cam.CFrame.Position
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	local Me = Root and Root.Position or From
	local function x(Rel: number): number return WIDTH / 2 + Rel / (FOV / 2) * (WIDTH / 2) end

	-- (2.38) the tiled ticks scroll with the heading: a tile is 30 degrees; the heading sits at the clip's centre
	if Ui.TileArt then
		local TileW = WIDTH / FOV * 30
		local Centre = WIDTH / 2 - CHANNEL_X
		local Phase = (((Heading - TICK_PHASE) % 30) / 30) * TileW
		Ui.Tile.Position = UDim2.fromOffset((Centre % TileW) - TileW - Phase, 0)
	end

	local Shown = {} :: { number } -- (2.38) the x of every icon on the strip, for the letters' clearance
	local Best, BestRel = nil, FACING
	for I, P in Places do
		local M = Ui.Markers[I]
		local Pos = M and P.Thing.Parent and Local.Position(P.Thing)
		if Pos then
			local Flat = Vector3.new(Pos.X - Me.X, 0, Pos.Z - Me.Z)
			local Dist = Flat.Magnitude
			local Rel = wrap(bearing(Flat) - Heading)
			local Show = Dist <= P.Range and Dist > 4 and math.abs(Rel) <= FOV / 2
			M.Visible = Show
			if Show then
				M.Position = UDim2.fromOffset(x(Rel), HEIGHT / 2)
				table.insert(Shown, x(Rel)) -- (2.38)
				-- closer places sit brighter
				M.ImageTransparency = math.clamp(Dist / P.Range, 0, 0.55)
				if math.abs(Rel) < BestRel then Best, BestRel = { P.Label, Dist, P.Color }, math.abs(Rel) end
			end
		elseif M then
			M.Visible = false
		end
	end

	-- your quest: always shown, pinned to the edge when it's behind you
	local QPos, QLabel = Local.QuestTarget()
	if QPos and Ui.Quest then
		local Flat = Vector3.new(QPos.X - Me.X, 0, QPos.Z - Me.Z)
		local Rel = wrap(bearing(Flat) - Heading)
		local Clamped = math.clamp(Rel, -FOV / 2 + 6, FOV / 2 - 6)
		Ui.Quest.Visible = true
		Ui.Quest.Position = UDim2.fromOffset(x(Clamped), HEIGHT / 2)
		table.insert(Shown, x(Clamped)) -- (2.38)
		Ui.Quest.Rotation = if Clamped ~= Rel then (if Rel > 0 then 90 else -90) else 0
		if math.abs(Rel) < FACING * 2 then Best = { QLabel, Flat.Magnitude, C.Gold } end
	elseif Ui.Quest then
		Ui.Quest.Visible = false
	end

	-- ticks and letters (2.38: after the icons, so a letter can step aside for them)
	for _, T in Ui.Ticks do
		local Rel = wrap(T.Deg - Heading)
		local In = math.abs(Rel) <= FOV / 2
		if not T.Letter and Ui.TileArt then In = false end -- (2.38) the tile draws the ticks
		if In then
			local X = x(Rel)
			T.Item.Position = UDim2.fromOffset(X, T.Item.Position.Y.Offset)
			-- (2.38) a letter never draws within LETTER_CLEAR px of a shown icon (edge to edge; icons are up to 20 wide)
			if T.Letter then
				local Half = math.max(T.Item.TextBounds.X, 12) / 2
				for _, Mx in Shown do
					if math.abs(Mx - X) < Half + 10 + LETTER_CLEAR then In = false break end
				end
			end
		end
		T.Item.Visible = In
	end

	local Text, Now = ``, nil
	if Best then
		Text = `<font color="#{Best[3]:ToHex()}">◆</font>  {Best[1]}  <font color="#{C.TextFaint:ToHex()}">·  {math.floor(Best[2])} studs</font>`
		Now = Best[1]
	elseif Region then
		-- facing nothing: the place you are in, quietly (Controllers.World.Regions)
		Text = `<font color="#{Region.Color:ToHex()}">◇</font>  <font color="#{C.TextDim:ToHex()}">{Region.Name}</font>`
		Now = Region.Name
	end
	if Ui.Readout.Text ~= Text then Ui.Readout.Text = Text end
	-- (2.38) a new subject in the readout (not its distance ticking down as you walk) wakes the Compass cluster
	if Now ~= Subject then
		Subject = Now
		if Now ~= nil then
			local Hud = hudState()
			if Hud then pcall(Hud.Wake, `Compass`) end
		end
	end
	-- (2.38) spec §2: no readout in combat
	Ui.Readout.Visible = Player:GetAttribute(`NHHudState`) ~= `Combat`
end

---| API |---

-- the place you are in, shown under the strip when you are not facing anything (nil clears it)
function Shared.SetRegion(Name: string?, Color: Color3?)
	Region = if Name then { Name = Name; Color = Color or C.Gold } else nil
end

function Shared.Toggle(Show: boolean?)
	if Show == nil then Show = not On end
	On = Show
	if Ui then Ui.Root.Visible = On end
end

function Shared.OnStart()
	Local.Build()
	Local.Scan()
	-- (the game's toasts sit just under the compass: Controllers.Gui.Notifications places them at y = 72)
	task.spawn(function()
		while true do
			task.wait(10)
			pcall(Local.Scan)
		end
	end)
	local Cam = workspace.CurrentCamera
	if Cam then Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(Local.Place) end
	-- the top bar is built (and moved by Roblox's own buttons) after the compass: re-check now and then
	task.spawn(function()
		while Ui and Ui.Gui.Parent do
			task.wait(2)
			pcall(Local.Place)
		end
	end)
	task.delay(2, Local.Place) -- once the top bar has settled
	-- (audit) back off for a second after an error (task.wait in the handler didn't: the next frame runs anyway)
	local ErrorUntil = 0
	RunService.RenderStepped:Connect(function()
		if os.clock() < ErrorUntil then return end
		local Ok, Err = pcall(Local.Step)
		if not Ok then warn(`[Compass] {Err}`) ErrorUntil = os.clock() + 1 end
	end)
	-- (2.38) Quiet Corners: each race its own strip and lubber
	Player:GetAttributeChangedSignal(`Race`):Connect(function() pcall(Local.Skin) end)
	-- (2.38) the strip is the Compass cluster of Controllers.Gui.HudState; Place then sizes the fade to hold it
	local Hud = hudState()
	if Hud then
		local Ok, Err = pcall(Hud.Adopt, Ui.Gui, `Compass`, { `Compass` }, `Top`, 130)
		if not Ok then warn(`[Compass] HudState.Adopt failed: {Err}`) end
		pcall(Local.Place)
	end
end

return Shared
