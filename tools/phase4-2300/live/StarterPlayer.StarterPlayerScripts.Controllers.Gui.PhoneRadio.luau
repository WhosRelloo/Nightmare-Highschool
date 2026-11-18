--[[ (2.30) PhoneRadio (client). Controllers.Gui.PhoneRadio: Night FM, remade as a music app in the school's dress
	(the owner's reference, 2026-11-18: a Spotify-like home, library and now-playing, with a floating tab bar).
	Tabs: Home (greeting, chips, the Midnight Broadcast banner, recent tracks), Library (saved + recent, add by ID),
	Station (Midnight Broadcast, 21:00-03:00: caller lines, campus reports, transmissions; World.Broadcast), and the
	Now Playing sheet (cover, title, creator, like, waveform scrubber, loop / prev / play / next / volume).
	Art: "The Midnight Wireless" (owner: "wayy higher quality ... UNIQUE designs ... PBR textures, easy to read"), baked by
	art/ui/hud/make_nightfm_ui.py and staged in art/group-upload-nightfm (group 15981569): lacquer, gilt bezels, amethyst
	enamel, 12 painted covers, 16 bold icons. Until an id in ART is set, that piece falls back to the kit look (never the Seal).
	Voices (the owner's clips, Config.Broadcast.Voice): tuning in to the Station tab plays the host, the hall monitors, the
	PSA or the lore (World.Broadcast.Voice picks), with the music ducked under it, and the next one after a gap while you stay.
	Driven by Controllers.Gui.Phone: Open(Ctx), Tick(). ]]
local Players = game:GetService(`Players`)
local MarketplaceService = game:GetService(`MarketplaceService`)
local UserInputService = game:GetService(`UserInputService`)

local Shared = {}
local Ctx = nil
local Ui = nil
local Tab = `Home`
local Chip = `All`
local Info = {} :: { [number]: { Title: string, Creator: string } }

local PURPLE = Color3.fromRGB(150, 95, 230)
local PURPLE_DEEP = Color3.fromRGB(46, 22, 78)
local COVERS = { `IconAppRadio`, `IconCandle`, `Crest`, `IconBannerFullMoon`, `IconBannerBlueMoon`, `IconBannerCrimsonMoon`, `IconNib`, `Bell`, `IconCardBack` } -- (owner: no Seal icon)
local GRADS = {
	{ Color3.fromRGB(120, 60, 200), Color3.fromRGB(150, 30, 60) }, { Color3.fromRGB(70, 40, 150), Color3.fromRGB(20, 10, 40) },
	{ Color3.fromRGB(170, 70, 140), Color3.fromRGB(60, 20, 90) }, { Color3.fromRGB(90, 30, 40), Color3.fromRGB(150, 95, 230) },
}

-- (2.30) Night FM's PBR art (art/group-upload-nightfm, uploaded under group 15981569). 0 = not imported yet: the kit look stands in.
local ART = {
	FmBackdrop = 0; FmCard = 0; FmChip = 0; FmChipOn = 0; FmKnob = 0; FmKnobOn = 0; FmTabBar = 0; FmOnAir = 0; FmBanner = 0; FmCoverFrame = 0;
	FmCover01 = 0; FmCover02 = 0; FmCover03 = 0; FmCover04 = 0; FmCover05 = 0; FmCover06 = 0; FmCover07 = 0; FmCover08 = 0; FmCover09 = 0; FmCover10 = 0; FmCover11 = 0; FmCover12 = 0;
	FmIconPlay = 0; FmIconPause = 0; FmIconPrev = 0; FmIconNext = 0; FmIconLoop = 0; FmIconQueue = 0; FmIconHeart = 0; FmIconHeartFull = 0; FmIconSearch = 0; FmIconBell = 0; FmIconHome = 0; FmIconLibrary = 0; FmIconStation = 0; FmIconBack = 0; FmIconPlus = 0; FmIconVolume = 0;
}
local function art(Name: string): string?
	local Id = ART[Name]
	if type(Id) == `string` then return Id end -- (a local preview: rbxasset://)
	return if Id and Id > 0 then `rbxassetid://` .. Id else nil
end
local ICON_GOLD = Color3.fromRGB(240, 206, 130)
-- a 9-slice plate from the art (Rect in pixels of the source, Scale shrinks the corners to fit the phone)
local SLICES = { FmCard = { Rect.new(44, 44, 148, 148), 0.3 }; FmChip = { Rect.new(30, 30, 162, 34), 0.47 }; FmChipOn = { Rect.new(30, 30, 162, 34), 0.47 };
	FmTabBar = { Rect.new(60, 60, 452, 68), 0.45 }; FmOnAir = { Rect.new(34, 34, 222, 38), 0.36 } }
local function sliced(Img, Name: string): boolean
	local A = art(Name)
	if not A then return false end
	Img.Image = A
	Img.ScaleType = Enum.ScaleType.Slice
	Img.SliceCenter = SLICES[Name][1]
	Img.SliceScale = SLICES[Name][2]
	Img.BackgroundTransparency = 1
	return true
end

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local function corner(I, R) new(`UICorner`, { CornerRadius = if R then UDim.new(0, R) else UDim.new(1, 0) }, I) end
local function T() return Ctx.Theme end
local function label(Parent, Text, Size, Props)
	local L = new(`TextLabel`, { BackgroundTransparency = 1; Text = Text; TextSize = Size; Font = T().Fonts.Body; TextColor3 = T().Colors.Text;
		TextXAlignment = Enum.TextXAlignment.Left; RichText = true; TextTruncate = Enum.TextTruncate.AtEnd }, Parent)
	for K, V in Props or {} do L[K] = V end
	return L
end
local function hash(N: number): number return (N * 2654435761) % 4294967296 end

-- (2.30) the station's voice: one clip at a time, the music ducked under it
local Voice = { Sound = nil :: Sound?; Now = nil :: any; Busy = false; NextAt = 0; Ducked = nil :: number? }
local function duck(On: boolean)
	local M = Ctx and Ctx.Music and Ctx.Music.Sound
	if On then
		if M and not Voice.Ducked then Voice.Ducked = M.Volume M.Volume = M.Volume * 0.3 end
	else
		if M and Voice.Ducked then M.Volume = Voice.Ducked end
		Voice.Ducked = nil
	end
end
function Shared.StopVoice()
	if Voice.Sound then Voice.Sound:Destroy() Voice.Sound = nil end
	Voice.Now = nil
	duck(false)
	Voice.NextAt = os.clock() + 20
end
-- tuning in: ask the station for the next voice (nothing while one plays, or before the gap is up)
function Shared.TuneIn(Force: boolean?)
	if Voice.Busy or (Voice.Sound and Voice.Now) then return end
	if not Force and os.clock() < Voice.NextAt then return end
	Voice.Busy = true
	task.spawn(function()
		local V = Ctx and Ctx.Call(`Voice`)
		Voice.Busy = false
		if not (V and V.Id) then Voice.NextAt = os.clock() + 60 return end
		local S = new(`Sound`, { Name = `NightFMVoice`; SoundId = if typeof(V.Id) == `string` then V.Id else `rbxassetid://{V.Id}`; Volume = 0.9 }, game:GetService(`SoundService`))
		Voice.Sound, Voice.Now = S, V
		duck(true)
		S.Ended:Connect(function()
			if Voice.Sound ~= S then return end
			S:Destroy()
			Voice.Sound, Voice.Now = nil, nil
			duck(false)
			Voice.NextAt = os.clock() + (V.Gap or 45)
			Shared.Refresh()
			task.delay((V.Gap or 45) + 0.5, function() -- still tuned in? the next voice
				if Ui and Ui.Root and Ui.Root.Parent and Tab == `Station` then Shared.TuneIn() end
			end)
		end)
		S:Play()
		pcall(Ctx.Kit.PlaySound, `Tick`, 0.4, 0.7) -- the dial clicking over
		Shared.Refresh()
	end)
end

local function titleOf(Id: number): (string, string)
	local I = Info[Id]
	if I then return I.Title, I.Creator end
	Info[Id] = { Title = `Track {Id}`; Creator = `Night FM` }
	task.spawn(function()
		local Ok, P = pcall(MarketplaceService.GetProductInfo, MarketplaceService, Id, Enum.InfoType.Asset)
		if Ok and P then
			Info[Id] = { Title = P.Name or `Track {Id}`; Creator = (P.Creator and P.Creator.Name) or `Unknown` }
			Shared.Refresh()
		end
	end)
	return Info[Id].Title, Info[Id].Creator
end

-- a cover: one of the kit's emblems on a gradient, picked by the track id (the same track, the same cover)
local function cover(Parent, Id: number, Size: number)
	local H = hash(Id)
	local Plate = art(string.format(`FmCover%02d`, H % 12 + 1))
	if Plate then
		local F = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Plate; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromOffset(Size, Size) }, Parent)
		corner(F, math.floor(Size / 6))
		return F
	end
	local G = GRADS[H % #GRADS + 1]
	local F = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(F, math.floor(Size / 6))
	new(`UIGradient`, { Rotation = 35 + H % 90; Color = ColorSequence.new(G[1], G[2]) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.Glow; ImageTransparency = 0.55; Size = UDim2.fromScale(1, 1) }, F)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images[COVERS[(H // 7) % #COVERS + 1]]; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.62, 0.62) }, F)
	return F
end

-- a round button on the kit's orb ring, with a glyph
local function roundBtn(Parent, Icon: string, Glyph: string, Size: number, Filled: boolean?, Fn)
	local Knob, Img = art(if Filled then `FmKnobOn` else `FmKnob`), art(`FmIcon` .. Icon)
	if Knob and Img then
		local B = new(`ImageButton`, { Image = Knob; BackgroundTransparency = 1; AutoButtonColor = true; Size = UDim2.fromOffset(Size, Size) }, Parent)
		new(`ImageLabel`, { Name = `Icon`; BackgroundTransparency = 1; Image = Img; ImageColor3 = if Filled then Color3.new(1, 1, 1) else ICON_GOLD;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.6, 0.6) }, B)
		B.Activated:Connect(function() pcall(Ctx.Kit.PlaySound, `Tick`, 0.5, 1.3) Fn() end)
		return B
	end
	local B = new(`TextButton`, { Text = Glyph; Font = T().Fonts.Title; TextSize = math.floor(Size * 0.42); TextColor3 = if Filled then Color3.new(1, 1, 1) else T().Colors.Gold;
		BackgroundColor3 = if Filled then PURPLE else T().Colors.Ink; BackgroundTransparency = if Filled then 0 else 0.25; AutoButtonColor = true; Size = UDim2.fromOffset(Size, Size) }, Parent)
	corner(B)
	new(`UIStroke`, { Color = if Filled then Color3.fromRGB(210, 180, 255) else T().Colors.GoldDeep; Thickness = 1; Transparency = 0.35 }, B)
	-- (a UIGradient here would tint the glyph as well, so filled buttons are a solid fill)
	B.Activated:Connect(function() pcall(Ctx.Kit.PlaySound, `Tick`, 0.5, 1.3) Fn() end)
	return B
end
-- swap a round button's icon (art) or glyph (stand-in), and optionally its colour
local function setIcon(B, Icon: string, Glyph: string, Color: Color3?)
	local I = B:FindFirstChild(`Icon`)
	if I then
		I.Image = art(`FmIcon` .. Icon) or I.Image
		if Color then I.ImageColor3 = Color end
	else
		B.Text = Glyph
		if Color then B.TextColor3 = Color end
	end
end

local function chip(Parent, Text: string, Active: boolean, Fn)
	local Img = Instance.new(`ImageButton`)
	if sliced(Img, if Active then `FmChipOn` else `FmChip`) then
		Img.AutomaticSize = Enum.AutomaticSize.X
		Img.Size = UDim2.fromOffset(0, 30)
		Img.Parent = Parent
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 15); PaddingRight = UDim.new(0, 15) }, Img)
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Text; Font = T().Fonts.Title; TextSize = 14; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromScale(0, 1);
			TextColor3 = if Active then Color3.new(1, 1, 1) else Color3.fromRGB(225, 210, 190) }, Img)
		Img.Activated:Connect(Fn)
		return Img
	end
	Img:Destroy()
	local B = new(`TextButton`, { Text = Text; Font = T().Fonts.Body; TextSize = 13; TextColor3 = if Active then Color3.new(1, 1, 1) else T().Colors.TextDim;
		BackgroundColor3 = if Active then PURPLE else T().Colors.Ink; BackgroundTransparency = if Active then 0 else 0.3; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, 28) }, Parent)
	corner(B)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 14); PaddingRight = UDim.new(0, 14) }, B)
	new(`UIStroke`, { Color = if Active then Color3.fromRGB(210, 180, 255) else T().Colors.IronDim; Transparency = 0.4 }, B)
	B.Activated:Connect(Fn)
	return B
end

-- a track row: cover, title, creator, a round play button (the reference's list)
local function row(Parent, Id: number, Order: number)
	local Carded = art(`FmCard`) ~= nil
	local R = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, if Carded then 62 else 52); LayoutOrder = Order }, Parent)
	if Carded then sliced(new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, R), `FmCard`) end
	local X0, Y0 = if Carded then 9 else 0, if Carded then 9 else 4
	local C = cover(R, Id, 44) C.Position = UDim2.fromOffset(X0, Y0)
	local Title, By = titleOf(Id)
	label(R, Title, 15, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(245, 236, 222); Position = UDim2.fromOffset(X0 + 54, Y0 + 4); Size = UDim2.new(1, -(X0 + 112), 0, 18) })
	label(R, By, 13, { TextColor3 = Color3.fromRGB(196, 184, 206); Position = UDim2.fromOffset(X0 + 54, Y0 + 24); Size = UDim2.new(1, -(X0 + 112), 0, 16) })
	local Playing = Ctx.Music.Id == Id and Ctx.Music.Sound and Ctx.Music.Sound.IsPlaying
	local B = roundBtn(R, if Playing then `Pause` else `Play`, if Playing then `\u{23F8}` else `\u{25B6}`, 34, false, function()
		if Ctx.Music.Id == Id and Ctx.Music.Sound then
			if Ctx.Music.Sound.IsPlaying then Ctx.Music.Sound:Pause() else Ctx.Music.Sound:Resume() end
		else Ctx.Play(Id) end
		Shared.Render()
	end)
	B.Position = if Carded then UDim2.new(1, -46, 0, 13) else UDim2.new(1, -38, 0, 9)
	R.Activated:Connect(function() if Ctx.Music.Id ~= Id then Ctx.Play(Id) end Shared.NowPlaying() end)
	return R
end

local function body(Parent)
	local S = new(`ScrollingFrame`, { BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, 0, 1, -74);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 2; ScrollBarImageColor3 = T().Colors.IronDim }, Parent)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 8) }, S)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 16); PaddingRight = UDim.new(0, 16); PaddingTop = UDim.new(0, 12); PaddingBottom = UDim.new(0, 12) }, S)
	return S
end

local function heading(Parent, Text, Order, Right, RightFn)
	local F = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = Order }, Parent)
	label(F, Text, 17, { Font = T().Fonts.Title; TextColor3 = T().Colors.Gold; Size = UDim2.new(1, -80, 1, 0) })
	if Right then
		local B = new(`TextButton`, { Text = Right .. ` \u{203A}`; Font = T().Fonts.Title; TextSize = 13; TextColor3 = Color3.fromRGB(205, 190, 215); BackgroundTransparency = 1;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.fromOffset(80, 24); TextXAlignment = Enum.TextXAlignment.Right }, F)
		B.Activated:Connect(RightFn)
	end
end

function Shared.Home(Parent)
	local S = body(Parent)
	-- greeting with avatar, search and bell (the reference's header)
	local Head = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 86); LayoutOrder = 1 }, S)
	local Av = new(`ImageLabel`, { BackgroundColor3 = T().Colors.Ink; Size = UDim2.fromOffset(40, 40) }, Head)
	corner(Av) new(`UIStroke`, { Color = T().Colors.Gold; Transparency = 0.3 }, Av)
	task.spawn(function()
		local Ok, Url = pcall(Players.GetUserThumbnailAsync, Players, Players.LocalPlayer.UserId, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100)
		if Ok then Av.Image = Url end
	end)
	local B1 = roundBtn(Head, `Search`, `\u{1F50D}`, 36, false, function() Tab = `Library` Shared.Render() end) B1.Position = UDim2.new(1, -82, 0, 2)
	local B2 = roundBtn(Head, `Bell`, `\u{1F514}`, 36, false, function() Tab = `Station` Shared.Render() end) B2.Position = UDim2.new(1, -38, 0, 2)
	local Hour = game:GetService(`Lighting`).ClockTime -- the school's clock (SchoolClock syncs Lighting), not the real one
	local Hi = if Hour < 12 then `Good morning` elseif Hour < 18 then `Good afternoon` else `Good evening`
	label(Head, `{Hi}, {Players.LocalPlayer.DisplayName}`, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(0, 50); Size = UDim2.new(1, 0, 0, 30) })
	-- chips
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Recent`, `Saved`, `Station` } do
		chip(Chips, Name, Chip == Name, function()
			if Name == `Station` then Tab = `Station` else Chip = Name end
			Shared.Render()
		end)
	end
	-- the banner: tonight on Night FM (the reference's "For you" card)
	heading(S, `Tonight`, 3)
	local St = Ctx.Station or { OnAir = false }
	local Banner = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 132); LayoutOrder = 4 }, S)
	corner(Banner, 16)
	new(`UIGradient`, { Rotation = 20; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(110, 50, 190)), ColorSequenceKeypoint.new(1, Color3.fromRGB(140, 30, 60)) }) }, Banner)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.PanelBg; ImageTransparency = 0.85; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Banner)
	local BArt = art(`FmBanner`)
	if BArt then -- the painted bell tower and wireless mast under the moon (the left is left clear for the words)
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = BArt; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Banner)
		new(`UIStroke`, { Color = ICON_GOLD; Transparency = 0.45; Thickness = 1.5 }, Banner)
	else
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = T().Images.IconAppRadio; ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -10, 0.5, 0); Size = UDim2.fromOffset(104, 104) }, Banner)
	end
	label(Banner, `Midnight Broadcast`, 19, { Font = T().Fonts.Title; TextColor3 = Color3.new(1, 0.97, 0.92); Position = UDim2.fromOffset(14, 12); Size = UDim2.new(0.62, 0, 0, 24) })
	label(Banner, if St.OnAir then `On air now: callers, campus reports, and things on the static.` else `Off air until 9 PM. The school talks after dark.`, 13,
		{ TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = Color3.fromRGB(240, 232, 248); TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(14, 40); Size = UDim2.new(0.5, 0, 0, 50) })
	local Go = new(`TextButton`, { Text = if St.OnAir then `Tune in` else `See tonight`; Font = T().Fonts.Title; TextSize = 13; TextColor3 = Color3.new(1, 1, 1);
		BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 0.82; Position = UDim2.fromOffset(14, 92); Size = UDim2.fromOffset(110, 28) }, Banner)
	corner(Go)
	local GoArt = new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, Go)
	if sliced(GoArt, `FmChipOn`) then Go.BackgroundTransparency = 1 GoArt.ZIndex = 0 Go.TextTransparency = 1
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Go.Text; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Go)
	else GoArt:Destroy() new(`UIStroke`, { Color = Color3.new(1, 1, 1); Transparency = 0.5 }, Go) end
	Go.Activated:Connect(function() Tab = `Station` Shared.Render() end)
	-- the list
	local Ids = if Chip == `Saved` then (Ctx.State.Liked or {}) else (Ctx.State.Recent or {})
	heading(S, if Chip == `Saved` then `Saved` else `Recently played`, 5, `Show all`, function() Tab = `Library` Shared.Render() end)
	if #Ids == 0 then label(S, `<i>Nothing here yet. Add a track by its audio ID in your library.</i>`, 13, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextColor3 = T().Colors.TextDim; Size = UDim2.new(1, 0, 0, 34); LayoutOrder = 6 }) end
	for K, Id in Ids do if K <= 6 then row(S, Id, 10 + K) end end
end

function Shared.Library(Parent)
	local S = body(Parent)
	label(S, `Your library`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Chips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 2 }, S)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 6) }, Chips)
	for _, Name in { `All`, `Saved`, `Recent` } do chip(Chips, Name, Chip == Name, function() Chip = Name Shared.Render() end) end
	local Input, Api = Ctx.Kit.SearchBar({ placeholder = `Add a track: audio ID, then Enter`; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = 3; Parent = S;
		onSubmit = function(Text) local N = tonumber((Text or ``):match(`%d+`)) if N then Ctx.Play(N) Shared.NowPlaying() end end })
	local Seen, Ids = {}, {}
	local function add(List) for _, Id in List or {} do if not Seen[Id] then Seen[Id] = true table.insert(Ids, Id) end end end
	if Chip ~= `Recent` then add(Ctx.State.Liked) end
	if Chip ~= `Saved` then add(Ctx.State.Recent) end
	if #Ids == 0 then label(S, `<i>Nothing yet.</i>`, 15, { TextColor3 = Color3.fromRGB(205, 192, 218); Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 4 }) end
	for K, Id in Ids do row(S, Id, 10 + K) end
end

function Shared.Station(Parent)
	local S = body(Parent)
	local St = Ctx.Station or { OnAir = false; Items = {}; LastRead = 0 }
	label(S, `Midnight Broadcast`, 22, { Font = T().Fonts.Title; Size = UDim2.new(1, 0, 0, 30); LayoutOrder = 1 })
	local Badge = new(`TextLabel`, { Text = if St.OnAir then `\u{25CF}  ON AIR` else `OFF AIR  \u{00B7}  9 PM to 3 AM`; Font = T().Fonts.Title; TextSize = 12;
		TextColor3 = Color3.new(1, 1, 1); BackgroundColor3 = if St.OnAir then T().Colors.Crimson else T().Colors.Iron; AutomaticSize = Enum.AutomaticSize.X;
		Size = UDim2.fromOffset(0, 24); LayoutOrder = 2 }, S)
	corner(Badge) new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12) }, Badge)
	if St.OnAir and art(`FmOnAir`) then -- the crimson enamel lamp
		local Lamp = new(`ImageLabel`, { ZIndex = 0; Size = UDim2.new(1, 24, 1, 4); Position = UDim2.fromOffset(-12, -2) }, Badge)
		sliced(Lamp, `FmOnAir`)
		Badge.BackgroundTransparency = 1
		Badge.TextTransparency = 1 -- (it still sizes the badge) the words ride above the lamp
		new(`TextLabel`, { BackgroundTransparency = 1; Text = Badge.Text; Font = Badge.Font; TextSize = 13; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Badge)
	end
	if Voice.Now then -- who's on the air right now (the voice playing), with a stop
		local V = Voice.Now
		local Card = new(if art(`FmCard`) then `ImageLabel` else `Frame`, { BackgroundColor3 = PURPLE_DEEP; BackgroundTransparency = 0.15; Size = UDim2.new(1, 0, 0, 66); LayoutOrder = 3 }, S)
		corner(Card, 12)
		if art(`FmCard`) then sliced(Card, `FmCard`) Card.ImageColor3 = Color3.fromRGB(215, 185, 255) else new(`UIStroke`, { Color = PURPLE; Transparency = 0.3 }, Card) end
		local Pad = if art(`FmCard`) then 12 else 10
		label(Card, `<font color="#{Color3.fromRGB(255, 120, 130):ToHex()}">\u{25CF}</font>  ON THE AIR  \u{00B7}  {string.upper(V.Who or `Night FM`)}`, 11,
			{ Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(215, 190, 255); Position = UDim2.fromOffset(Pad, 10); Size = UDim2.new(1, -(Pad + 56), 0, 14) })
		label(Card, V.Title or ``, 16, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(248, 240, 228); Position = UDim2.fromOffset(Pad, 28); Size = UDim2.new(1, -(Pad + 56), 0, 22) })
		local Stop = roundBtn(Card, `Pause`, `\u{23F9}`, 38, false, function() Shared.StopVoice() Shared.Refresh() end)
		Stop.AnchorPoint = Vector2.new(1, 0.5) Stop.Position = UDim2.new(1, -(Pad - 2), 0.5, 0)
	elseif St.OnAir or Voice.NextAt > 0 then -- (nothing playing) a dial to tune in again
		local Go = new(`TextButton`, { Text = `\u{1F4FB}  Tune in`; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); BackgroundColor3 = PURPLE;
			AutoButtonColor = true; Size = UDim2.fromOffset(120, 32); LayoutOrder = 3 }, S)
		corner(Go)
		local GoArt = new(`ImageLabel`, { Size = UDim2.fromScale(1, 1) }, Go)
		if sliced(GoArt, `FmChipOn`) then Go.BackgroundTransparency = 1 GoArt.ZIndex = 0 Go.TextTransparency = 1
			new(`TextLabel`, { BackgroundTransparency = 1; Text = `Tune in`; Font = T().Fonts.Title; TextSize = 14; TextColor3 = Color3.new(1, 1, 1); ZIndex = 2; Size = UDim2.fromScale(1, 1) }, Go)
		else GoArt:Destroy() end
		Go.Activated:Connect(function() Shared.TuneIn(true) end)
	end
	local Kick = { Announcement = `ANNOUNCEMENT`; IncidentReport = `CAMPUS REPORT`; CallerLine = `CALLER LINE`; Transmission = `TRANSMISSION` }
	local Items = St.Items or {}
	if #Items == 0 then label(S, `<i>Quiet tonight. Nothing on the line yet.</i>`, 15, { TextColor3 = Color3.fromRGB(205, 192, 218); Size = UDim2.new(1, 0, 0, 20); LayoutOrder = 4 }) end
	local Newest = 0
	for K = #Items, 1, -1 do
		local It = Items[K]
		Newest = math.max(Newest, It.Id)
		local Card = new(if art(`FmCard`) then `ImageLabel` else `Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.3; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 0); LayoutOrder = 100 - K + 10 }, S)
		corner(Card, 12)
		if art(`FmCard`) then
			sliced(Card, `FmCard`) -- the card is the lacquer plate itself (a child plate would join the list layout)
			if It.Kind == `Transmission` then Card.ImageColor3 = Color3.fromRGB(255, 170, 170) end
		else
			new(`UIStroke`, { Color = if It.Kind == `Transmission` then T().Colors.Crimson else T().Colors.IronDim; Transparency = 0.4 }, Card)
		end
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12); PaddingTop = UDim.new(0, 8); PaddingBottom = UDim.new(0, 10) }, Card)
		new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 4) }, Card)
		label(Card, (if It.Id > (St.LastRead or 0) then `<font color="#{T().Colors.Gold:ToHex()}">\u{25CF} NEW</font>  ` else ``) .. (Kick[It.Kind] or It.Kind), 11,
			{ Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(200, 170, 255); Size = UDim2.new(1, 0, 0, 14); LayoutOrder = 1 })
		label(Card, It.Text, 14, { TextWrapped = true; TextTruncate = Enum.TextTruncate.None; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, 18); LayoutOrder = 2;
			Font = if It.Kind == `Transmission` then T().Fonts.Title else T().Fonts.Body })
	end
	if Newest > (St.LastRead or 0) then task.spawn(Ctx.Call, `StationRead`, Newest) end
end

-- the now playing sheet (the reference's third screen)
function Shared.NowPlaying()
	if not Ui then return end
	if Ui.Sheet then Ui.Sheet:Destroy() end
	local Id = Ctx.Music.Id
	if not Id then return end
	local Sheet = new(`Frame`, { Name = `NowPlaying`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1); ZIndex = 20 }, Ui.Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(80, 40, 140)), ColorSequenceKeypoint.new(0.6, Color3.fromRGB(40, 20, 70)), ColorSequenceKeypoint.new(1, Color3.fromRGB(20, 12, 30)) }) }, Sheet)
	Ui.Sheet = Sheet
	if art(`FmBackdrop`) then -- the lacquer wall under a violet wash
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = art(`FmBackdrop`); ImageTransparency = 0.25; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Sheet)
	end
	local Back = roundBtn(Sheet, `Back`, `\u{2039}`, 36, false, function() Sheet:Destroy() Ui.Sheet = nil end) Back.Position = UDim2.fromOffset(14, 10)
	label(Sheet, `Now Playing`, 15, { Font = T().Fonts.Title; TextColor3 = Color3.fromRGB(230, 214, 240); TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(60, 10); Size = UDim2.new(1, -120, 0, 36) })
	-- the neighbours peek in from the sides, as in the reference
	local Recent = Ctx.State.Recent or {}
	local At = table.find(Recent, Id) or 1
	local Prev, Next = Recent[At + 1], Recent[At - 1]
	if Prev then local P = cover(Sheet, Prev, 170) P.Position = UDim2.new(0, -130, 0, 82) if P:IsA(`ImageLabel`) then P.ImageTransparency = 0.45 else P.BackgroundTransparency = 0.4 end end
	if Next then local N = cover(Sheet, Next, 170) N.Position = UDim2.new(1, -40, 0, 82) if N:IsA(`ImageLabel`) then N.ImageTransparency = 0.45 else N.BackgroundTransparency = 0.4 end end
	local Big = cover(Sheet, Id, 220) Big.AnchorPoint = Vector2.new(0.5, 0) Big.Position = UDim2.new(0.5, 0, 0, 62)
	local Fr = art(`FmCoverFrame`)
	if Fr then
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Fr; Size = UDim2.new(1, 12, 1, 12); Position = UDim2.fromOffset(-6, -6); ZIndex = 2 }, Big)
	else
		new(`UIStroke`, { Color = Color3.fromRGB(210, 180, 255); Transparency = 0.5; Thickness = 1 }, Big)
	end
	local Title, By = titleOf(Id)
	label(Sheet, By, 14, { TextColor3 = Color3.fromRGB(214, 200, 228); Position = UDim2.fromOffset(22, 296); Size = UDim2.new(1, -90, 0, 18) })
	local TitleL = label(Sheet, Title, 22, { Font = T().Fonts.Title; Position = UDim2.fromOffset(22, 316); Size = UDim2.new(1, -90, 0, 28) })
	local Liked = table.find(Ctx.State.Liked or {}, Id) ~= nil
	local Heart Heart = roundBtn(Sheet, if Liked then `HeartFull` else `Heart`, if Liked then `\u{2665}` else `\u{2661}`, 40, false, function()
		local L = table.clone(Ctx.State.Liked or {})
		local K = table.find(L, Id)
		if K then table.remove(L, K) else table.insert(L, 1, Id) end
		Ctx.State.Liked = L
		setIcon(Heart, if K then `Heart` else `HeartFull`, if K then `\u{2661}` else `\u{2665}`, if K then (if Heart:FindFirstChild(`Icon`) then ICON_GOLD else T().Colors.Gold) else Color3.fromRGB(235, 70, 90))
		task.spawn(Ctx.Call, `SaveLiked`, L)
	end)
	Heart.Position = UDim2.new(1, -62, 0, 302)
	if Liked then setIcon(Heart, `HeartFull`, `\u{2665}`, Color3.fromRGB(235, 70, 90)) end
	-- the waveform: bars from the track id, the played part lit; click or drag to seek
	local Wave = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Position = UDim2.fromOffset(22, 360); Size = UDim2.new(1, -44, 0, 44) }, Sheet)
	local Bars = {}
	local N = 46
	for K = 1, N do
		local Hh = 0.25 + ((hash(Id + K * 31) % 1000) / 1000) * 0.75
		local B = new(`Frame`, { BorderSizePixel = 0; BackgroundColor3 = Color3.fromRGB(120, 105, 140); AnchorPoint = Vector2.new(0, 0.5);
			Position = UDim2.new((K - 1) / N, 1, 0.5, 0); Size = UDim2.new(1 / N, -2, Hh, 0) }, Wave)
		corner(B, 2)
		Bars[K] = B
	end
	local Cur = label(Sheet, `0:00`, 13, { TextColor3 = Color3.fromRGB(214, 200, 228); Position = UDim2.fromOffset(22, 406); Size = UDim2.fromOffset(60, 14) })
	local Len = label(Sheet, `0:00`, 13, { TextColor3 = Color3.fromRGB(214, 200, 228); TextXAlignment = Enum.TextXAlignment.Right; Position = UDim2.new(1, -82, 0, 406); Size = UDim2.fromOffset(60, 14) })
	local function seek(X: number)
		local S = Ctx.Music.Sound
		if not (S and S.TimeLength > 0) then return end
		local A = math.clamp((X - Wave.AbsolutePosition.X) / Wave.AbsoluteSize.X, 0, 1)
		S.TimePosition = A * S.TimeLength
	end
	Wave.InputBegan:Connect(function(Inp)
		if Inp.UserInputType == Enum.UserInputType.MouseButton1 or Inp.UserInputType == Enum.UserInputType.Touch then seek(Inp.Position.X) end
	end)
	-- controls
	local Row = new(`Frame`, { BackgroundTransparency = 1; Position = UDim2.fromOffset(18, 436); Size = UDim2.new(1, -36, 0, 70) }, Sheet)
	local function place(B, X) B.AnchorPoint = Vector2.new(0.5, 0.5) B.Position = UDim2.new(X, 0, 0.5, 0) end
	local Loop = roundBtn(Row, `Loop`, `\u{1F501}`, 38, false, function() if Ctx.Music.Sound then Ctx.Music.Sound.Looped = not Ctx.Music.Sound.Looped end end) place(Loop, 0.08)
	place(roundBtn(Row, `Prev`, `\u{23EE}`, 44, false, function() if Prev then Ctx.Play(Prev) Shared.NowPlaying() elseif Ctx.Music.Sound then Ctx.Music.Sound.TimePosition = 0 end end), 0.29)
	local Pl Pl = roundBtn(Row, `Pause`, `\u{23F8}`, 64, true, function()
		local S = Ctx.Music.Sound
		if not S then return end
		if S.IsPlaying then S:Pause() else S:Resume() end
	end) place(Pl, 0.5)
	place(roundBtn(Row, `Next`, `\u{23ED}`, 44, false, function() if Next then Ctx.Play(Next) Shared.NowPlaying() end end), 0.71)
	place(roundBtn(Row, `Queue`, `\u{266A}`, 38, false, function() Sheet:Destroy() Ui.Sheet = nil Tab = `Library` Shared.Render() end), 0.92)
	Ctx.Kit.Slider({ label = `Volume`; min = 0; max = 100; step = 5; value = if Ctx.Music.Sound then math.floor(Ctx.Music.Sound.Volume * 100) else 50;
		Size = UDim2.new(1, -44, 0, 34); Position = UDim2.fromOffset(22, 520); Parent = Sheet;
		onChanged = function(V) if Ctx.Music.Sound then Ctx.Music.Sound.Volume = V / 100 end end })
	Ui.NP = { Bars = Bars; Cur = Cur; Len = Len; Play = Pl; Loop = Loop; Title = TitleL; Id = Id }
end

-- the floating tab bar (the reference's pill): Home, Library, Station
function Shared.TabBar(Parent)
	local Bar = new(`Frame`, { BackgroundColor3 = T().Colors.Ink; BackgroundTransparency = 0.1; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -12); Size = UDim2.fromOffset(186, 56); ZIndex = 10 }, Parent)
	corner(Bar)
	local BarArt = art(`FmTabBar`)
	if BarArt then
		Bar.BackgroundTransparency = 1
		local Plate = new(`ImageLabel`, { ZIndex = 9; Size = UDim2.fromScale(1, 1) }, Bar)
		sliced(Plate, `FmTabBar`)
		Plate.Parent = Bar.Parent
		Plate.AnchorPoint, Plate.Position, Plate.Size = Bar.AnchorPoint, Bar.Position, Bar.Size
	else
		new(`UIStroke`, { Color = T().Colors.GoldDeep; Transparency = 0.45 }, Bar)
	end
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Center; VerticalAlignment = Enum.VerticalAlignment.Center; Padding = UDim.new(0, 10) }, Bar)
	for _, Def in { { `Home`, `\u{2302}` }, { `Library`, `\u{266A}` }, { `Station`, `\u{1F4FB}` } } do
		local B = roundBtn(Bar, Def[1], Def[2], 46, Tab == Def[1], function() Tab = Def[1] Shared.Render() end)
		B.ZIndex = 11
	end
	if Ctx.Music.Id then -- a mini player above the bar
		local Mini = new(`TextButton`, { Text = ``; BackgroundColor3 = PURPLE_DEEP; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -74); Size = UDim2.new(1, -24, 0, 46); ZIndex = 10 }, Parent)
		corner(Mini, 12)
		if art(`FmCard`) then
			local Plate = new(`ImageLabel`, { ZIndex = 10; Size = UDim2.fromScale(1, 1) }, Mini)
			sliced(Plate, `FmCard`)
			Plate.ImageColor3 = Color3.fromRGB(215, 185, 255)
			Mini.BackgroundTransparency = 1
		else
			new(`UIStroke`, { Color = PURPLE; Transparency = 0.5 }, Mini)
		end
		local C = cover(Mini, Ctx.Music.Id, 34) C.Position = UDim2.fromOffset(6, 6) C.ZIndex = 11
		local Title = titleOf(Ctx.Music.Id)
		label(Mini, Title, 14, { Font = T().Fonts.Title; ZIndex = 11; Position = UDim2.fromOffset(48, 0); Size = UDim2.new(1, -100, 1, 0) })
		Mini.Activated:Connect(Shared.NowPlaying)
	end
end

-- a redraw soon after names arrive (one for several), unless the now playing sheet is up (it updates itself)
local RefreshQueued = false
local StationAt = 0 -- (2.30) when the Station tab last fetched
function Shared.Refresh()
	if RefreshQueued then return end
	RefreshQueued = true
	task.delay(0.3, function()
		RefreshQueued = false
		if Ui and Ui.Root and Ui.Root.Parent and not (Ui.Sheet and Ui.Sheet.Parent) then Shared.Render() end
	end)
end

function Shared.Render()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	for _, Ch in Ui.Root:GetChildren() do if Ch ~= Ui.Bg and Ch.Name ~= `NowPlaying` then Ch:Destroy() end end
	local Page = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Ui.Root)
	if Tab == `Station` then
		if os.clock() - StationAt > 5 then -- (fetch, then redraw once: the redraw doesn't fetch again within 5 s)
			StationAt = os.clock()
			task.spawn(function() Ctx.Station = Ctx.Call(`Station`) or Ctx.Station if Tab == `Station` and Page.Parent then Page:Destroy() Shared.Render() end end)
		end
		Shared.TuneIn() -- (the voices; it waits out the gap and never talks over itself)
	end
	if Tab == `Home` then Shared.Home(Page) elseif Tab == `Library` then Shared.Library(Page) else Shared.Station(Page) end
	Shared.TabBar(Page)
end

function Shared.Open(C)
	Ctx = C
	local App = C.App
	for _, Ch in App:GetChildren() do if Ch.Name ~= `Grain` then Ch:Destroy() end end
	App.Visible = true
	local Root = new(`Frame`, { Name = `NightFM`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ClipsDescendants = true }, App)
	local Bg = new(`Frame`, { Name = `Bg`; BackgroundColor3 = Color3.new(1, 1, 1); Size = UDim2.fromScale(1, 1) }, Root)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(58, 28, 96)), ColorSequenceKeypoint.new(0.45, Color3.fromRGB(26, 16, 36)), ColorSequenceKeypoint.new(1, Color3.fromRGB(14, 10, 18)) }) }, Bg)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = art(`FmBackdrop`) or C.Theme.Images.PanelBg; ImageTransparency = if art(`FmBackdrop`) then 0 else 0.9; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1) }, Bg)
	-- a back-to-home control in the corner (the phone's Home)
	Ui = { Root = Root; Bg = Bg }
	task.spawn(function() Ctx.Station = Ctx.Call(`Station`) if Ui and Tab == `Home` then Shared.Render() end end)
	Shared.Render()
	-- the phone's back: a thin gold chevron over the page, top-left of the status area
	local Back = new(`TextButton`, { Text = `\u{2039}`; Font = C.Theme.Fonts.Title; TextSize = 26; TextColor3 = C.Theme.Colors.Gold; BackgroundTransparency = 1; Position = UDim2.fromOffset(4, -2); Size = UDim2.fromOffset(26, 30); ZIndex = 30 }, Root)
	Back.Activated:Connect(function() C.Home() end)
end

-- tests: point the art at local files (Studio's content folder) to preview it before the ids are in
function Shared.UseArt(Map) for K, V in Map do ART[K] = V end end

function Shared.Tick()
	if not (Ui and Ui.Root and Ui.Root.Parent) then return end
	local NP = Ui.NP
	local S = Ctx.Music.Sound
	if NP and Ui.Sheet and Ui.Sheet.Parent and S then
		local A = if S.TimeLength > 0 then S.TimePosition / S.TimeLength else 0
		local Lit = math.floor(A * #NP.Bars + 0.5)
		for K, B in NP.Bars do B.BackgroundColor3 = if K <= Lit then Color3.fromRGB(205, 165, 255) else Color3.fromRGB(110, 96, 130) end
		local function mmss(X) X = math.floor(X) return string.format(`%d:%02d`, X // 60, X % 60) end
		NP.Cur.Text = mmss(S.TimePosition) NP.Len.Text = mmss(S.TimeLength)
		setIcon(NP.Play, if S.IsPlaying then `Pause` else `Play`, if S.IsPlaying then `\u{23F8}` else `\u{25B6}`)
		setIcon(NP.Loop, `Loop`, `\u{1F501}`, if S.Looped then Color3.fromRGB(205, 165, 255) else (if NP.Loop:FindFirstChild(`Icon`) then ICON_GOLD else Ctx.Theme.Colors.Gold))
		NP.Title.Text = (titleOf(NP.Id))
	end
end

return Shared
