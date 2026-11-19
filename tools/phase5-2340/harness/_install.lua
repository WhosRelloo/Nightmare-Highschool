local Report = {}
local Items = {}
table.insert(Items, { Path = {"StarterPlayer", "StarterPlayerScripts", "Controllers", "Gui", "Phone"}; Source = [==[
--[[
	Phone (client). Controllers.Gui.Phone   (the Phone in your hotbar, or Y to take it out / put it away)
	Every student spawns with a Phone tool (Services.Features.Phone builds it from the owner's model). Holding it
	slides the handset up from the bottom-right corner; putting it away slides it down.
	Laid out like a modern smartphone (owner's reference, 2026-11-02), dressed for the school: a rounded iron body with
	a polished-gold edge and side buttons, the kit's PBR slate grain, a notch with a lens, a status bar with the school
	clock, a 4-wide grid of rounded enamel app icons (the kit's glyph art pressed into a slot well), page dots, a
	frosted dock and red badges (money received, a new paper each day). Labels are outlined and shadowed so they read
	on any wallpaper.
	  Dock: Wallet, Night FM, Classmates, Camera     Grid: Midnight Bell, Timetable, Study Group, Cliques, Style, Options,
	        Wisp Flight, Hex Slash, Crypt Crush
	  Wallet         your Yen, send money to a classmate (pick them, type an amount, confirm), and your history
	  Night FM       (2.30) Controllers.Gui.PhoneRadio, after the owner's reference: home (greeting, chips, the Midnight
	                 Broadcast banner, recent tracks), library (saved + recent, add by audio ID), now playing (cover,
	                 like, waveform scrubber, loop / prev / play / next, volume) and the station (21:00-03:00). Only you
	                 hear your music; it keeps playing with the phone away and the hotbar slot shows a note.
	  Midnight Bell  the school paper, written live by the server (moon, top students, discipline, specials,
	                 clubs, rumours)
	  Classmates     everyone in the building (names only if you know them): send Yen or invite to your study group
	  Camera         the cinematic view (Controllers.Gui.Cinematic)
	  Style          your wallpaper: eight presets, or your own image / decal ID (saved; only you see it)
	  Cliques        all eight cliques (Config.Cliques, server Services.Social.Cliques): who they are, their hangout,
	                 leader and rival, and your standing with each on a -100 to 100 bar with its tier. The Vigil and
	                 the Crimson Court also show your faction rank and open the faction panel (join, missions). (1.20)
	  Timetable / Study Group / Options   open those panels
	  Wisp Flight / Hex Slash / Crypt Crush   the arcade: three small games played on the screen, with your best and
	                 the building's top five (Controllers.Gui.PhoneGames; server Services.Features.PhoneGames).
	                 Back or putting the phone away stops the game.
	  Texts          (2.23.0) like a messaging app in the school's dress: conversations by sender, inked and crimson
	                 bubbles, dare and invite cards, quick replies (players never type to NPCs). See docs/Phone.md.
	  (Owner: no Locker or Journal in the phone. The Report Card app came later, in 1.40.)
	It never captures input: combat and movement keys keep working with the phone up.
	Server: Services.Features.Phone (ReplicatedStorage.NHPhone).
]]
local MarketplaceService = game:GetService(`MarketplaceService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local SoundService = game:GetService(`SoundService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local Img = Theme.Images
local YEN = `\u{A5}`
local TOGGLE_KEY = Enum.KeyCode.Y
local W, H = 360, 690
local SECTION = Color3.fromRGB(214, 178, 112) -- section headers: muted gold
local HINT = Color3.fromRGB(205, 196, 186) -- hints and empty states: light enough to read on the dark pages
local RACE_COLOR = {
	Vampire = Color3.fromRGB(220, 60, 70); Werewolf = Color3.fromRGB(235, 170, 70); Ghoul = Color3.fromRGB(140, 210, 100);
	Wraith = Color3.fromRGB(150, 200, 245); Priest = Color3.fromRGB(235, 205, 120); Human = Color3.fromRGB(200, 190, 170);
}

local Shared = {}
local Local = {}
local Ui = nil
local State = { History = {}; Recent = {}; Yen = 0 }
local Open = false
local Music = { Sound = nil :: Sound?; Title = ``; Id = nil :: number? }
local Pending = nil -- wallet: { UserId, Name }

---| helpers |---

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function tween(I: Instance, T: number, Props, Style: Enum.EasingStyle?)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Style or Enum.EasingStyle.Quart, Enum.EasingDirection.Out), Props)
	Tw:Play()
	return Tw
end

function Local.Remote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHPhone`)
	return F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
end

function Local.Call(Name: string, ...)
	local R = Local.Remote(Name)
	if not R then return nil end
	local Ok, A, B = pcall(R.InvokeServer, R, ...)
	if not Ok then return nil end
	return A, B
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; RichText = true; TextXAlignment = Enum.TextXAlignment.Left; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

-- the number in a typed box ("12,500" -> 12500); nil if there's none
function Local.Digits(Text: string?): number?
	local Clean = string.gsub(Text or ``, `[^%d]`, ``)
	return tonumber(Clean)
end

function Local.Clock(): string
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return `--:--`, `` end
	local S = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	return S.ClockText, S.DayName
end

function Local.Controller(Name: string)
	local M = script.Parent:FindFirstChild(Name)
	if not M then return nil end
	local Ok, Mod = pcall(require, M)
	return if Ok then Mod else nil
end

---| the handset |---

-- Home screen laid out like a modern smartphone (owner's reference, 2026-11-02), dressed for Nightmare High:
-- a rounded iron handset with a gold rim and side buttons, a notch with a lens, a status bar, a 4-wide grid of
-- rounded app icons (each its own ink colour, the kit's glyph art), page dots, a frosted dock, red badges.
local APPS = {
	{ Id = `Gazette`; Name = `Midnight Bell`; Icon = `IconAppGazette`; A = Color3.fromRGB(64, 52, 44); B = Color3.fromRGB(28, 22, 20); Tint = Color3.new(1, 1, 1) };
	{ Id = `Timetable`; Name = `Timetable`; Icon = `IconAppTimetable`; A = Color3.fromRGB(200, 140, 60); B = Color3.fromRGB(110, 60, 20); Tint = Color3.fromRGB(255, 240, 210) };
	{ Id = `Group`; Name = `Study Group`; Icon = `IconAppGroup`; A = Color3.fromRGB(170, 30, 44); B = Color3.fromRGB(70, 8, 16); Tint = Color3.fromRGB(255, 220, 220) };
	{ Id = `Cliques`; Name = `Cliques`; Icon = `IconAppCliques`; A = Color3.fromRGB(120, 20, 60); B = Color3.fromRGB(40, 6, 22); Tint = Color3.fromRGB(255, 200, 220) };
	{ Id = `Texts`; Name = `Texts`; Icon = `IconAppTexts`; A = Color3.fromRGB(60, 150, 90); B = Color3.fromRGB(14, 56, 30); Tint = Color3.fromRGB(230, 255, 230) }; -- (1.33) dares and news from leaders
	{ Id = `Report`; Name = `Report Card`; Icon = `IconReport`; A = Color3.fromRGB(92, 58, 36); B = Color3.fromRGB(28, 16, 10); Tint = Color3.fromRGB(255, 246, 226) }; -- (1.40) weekly report cards
	{ Id = `Style`; Name = `Style`; Icon = `IconAppStyle`; A = Color3.fromRGB(110, 70, 170); B = Color3.fromRGB(40, 20, 80); Tint = Color3.new(1, 1, 1) };
	{ Id = `Options`; Name = `Options`; Icon = `IconAppOptions`; A = Color3.fromRGB(90, 90, 100); B = Color3.fromRGB(36, 36, 44); Tint = Color3.fromRGB(235, 235, 245) };
	{ Id = `Wisp`; Name = `Wisp Flight`; Icon = `IconAppWisp`; A = Color3.fromRGB(56, 64, 150); B = Color3.fromRGB(14, 14, 48); Tint = Color3.fromRGB(255, 214, 140) };
	{ Id = `Hex`; Name = `Hex Slash`; Icon = `IconAppHex`; A = Color3.fromRGB(196, 44, 40); B = Color3.fromRGB(66, 8, 12); Tint = Color3.fromRGB(255, 226, 190) };
	{ Id = `Crypt`; Name = `Crypt Crush`; Icon = `IconAppCrypt`; A = Color3.fromRGB(42, 118, 96); B = Color3.fromRGB(8, 36, 30); Tint = Color3.fromRGB(232, 244, 224) };
}
local DOCK = {
	{ Id = `Wallet`; Name = `Wallet`; Icon = `IconAppWallet`; A = Color3.fromRGB(168, 124, 44); B = Color3.fromRGB(70, 44, 12); Tint = Color3.fromRGB(255, 244, 226) };
	{ Id = `Radio`; Name = `Night FM`; Icon = `IconAppRadio`; A = Color3.fromRGB(140, 90, 220); B = Color3.fromRGB(50, 20, 100); Tint = Color3.new(1, 1, 1) };
	{ Id = `Contacts`; Name = `Classmates`; Icon = `IconAppContacts`; A = Color3.fromRGB(70, 140, 160); B = Color3.fromRGB(16, 50, 64); Tint = Color3.new(1, 1, 1) };
	{ Id = `Camera`; Name = `Camera`; Icon = `IconAppCamera`; A = Color3.fromRGB(70, 70, 78); B = Color3.fromRGB(18, 18, 22); Tint = Color3.fromRGB(220, 220, 230) };
}
-- wallpapers (Style app): presets, or any image / decal ID shown through rbxthumb
local WALLPAPERS = {
	{ Id = `CrimsonInk`; Name = `Crimson Ink`; Top = Color3.fromRGB(14, 10, 18); Bottom = Color3.fromRGB(96, 14, 26) };
	{ Id = `VioletNight`; Name = `Violet Night`; Top = Color3.fromRGB(40, 16, 70); Bottom = Color3.fromRGB(150, 70, 140) };
	{ Id = `BloodMoon`; Name = `Blood Moon`; Top = Color3.fromRGB(60, 6, 10); Bottom = Color3.fromRGB(200, 40, 30) };
	{ Id = `VigilCandle`; Name = `Vigil Candle`; Top = Color3.fromRGB(20, 14, 8); Bottom = Color3.fromRGB(150, 96, 30) };
	{ Id = `CourtVelvet`; Name = `Court Velvet`; Top = Color3.fromRGB(30, 4, 14); Bottom = Color3.fromRGB(110, 10, 50) };
	{ Id = `GraveFog`; Name = `Grave Fog`; Top = Color3.fromRGB(16, 22, 24); Bottom = Color3.fromRGB(80, 100, 100) };
	{ Id = `MidnightBlue`; Name = `Midnight Blue`; Top = Color3.fromRGB(6, 10, 26); Bottom = Color3.fromRGB(40, 60, 130) };
	{ Id = `Ash`; Name = `Ash`; Top = Color3.fromRGB(12, 12, 14); Bottom = Color3.fromRGB(70, 66, 70) };
}
local WallById = {}
for _, Wp in WALLPAPERS do WallById[Wp.Id] = Wp end

function Local.Build()
	local G = new(`ScreenGui`, { Name = `NHPhone`; ResetOnSpawn = false; DisplayOrder = 11; ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, Player:WaitForChild(`PlayerGui`))
	Kit.AutoScale(G)
	-- the handset: dark iron, a gold rim, side buttons
	local Body = new(`Frame`, { Name = `Body`; BackgroundColor3 = Color3.fromRGB(22, 20, 26); BorderSizePixel = 0; AnchorPoint = Vector2.new(1, 1);
		Position = UDim2.new(1, -22, 1, H + 40); Size = UDim2.fromOffset(W, H); Visible = false }, G)
	new(`UICorner`, { CornerRadius = UDim.new(0, 56) }, Body)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 2; Transparency = 0.15 }, Body)
	new(`UIGradient`, { Rotation = 35; Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(70, 66, 74)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(26, 24, 30)), ColorSequenceKeypoint.new(1, Color3.fromRGB(60, 56, 64)) }) }, Body)
	-- PBR finish (the kit's baked art): a worked slate grain over the iron, and the kit's hammered-iron rim
	local Grain = new(`ImageLabel`, { Name = `Grain`; BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = Color3.fromRGB(120, 112, 124);
		ImageTransparency = 0.3; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(160, 160); Size = UDim2.fromScale(1, 1) }, Body)
	new(`UICorner`, { CornerRadius = UDim.new(0, 56) }, Grain)
	-- a rounded polished-metal edge (a square 9-slice frame left sharp corners sticking out past the curve)
	local RimLine = Body:FindFirstChildOfClass(`UIStroke`)
	if RimLine then
		RimLine.Thickness = 2.5
		RimLine.Transparency = 0
		RimLine.Color = Color3.new(1, 1, 1)
		new(`UIGradient`, { Rotation = 45; Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.fromRGB(240, 214, 150)), ColorSequenceKeypoint.new(0.3, Color3.fromRGB(120, 92, 50)),
			ColorSequenceKeypoint.new(0.55, Color3.fromRGB(235, 205, 130)), ColorSequenceKeypoint.new(0.8, Color3.fromRGB(96, 72, 40)),
			ColorSequenceKeypoint.new(1, Color3.fromRGB(220, 190, 120)) }) }, RimLine)
	end
	local Inner = new(`Frame`, { Name = `InnerRim`; BackgroundTransparency = 1; Position = UDim2.fromOffset(5, 5); Size = UDim2.new(1, -10, 1, -10) }, Body)
	new(`UICorner`, { CornerRadius = UDim.new(0, 50) }, Inner)
	new(`UIStroke`, { Color = Color3.fromRGB(8, 6, 10); Thickness = 1.5; Transparency = 0.2 }, Inner)
	for _, B in { { -1, 120, 30 }, { -1, 170, 56 }, { -1, 236, 56 }, { 1, 180, 90 } } do
		local Btn = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(46, 42, 50); BorderSizePixel = 0; AnchorPoint = Vector2.new(if B[1] < 0 then 1 else 0, 0);
			Position = UDim2.new(if B[1] < 0 then 0 else 1, 0, 0, B[2]); Size = UDim2.fromOffset(4, B[3]) }, Body)
		new(`UICorner`, { CornerRadius = UDim.new(0, 2) }, Btn)
		new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.5 }, Btn)
	end
	local Screen = new(`CanvasGroup`, { Name = `Screen`; BackgroundColor3 = Color3.fromRGB(10, 8, 12); BorderSizePixel = 0;
		Position = UDim2.fromOffset(11, 11); Size = UDim2.new(1, -22, 1, -22) }, Body)
	new(`UICorner`, { CornerRadius = UDim.new(0, 46) }, Screen)
	-- wallpaper
	local Wall = new(`Frame`, { Name = `Wall`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromScale(1, 1) }, Screen)
	local WallGrad = new(`UIGradient`, { Rotation = 90 }, Wall)
	local WallImage = new(`ImageLabel`, { Name = `Image`; BackgroundTransparency = 1; ScaleType = Enum.ScaleType.Crop; Size = UDim2.fromScale(1, 1); Visible = false }, Wall)
	local Shade = new(`Frame`, { Name = `Shade`; BackgroundColor3 = Color3.new(0, 0, 0); BackgroundTransparency = 0.55; BorderSizePixel = 0; Size = UDim2.fromScale(1, 1); Visible = false }, Wall)
	new(`UIGradient`, { Rotation = 90; Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(0.5, 1), NumberSequenceKeypoint.new(1, 0.2) }) }, Shade)
	-- ink-on-slate grain over the wallpaper (the kit's PanelBg)
	new(`ImageLabel`, { Name = `Grain`; BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = Color3.fromRGB(26, 16, 28); ImageTransparency = 0.5;
		ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(200, 200); Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Wall)
	local Crest = new(`ImageLabel`, { Name = `Crest`; BackgroundTransparency = 1; Image = Img.CrestFlat; ImageTransparency = 0.9; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.62); Size = UDim2.fromOffset(240, 240) }, Wall)
	-- the notch: a speaker slot and a lens
	local Notch = new(`Frame`, { Name = `Notch`; BackgroundColor3 = Color3.fromRGB(6, 5, 8); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 0, -14); Size = UDim2.fromOffset(150, 40); ZIndex = 8 }, Screen)
	new(`UICorner`, { CornerRadius = UDim.new(0, 16) }, Notch)
	local Slot = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(34, 30, 36); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, -10, 0, 27); Size = UDim2.fromOffset(46, 5); ZIndex = 9 }, Notch)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Slot)
	local Lens = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(20, 18, 40); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 30, 0, 27); Size = UDim2.fromOffset(9, 9); ZIndex = 9 }, Notch)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Lens)
	new(`UIStroke`, { Color = Color3.fromRGB(120, 30, 50); Thickness = 1; Transparency = 0.3 }, Lens)
	-- status bar
	local Bar = new(`Frame`, { Name = `Status`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 34); ZIndex = 7 }, Screen)
	local BarTime = Local.Label(Bar, ``, 15, { Font = Fonts.Title; Position = UDim2.fromOffset(26, 6); Size = UDim2.fromOffset(84, 24) })
	for I = 1, 4 do
		new(`Frame`, { BackgroundColor3 = C.Text; BackgroundTransparency = if I == 4 then 0.55 else 0.05; BorderSizePixel = 0; AnchorPoint = Vector2.new(0, 1);
			Position = UDim2.new(1, -84 + I * 5, 0, 23); Size = UDim2.fromOffset(3, 3 + I * 2) }, Bar)
	end
	local Batt = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -24, 0, 13); Size = UDim2.fromOffset(22, 10) }, Bar)
	new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Batt)
	new(`UIStroke`, { Color = C.Text; Thickness = 1 }, Batt)
	new(`Frame`, { BackgroundColor3 = C.Gold; BorderSizePixel = 0; Position = UDim2.fromOffset(2, 2); Size = UDim2.new(0.72, -2, 1, -4) }, Batt)
	-- pages
	local Home = new(`Frame`, { Name = `Home`; BackgroundTransparency = 1; Position = UDim2.fromOffset(0, 34); Size = UDim2.new(1, 0, 1, -34); ZIndex = 3 }, Screen)
	local App = new(`Frame`, { Name = `App`; BackgroundColor3 = Color3.fromRGB(12, 10, 14); BackgroundTransparency = 0.12; BorderSizePixel = 0;
		Position = UDim2.fromOffset(0, 34); Size = UDim2.new(1, 0, 1, -56); ZIndex = 3; Visible = false }, Screen)
	new(`ImageLabel`, { Name = `Grain`; BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = Color3.fromRGB(80, 70, 84); ImageTransparency = 0.55;
		ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(200, 200); Size = UDim2.fromScale(1, 1); ZIndex = 0 }, App)
	local HomeBar = new(`TextButton`, { Name = `HomeBar`; Text = ``; BackgroundColor3 = C.Text; BackgroundTransparency = 0.25; BorderSizePixel = 0; AutoButtonColor = false;
		AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -8); Size = UDim2.fromOffset(120, 5); ZIndex = 9 }, Screen)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, HomeBar)
	HomeBar.Activated:Connect(function() Local.ShowHome() end)
	Ui = { Gui = G; Body = Body; Screen = Screen; Home = Home; App = App; BarTime = BarTime; WallGrad = WallGrad; WallImage = WallImage; Shade = Shade; Crest = Crest; Badges = {} }
	Local.BuildHome()
	Local.ApplyWallpaper()
end

function Local.Icon(Parent: Instance, A, Size: number): Frame
	local Tile = new(`Frame`, { Name = `Tile`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 0, 0); Size = UDim2.fromOffset(Size, Size) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, math.floor(Size * 0.24)) }, Tile)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(A.A, A.B) }, Tile)
	-- PBR: the kit's recessed slot well pressed into the enamel, and a thin hammered-iron rim
	local Well = new(`ImageLabel`, { Name = `Well`; BackgroundTransparency = 1; Image = Img.SlotBg; ImageColor3 = A.B:Lerp(Color3.new(0, 0, 0), 0.35); ImageTransparency = 0.4;
		ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Tile)
	new(`UICorner`, { CornerRadius = UDim.new(0, math.floor(Size * 0.24)) }, Well)
	new(`UIStroke`, { Color = Color3.fromRGB(190, 160, 100); Thickness = 1.2; Transparency = 0.35 }, Tile)
	-- a soft gloss across the top
	local Gloss = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 0.88; BorderSizePixel = 0; Size = UDim2.fromScale(1, 0.48) }, Tile)
	new(`UICorner`, { CornerRadius = UDim.new(0, math.floor(Size * 0.24)) }, Gloss)
	new(`UIGradient`, { Rotation = 90; Transparency = NumberSequence.new(0, 1) }, Gloss)
	if A.Glyph then
		Local.Label(Tile, A.Glyph, math.floor(Size * 0.55), { Font = Fonts.Title; TextColor3 = A.Tint; TextXAlignment = Enum.TextXAlignment.Center; TextStrokeTransparency = 1; ZIndex = 4 })
	else
		-- (1.40) the custom app icons: big enough to keep their detail, one warm bone tint so the relief reads on any tile colour,
		-- and a soft drop shadow under each so it sits on the tile rather than in it
		local Icon = Img[A.Icon] or Img.Pip
		new(`ImageLabel`, { Name = `GlyphShadow`; BackgroundTransparency = 1; Image = Icon; ImageColor3 = Color3.new(0, 0, 0); ImageTransparency = 0.45; ScaleType = Enum.ScaleType.Fit;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, math.max(1, math.floor(Size * 0.035))); Size = UDim2.fromScale(0.74, 0.74); ZIndex = 3 }, Tile)
		new(`ImageLabel`, { Name = `Glyph`; BackgroundTransparency = 1; Image = Icon; ImageColor3 = Color3.fromRGB(255, 244, 226); ScaleType = Enum.ScaleType.Fit;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.74, 0.74); ZIndex = 4 }, Tile)
	end
	return Tile
end

function Local.AppButton(Parent: Instance, A, Order: number, Label: boolean)
	local Cell = new(`TextButton`, { Name = A.Id; Text = ``; AutoButtonColor = false; BackgroundTransparency = 1; LayoutOrder = Order }, Parent)
	local Tile = Local.Icon(Cell, A, 58)
	if Label then
		-- readable on any wallpaper: heavier type, a full black outline, and a soft drop shadow behind it
		for _, L in {
			Local.Label(Cell, A.Name, 13, { Name = `Shadow`; Font = Fonts.Title; TextColor3 = Color3.new(0, 0, 0); TextTransparency = 0.35; TextStrokeTransparency = 1;
				TextScaled = true; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(-1, 64); Size = UDim2.new(1, 4, 0, 17) }),
			Local.Label(Cell, A.Name, 13, { Name = `Name`; Font = Fonts.Title; TextColor3 = Color3.fromRGB(250, 244, 232); TextStrokeColor3 = Color3.new(0, 0, 0);
				TextStrokeTransparency = 0; TextScaled = true; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(-2, 63); Size = UDim2.new(1, 4, 0, 17); ZIndex = 4 }),
		} do new(`UITextSizeConstraint`, { MaxTextSize = 13; MinTextSize = 10 }, L) end
	end
	local Badge = new(`TextLabel`, { Name = `Badge`; BackgroundColor3 = Color3.fromRGB(220, 40, 50); BorderSizePixel = 0; Text = ``; Font = Fonts.Title; TextSize = 12;
		TextColor3 = Color3.new(1, 1, 1); AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 27, 0, 3); Size = UDim2.fromOffset(20, 20); ZIndex = 6; Visible = false }, Cell)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Badge)
	Ui.Badges[A.Id] = Badge
	local Scale = new(`UIScale`, {}, Tile)
	Cell.MouseButton1Down:Connect(function() tween(Scale, 0.08, { Scale = 0.9 }) end)
	Cell.MouseLeave:Connect(function() tween(Scale, 0.12, { Scale = 1 }) end)
	Cell.Activated:Connect(function() tween(Scale, 0.12, { Scale = 1 }) Local.OpenApp(A.Id) end)
end

function Local.BuildHome()
	local Home = Ui.Home
	Local.BuildToday(Home) -- (2.34) the Today card, above the grid
	local Grid = new(`Frame`, { Name = `Grid`; BackgroundTransparency = 1; Position = UDim2.fromOffset(14, 162); Size = UDim2.new(1, -28, 0, 320) }, Home)
	new(`UIGridLayout`, { CellSize = UDim2.fromOffset(70, 88); CellPadding = UDim2.fromOffset(5, 14); SortOrder = Enum.SortOrder.LayoutOrder; HorizontalAlignment = Enum.HorizontalAlignment.Center }, Grid)
	for I, A in APPS do Local.AppButton(Grid, A, I, true) end
	-- page dots
	local Dots = new(`Frame`, { Name = `Dots`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -116); Size = UDim2.fromOffset(60, 8) }, Home)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Center; Padding = UDim.new(0, 8) }, Dots)
	for I = 1, 3 do
		local D = new(`Frame`, { BackgroundColor3 = C.Text; BackgroundTransparency = if I == 2 then 0 else 0.6; BorderSizePixel = 0; Size = UDim2.fromOffset(7, 7); LayoutOrder = I }, Dots)
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, D)
	end
	-- the dock: frosted ink
	local Dock = new(`Frame`, { Name = `Dock`; BackgroundColor3 = Color3.fromRGB(30, 20, 34); BackgroundTransparency = 0.35; BorderSizePixel = 0;
		AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -22); Size = UDim2.new(1, -20, 0, 84) }, Home)
	new(`UICorner`, { CornerRadius = UDim.new(0, 28) }, Dock)
	-- PBR: slate grain and a thin iron rim on the dock
	local DockGrain = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = Color3.fromRGB(90, 70, 96); ImageTransparency = 0.45;
		ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(160, 160); Size = UDim2.fromScale(1, 1) }, Dock)
	new(`UICorner`, { CornerRadius = UDim.new(0, 28) }, DockGrain)
	new(`UIStroke`, { Color = Color3.fromRGB(190, 160, 100); Thickness = 1.2; Transparency = 0.45 }, Dock)
	local DockRow = new(`Frame`, { BackgroundTransparency = 1; Position = UDim2.fromOffset(6, 13); Size = UDim2.new(1, -12, 0, 62) }, Dock)
	new(`UIGridLayout`, { CellSize = UDim2.fromOffset(70, 62); CellPadding = UDim2.fromOffset(5, 0); SortOrder = Enum.SortOrder.LayoutOrder; HorizontalAlignment = Enum.HorizontalAlignment.Center }, DockRow)
	for I, A in DOCK do Local.AppButton(DockRow, A, I, false) end
end

-- (2.34) The Today card (docs/expansion/14 §6.2): up to four quiet lines, each only when there's something real to say.
-- NOW (the timetable), HEARD (one live rumour), NEXT STEP (the closest path tier), LEAD (the tracked quest's objective).
-- Tap a line to open its app. It never nags: no badges, no sounds, no notifications; it refreshes when the phone opens.
local TODAY_ROWS = {
	{ Key = `Now`; Label = `NOW`; Open = function() Local.OpenApp(`Timetable`) end };
	{ Key = `Heard`; Label = `HEARD`; Open = function() Local.Seen = Local.Seen or {} local _, Day = Local.Clock() Local.Seen.Paper = Day Local.Gazette() end };
	{ Key = `Next`; Label = `NEXT STEP`; Open = function()
		Shared.Toggle(false)
		local M = Local.Controller(`StatsPanel`)
		if M and M.Toggle then task.delay(0.15, function() pcall(M.Toggle, true) end) end
	end };
	{ Key = `Lead`; Label = `LEAD`; Open = function()
		Shared.Toggle(false)
		local M = Local.Controller(`QuestJournal`)
		if M and M.Toggle then task.delay(0.15, function() pcall(M.Toggle, true) end) end
	end };
}

function Local.BuildToday(Home: Instance)
	local Card = new(`Frame`, { Name = `Today`; BackgroundColor3 = Color3.fromRGB(30, 20, 34); BackgroundTransparency = 0.3; BorderSizePixel = 0;
		Position = UDim2.fromOffset(12, 8); Size = UDim2.new(1, -24, 0, 144); ZIndex = 3 }, Home)
	new(`UICorner`, { CornerRadius = UDim.new(0, 22) }, Card)
	-- dressed like the dock: slate grain and a thin iron rim
	local Grain = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = Color3.fromRGB(90, 70, 96); ImageTransparency = 0.45;
		ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(160, 160); Size = UDim2.fromScale(1, 1); ZIndex = 3 }, Card)
	new(`UICorner`, { CornerRadius = UDim.new(0, 22) }, Grain)
	new(`UIStroke`, { Color = Color3.fromRGB(190, 160, 100); Thickness = 1.2; Transparency = 0.45 }, Card)
	local Head = Local.Label(Card, `TODAY`, 14, { Name = `Head`; Font = Fonts.Title; TextColor3 = C.Gold; TextStrokeTransparency = 1;
		Position = UDim2.fromOffset(16, 9); Size = UDim2.new(1, -32, 0, 16); ZIndex = 5 })
	local Day = Local.Label(Card, ``, 13, { Name = `Day`; Font = Fonts.Body; TextColor3 = HINT; TextStrokeTransparency = 1;
		TextXAlignment = Enum.TextXAlignment.Right; Position = UDim2.fromOffset(16, 9); Size = UDim2.new(1, -32, 0, 16); ZIndex = 5 })
	local List = new(`Frame`, { Name = `Lines`; BackgroundTransparency = 1; Position = UDim2.fromOffset(10, 30); Size = UDim2.new(1, -20, 1, -34); ZIndex = 4 }, Card)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 2) }, List)
	local Lines = {}
	for I, R in TODAY_ROWS do
		local Row = new(`TextButton`, { Name = R.Key; Text = ``; AutoButtonColor = false; BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 1;
			BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 26); LayoutOrder = I; Visible = false; ZIndex = 4 }, List)
		new(`UICorner`, { CornerRadius = UDim.new(0, 8) }, Row)
		Local.Label(Row, R.Label, 12, { Name = `Tag`; Font = Fonts.Title; TextColor3 = C.GoldDeep:Lerp(C.Gold, 0.6); TextStrokeTransparency = 1;
			Position = UDim2.fromOffset(6, 0); Size = UDim2.new(0, 76, 1, 0); ZIndex = 5 })
		local Text = Local.Label(Row, ``, 15, { Name = `Text`; Font = Fonts.Body; TextColor3 = Color3.fromRGB(240, 232, 220); TextStrokeTransparency = 1;
			RichText = true; TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(84, 0); Size = UDim2.new(1, -90, 1, 0); ZIndex = 5 })
		Row.MouseEnter:Connect(function() tween(Row, 0.12, { BackgroundTransparency = 0.92 }) end)
		Row.MouseLeave:Connect(function() tween(Row, 0.12, { BackgroundTransparency = 1 }) end)
		Row.Activated:Connect(function() pcall(Kit.PlaySound, `Tick`, 0.6, 1.2) R.Open() end)
		Lines[R.Key] = { Row = Row; Text = Text }
	end
	local Quiet = Local.Label(List, `A quiet day.`, 15, { Name = `Quiet`; Font = Fonts.Body; TextColor3 = HINT; TextStrokeTransparency = 1;
		Size = UDim2.new(1, 0, 0, 26); LayoutOrder = 99; Visible = false; ZIndex = 5 })
	Ui.Today = { Card = Card; Day = Day; Lines = Lines; Quiet = Quiet; Head = Head }
end

-- NOW from the school clock and the class list: "Chemistry until 9:45 AM, Room 103" / "Next: Chemistry at 9:50 AM, Room 103" /
-- "Lunch until 12:00 PM"
function Local.TodayNow(): string?
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	local St = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	local Seg = St and St.Segment
	if not Seg then return nil end
	local Ok, Classes = pcall(require, ReplicatedStorage.Config.Classes)
	local function room(Cl) return if Ok then (Classes.Rooms[Cl.Room] or Cl.Room) else Cl.Room end
	local Cl = Ok and Seg.Kind == `Class` and Classes.Periods[Seg.Name]
	if Cl then return `<b>{Cl.Subject}</b> until {SchoolTime.FormatClock(Seg.End)}, {room(Cl)}` end
	if Seg.Kind == `Passing` or Seg.Kind == `BeforeSchool` then
		local Nx = SchoolTime.Segments[St.SegmentIndex + 1]
		local NCl = Ok and Nx and Nx.Kind == `Class` and Classes.Periods[Nx.Name]
		if NCl then return `<b>{NCl.Subject}</b> at {SchoolTime.FormatClock(Nx.Start)}, {room(NCl)}` end
	end
	return `<b>{Seg.Name}</b> until {SchoolTime.FormatClock(Seg.End)}`
end

-- LEAD from your saved quests: the tracked quest's current objective
function Local.TodayLead(): string?
	local Ok, Line = pcall(function()
		local Sc = require(script.Parent.Parent.StateController)
		local Profile = Sc.GetProfile(false)
		local Q = Profile and Profile.Quests
		local Id = Q and Q.Tracked
		local St = Id and Id ~= `` and Q.Active and Q.Active[Id]
		local Def = St and require(ReplicatedStorage.Config.Quests).Quests[Id]
		local Obj = Def and Def.Objectives[St.Stage]
		if not Obj then return nil end
		local Need, Have = Obj.Count or 1, (St.Counts or {})[Obj.Id] or 0
		return `<b>{Def.Name}:</b> {Obj.Text}` .. (if Need > 1 then ` ({Have}/{Need})` else ``)
	end)
	return if Ok then Line else nil
end

function Local.Today()
	local T = Ui and Ui.Today
	if not T then return end
	local _, DayName = Local.Clock()
	T.Day.Text = DayName or ``
	local Vals = { Now = Local.TodayNow(); Lead = Local.TodayLead() }
	local function show()
		local Any = 0
		for _, R in TODAY_ROWS do
			local L, V = T.Lines[R.Key], Vals[R.Key]
			L.Row.Visible = V ~= nil and V ~= ``
			L.Text.Text = V or ``
			if L.Row.Visible then Any += 1 end
		end
		T.Quiet.Visible = Any == 0
	end
	show()
	-- the server's two lines arrive a beat later (never blocks the home screen)
	task.spawn(function()
		local S = Local.Call(`Today`)
		if typeof(S) ~= `table` or not Ui then return end
		if typeof(S.Heard) == `string` and S.Heard ~= `` then Vals.Heard = `"{S.Heard}"` end
		local N = S.Next
		if typeof(N) == `table` and N.Name then
			Vals.Next = `<b>{N.Name}:</b> {N.Missing}` .. (if (N.More or 0) > 0 then ` <font color="#{HINT:ToHex()}">(+{N.More} more)</font>` else ``)
		end
		show()
	end)
end
function Shared.TodayForTests()
	Local.Today()
	task.wait(1.5)
	local T = Ui and Ui.Today
	if not T then return nil end
	local Out = {}
	for K, L in T.Lines do Out[K] = if L.Row.Visible then L.Text.Text else nil end
	return Out
end

function Local.ApplyWallpaper()
	if not Ui then return end
	local Wp = State.Wallpaper or {}
	local Preset = WallById[Wp.Preset or ``] or WALLPAPERS[1]
	Ui.WallGrad.Color = ColorSequence.new(Preset.Top, Preset.Bottom)
	local Image = tonumber(Wp.Image)
	Ui.WallImage.Visible = Image ~= nil
	Ui.Shade.Visible = Image ~= nil
	Ui.Crest.Visible = Image == nil
	if Image then Ui.WallImage.Image = `rbxthumb://type=Asset&id={Image}&w=420&h=420` end
end

-- (audit) the newest incoming wallet row's Seq (0 when none, or only old rows without one)
function Local.TopIn(): number
	local Top = 0
	for _, Hx in State.History or {} do
		if Hx.Dir == `In` then Top = math.max(Top, tonumber(Hx.Seq) or 0) end
	end
	return Top
end

-- red badges: money that arrived since you last opened the wallet, a new issue of the paper each day
function Local.Badges()
	if not Ui then return end
	Local.Seen = Local.Seen or {}
	local Seen = Local.Seen
	-- (audit) count incoming rows newer than the newest one seen (the server's Seq): counting In rows stopped working
	-- once the 15-row history was full, and showed every old row as new after a rejoin
	if Seen.InSeq == nil then Seen.InSeq = Local.TopIn() end
	local NewIn = 0
	for _, Hx in State.History or {} do
		if Hx.Dir == `In` and (tonumber(Hx.Seq) or 0) > Seen.InSeq then NewIn += 1 end
	end
	local B = Ui.Badges
	if B.Wallet then B.Wallet.Visible = NewIn > 0 B.Wallet.Text = tostring(NewIn) end
	local _, Day = Local.Clock()
	if B.Gazette then B.Gazette.Visible = Day ~= `` and Seen.Paper ~= Day B.Gazette.Text = `1` end
	local Unread = tonumber(State.Unread) or 0
	if B.Texts then B.Texts.Visible = Unread > 0 B.Texts.Text = tostring(Unread) end
	if B.Report then B.Report.Visible = State.ReportUnread == true B.Report.Text = `1` end -- (1.40)
end

function Local.ShowHome()
	Local.StopGames()
	Ui.App.Visible = false
	Ui.Home.Visible = true
	Pending = nil
	Local.Badges()
	Local.Today() -- (2.34)
end

-- an app page: a header with back and a title, then a scrolling body
function Local.Page(Title: string): ScrollingFrame
	local App = Ui.App
	for _, Ch in App:GetChildren() do if Ch.Name ~= `Grain` then Ch:Destroy() end end
	local Head = new(`Frame`, { Name = `Head`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 40) }, App)
	local Back = new(`TextButton`, { Text = `\u{2039}`; Font = Fonts.Title; TextSize = 30; TextColor3 = C.Gold; BackgroundTransparency = 1; Position = UDim2.fromOffset(8, 0); Size = UDim2.fromOffset(34, 40) }, Head)
	Back.Activated:Connect(function() Local.ShowHome() end)
	Local.Label(Head, Title, 20, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(44, 0); Size = UDim2.new(1, -60, 1, 0) })
	local Rule = new(`Frame`, { BackgroundColor3 = C.Crimson; BorderSizePixel = 0; Position = UDim2.new(0, 14, 1, -1); Size = UDim2.new(1, -28, 0, 1) }, Head)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, Rule)
	local Body = new(`ScrollingFrame`, { Name = `Body`; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 46); Size = UDim2.new(1, 0, 1, -46);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 3; ScrollBarImageColor3 = C.IronDim }, App)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 6); HorizontalAlignment = Enum.HorizontalAlignment.Center }, Body)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 14); PaddingRight = UDim.new(0, 14); PaddingBottom = UDim.new(0, 10) }, Body)
	Ui.Home.Visible = false
	App.Visible = true
	return Body
end

local Order = 0
function Local.Line(Body: Instance, Text: string, Size: number, Props)
	Order += 1
	local T = Local.Label(Body, Text, Size, { TextWrapped = true; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, Size + 4); LayoutOrder = Order })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.Card(Body: Instance, Height: number): Frame
	Order += 1
	local F = new(`Frame`, { BackgroundColor3 = C.Ink; BackgroundTransparency = 0.35; BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, Height); LayoutOrder = Order }, Body)
	new(`UICorner`, { CornerRadius = UDim.new(0, 8) }, F)
	new(`UIStroke`, { Color = C.IronDim; Thickness = 1; Transparency = 0.5 }, F)
	return F
end

---| apps |---

function Local.OpenApp(Id: string)
	pcall(Kit.PlaySound, `Tick`, 0.6, 1.2)
	Order = 0
	if Id == `Camera` then
		Shared.Toggle(false)
		local Cm = Local.Controller(`Cinematic`)
		if Cm then task.delay(0.3, function() Cm.Toggle(true) end) end
		return
	elseif Id == `Timetable` or Id == `Group` or Id == `Options` or Id == `Factions` then
		Shared.Toggle(false)
		local Name = ({ Timetable = `Timetable`; Group = `StudyGroup`; Options = `SettingsMenu`; Factions = `FactionsPanel` })[Id]
		local M = Local.Controller(Name)
		if M and M.Toggle then task.delay(0.15, function() pcall(M.Toggle, true) end) end
		return
	end
	if Id == `Wisp` or Id == `Hex` or Id == `Crypt` then Local.Arcade(Id) return end
	if Id == `Cliques` then Local.Cliques() return end
	if Id == `Texts` then Local.Texts() return end
	if Id == `Report` then Local.Report() return end -- (1.40)
	Local.Seen = Local.Seen or {}
	if Id == `Wallet` then
		Local.Seen.InSeq = Local.TopIn() -- (audit) seen up to the newest incoming row
	elseif Id == `Gazette` then
		local _, Day = Local.Clock()
		Local.Seen.Paper = Day
	end
	if Id == `Style` then Local.Style() return end
	if Id == `Wallet` then Local.Wallet()
	elseif Id == `Radio` then Local.Radio()
	elseif Id == `Gazette` then Local.Gazette()
	elseif Id == `Contacts` then Local.Contacts() end
end

-- the arcade (Controllers.Gui.PhoneGames): the game plays on a stage under the page header
local ARCADE = { Wisp = `Wisp Flight`; Hex = `Hex Slash`; Crypt = `Crypt Crush` }
function Local.StopGames()
	local M = script.Parent:FindFirstChild(`PhoneGames`)
	local Ok, PG = pcall(require, M)
	if M and Ok and PG and PG.Close then PG.Close() end
end

function Local.Arcade(Id: string)
	local Body = Local.Page(ARCADE[Id])
	Body:Destroy()
	local Stage = new(`Frame`, { Name = `Stage`; BackgroundColor3 = Color3.fromRGB(8, 6, 10); BorderSizePixel = 0; ClipsDescendants = true;
		Position = UDim2.fromOffset(0, 46); Size = UDim2.new(1, 0, 1, -46) }, Ui.App)
	local M = script.Parent:WaitForChild(`PhoneGames`, 5)
	local Ok, PG = pcall(require, M)
	if M and Ok and PG then PG.Open(Id, Stage, Local.ShowHome) end
end

-- Wallet
function Local.Wallet()
	local Body = Local.Page(`Wallet`)
	local S = Local.Call(`Get`)
	if S then State = S end
	local Bal = Local.Card(Body, 84)
	Local.Label(Bal, `BALANCE`, 13, { Font = Fonts.Title; TextColor3 = SECTION; Position = UDim2.fromOffset(14, 8); Size = UDim2.new(1, -28, 0, 16) })
	Local.Label(Bal, `{YEN} {State.Yen}`, 36, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(14, 26); Size = UDim2.new(1, -28, 0, 44) })
	Local.Line(Body, `SEND TO`, 14, { Font = Fonts.Title; TextColor3 = SECTION })
	local Who = Local.Line(Body, if Pending then `<b>{Pending.Name}</b>` else `<i>Pick a classmate below.</i>`, 15)
	Order += 1
	local _, AmountApi = Kit.SearchBar({ placeholder = `Amount`; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = Order; Parent = Body })
	local Status = nil
	local Confirm = false
	local ConfirmN = nil -- (audit) the amount that was confirmed
	local Page = Body
	Order += 1
	local SendBtn, SendApi = Kit.Button({ text = `Send`; style = `gold`; Size = UDim2.new(1, 0, 0, 40); LayoutOrder = Order; Parent = Body;
		onClick = function(Api)
			local N = Local.Digits(AmountApi:Get())
			if not Pending then Status.Text = `Pick who to send to.` return end
			if not N or N < 1 then Status.Text = `Type an amount.` return end
			if Confirm and N ~= ConfirmN then Confirm = false end -- (audit) the amount changed: confirm it again
			if not Confirm then
				Confirm = true
				ConfirmN = N
				Api:SetText(`Confirm {YEN}{N} to {Pending.Name}?`)
				task.delay(4, function() if Confirm then Confirm = false pcall(function() Api:SetText(`Send`) end) end end)
				return
			end
			Confirm = false
			Api:SetText(`Send`)
			local Ok, Msg = Local.Call(`Send`, Pending.UserId, N)
			Status.Text = Msg or ``
			Status.TextColor3 = if Ok then Color3.fromRGB(150, 205, 140) else Color3.fromRGB(235, 120, 110)
			if Ok then pcall(Kit.PlaySound, `Confirm`) task.delay(1.2, function() if Open and Ui.App.Visible and Page.Parent then Local.Wallet() end end) end -- (audit) only if the Wallet is still the open page
		end })
	Status = Local.Line(Body, ``, 15, { TextColor3 = HINT })
	-- pick a classmate
	local List = Local.Call(`Contacts`) or {}
	if #List == 0 then Local.Line(Body, `<i>Nobody else is in the building.</i>`, 15, { TextColor3 = HINT }) end
	for _, P in List do
		local Row = Local.Card(Body, 40)
		local Btn = new(`TextButton`, { Text = ``; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Row)
		Local.Label(Row, P.Name, 15, { Font = Fonts.Title; Position = UDim2.fromOffset(12, 2); Size = UDim2.new(1, -24, 0, 20) })
		Local.Label(Row, string.upper(`{P.Race}  \u{00B7}  LV {P.Level}`), 12, { Font = Fonts.Title; TextColor3 = RACE_COLOR[P.Family] or C.Text; Position = UDim2.fromOffset(12, 22); Size = UDim2.new(1, -24, 0, 16) })
		Btn.Activated:Connect(function() Pending = { UserId = P.UserId; Name = P.Name } Who.Text = `<b>{P.Name}</b>` Confirm = false end)
	end
	Local.Line(Body, `HISTORY`, 14, { Font = Fonts.Title; TextColor3 = SECTION })
	if #State.History == 0 then Local.Line(Body, `<i>No transfers yet.</i>`, 15, { TextColor3 = HINT }) end
	for _, Hx in State.History do
		local In = Hx.Dir == `In`
		Local.Line(Body, `<font color="#{(if In then Color3.fromRGB(150, 205, 140) else Color3.fromRGB(235, 120, 110)):ToHex()}">{if In then `+` else `\u{2212}`}{YEN}{Hx.Amount}</font>  {if In then `from` else `to`} {Hx.Who}  <font color="#{HINT:ToHex()}">{Hx.At}</font>`, 15)
	end
end

-- Night FM
function Local.Play(Id: number)
	if not Music.Sound then
		Music.Sound = new(`Sound`, { Name = `NHPhoneMusic`; Volume = 0.5; Looped = true }, SoundService)
	end
	local S = Music.Sound
	S:Stop()
	S.SoundId = `rbxassetid://{Id}`
	Music.Id = Id
	Music.Title = `Track {Id}`
	task.spawn(function()
		local Ok, Info = pcall(MarketplaceService.GetProductInfo, MarketplaceService, Id, Enum.InfoType.Asset)
		if Ok and Info and Info.AssetTypeId == 3 then Music.Title = Info.Name or Music.Title
		elseif Ok and Info then Music.Title = `Not an audio ID` end
	end)
	S:Play()
	-- remember it
	local Recent = table.clone(State.Recent or {})
	local At = table.find(Recent, Id)
	if At then table.remove(Recent, At) end
	table.insert(Recent, 1, Id)
	while #Recent > 10 do table.remove(Recent) end
	State.Recent = Recent
	task.spawn(Local.Call, `SaveRecent`, Recent)
end

function Local.Radio() -- (2.30) Night FM is its own module now (Controllers.Gui.PhoneRadio), dressed like the owner's reference
	Ui.Radio = nil
	require(script.Parent:WaitForChild(`PhoneRadio`)).Open({ App = Ui.App; Music = Music; State = State; Play = Local.Play;
		Call = Local.Call; Home = Local.ShowHome; Kit = Kit; Theme = Theme })
	Ui.Home.Visible = false
end

-- The Midnight Bell
-- (1.40) the Report Card app: last week's card on parchment, a wax seal with your average, earlier weeks, this week so far
local PARCH_TOP, PARCH_BOT = Color3.fromRGB(242, 233, 208), Color3.fromRGB(214, 196, 160)
local INK = Color3.fromRGB(30, 20, 16)
local INK_SOFT = Color3.fromRGB(78, 58, 44)
local BOLD = Theme.FontFaces.BodyBold -- bold Garamond: thin strokes blur on parchment at phone size
local WAX = Color3.fromRGB(150, 22, 34)
local GRADE_INK = {
	[`A+`] = Color3.fromRGB(34, 96, 58); A = Color3.fromRGB(34, 96, 58);
	B = Color3.fromRGB(38, 62, 124); C = Color3.fromRGB(70, 56, 40);
	D = Color3.fromRGB(150, 22, 34); F = Color3.fromRGB(150, 22, 34);
}
local function when(Ago: number): string
	if Ago <= 1 then return `LAST WEEK` end
	if Ago == 2 then return `TWO WEEKS AGO` end
	if Ago == 3 then return `THREE WEEKS AGO` end
	return `{Ago} WEEKS AGO`
end
local function seal(Parent: Instance, Size: number, Letter: string?, Pos: UDim2, Anchor: Vector2, Z: number)
	local Holder = new(`Frame`, { Name = `Seal`; BackgroundTransparency = 1; AnchorPoint = Anchor; Position = Pos; Size = UDim2.fromOffset(Size, Size); ZIndex = Z }, Parent)
	Kit.Image(`Glow`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.55); Size = UDim2.fromScale(1.5, 1.5); ImageColor3 = Color3.fromRGB(60, 8, 12);
		ImageTransparency = 0.55; ScaleType = Enum.ScaleType.Stretch; ZIndex = Z; Parent = Holder })
	local S = Kit.Image(`IconGradeSeal`, { Name = `Wax`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ImageColor3 = WAX; ZIndex = Z + 1; Parent = Holder })
	local L = Local.Label(Holder, Letter or `\u{2014}`, math.floor(Size * (if Letter and #Letter > 1 then 0.34 else 0.42)), { Name = `Letter`; Font = Fonts.Title;
		TextColor3 = Color3.fromRGB(252, 232, 206); TextStrokeColor3 = Color3.fromRGB(70, 6, 12); TextStrokeTransparency = 0.35;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.52); Size = UDim2.fromScale(0.8, 0.5); ZIndex = Z + 2 })
	return Holder, S, L
end

function Local.Report()
	local Body = Local.Page(`Report Card`)
	local R = Local.Call(`Reports`)
	State.ReportUnread = false
	Local.Badges()
	-- the masthead: the crest, the school, the title, an ornate rule
	Order += 1
	-- the crest at a size its detail survives (no glow behind it: a glow only smears it)
	local Mast = new(`Frame`, { Name = `Mast`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 138); LayoutOrder = Order }, Body)
	Kit.Image(`CrestFlat`, { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 0); Size = UDim2.fromOffset(66, 66); ScaleType = Enum.ScaleType.Fit; Parent = Mast })
	Local.Label(Mast, `N I G H T M A R E   H I G H`, 13, { Font = Fonts.Title; TextColor3 = SECTION; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 70); Size = UDim2.new(1, 0, 0, 16) })
	Local.Label(Mast, `Report Card`, 28, { Font = Fonts.Title; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 86); Size = UDim2.new(1, 0, 0, 30) })
	Kit.Image(`Divider`, { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 120); Size = UDim2.new(0.86, 0, 0, 14); ImageColor3 = C.Gold; ImageTransparency = 0.15;
		ScaleType = Enum.ScaleType.Fit; Parent = Mast })
	if type(R) ~= `table` then Local.Line(Body, `<i>The Office isn't answering. Try again in a moment.</i>`, 15, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center }) return end
	local Cards = type(R.Cards) == `table` and R.Cards or {}
	local Now = tonumber(R.Week) or 0

	-- one parchment card
	local function parchment(Height: number?)
		Order += 1
		local Outer = new(`Frame`, { Name = `Parchment`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, Height or 0);
			AutomaticSize = if Height then Enum.AutomaticSize.None else Enum.AutomaticSize.Y; LayoutOrder = Order }, Body)
		new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Outer)
		new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(PARCH_TOP, PARCH_BOT) }, Outer)
		-- a soft burnt edge and the gilt frame
		new(`UIStroke`, { Color = Color3.fromRGB(96, 66, 36); Thickness = 2; Transparency = 0.45 }, Outer)
		Kit.Slice(`FrameThin`, Color3.fromRGB(196, 154, 82), { Name = `Gilt`; SliceScale = 0.34; ImageTransparency = 0.05; ZIndex = 6; Parent = Outer })
		local Inner = new(`Frame`, { Name = `Inner`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y }, Outer)
		new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 4) }, Inner)
		new(`UIPadding`, { PaddingLeft = UDim.new(0, 18); PaddingRight = UDim.new(0, 18); PaddingTop = UDim.new(0, 16); PaddingBottom = UDim.new(0, 16) }, Inner)
		return Outer, Inner
	end
	local function ink(Parent, Text, Size, N, Props)
		local L = Local.Label(Parent, Text, Size, { FontFace = BOLD; TextColor3 = INK; TextWrapped = true; AutomaticSize = Enum.AutomaticSize.Y; Size = UDim2.new(1, 0, 0, Size + 2); LayoutOrder = N; ZIndex = 7 })
		for K, V in Props or {} do L[K] = V end
		return L
	end
	local function rule(Parent, N)
		local F = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 14); LayoutOrder = N }, Parent)
		Kit.Image(`Divider`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(0.9, 0, 0, 12); ImageColor3 = Color3.fromRGB(110, 78, 46);
			ImageTransparency = 0.3; ScaleType = Enum.ScaleType.Fit; ZIndex = 7; Parent = F })
	end
	local function heading(Parent, Text, N)
		return ink(Parent, Text, 14, N, { Font = Fonts.Title; TextColor3 = WAX })
	end

	if #Cards == 0 then
		local _, In = parchment()
		heading(In, `YOUR FIRST REPORT CARD`, 1)
		ink(In, `Mr. Hale sends report cards on Monday morning, for the week before: your grades in every subject, your attendance and your conduct. Good marks earn an allowance.`, 16, 2, { TextColor3 = INK_SOFT })
	else
		local Card = Cards[1]
		local Outer, In = parchment()
		-- the head: when, who, and the seal
		local Head = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 90); LayoutOrder = 1 }, In)
		Local.Label(Head, when(Now - (tonumber(Card.Week) or Now - 1)), 14, { Font = Fonts.Title; TextColor3 = WAX; Size = UDim2.new(1, -96, 0, 18); ZIndex = 7 })
		Local.Label(Head, R.Student ~= `` and R.Student or Player.DisplayName, 23, { Font = Fonts.Title; TextColor3 = INK; TextWrapped = true; Position = UDim2.fromOffset(0, 20); Size = UDim2.new(1, -96, 0, 48); ZIndex = 7;
			TextYAlignment = Enum.TextYAlignment.Top })
		Local.Label(Head, `{R.Race or `Student`}  \u{00B7}  Homeroom 101`, 15, { FontFace = BOLD; TextColor3 = INK_SOFT; Position = UDim2.fromOffset(0, 68); Size = UDim2.new(1, -96, 0, 18); ZIndex = 7 })
		local SealF, Wax = seal(Head, 76, Card.Average, UDim2.new(1, 4, 0, -4), Vector2.new(1, 0), 8)
		Local.Label(SealF, `AVERAGE`, 12, { Font = Fonts.Title; TextColor3 = INK_SOFT; TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0);
			Position = UDim2.new(0.5, 0, 1, -2); Size = UDim2.new(1, 0, 0, 12); ZIndex = 9 })
		if R.New and not Kit.ReducedMotion() then
			-- pressed in: the seal drops onto the paper with a little give
			SealF.Rotation = -14
			Wax.Size = UDim2.fromScale(1.9, 1.9)
			Wax.ImageTransparency = 1
			tween(Wax, 0.32, { Size = UDim2.fromScale(1, 1); ImageTransparency = 0 }, Enum.EasingStyle.Back)
			tween(SealF, 0.32, { Rotation = 0 }, Enum.EasingStyle.Back)
			task.delay(0.2, function() pcall(Kit.PlaySound, `Confirm`, 0.6, 0.9) end)
		end
		rule(In, 2)
		-- the grades
		heading(In, `GRADES`, 3)
		local Rows = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = 4 }, In)
		new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 2) }, Rows)
		for I, S in Card.Subjects or {} do
			-- a shaded stripe on every other row, so the eye can follow it to the grade
			local Row = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(120, 86, 50); BackgroundTransparency = if I % 2 == 1 then 0.86 else 1; BorderSizePixel = 0;
				Size = UDim2.new(1, 0, 0, 30); LayoutOrder = I; ZIndex = 7 }, Rows)
			new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, Row)
			new(`UIPadding`, { PaddingLeft = UDim.new(0, 8); PaddingRight = UDim.new(0, 8) }, Row)
			Local.Label(Row, S.Name, 18, { FontFace = BOLD; TextColor3 = INK; Size = UDim2.new(0.68, 0, 1, 0); ZIndex = 8 })
			local G = S.Grade
			local Letter = G == `Attended` or G == `Absent`
			Local.Label(Row, if Letter then string.lower(G) else G, if Letter then 16 else 23, { Font = if Letter then nil else Fonts.Title; FontFace = if Letter then BOLD else nil;
				TextColor3 = if G == `Absent` then WAX elseif Letter then INK_SOFT else (GRADE_INK[G] or INK); TextXAlignment = Enum.TextXAlignment.Right;
				AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.new(0.32, 0, 1, 0); ZIndex = 8 })
		end
		if #(Card.Subjects or {}) == 0 then ink(In, `No classes attended.`, 16, 4, { TextColor3 = INK_SOFT }) end
		rule(In, 5)
		-- attendance: a pip for every class (ink: there; crimson: missed)
		local A = Card.Attendance or {}
		heading(In, `ATTENDANCE`, 6)
		local Parts = { `{A.Attended or 0} of {A.Total or 0} classes` }
		if (A.Tardy or 0) > 0 then table.insert(Parts, `{A.Tardy} late`) end
		if (A.LeftEarly or 0) > 0 then table.insert(Parts, `{A.LeftEarly} left early`) end
		if (A.Absent or 0) > 0 then table.insert(Parts, `{A.Absent} absent`) end
		ink(In, table.concat(Parts, `  \u{00B7}  `), 17, 7)
		local Pips = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = 8 }, In)
		new(`UIGridLayout`, { CellSize = UDim2.fromOffset(13, 13); CellPadding = UDim2.fromOffset(4, 4); SortOrder = Enum.SortOrder.LayoutOrder }, Pips)
		local Missed = (A.Absent or 0)
		local Late = (A.Tardy or 0) + (A.LeftEarly or 0)
		for I = 1, math.min(30, A.Total or 0) do
			local Col = if I > (A.Total or 0) - Missed then WAX elseif I > (A.Total or 0) - Missed - Late then Color3.fromRGB(176, 120, 50) else INK
			Kit.Image(`Pip`, { ImageColor3 = Col; LayoutOrder = I; ZIndex = 7; Parent = Pips })
		end
		if A.Perfect then
			ink(In, `\u{2726}  Perfect attendance  \u{2726}`, 16, 9, { Font = Fonts.Title; TextColor3 = Color3.fromRGB(140, 94, 24) })
		elseif (A.Streak or 0) > 1 then
			ink(In, `On-time streak: {A.Streak} classes`, 15, 9, { TextColor3 = INK_SOFT })
		end
		-- conduct
		heading(In, `CONDUCT`, 10)
		local Cn = Card.Conduct or `Clear`
		ink(In, if Cn == `Clear` then `Clear. Not a mark against you.` elseif Cn == `Detention` then `Detention. See the Office.` else `{Cn} from the hall monitors.`, 17, 11,
			{ TextColor3 = if Cn == `Clear` then Color3.fromRGB(34, 96, 58) elseif Cn == `Detention` then WAX else INK })
		rule(In, 12)
		-- the comment, signed
		heading(In, `MR. HALE SAYS`, 13)
		ink(In, `\u{201C}{Card.Comment or ``}\u{201D}`, 17, 14, { TextColor3 = INK })
		-- the signature: the nib right beside the name, both flush right
		local Sig = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = 15 }, In)
		new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Right; VerticalAlignment = Enum.VerticalAlignment.Center;
			SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 6) }, Sig)
		Kit.Image(`IconNib`, { Size = UDim2.fromOffset(20, 20); ImageColor3 = INK; ZIndex = 7; LayoutOrder = 1; Parent = Sig })
		Local.Label(Sig, `{Card.Teacher or `Mr. Hale, Homeroom`}`, 15, { FontFace = BOLD; TextColor3 = INK_SOFT; AutomaticSize = Enum.AutomaticSize.X;
			Size = UDim2.new(0, 0, 1, 0); ZIndex = 7; LayoutOrder = 2 })
		-- the allowance: a dark ribbon across the foot of the card
		-- the allowance: a bursar's voucher pinned to the foot of the card, a gold coin, the sum, and a rubber stamp
		local Paid = tonumber(Card.Allowance) or 0
		local Gap = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 6); LayoutOrder = 16 }, In)
		local Slip = new(`Frame`, { Name = `Voucher`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 74); LayoutOrder = 17; ZIndex = 7 }, In)
		new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, Slip)
		new(`UIGradient`, { Rotation = 0; Color = ColorSequence.new(Color3.fromRGB(222, 204, 164), Color3.fromRGB(232, 218, 184)) }, Slip)
		new(`UIStroke`, { Color = Color3.fromRGB(120, 86, 44); Thickness = 1; Transparency = 0.5 }, Slip)
		Kit.Slice(`FrameThin`, Color3.fromRGB(188, 146, 70), { SliceScale = 0.28; ImageTransparency = 0.1; ZIndex = 8; Parent = Slip })
		-- the coin: a struck gold yen (IconCoinYen)
		local Coin = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 10, 0.5, 0); Size = UDim2.fromOffset(48, 48); ZIndex = 8 }, Slip)
		Kit.Image(`IconCoinYen`, { Size = UDim2.fromScale(1, 1); ImageColor3 = if Paid > 0 then Color3.new(1, 1, 1) else Color3.fromRGB(150, 140, 126); ZIndex = 9; Parent = Coin })
		Local.Label(Coin, ``, 22, { -- the coin art is struck with the yen Font = Fonts.Title; TextColor3 = if Paid > 0 then Color3.fromRGB(96, 58, 14) else Color3.fromRGB(80, 72, 64);
			TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.52); Size = UDim2.fromScale(1, 0.6); ZIndex = 10 })
		Local.Label(Slip, `Allowance`, 19, { Font = Fonts.Title; TextColor3 = INK; Position = UDim2.fromOffset(68, 14); Size = UDim2.new(1, -160, 0, 24); ZIndex = 9 })
		Local.Label(Slip, if Paid > 0 then `From the Bursar` else `Better marks next week`, 14, { FontFace = BOLD; TextColor3 = INK_SOFT; TextWrapped = true;
			Position = UDim2.fromOffset(68, 38); Size = UDim2.new(1, -160, 0, 32); TextYAlignment = Enum.TextYAlignment.Top; ZIndex = 9 })
		Local.Label(Slip, if Paid > 0 then `{YEN}{Paid}` else `\u{2014}`, 28, { Font = Fonts.Title; TextColor3 = if Paid > 0 then Color3.fromRGB(122, 80, 16) else INK_SOFT;
			TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 36); Size = UDim2.fromOffset(84, 32); ZIndex = 9 })
		-- the rubber stamp, struck at a slant above the sum
		local Stamp = new(`Frame`, { Name = `Stamp`; BackgroundColor3 = WAX; BackgroundTransparency = 0.9; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(1, -54, 0, 22);
			Size = UDim2.fromOffset(74, 26); Rotation = -9; ZIndex = 11 }, Slip)
		new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Stamp)
		new(`UIStroke`, { Color = WAX; Thickness = 2; Transparency = 0.05 }, Stamp)
		Local.Label(Stamp, if Paid > 0 then `PAID` else `NONE`, 17, { Font = Fonts.Title; TextColor3 = WAX; TextXAlignment = Enum.TextXAlignment.Center;
			Size = UDim2.fromScale(1, 1); ZIndex = 12 })
		if R.New and not Kit.ReducedMotion() then
			Stamp.Size = UDim2.fromOffset(120, 42)
			Stamp.Rotation = -24
			task.delay(0.45, function()
				tween(Stamp, 0.22, { Size = UDim2.fromOffset(74, 26); Rotation = -9 }, Enum.EasingStyle.Back)
			end)
		end
		-- earlier weeks
		if #Cards > 1 then
			Local.Line(Body, `EARLIER WEEKS`, 14, { Font = Fonts.Title; TextColor3 = SECTION })
			for I = 2, #Cards do
				local K = Cards[I]
				local Row = Local.Card(Body, 58)
				seal(Row, 42, K.Average, UDim2.fromOffset(8, 8), Vector2.zero, 2)
				local Ka = K.Attendance or {}
				Local.Label(Row, when(Now - (tonumber(K.Week) or Now - I)), 14, { Font = Fonts.Title; TextColor3 = SECTION; Position = UDim2.fromOffset(60, 8); Size = UDim2.new(1, -70, 0, 18) })
				Local.Label(Row, `{if K.Average then `{K.Average} average` else `no grades`}  \u{00B7}  {Ka.Attended or 0} of {Ka.Total or 0} classes  \u{00B7}  {YEN}{K.Allowance or 0}`, 15,
					{ FontFace = BOLD; TextColor3 = HINT; Position = UDim2.fromOffset(60, 28); Size = UDim2.new(1, -70, 0, 20); TextWrapped = true })
			end
		end
	end
	-- this week so far
	local So = R.SoFar or {}
	local Row = Local.Card(Body, 70)
	Kit.Image(`Bell`, { AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 10, 0.5, 0); Size = UDim2.fromOffset(30, 30); ImageColor3 = SECTION; Parent = Row })
	Local.Label(Row, `THIS WEEK SO FAR`, 14, { Font = Fonts.Title; TextColor3 = SECTION; Position = UDim2.fromOffset(50, 8); Size = UDim2.new(1, -60, 0, 18) })
	Local.Label(Row, if (So.Total or 0) > 0 then `{So.Attended} of {So.Total} classes{if So.Average then `, {So.Average} average` else ``}. The next card comes Monday.` else `No classes yet this week. The next card comes Monday.`, 15,
		{ FontFace = BOLD; TextColor3 = HINT; TextWrapped = true; TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(50, 28); Size = UDim2.new(1, -60, 0, 38) })
end

function Local.Gazette()
	local Body = Local.Page(`The Midnight Bell`)
	local G = Local.Call(`Gazette`)
	Local.Line(Body, `THE  MIDNIGHT  BELL`, 24, { Font = Fonts.Title; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center })
	Local.Line(Body, `<i>Nightmare Highschool's paper of record  \u{00B7}  Issue {G and G.Issue or `?`}</i>`, 13, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center })
	Local.Line(Body, G and G.Date or ``, 14, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center })
	if not G then Local.Line(Body, `<i>The presses are down. Try again in a moment.</i>`, 14) return end
	for I, A in G.Articles do
		Order += 1
		local Rule = new(`Frame`, { BackgroundColor3 = if I == 1 then C.Gold else C.IronDim; BackgroundTransparency = 0.3; BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 1); LayoutOrder = Order }, Body)
		Local.Line(Body, A.Kicker, 12, { Font = Fonts.Title; TextColor3 = Color3.fromRGB(225, 80, 90) })
		Local.Line(Body, A.Title, if I == 1 then 22 else 17, { Font = Fonts.Title })
		Local.Line(Body, A.Body, 15, { TextColor3 = Color3.fromRGB(225, 218, 206) })
	end
end

-- Cliques (1.20): every clique, your standing with each, and the two factions' ranks
local CliqueConn = nil
local CliqueTab = 1 -- (1.33) Standing | Today
function Local.Cliques()
	local Body = Local.Page(`Cliques`)
	local F = ReplicatedStorage:FindFirstChild(`NHCliques`)
	local Tabs = Kit.TabBar({ tabs = { `Standing`, `Today` }; selected = CliqueTab; textSize = 15; Size = UDim2.new(1, 0, 0, 38); Parent = Body;
		onChanged = function(I) if I ~= CliqueTab then CliqueTab = I Order = 0 Local.Cliques() end end })
	if typeof(Tabs) == `Instance` then Tabs.LayoutOrder = 0 end
	if CliqueTab == 2 then Local.CliquesToday(Body, F) return end
	local Get = F and F:GetAttribute(`Ready`) and F:FindFirstChild(`Get`)
	local List = nil
	if Get then local Ok, R = pcall(Get.InvokeServer, Get) if Ok then List = R end end
	Local.Line(Body, `<i>Every crowd at Nightmare High, and how its members see you. Hurt one of theirs and they remember; their rivals may not mind.</i>`, 14, { TextColor3 = HINT })
	if type(List) ~= `table` then Local.Line(Body, `<i>No signal. Try again in a moment.</i>`, 15, { TextColor3 = HINT }) return end
	for _, Q in List do
		local Faction = type(Q.Faction) == `table` and Q.Faction or nil
		local Member = type(Q.Member) == `table` and Q.Member or nil -- (1.35) one of the six you've joined
		local Row = Local.Card(Body, if Faction or Member then 150 else 118)
		local Col = typeof(Q.Color) == `Color3` and Q.Color or C.Text
		local Chip = new(`Frame`, { BackgroundColor3 = Col; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 10); Size = UDim2.new(0, 4, 1, -20) }, Row)
		new(`UICorner`, { CornerRadius = UDim.new(0, 2) }, Chip)
		Local.Label(Row, Q.Name, 17, { Font = Fonts.Title; TextColor3 = Col; Position = UDim2.fromOffset(14, 6); Size = UDim2.new(1, -120, 0, 22) })
		local TierCol = if Q.Standing >= 20 then Color3.fromRGB(150, 210, 120) elseif Q.Standing <= -10 then Color3.fromRGB(230, 90, 90) else HINT
		Local.Label(Row, string.upper(Q.Tier), 12, { Font = Fonts.Title; TextColor3 = TierCol; TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 10); Size = UDim2.fromOffset(100, 16) })
		Local.Label(Row, string.upper(`{Q.Archetype}  \u{00B7}  {Q.Hangout}`), 11, { Font = Fonts.Title; TextColor3 = SECTION; Position = UDim2.fromOffset(14, 28); Size = UDim2.new(1, -28, 0, 14) })
		Local.Label(Row, `<i>{Q.Tagline}</i>`, 13, { TextColor3 = HINT; TextWrapped = true; TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(14, 44); Size = UDim2.new(1, -28, 0, 32) })
		-- standing bar: -100 on the left, 0 in the middle, 100 on the right
		local Bar = new(`Frame`, { BackgroundColor3 = C.Ink; BorderSizePixel = 0; Position = UDim2.fromOffset(14, 82); Size = UDim2.new(1, -70, 0, 5) }, Row)
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Bar)
		new(`UIStroke`, { Color = C.IronDim; Thickness = 1; Transparency = 0.4 }, Bar)
		local V = math.clamp(tonumber(Q.Standing) or 0, -100, 100) / 100
		local Fill = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.BarFill; ImageColor3 = TierCol; ScaleType = Enum.ScaleType.Stretch;
			AnchorPoint = Vector2.new(if V < 0 then 1 else 0, 0); Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromScale(math.abs(V) / 2, 1) }, Bar)
		new(`Frame`, { BackgroundColor3 = C.Gold; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(0, 1, 1, 6) }, Bar)
		Local.Label(Row, `{if Q.Standing > 0 then `+` else ``}{Q.Standing}`, 13, { Font = Fonts.Title; TextColor3 = TierCol; TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 76); Size = UDim2.fromOffset(46, 16) })
		Local.Label(Row, `Leader <b>{Q.Leader}</b>   \u{00B7}   Rival <b>{Q.Rival}</b>`, 12, { TextColor3 = C.Text; TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(14, 94); Size = UDim2.new(1, -28, 0, 16) })
		if Member then
			Local.Label(Row, `MEMBER  \u{00B7}  {string.upper(tostring(Member.Rank or `Hanger-on`))}`, 11, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(14, 120); Size = UDim2.new(0.5, 0, 0, 16) })
			Kit.Button({ text = `Leave`; style = `crimson`; textSize = 13; Size = UDim2.fromOffset(110, 26); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 114); Parent = Row;
				onClick = function(Api)
					local R = F and F:FindFirstChild(`Leave`)
					if not R then return end
					local Ok, Done, Text = pcall(R.InvokeServer, R)
					if Ok and Api and not Done then Api:SetText(`Sure?`) end
					if Ok and Text then Local.Line(Body, `<i>{Text}</i>`, 13, { TextColor3 = HINT; LayoutOrder = -1 }) end
				end })
		end
		if Faction then
			Local.Label(Row, `FACTION  \u{00B7}  {string.upper(tostring(Faction.Rank or `Outsider`))}{if Faction.Member then `  \u{00B7}  MEMBER` else ``}`, 11, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(14, 120); Size = UDim2.new(0.5, 0, 0, 16) })
			Kit.Button({ text = `Faction`; style = `gold`; textSize = 13; Size = UDim2.fromOffset(110, 26); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 114); Parent = Row;
				onClick = function()
					Shared.Toggle(false)
					local M = Local.Controller(`FactionsPanel`)
					if M and M.Toggle then task.delay(0.15, function() pcall(M.Toggle, true) end) end
				end })
		end
	end
	-- refresh while this page is open
	if CliqueConn then CliqueConn:Disconnect() CliqueConn = nil end
	local Changed = F and F:FindFirstChild(`Changed`)
	local Page = Body
	if Changed then
		CliqueConn = Changed.OnClientEvent:Connect(function()
			if Page.Parent and Ui.App.Visible then Order = 0 Local.Cliques() elseif CliqueConn then CliqueConn:Disconnect() CliqueConn = nil end
		end)
	end
end

-- (1.33) the bulletin: what's going on between the cliques today
local TodayConn = nil
function Local.CliquesToday(Body: Instance, F: Instance?)
	local Get = F and F:FindFirstChild(`Today`)
	local D = nil
	if Get then local Ok, R = pcall(Get.InvokeServer, Get) if Ok then D = R end end
	if type(D) ~= `table` then Local.Line(Body, `<i>No signal. Try again in a moment.</i>`, 15, { TextColor3 = HINT }) return end
	local function Head(Text: string) Local.Line(Body, string.upper(Text), 12, { Font = Fonts.Title; TextColor3 = SECTION }) end
	local function Row(Text: string, Col: Color3?) Local.Line(Body, Text, 14, { TextColor3 = Col or C.Text }) end
	local function None(Text: string) Local.Line(Body, `<i>{Text}</i>`, 13, { TextColor3 = HINT }) end
	-- rumble
	Head(`Rumble`)
	local R = D.Rumble
	if R and R.Live then
		Row(`<b>LIVE</b> at {R.Venue}: {R.A} ({R.WavesA or 0} waves left) vs {R.B} ({R.WavesB or 0} left)`, Color3.fromRGB(240, 120, 110))
	elseif R and R.Plan then
		Row(`{R.Plan.A} vs {R.Plan.B}, after school {if R.Plan.Today then `<b>today</b>` else `tomorrow`}, at {R.Venue}.`)
	else
		None(`Nothing planned. They come every few days.`)
	end
	if R and R.Last then Row(`Last time: {R.Last.A} vs {R.Last.B}, {if R.Last.Winner then `{R.Last.Winner} won` else `nobody won`}.`, HINT) end
	-- turf
	Head(`Turf`)
	if #(D.Turf or {}) == 0 then None(`Every hangout is with its own crowd.`) end
	for _, T in D.Turf or {} do Row(`{T.Hangout}: held by <b>{T.Holder}</b> (it's {T.Owner}'s)`, typeof(T.Color) == `Color3` and T.Color or nil) end
	-- pranks
	Head(`Pranks`)
	if #(D.Pranks or {}) == 0 and #(D.Messes or {}) == 0 then None(`All quiet. For now.`) end
	for _, P in D.Pranks or {} do Row(`<b>Right now:</b> {P.By} at {P.Hangout}{if P.Stopped then ` (someone stopped them)` else ``}`, Color3.fromRGB(240, 200, 110)) end
	for _, M in D.Messes or {} do Row(`{M.Hangout}: a {string.lower(tostring(M.Kind or `mess`))} mess, by {M.By}`) end
	-- feuds
	Head(`Feuds today`)
	if #(D.Feuds or {}) == 0 then None(`No fights yet today.`) end
	for _, Fe in D.Feuds or {} do Row(`{Fe.A} vs {Fe.B}: {Fe.Count} fight{if Fe.Count == 1 then `` else `s`}{if Fe.Wins ~= `` then ` ({Fe.Wins})` else ``}`) end
	-- (1.35) your clique
	local Mb = D.Member
	if type(Mb) == `table` then
		Head(`Your clique`)
		if Mb.Faction then
			Row(`<b>{Mb.Clique}</b> (your faction: see the Factions panel)`)
		else
			Row(`<b>{Mb.Clique}</b>, {Mb.Rank or `Hanger-on`}{if Mb.Next then `  \u{00B7}  {Mb.ToNext} to {Mb.Next}` else ``}`, C.Gold)
			if Mb.Job then Row(`Today's job: <b>{Mb.Job}</b> ({Mb.JobState})`) end
		end
	end
	-- (1.34) showdowns with the leaders
	local Sd = D.Showdowns
	if type(Sd) == `table` then
		Head(`Showdowns  \u{00B7}  {Sd.Beaten or 0}/{Sd.Of or 8} leaders beaten`)
		if Sd.King then Row(`<b>You run this school.</b> 10% off at every shop, and backup at every hangout.`, C.Gold) end
		for _, O in Sd.Open or {} do
			Row(if O.Foe then `<b>{O.Leader}</b> challenged you: {O.Hangout}, after school or tonight.` else `<b>{O.Leader}</b> is waiting for you at {O.Hangout}.`,
				if O.Foe then Color3.fromRGB(240, 120, 110) else nil)
		end
		if #(Sd.Open or {}) == 0 and not Sd.King then None(`Friendly with a clique and done its leader's quests? Ask them: "I want to test myself."`) end
	end
	-- your dares
	local Left = tonumber(D.HoursLeft)
	Head(`Your dares{if Left then `  \u{00B7}  {math.max(1, math.floor(Left + 0.5))} h to dawn` else ``}`)
	if #(D.Dares or {}) == 0 then None(`None today. Leaders text them in the morning, or ask one: "Got a dare for me?"`) end
	for _, Dr in D.Dares or {} do
		local St = if Dr.State == `Done` then `\u{2713} done` elseif Dr.State == `Offered` then `in your Texts` else (Dr.Status or `on it`)
		Row(`<b>{Dr.Name}</b> from {Dr.From}: {St}`, if Dr.State == `Done` then Color3.fromRGB(150, 210, 120) elseif typeof(Dr.Color) == `Color3` then Dr.Color else nil)
	end
	-- refresh while open (standing changes, and every 5 s)
	if TodayConn then TodayConn:Disconnect() TodayConn = nil end
	local Page = Body
	local Changed = F and F:FindFirstChild(`Changed`)
	if Changed then
		TodayConn = Changed.OnClientEvent:Connect(function()
			if Page.Parent and Ui.App.Visible and CliqueTab == 2 then Order = 0 Local.Cliques() elseif TodayConn then TodayConn:Disconnect() TodayConn = nil end
		end)
	end
	task.delay(5, function()
		if Page.Parent and Ui.App.Visible and CliqueTab == 2 then Order = 0 Local.Cliques() end
	end)
end

-- (2.23.0) Texts, laid out like a modern messaging app (owner, 2026-11-17: "make it look more like iMessage (our theme
-- though)"). Messages: one conversation per sender (a wax-seal avatar in their clique's colour, the last line, when it
-- came, a crimson unread dot), with search. A conversation: their texts sit left in inked leather with a hairline of
-- gold, your answers right in crimson lacquer; tails on the last of a run, day stamps between days, a dare or a dorm
-- invite as a card under its bubble, quick replies over a sealed composer (players never type to NPCs), a typing quill
-- when a new text lands while you're reading, and "Sealed" under your last answer. Opening a conversation marks only
-- that sender's texts read (NHPhone.Texts(true, From)).
local TextService = game:GetService(`TextService`)
local TX = {
	MaxShare = 0.74;                                                     -- a bubble is at most this share of the page
	In = { Color3.fromRGB(50, 44, 58), Color3.fromRGB(28, 24, 32) };      -- theirs: inked leather
	Out = { Color3.fromRGB(184, 38, 58), Color3.fromRGB(116, 18, 34) };   -- yours: crimson lacquer
	Office = Color3.fromRGB(214, 178, 112);
	Family = Color3.fromRGB(214, 128, 138);
	Other = Color3.fromRGB(150, 140, 160);
	TextSize = 15;
}
local TextsView = { Mode = `List`; From = nil :: string?; Filter = ``; Conn = nil :: RBXScriptConnection?; Token = 0 }

function Local.TextsCalm(): boolean
	local Ok, Calm = pcall(Kit.ReducedMotion)
	return Ok and Calm == true
end

-- who a sender is: their colour, initials, a line under their name, and whether they sign with the school crest
function Local.TextSender(From: string)
	local Info = { Color = TX.Other; Initials = ``; Sub = ``; Crest = false }
	if From == `The Office` then
		Info.Color, Info.Crest, Info.Sub = TX.Office, true, `Nightmare High front office`
		return Info
	end
	if From == `Mom & Dad` then
		Info.Color, Info.Initials, Info.Sub = TX.Family, `M&D`, `Home`
		return Info
	end
	local Ok, CC = pcall(function() return require(ReplicatedStorage.Config.Cliques) end)
	if Ok and CC and CC.Defs then
		for _, Id in CC.Order or {} do
			local D = CC.Defs[Id]
			if D and D.Leader == From then
				Info.Color = D.Color or Info.Color
				Info.Sub = `{D.Name} \u{00B7} leader`
				break
			end
		end
	end
	local Words = {}
	for Wd in From:gmatch(`%a+`) do if Wd ~= `Captain` and Wd ~= `The` then table.insert(Words, Wd) end end
	Info.Initials = string.upper((Words[1] or `?`):sub(1, 1) .. (Words[#Words] and #Words > 1 and Words[#Words]:sub(1, 1) or ``))
	return Info
end

-- the school's "today" as texts store it (Config.Cliques.EventDay: a night belongs to the evening before it), and the
-- weekday on the clock right now. Returns { Day, Name } or nil.
function Local.TextsToday()
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	local St = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	local Day = if St.Hour >= 6 then St.Day else St.Day - 1
	pcall(function() Day = require(ReplicatedStorage.Config.Cliques).EventDay(St) or Day end)
	return { Day = Day; Name = Local.TextsDayName(St.Day) }
end

function Local.TextsDayName(Day: number?): string
	local Ok, Sched = pcall(function() return require(ReplicatedStorage.Config.SchoolSchedule) end)
	if not (Ok and Sched and Sched.DayNames and typeof(Day) == `number`) then return `` end
	return Sched.DayNames[(Day % #Sched.DayNames) + 1] or ``
end

-- when a text came, the way the player reads the clock: (`Today` | `Yesterday` | a weekday, "8:35 AM").
-- At is "Friday 8:35 AM"; Day is the event day (texts sent at 5 AM Friday belong to Thursday's night, but read as today).
function Local.TextsStamp(T, Now): (string, string)
	local At = tostring(T.At or ``)
	local Weekday = At:match(`^(%a+)`) or ``
	local Time = At:match(`%d+:%d+%s*[AP]M`) or At
	if not (Now and typeof(T.Day) == `number`) then return Weekday, Time end
	if T.Day >= Now.Day - 1 and Weekday == Now.Name then return `Today`, Time end
	if T.Day >= Now.Day - 1 then return `Yesterday`, Time end
	return Weekday, Time
end

-- "8:35 AM" today, "Yesterday", or the weekday
function Local.TextsWhen(T, Now): string
	local Rel, Time = Local.TextsStamp(T, Now)
	return if Rel == `Today` then Time else Rel
end

-- a dare's text ends "(Dare: Stand Up)"; the card under the bubble already names it
function Local.TextsClean(T): string
	local Body = tostring(T.Body or ``)
	if T.Dare then Body = Body:gsub(`%s*%(Dare:[^)]*%)%s*$`, ``) end
	return Body
end

-- a wax-seal avatar: the kit's baked Seal art tinted to the sender, their initials (or the crest) pressed in
function Local.TextAvatar(Parent: Instance, Info, Size: number, Props)
	local A = new(`Frame`, { Name = `Avatar`; BackgroundTransparency = 1; Size = UDim2.fromOffset(Size, Size) }, Parent)
	new(`ImageLabel`, { Name = `Shadow`; BackgroundTransparency = 1; Image = Img.Shadow; ImageTransparency = 0.45; ImageColor3 = Color3.new(0, 0, 0);
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 1, 0.5, 3); Size = UDim2.fromScale(1.35, 1.35) }, A)
	new(`ImageLabel`, { Name = `Seal`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = Info.Color; ScaleType = Enum.ScaleType.Fit;
		Size = UDim2.fromScale(1, 1) }, A)
	if Info.Crest then
		new(`ImageLabel`, { Name = `Crest`; BackgroundTransparency = 1; Image = Img.CrestFlat; ImageColor3 = Color3.fromRGB(40, 26, 18); ImageTransparency = 0.1;
			ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(0.56, 0.56) }, A)
	else
		local T = Local.Label(A, Info.Initials, math.floor(Size * (if #Info.Initials > 2 then 0.26 else 0.34)), { Font = Fonts.Title; TextColor3 = Color3.fromRGB(30, 20, 16);
			TextXAlignment = Enum.TextXAlignment.Center; RichText = false; Size = UDim2.fromScale(1, 1) })
		T.TextStrokeTransparency = 1
		local Hi = new(`UIStroke`, { Color = Color3.new(1, 1, 1); Thickness = 1; Transparency = 0.75; ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, T)
		_ = Hi
	end
	for K, V in Props or {} do A[K] = V end
	return A
end

-- the Texts app's own page: the shared App frame, cleared, holding one CanvasGroup we can slide and fade
function Local.TextsPage(Dir: number?): CanvasGroup
	local App = Ui.App
	for _, Ch in App:GetChildren() do if Ch.Name ~= `Grain` then Ch:Destroy() end end
	local Page = new(`CanvasGroup`, { Name = `Texts`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, App)
	Ui.Home.Visible = false
	App.Visible = true
	if Dir and not Local.TextsCalm() then
		Page.GroupTransparency = 1
		Page.Position = UDim2.fromOffset(28 * Dir, 0)
		tween(Page, 0.32, { GroupTransparency = 0; Position = UDim2.fromOffset(0, 0) })
	end
	return Page
end

function Local.TextsFetch(MarkFrom: string?)
	local List = if MarkFrom then Local.Call(`Texts`, true, MarkFrom) else Local.Call(`Texts`, false)
	if type(List) ~= `table` then return nil end
	return List
end

-- newest-first texts -> conversations (newest first), each with its texts oldest first
function Local.TextsThreads(List)
	local Threads, ByFrom = {}, {}
	-- only the newest copy of a dare, sent today, can be answered (a leader resends the same dare on later days, and
	-- the server still says yes to every copy while that dare is current)
	local Now = Local.TextsToday()
	local SeenDare = {}
	for _, T in List do
		if T.Dare then
			if T.CanAccept and (SeenDare[T.Dare] or (Now and typeof(T.Day) == `number` and T.Day ~= Now.Day)) then T.CanAccept = false end
			SeenDare[T.Dare] = true
		end
	end
	for _, T in List do
		local From = T.From or `Unknown`
		local Th = ByFrom[From]
		if not Th then
			Th = { From = From; Texts = {}; Unread = 0; Open = false; Latest = T }
			ByFrom[From] = Th
			table.insert(Threads, Th)
		end
		table.insert(Th.Texts, 1, T)
		if T.State == `New` then Th.Unread += 1 end
		if (T.Dare or T.Invite) and T.CanAccept then Th.Open = true end
	end
	return Threads, ByFrom
end

function Local.TextsUnreadExcept(List, From: string?): number
	local N = 0
	for _, T in List do if T.State == `New` and T.From ~= From then N += 1 end end
	return N
end

-- the hook for a new text arriving while the app is open
function Local.TextsWatch()
	if TextsView.Conn then TextsView.Conn:Disconnect() TextsView.Conn = nil end
	local F = ReplicatedStorage:FindFirstChild(`NHPhone`)
	local Changed = F and F:FindFirstChild(`Changed`)
	if not Changed then return end
	TextsView.Conn = Changed.OnClientEvent:Connect(function(S)
		local Page = Ui and Ui.App:FindFirstChild(`Texts`)
		if not (Page and Ui.App.Visible) then
			if TextsView.Conn then TextsView.Conn:Disconnect() TextsView.Conn = nil end
			return
		end
		if not (typeof(S) == `table` and (tonumber(S.Unread) or 0) > 0) then return end
		if TextsView.Mode == `Thread` and TextsView.From then
			local List = Local.TextsFetch(nil)
			if not List then return end
			local _, ByFrom = Local.TextsThreads(List)
			local Th = ByFrom[TextsView.From]
			if Th and Th.Unread > 0 then
				Local.TextsTyping(Page, function() Local.TextsThread(TextsView.From, nil, true) end)
			end
		else
			Local.Texts(nil, true)
		end
	end)
end

---| the conversation list |---

function Local.Texts(Dir: number?, Fresh: boolean?)
	TextsView.Mode, TextsView.From = `List`, nil
	TextsView.Token += 1
	local Token = TextsView.Token
	local Page = Local.TextsPage(Dir)
	local Calm = Local.TextsCalm()
	-- header: back, a large title, the search pill
	local Back = new(`TextButton`, { Name = `Back`; Text = `\u{2039}`; Font = Fonts.Title; TextSize = 30; TextColor3 = C.Gold; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(8, 0); Size = UDim2.fromOffset(40, 36) }, Page)
	Back.Activated:Connect(function() Local.ShowHome() end)
	local Title = Local.Label(Page, `Messages`, 30, { Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(18, 30); Size = UDim2.new(1, -36, 0, 36) })
	pcall(Kit.Emboss, Title)
	local Search = new(`Frame`, { Name = `Search`; BackgroundColor3 = Color3.fromRGB(34, 30, 38); BackgroundTransparency = 0.15; BorderSizePixel = 0;
		Position = UDim2.fromOffset(14, 72); Size = UDim2.new(1, -28, 0, 32) }, Page)
	new(`UICorner`, { CornerRadius = UDim.new(0, 10) }, Search)
	new(`UIStroke`, { Color = C.IronDim; Thickness = 1; Transparency = 0.55 }, Search)
	-- a drawn magnifier (the fonts have no search glyph): a ring and a short handle
	local Lens = new(`Frame`, { Name = `Lens`; BackgroundTransparency = 1; Position = UDim2.fromOffset(11, 9); Size = UDim2.fromOffset(10, 10) }, Search)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Lens)
	new(`UIStroke`, { Color = HINT; Thickness = 1.5 }, Lens)
	new(`Frame`, { Name = `Handle`; BackgroundColor3 = HINT; BorderSizePixel = 0; Rotation = 45; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromOffset(22, 21); Size = UDim2.fromOffset(6, 2) }, Search)
	local Box = new(`TextBox`, { Name = `Box`; Text = TextsView.Filter; PlaceholderText = `Search`; PlaceholderColor3 = HINT; ClearTextOnFocus = false;
		Font = Fonts.Body; TextSize = 15; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Left; BackgroundTransparency = 1;
		Position = UDim2.fromOffset(30, 0); Size = UDim2.new(1, -38, 1, 0) }, Search)
	local Body = new(`ScrollingFrame`, { Name = `Body`; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 112); Size = UDim2.new(1, 0, 1, -112);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 3; ScrollBarImageColor3 = C.IronDim }, Page)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 0) }, Body)
	new(`UIPadding`, { PaddingBottom = UDim.new(0, 12) }, Body)

	local List = Local.TextsFetch(nil)
	if Token ~= TextsView.Token then return end
	if not List then
		Local.Label(Body, `<i>No signal. Try again in a moment.</i>`, 14, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 60) })
		return
	end
	State.Unread = Local.TextsUnreadExcept(List, nil)
	Local.Badges()
	local Threads = Local.TextsThreads(List)
	local Now = Local.TextsToday()
	if #Threads == 0 then
		local Empty = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 220) }, Body)
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.IconAppTexts; ScaleType = Enum.ScaleType.Fit; ImageTransparency = 0.25;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 40); Size = UDim2.fromOffset(72, 72) }, Empty)
		Local.Label(Empty, `No messages yet`, 18, { Font = Fonts.Title; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 124); Size = UDim2.new(1, 0, 0, 24) })
		Local.Label(Empty, `<i>Leaders text you dares, your parents write after report cards, and the Office keeps you posted.</i>`, 13,
			{ TextColor3 = HINT; TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(30, 152); Size = UDim2.new(1, -60, 0, 50) })
		Local.TextsWatch()
		return
	end
	local Rows = {}
	for I, Th in Threads do
		local Info = Local.TextSender(Th.From)
		local L = Th.Latest
		local Row = new(`CanvasGroup`, { Name = `Row_{I}`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 70); LayoutOrder = I }, Body)
		local Btn = new(`TextButton`, { Name = `Open`; Text = ``; AutoButtonColor = false; BackgroundColor3 = C.Gold; BackgroundTransparency = 1;
			Size = UDim2.fromScale(1, 1) }, Row)
		if Th.Unread > 0 then
			local Dot = new(`Frame`, { Name = `Unread`; BackgroundColor3 = C.Crimson; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5);
				Position = UDim2.new(0, 11, 0.5, 0); Size = UDim2.fromOffset(9, 9); ZIndex = 3 }, Row)
			new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Dot)
			local Glow = new(`ImageLabel`, { Name = `Glow`; BackgroundTransparency = 1; Image = Img.Glow; ImageColor3 = C.Crimson; ImageTransparency = 0.35;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0, 11, 0.5, 0); Size = UDim2.fromOffset(26, 26); ZIndex = 2 }, Row)
			if not Calm then
				TweenService:Create(Glow, TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { ImageTransparency = 0.8 }):Play()
			end
		end
		Local.TextAvatar(Row, Info, 46, { Position = UDim2.fromOffset(22, 12) })
		local Name = Local.Label(Row, Th.From, 16, { Font = Fonts.Title; RichText = false; TextColor3 = if Th.Unread > 0 then C.Gold else C.Text;
			TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(80, 10); Size = UDim2.new(1, -170, 0, 20) })
		_ = Name
		Local.Label(Row, `{Local.TextsWhen(L, Now)}  \u{203A}`, 12, { RichText = false; TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Right;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -14, 0, 12); Size = UDim2.fromOffset(90, 18) })
		local Tag = if Th.Open then `<font color="{`#` .. C.Gold:ToHex()}"><b>{if L.Invite then `INVITE` else `DARE`}</b></font>  ` else ``
		local Preview = Local.TextsClean(L):gsub(`[<>&]`, { [`<`] = `&lt;`; [`>`] = `&gt;`; [`&`] = `&amp;` })
		Local.Label(Row, Tag .. Preview, 13, { TextColor3 = if Th.Unread > 0 then C.Text else HINT; TextWrapped = true; TextYAlignment = Enum.TextYAlignment.Top;
			TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(80, 31); Size = UDim2.new(1, -96, 0, 34) })
		local Rule = new(`Frame`, { Name = `Rule`; BackgroundColor3 = C.IronDim; BackgroundTransparency = 0.55; BorderSizePixel = 0;
			AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 80, 1, 0); Size = UDim2.new(1, -80, 0, 1) }, Row)
		_ = Rule
		Btn.MouseEnter:Connect(function() if not Calm then tween(Btn, 0.12, { BackgroundTransparency = 0.93 }) end end)
		Btn.MouseLeave:Connect(function() tween(Btn, 0.2, { BackgroundTransparency = 1 }) end)
		Btn.Activated:Connect(function()
			pcall(Kit.PlaySound, `Tick`, 0.5, 1.35)
			Btn.BackgroundTransparency = 0.86
			Local.TextsThread(Th.From, 1)
		end)
		table.insert(Rows, { Row = Row; Hay = string.lower(Th.From .. ` ` .. tostring(L.Body or ``)); I = I })
	end
	-- rows slide in, one after another (a fresh text drops in from the top instead)
	if not Calm then
		for K, R in Rows do
			R.Row.GroupTransparency = 1
			local Delay = if Fresh then 0 else (K - 1) * 0.035
			task.delay(Delay, function()
				if R.Row.Parent then tween(R.Row, 0.28, { GroupTransparency = 0 }) end
			end)
		end
	end
	local function Filter()
		local Q = string.lower(Box.Text or ``)
		TextsView.Filter = Box.Text or ``
		for _, R in Rows do R.Row.Visible = Q == `` or string.find(R.Hay, Q, 1, true) ~= nil end
	end
	Box:GetPropertyChangedSignal(`Text`):Connect(Filter)
	Filter()
	Local.TextsWatch()
end

---| a conversation |---

local function textSize(Text: string, Size: number, Font: Enum.Font, Width: number): Vector2
	local Ok, V = pcall(TextService.GetTextSize, TextService, Text, Size, Font, Vector2.new(Width, 10000))
	return if Ok then V else Vector2.new(Width, Size * 2)
end

-- one bubble. Side "In" (theirs, left) or "Out" (yours, right); Tail on the last of a run. Returns its row and bubble.
function Local.TextBubble(Body: Instance, Order: number, Side: string, Text: string, Tail: boolean, Width: number)
	local MaxW = math.floor(Width * TX.MaxShare)
	local Sz = textSize(Text, TX.TextSize, Fonts.Body, MaxW - 26)
	-- a few units of slack: the font rounds up at the handset's scale, and a tight bubble wraps its last word
	local BW, BH = math.min(MaxW, math.max(44, math.ceil(Sz.X) + 32)), math.ceil(Sz.Y) + 16
	local Row = new(`Frame`, { Name = `Bubble`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, BH); LayoutOrder = Order }, Body)
	local Out = Side == `Out`
	local Cols = if Out then TX.Out else TX.In
	local B = new(`Frame`, { Name = `B`; BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; ZIndex = 3;
		AnchorPoint = Vector2.new(if Out then 1 else 0, 0); Position = UDim2.new(if Out then 1 else 0, 0, 0, 0); Size = UDim2.fromOffset(BW, BH) }, Row)
	new(`UICorner`, { CornerRadius = UDim.new(0, 17) }, B)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(Cols[1], Cols[2]) }, B)
	-- the kit's baked grain, so the leather and lacquer read as surfaces (clipped to the same rounding)
	local Grain = new(`ImageLabel`, { Name = `Grain`; BackgroundTransparency = 1; Image = Img.PanelBg; ImageColor3 = if Out then Color3.fromRGB(255, 190, 190) else Color3.fromRGB(150, 140, 160);
		ImageTransparency = if Out then 0.86 else 0.8; ScaleType = Enum.ScaleType.Tile; TileSize = UDim2.fromOffset(120, 120); Size = UDim2.fromScale(1, 1); ZIndex = 3 }, B)
	new(`UICorner`, { CornerRadius = UDim.new(0, 17) }, Grain)
	-- a soft sheen across the top, like lacquer catching light
	local Sheen = new(`Frame`, { Name = `Sheen`; BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = if Out then 0.84 else 0.92; BorderSizePixel = 0;
		Position = UDim2.fromOffset(4, 2); Size = UDim2.new(1, -8, 0, math.min(12, BH * 0.4)); ZIndex = 3 }, B)
	new(`UICorner`, { CornerRadius = UDim.new(0, 12) }, Sheen)
	new(`UIGradient`, { Rotation = 90; Transparency = NumberSequence.new(0, 1) }, Sheen)
	new(`UIStroke`, { Color = if Out then Color3.fromRGB(255, 120, 130) else C.GoldDeep; Thickness = 1; Transparency = if Out then 0.7 else 0.55 }, B)
	local T = new(`TextLabel`, { Name = `Text`; BackgroundTransparency = 1; Text = Text; RichText = false; TextWrapped = true; Font = Fonts.Body; TextSize = TX.TextSize;
		TextColor3 = if Out then Color3.fromRGB(255, 240, 236) else C.Text; TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Center;
		Position = UDim2.fromOffset(13, 0); Size = UDim2.new(1, -26, 1, 0); ZIndex = 4 }, B)
	_ = T
	if Tail then
		-- the tail: a small turned square tucked under the bottom corner, in the bubble's bottom colour
		local Tl = new(`Frame`, { Name = `Tail`; BackgroundColor3 = Cols[2]; BorderSizePixel = 0; Rotation = 45; ZIndex = 2;
			AnchorPoint = Vector2.new(0.5, 0.5); Position = if Out then UDim2.new(1, -3, 1, -7) else UDim2.new(0, 3, 1, -7); Size = UDim2.fromOffset(12, 12) }, Row)
		new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Tl)
	end
	local Scale = new(`UIScale`, { Scale = 1 }, B)
	return Row, B, Scale
end

-- a dare or invite, shown as a card under its bubble (like a link preview)
function Local.TextCard(Body: Instance, Order: number, T, Width: number)
	local MaxW = math.floor(Width * TX.MaxShare)
	local Row = new(`Frame`, { Name = `Card`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 52); LayoutOrder = Order }, Body)
	local Card = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(18, 15, 20); BackgroundTransparency = 0.1; BorderSizePixel = 0; Size = UDim2.fromOffset(MaxW, 48) }, Row)
	new(`UICorner`, { CornerRadius = UDim.new(0, 12) }, Card)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.45 }, Card)
	new(`ImageLabel`, { BackgroundTransparency = 1; Image = if T.Invite then Img.IconAppContacts else Img.IconNpcOffer; ScaleType = Enum.ScaleType.Fit;
		Position = UDim2.fromOffset(8, 8); Size = UDim2.fromOffset(32, 32) }, Card)
	local Kind = if T.Invite then `DORM INVITE` else `DARE`
	local Name = if T.Invite then `Their room, tonight` else (T.DareName or `A dare`)
	local Status = if T.State == `Accepted` then (if T.Invite then `Visited` else `Accepted`)
		elseif T.State == `Declined` then (if T.Invite then `Maybe later` else `Not today`)
		elseif T.CanAccept then (if T.Invite then `Open now` else `Runs out at 6 AM`)
		else (if T.Invite then `This invite's over` else `This dare's over`)
	local StatusColor = if T.State == `Accepted` then Color3.fromRGB(150, 210, 120) elseif T.CanAccept then C.Gold else HINT
	Local.Label(Card, `<b>{Kind}</b>  \u{00B7}  <font color="#{StatusColor:ToHex()}">{Status}</font>`, 11, { TextColor3 = HINT; Position = UDim2.fromOffset(48, 6); Size = UDim2.new(1, -56, 0, 16) })
	Local.Label(Card, Name, 15, { Font = Fonts.Title; RichText = false; TextColor3 = C.Text; TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(48, 22); Size = UDim2.new(1, -56, 0, 20) })
	return Row
end

-- three embers bobbing in an inked bubble: someone is writing to you
function Local.TextsTyping(Page: Instance, OnDone: () -> ())
	local Body = Page:FindFirstChild(`Body`)
	if not Body then OnDone() return end
	local Row = new(`Frame`, { Name = `Typing`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 36); LayoutOrder = 100000 }, Body)
	local B = new(`Frame`, { BackgroundColor3 = TX.In[1]; BorderSizePixel = 0; Size = UDim2.fromOffset(62, 34) }, Row)
	new(`UICorner`, { CornerRadius = UDim.new(0, 17) }, B)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.55 }, B)
	local Dots = {}
	for I = 1, 3 do
		local D = new(`Frame`, { BackgroundColor3 = C.Gold; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0, 16 + (I - 1) * 15, 0.5, 0); Size = UDim2.fromOffset(7, 7) }, B)
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, D)
		Dots[I] = D
	end
	task.defer(function() Body.CanvasPosition = Vector2.new(0, math.max(0, Body.AbsoluteCanvasSize.Y - Body.AbsoluteSize.Y)) end)
	local T0 = os.clock()
	local Conn
	Conn = RunService.RenderStepped:Connect(function()
		if not Row.Parent then Conn:Disconnect() return end
		for I, D in Dots do
			local P = math.sin((os.clock() - T0) * 7 - I * 0.9)
			D.Position = UDim2.new(0, 16 + (I - 1) * 15, 0.5, -math.max(0, P) * 4)
			D.BackgroundTransparency = 0.45 - math.max(0, P) * 0.45
		end
	end)
	task.delay(if Local.TextsCalm() then 0.3 else 1.1, function()
		Conn:Disconnect()
		Row:Destroy()
		OnDone()
	end)
end

function Local.TextsThread(From: string, Dir: number?, Fresh: boolean?)
	TextsView.Mode, TextsView.From = `Thread`, From
	TextsView.Token += 1
	local Token = TextsView.Token
	local Page = Local.TextsPage(Dir)
	local Calm = Local.TextsCalm()
	local Info = Local.TextSender(From)
	-- header: back to Messages, their seal and name centred
	local Back = new(`TextButton`, { Name = `Back`; Text = `\u{2039} Messages`; Font = Fonts.Title; TextSize = 15; TextColor3 = C.Gold; BackgroundTransparency = 1;
		TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromOffset(12, 4); Size = UDim2.fromOffset(110, 30) }, Page)
	Back.Activated:Connect(function() pcall(Kit.PlaySound, `Tick`, 0.5, 1.1) Local.Texts(-1) end)
	Local.TextAvatar(Page, Info, 40, { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 4) })
	Local.Label(Page, From, 14, { Font = Fonts.Title; RichText = false; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center;
		TextTruncate = Enum.TextTruncate.AtEnd; Position = UDim2.fromOffset(40, 46); Size = UDim2.new(1, -80, 0, 18) })
	Local.Label(Page, Info.Sub, 11, { RichText = false; TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(20, 63); Size = UDim2.new(1, -40, 0, 14) })
	local Rule = new(`Frame`, { BackgroundColor3 = C.Crimson; BorderSizePixel = 0; Position = UDim2.new(0, 14, 0, 82); Size = UDim2.new(1, -28, 0, 1) }, Page)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.25), NumberSequenceKeypoint.new(1, 1) }) }, Rule)
	local COMPOSER = 46
	local Body = new(`ScrollingFrame`, { Name = `Body`; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 86); Size = UDim2.new(1, 0, 1, -86 - COMPOSER);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 3; ScrollBarImageColor3 = C.IronDim }, Page)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 3) }, Body)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 12); PaddingRight = UDim.new(0, 12); PaddingTop = UDim.new(0, 8); PaddingBottom = UDim.new(0, 10) }, Body)
	-- the composer: sealed (answers are the quick replies above it)
	local Comp = new(`Frame`, { Name = `Composer`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 0, 1, 0); Size = UDim2.new(1, 0, 0, COMPOSER) }, Page)
	local Pill = new(`TextButton`, { Name = `Pill`; Text = ``; AutoButtonColor = false; BackgroundColor3 = Color3.fromRGB(28, 24, 32); BackgroundTransparency = 0.1; BorderSizePixel = 0;
		Position = UDim2.fromOffset(14, 6); Size = UDim2.new(1, -62, 0, 34) }, Comp)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Pill)
	new(`UIStroke`, { Color = C.IronDim; Thickness = 1; Transparency = 0.45 }, Pill)
	local Hint = Local.Label(Pill, `Quick replies only`, 14, { RichText = false; TextColor3 = HINT; Position = UDim2.fromOffset(14, 0); Size = UDim2.new(1, -20, 1, 0) })
	local Send = new(`Frame`, { Name = `Send`; BackgroundColor3 = C.Crimson; BackgroundTransparency = 0.55; BorderSizePixel = 0; AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -14, 0, 8); Size = UDim2.fromOffset(30, 30) }, Comp)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Send)
	Local.Label(Send, `\u{2191}`, 17, { Font = Fonts.Title; RichText = false; TextColor3 = Color3.fromRGB(255, 230, 230); TextTransparency = 0.4; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1) })
	Pill.Activated:Connect(function()
		Hint.Text = `You can't write to them: answer with a quick reply`
		if not Calm then
			local X = Pill.Position
			tween(Pill, 0.06, { Position = X + UDim2.fromOffset(5, 0) }).Completed:Connect(function() tween(Pill, 0.12, { Position = X }, Enum.EasingStyle.Elastic) end)
		end
		task.delay(2.5, function() if Hint.Parent then Hint.Text = `Quick replies only` end end)
	end)

	local List = Local.TextsFetch(From)
	if Token ~= TextsView.Token then return end
	if not List then
		Local.Label(Body, `<i>No signal. Try again in a moment.</i>`, 14, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 60) })
		return
	end
	State.Unread = Local.TextsUnreadExcept(List, From)
	Local.Badges()
	local _, ByFrom = Local.TextsThreads(List)
	local Th = ByFrom[From]
	if not Th then Local.Texts(-1) return end
	local Now = Local.TextsToday()
	-- in the phone's own units (the handset is scaled to the screen, so AbsoluteSize would be too small)
	local Width = W - 22 - 24
	local N = 0
	local LastDay = nil
	local Bubbles = {}
	local Actionable = nil
	local LastAnswered = 0
	for I, T in Th.Texts do if T.State == `Accepted` or T.State == `Declined` then LastAnswered = I end end
	for I, T in Th.Texts do
		-- a day stamp whenever the day changes
		local Rel, Time = Local.TextsStamp(T, Now)
		-- one stamp per day as the player reads it (Today / Yesterday can span two school nights)
		local DayKey = if Rel == `Today` or Rel == `Yesterday` then Rel else `{T.Day}|{Rel}`
		if DayKey ~= LastDay then
			LastDay = DayKey
			N += 1
			Local.Label(Body, `<b>{string.upper(Rel)}</b>  {Time}`, 11, { TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = N })
		end
		local Next = Th.Texts[I + 1]
		local Answered = T.State == `Accepted` or T.State == `Declined`
		local NextRel = if Next then (Local.TextsStamp(Next, Now)) else nil
		local RunEnds = Answered or not Next or (if NextRel == `Today` or NextRel == `Yesterday` then NextRel else `{Next.Day}|{NextRel}`) ~= DayKey
		N += 1
		-- a tail on the last bubble of a run (not when a card hangs under it)
		local _, B, Scale = Local.TextBubble(Body, N, `In`, Local.TextsClean(T), RunEnds and not (T.Dare or T.Invite), Width)
		table.insert(Bubbles, { B = B; Scale = Scale })
		if T.Dare or T.Invite then
			N += 1
			Local.TextCard(Body, N, T, Width)
			if T.CanAccept then Actionable = T end
		end
		if Answered then
			local Reply = if T.Invite then (if T.State == `Accepted` then `On my way.` else `Maybe later.`)
				else (if T.State == `Accepted` then `I'm in.` else `Not today.`)
			N += 1
			local _, OB, OScale = Local.TextBubble(Body, N, `Out`, Reply, true, Width)
			table.insert(Bubbles, { B = OB; Scale = OScale })
			if I == LastAnswered then
				-- the receipt under your last answer
				N += 1
				Local.Label(Body, `Sealed`, 11, { RichText = false; TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Right; Size = UDim2.new(1, -4, 0, 14); LayoutOrder = N })
			end
		end
	end
	-- the last few bubbles pop in (a new text: just that one)
	if not Calm then
		local From0 = if Fresh then #Bubbles else math.max(1, #Bubbles - 5)
		for K = From0, #Bubbles do
			local Bb = Bubbles[K]
			Bb.Scale.Scale = 0.86
			Bb.B.BackgroundTransparency = 1
			task.delay((K - From0) * 0.04, function()
				if not Bb.B.Parent then return end
				TweenService:Create(Bb.Scale, TweenInfo.new(0.32, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
				tween(Bb.B, 0.18, { BackgroundTransparency = 0 })
			end)
		end
	end
	-- quick replies, over the composer
	if Actionable then
		local T = Actionable
		local Chips = new(`Frame`, { Name = `Replies`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 0, 1, -COMPOSER); Size = UDim2.new(1, 0, 0, 40) }, Page)
		Body.Size = UDim2.new(1, 0, 1, -86 - COMPOSER - 40)
		new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Right; Padding = UDim.new(0, 8); SortOrder = Enum.SortOrder.LayoutOrder }, Chips)
		new(`UIPadding`, { PaddingRight = UDim.new(0, 14); PaddingTop = UDim.new(0, 4) }, Chips)
		local Busy = false
		local function Answer(Action: string, Text: string)
			if Busy then return end
			Busy = true
			pcall(Kit.PlaySound, `Tick`, 0.6, 1.5)
			Chips.Visible = false
			Body.Size = UDim2.new(1, 0, 1, -86 - COMPOSER)
			-- your answer flies up out of the composer
			N += 1
			local _, OB, OScale = Local.TextBubble(Body, N, `Out`, Text, true, Width)
			local Status = Local.Label(Body, `Sending\u{2026}`, 11, { RichText = false; TextColor3 = HINT; TextXAlignment = Enum.TextXAlignment.Right; Size = UDim2.new(1, -4, 0, 14); LayoutOrder = N + 1 })
			if not Calm then
				OScale.Scale = 0.6
				OB.Position = UDim2.new(1, 0, 0, 28)
				TweenService:Create(OScale, TweenInfo.new(0.34, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
				tween(OB, 0.3, { Position = UDim2.new(1, 0, 0, 0) })
			end
			task.defer(function() Body.CanvasPosition = Vector2.new(0, math.max(0, Body.AbsoluteCanvasSize.Y - Body.AbsoluteSize.Y)) end)
			-- (audit) the text's id, with the index as the fallback for old texts
			local Ok, Msg = Local.Call(`TextAction`, T.Index, Action, T.Id)
			if Ok then
				Status.Text = `Sealed`
				task.delay(0.9, function() if Token == TextsView.Token then Local.TextsThread(From) end end)
			else
				-- not delivered: a red mark beside the bubble and the reason, and the replies come back
				Status.Text = `Not sent: {tostring(Msg or `try again`)}`
				Status.TextColor3 = C.Danger
				local Bang = new(`Frame`, { BackgroundColor3 = C.Danger; BorderSizePixel = 0; AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(0, -6, 0.5, 0); Size = UDim2.fromOffset(18, 18) }, OB)
				new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Bang)
				Local.Label(Bang, `!`, 13, { Font = Fonts.Title; RichText = false; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1) })
				Busy = false
				Chips.Visible = true
				Body.Size = UDim2.new(1, 0, 1, -86 - COMPOSER - 40)
				-- the replies take their room back: keep the reason in view
				task.defer(function()
					RunService.Heartbeat:Wait()
					if Body.Parent then Body.CanvasPosition = Vector2.new(0, math.max(0, Body.AbsoluteCanvasSize.Y - Body.AbsoluteSize.Y)) end
				end)
			end
		end
		local Yes = if T.Invite then `On my way.` else `I'm in.`
		local No = if T.Invite then `Maybe later.` else `Not today.`
		Kit.Button({ text = No; textSize = 14; Size = UDim2.fromOffset(112, 32); LayoutOrder = 1; Parent = Chips; onClick = function() Answer(`Decline`, No) end })
		Kit.Button({ text = Yes; style = `gold`; textSize = 14; Size = UDim2.fromOffset(112, 32); LayoutOrder = 2; Parent = Chips; onClick = function() Answer(`Accept`, Yes) end })
		-- the replies rise into place
		if not Calm then
			Chips.Position = UDim2.new(0, 0, 1, -COMPOSER + 16)
			tween(Chips, 0.3, { Position = UDim2.new(0, 0, 1, -COMPOSER) }, Enum.EasingStyle.Back)
		end
	end
	-- open at the newest message
	task.defer(function()
		RunService.Heartbeat:Wait()
		if Body.Parent then Body.CanvasPosition = Vector2.new(0, math.max(0, Body.AbsoluteCanvasSize.Y - Body.AbsoluteSize.Y)) end
	end)
	Local.TextsWatch()
end

-- Classmates
function Local.Contacts()
	local Body = Local.Page(`Classmates`)
	local List = Local.Call(`Contacts`) or {}
	Local.Line(Body, `<i>Everyone in the building. You only see names you've learned. Introduce yourself (G) to swap names.</i>`, 15, { TextColor3 = HINT })
	if #List == 0 then Local.Line(Body, `<i>Nobody else is here right now.</i>`, 15, { TextColor3 = HINT }) end
	for _, P in List do
		local Row = Local.Card(Body, 108)
		Local.Label(Row, P.Name, 16, { Font = Fonts.Title; TextColor3 = if P.Known then C.Text else C.TextDim; Position = UDim2.fromOffset(12, 4); Size = UDim2.new(1, -24, 0, 20) })
		Local.Label(Row, string.upper(`{P.Race}  \u{00B7}  LV {P.Level}`), 12, { Font = Fonts.Title; TextColor3 = RACE_COLOR[P.Family] or C.Text; Position = UDim2.fromOffset(12, 24); Size = UDim2.new(1, -24, 0, 16) })
		local Note = Local.Label(Row, ``, 11, { TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 6); Size = UDim2.fromOffset(150, 14) })
		Kit.Button({ text = `Send {YEN}`; textSize = 13; Size = UDim2.fromOffset(130, 28); Position = UDim2.fromOffset(12, 40); Parent = Row;
			onClick = function() Pending = { UserId = P.UserId; Name = P.Name } Order = 0 local Keep = Pending Local.Wallet() Pending = Keep end })
		Kit.Button({ text = `Invite to group`; style = `gold`; textSize = 13; Size = UDim2.fromOffset(150, 28); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -12, 0, 40); Parent = Row;
			onClick = function()
				local F = ReplicatedStorage:FindFirstChild(`NHParty`)
				local R = F and F:FindFirstChild(`Invite`)
				if R then local Ok, A, Msg = pcall(R.InvokeServer, R, P.UserId) Note.Text = (Ok and Msg) or `` end
			end })
		-- (homes) invite them to your dorm room (they get a text with a Visit button)
		Kit.Button({ text = `Invite to my room`; textSize = 13; Size = UDim2.fromOffset(170, 28); Position = UDim2.fromOffset(12, 74); Parent = Row;
			onClick = function()
				local F = ReplicatedStorage:FindFirstChild(`NHHomes`)
				local R = F and F:FindFirstChild(`Invite`)
				if R then local Ok, A, Msg = pcall(R.InvokeServer, R, P.UserId) Note.Text = (Ok and tostring(Msg or ``)) or `` end
			end })
	end
end

-- Style: pick a wallpaper, or use your own image / decal ID
function Local.Style()
	local Body = Local.Page(`Style`)
	Local.Line(Body, `WALLPAPER`, 14, { Font = Fonts.Title; TextColor3 = SECTION })
	Order += 1
	local Grid = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Order }, Body)
	new(`UIGridLayout`, { CellSize = UDim2.fromOffset(92, 150); CellPadding = UDim2.fromOffset(8, 8); SortOrder = Enum.SortOrder.LayoutOrder; HorizontalAlignment = Enum.HorizontalAlignment.Center }, Grid)
	local Current = (State.Wallpaper and State.Wallpaper.Preset) or WALLPAPERS[1].Id
	local Using = State.Wallpaper and State.Wallpaper.Image
	local function save(Preset: string?, Image: number?)
		local Wp = { Preset = Preset or Current; Image = Image }
		State.Wallpaper = Wp
		Local.ApplyWallpaper()
		task.spawn(Local.Call, `SaveWallpaper`, Wp)
	end
	for I, Wp in WALLPAPERS do
		local Cell = new(`TextButton`, { Text = ``; AutoButtonColor = false; BackgroundTransparency = 1; LayoutOrder = I }, Grid)
		local Swatch = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.new(1, 0, 0, 124) }, Cell)
		new(`UICorner`, { CornerRadius = UDim.new(0, 14) }, Swatch)
		new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(Wp.Top, Wp.Bottom) }, Swatch)
		new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.CrestFlat; ImageTransparency = 0.85; ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(0.5, 0.5);
			Position = UDim2.fromScale(0.5, 0.6); Size = UDim2.fromScale(0.7, 0.5) }, Swatch)
		local On = Wp.Id == Current and not Using
		new(`UIStroke`, { Color = if On then C.Gold else Color3.new(1, 1, 1); Thickness = if On then 2 else 1; Transparency = if On then 0 else 0.8 }, Swatch)
		Local.Label(Cell, Wp.Name, 12, { TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 128); Size = UDim2.new(1, 0, 0, 16) })
		Cell.Activated:Connect(function() Current = Wp.Id Using = nil save(Wp.Id, nil) Local.Style() end)
	end
	Local.Line(Body, `YOUR OWN IMAGE`, 14, { Font = Fonts.Title; TextColor3 = SECTION })
	Local.Line(Body, `<i>Paste a Roblox image or decal ID. Only you see your wallpaper.</i>`, 15, { TextColor3 = HINT })
	Order += 1
	local _, InputApi = Kit.SearchBar({ placeholder = if Using then tostring(Using) else `Image ID`; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = Order; Parent = Body })
	Order += 1
	local Row = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 38); LayoutOrder = Order }, Body)
	Kit.Button({ text = `Use image`; style = `gold`; textSize = 14; Size = UDim2.new(0.5, -4, 1, 0); Parent = Row;
		onClick = function()
			local N = Local.Digits(InputApi:Get())
			if N then Using = N save(Current, N) Local.Style() end
		end })
	Kit.Button({ text = `Clear image`; textSize = 14; Size = UDim2.new(0.5, -4, 1, 0); Position = UDim2.new(0.5, 4, 0, 0); Parent = Row;
		onClick = function() Using = nil save(Current, nil) Local.Style() end })
end

---| open / close |---

---| the Phone tool |---

function Local.Tool(): Tool?
	for _, Holder in { Player.Character, Player:FindFirstChildOfClass(`Backpack`) } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			if T:IsA(`Tool`) and T:GetAttribute(`NHPhone`) then return T end
		end
	end
	return nil
end

local Hooked = setmetatable({}, { __mode = `k` })
function Local.Hook(T: Instance)
	if not (T:IsA(`Tool`) and T:GetAttribute(`NHPhone`)) or Hooked[T] then return end
	Hooked[T] = true
	T.Equipped:Connect(function() Shared.Toggle(true) end)
	T.Unequipped:Connect(function() Shared.Toggle(false) end)
end

-- Y: take the phone out, or put it away
function Local.Key()
	local T = Local.Tool()
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	if T and Hum then
		if T.Parent == Player.Character then Hum:UnequipTools() else Hum:EquipTool(T) end
	else
		Shared.Toggle()
	end
end

function Shared.IsOpen(): boolean return Open end

function Shared.Toggle(On: boolean?)
	if not Ui then return end
	if On == nil then On = not Open end
	if On and Player:GetAttribute(`InMainMenu`) == true then return end
	if On == Open then return end
	Open = On
	local Reduced = Kit.ReducedMotion()
	if On then
		local S = Local.Call(`Get`)
		if S then State = S Local.ApplyWallpaper() end
		if not Open then return end -- (audit) put away while the server answered: don't show it again
		Local.ShowHome()
		Ui.Body.Visible = true
		Ui.Body.Position = UDim2.new(1, -22, 1, H + 40)
		tween(Ui.Body, if Reduced then 0.01 else 0.35, { Position = UDim2.new(1, -22, 1, -18) })
		pcall(Kit.PlaySound, `Tick`, 0.7, 0.9)
	else
		Local.StopGames()
		tween(Ui.Body, if Reduced then 0.01 else 0.28, { Position = UDim2.new(1, -22, 1, H + 40) })
		task.delay(0.3, function() if not Open and Ui then Ui.Body.Visible = false end end)
		-- closing from inside the phone (Camera, Timetable...) puts the handset away too
		local T = Local.Tool()
		local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
		if T and Hum and T.Parent == Player.Character then Hum:UnequipTools() end
	end
end

-- (1.39) open the phone straight to an app (the Midnight Bell notice board's "Read" prompt)
function Shared.OpenApp(Id: string)
	if not Ui then return end
	if not Open then Shared.Toggle(true) end
	if Open then Local.OpenApp(Id) end
end

function Shared.OnStart()
	Local.Build()
	task.spawn(function()
		local B = ReplicatedStorage:WaitForChild(`NHNoticeBoard`, 60)
		local R = B and B:WaitForChild(`Read`, 10)
		if R then R.OnClientEvent:Connect(function(App) Shared.OpenApp(if typeof(App) == `string` then App else `Gazette`) end) end
	end)
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHPhone`, 30)
		if not F then return end
		F:WaitForChild(`Changed`).OnClientEvent:Connect(function(S) if typeof(S) == `table` then State = S Local.ApplyWallpaper() Local.Badges() end end)
		local S = Local.Call(`Get`)
		if S then State = S Local.ApplyWallpaper() end
		-- (audit) what was in the wallet when you joined counts as seen (the badge is for money that arrives now)
		Local.Seen = Local.Seen or {}
		if S and Local.Seen.InSeq == nil then Local.Seen.InSeq = Local.TopIn() end
	end)
	UserInputService.InputBegan:Connect(function(Input)
		if Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() or Player:GetAttribute(`InMainMenu`) == true then return end
		Local.Key()
	end)
	-- hook the Phone tool wherever it turns up (spawn, respawn)
	local function watch(Holder: Instance?)
		if not Holder then return end
		for _, T in Holder:GetChildren() do Local.Hook(T) end
		Holder.ChildAdded:Connect(Local.Hook)
	end
	task.spawn(function() watch(Player:WaitForChild(`Backpack`, 20)) end)
	Player.CharacterAdded:Connect(function(Ch)
		watch(Ch)
		task.spawn(function() watch(Player:WaitForChild(`Backpack`, 20)) end)
		if Open then Shared.Toggle(false) end
	end)
	if Player.Character then watch(Player.Character) end
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.25 or not Ui then return end
		Acc = 0
		local InMenu = Player:GetAttribute(`InMainMenu`) == true
		Ui.Gui.Enabled = not InMenu
		if InMenu and Open then Shared.Toggle(false) end
		local T, Day = Local.Clock()
		Ui.BarTime.Text = T
		if Open and Ui.Home.Visible then Local.Badges() end
		-- the hotbar slot shows a note while your music plays (local only)
		local T = Local.Tool()
		if T then T.Name = if Music.Sound and Music.Sound.IsPlaying then `\u{266A} Phone` else `Phone` end
		pcall(function() require(script.Parent.PhoneRadio).Tick() end) -- (2.30) Night FM (Controllers.Gui.PhoneRadio)
	end)
end

return Shared
]==] })

for _, It in Items do
	local Fn, Err = loadstring(It.Source)
	if not Fn then return "PARSE FAIL " .. table.concat(It.Path, ".") .. ": " .. tostring(Err) end
end
for _, It in Items do
	local Node = game:GetService(It.Path[1])
	for I = 2, #It.Path - 1 do
		local Next = Node:FindFirstChild(It.Path[I])
		if not Next then Next = Instance.new("Folder") Next.Name = It.Path[I] Next.Parent = Node end
		Node = Next
	end
	local Name = It.Path[#It.Path]
	local Old = Node:FindFirstChild(Name)
	local New = Instance.new("ModuleScript")
	New.Name = Name
	New.Source = It.Source
	New.Parent = Node
	if Old then for _, K in Old:GetChildren() do K.Parent = New end Old:Destroy() end
	table.insert(Report, New:GetFullName() .. " " .. #New.Source)
end
return table.concat(Report, "\n")