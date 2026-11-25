--!strict
--[[
	Nightmare Highschool UI Theme
	Shared palette, fonts, sizes and texture ids for ReplicatedStorage.UI.Components.

	All sizes are in "design pixels" for a 1920x1080 screen. Components.AutoScale()
	adds one UIScale to a ScreenGui so the same numbers work on every screen.

	All textures are original greyscale/white art (made for this kit) so they can be
	tinted with ImageColor3. Frames: ornate panel = 4 corners + 4 tiled edge strips
	(gothic iron-gate arcade); small parts use the 9-slice "FrameThin".
]]

local Theme = {}

local rgb = Color3.fromRGB

----------------------------------------------------------------------
-- Colours
----------------------------------------------------------------------
Theme.Colors = {
	-- surfaces
	Base = rgb(14, 12, 18), -- near-black, matches the existing NH UI
	Ink = rgb(7, 6, 10), -- deepest wells (slots, tracks)
	PanelTint = rgb(52, 46, 60), -- multiplied over the slate texture
	Well = rgb(36, 32, 42), -- rows / plates (a left-to-right gradient darkens it)
	WellHover = rgb(58, 52, 66),
	RowFrame = rgb(196, 190, 204), -- border tint on rows
	Shadow = rgb(0, 0, 0),

	-- ornament metals
	Iron = rgb(226, 220, 232), -- default filigree tint (textures carry their own PBR shading)
	IronDim = rgb(150, 144, 158),

	-- text
	Text = rgb(228, 222, 208), -- bone / old paper
	TextDim = rgb(150, 142, 138),
	TextFaint = rgb(98, 92, 96),
	Chalk = rgb(222, 224, 214),

	-- accents
	Gold = rgb(235, 205, 120), -- The Vigil candle gold
	GoldDeep = rgb(150, 112, 50),
	Crimson = rgb(200, 40, 60), -- The Crimson Court blood red
	CrimsonDeep = rgb(96, 14, 26),
	Blood = rgb(150, 22, 34),
	Mana = rgb(92, 128, 210), -- ink blue
	Stamina = rgb(120, 170, 96), -- chalk green
	Wax = rgb(176, 36, 44),

	-- states
	On = rgb(235, 205, 120),
	Off = rgb(98, 92, 96),
	Danger = rgb(214, 46, 58),
}

-- Item rarities: colour of the wax seal on each slot.
Theme.Rarity = {
	Common = rgb(196, 190, 178), -- chalk
	Uncommon = rgb(98, 168, 110), -- ink green
	Rare = rgb(84, 126, 214), -- ink blue
	Epic = rgb(150, 92, 206), -- violet ink
	Legendary = rgb(235, 205, 120), -- candle gold
	Cursed = rgb(200, 40, 60), -- blood
}
Theme.RarityOrder = { "Common", "Uncommon", "Rare", "Epic", "Legendary", "Cursed" }

-- Faction accents (used by Panel{accent=...}, PlayerListRow, StatSheet).
Theme.Factions = {
	None = { Name = "Unaffiliated", Frame = rgb(226, 220, 232), Accent = rgb(228, 222, 208), Icon = "IconNib" },
	Vigil = { Name = "The Vigil", Frame = rgb(240, 208, 130), Accent = rgb(235, 205, 120), Icon = "IconCandle" },
	Court = { Name = "The Crimson Court", Frame = rgb(222, 86, 98), Accent = rgb(200, 40, 60), Icon = "IconDrop" },
}

-- Races (concept doc): Human, Priest, Vampire.
Theme.Races = {
	Human = { Color = rgb(228, 222, 208), Icon = "IconNib" },
	Priest = { Color = rgb(235, 205, 120), Icon = "IconCross" },
	Vampire = { Color = rgb(200, 40, 60), Icon = "IconDrop" },
}

----------------------------------------------------------------------
-- Fonts
----------------------------------------------------------------------
Theme.Fonts = {
	Title = Enum.Font.Fantasy, -- headings, names, numbers in orbs
	Body = Enum.Font.Garamond, -- everything else
	BodyBold = Enum.Font.Garamond,
}
-- FontFace versions (bold Garamond for labels that need weight)
local garamond = Font.fromEnum(Enum.Font.Garamond)
Theme.FontFaces = {
	Title = Font.fromEnum(Enum.Font.Fantasy),
	Body = garamond,
	BodyBold = Font.new(garamond.Family, Enum.FontWeight.Bold),
}

----------------------------------------------------------------------
-- Sizes (design pixels @1080p)
----------------------------------------------------------------------
Theme.Sizes = {
	TextHuge = 40,
	TextTitle = 28,
	TextHeader = 23,
	TextBody = 20, -- UI audit: readable text >= 18 design px
	TextSmall = 18,
	TextTiny = 15, -- key caps / tiny tags only

	RowHeight = 44, -- every tappable row / button is at least this tall
	TapMin = 44,
	RowGap = 6,
	Pad = 14,
	Slot = 78,
	SlotGap = 8,

	Edge = 20, -- ornate edge strip thickness
	Corner = 56, -- ornate corner size
	Tile = 16, -- arcade tile length
	ContentInset = 24, -- content padding inside an ornate panel
}

-- Scaling rules used by Components.AutoScale
Theme.Scale = {
	Design = Vector2.new(1920, 1080),
	Min = 0.5,
	Max = 1.6,
	-- On touch devices never shrink below this, so 44px rows stay >= 40px real.
	TouchMin = 0.92,
	-- Phones (touch, shorter side under PhoneBelow px) use PhoneTouchMin instead: 0.92 is a desktop layout on a
	-- 375 px tall screen. 44px rows stay >= 27 px, about Roblox's own mobile buttons.
	PhoneTouchMin = 0.62,
	PhoneBelow = 600,
	Curve = 0.6, -- below 1x the scale is raw^Curve (720p: 0.67 -> 0.78), so laptops keep readable text
}

----------------------------------------------------------------------
-- Textures (original art, uploaded for this kit). Pixel sizes are noted so
-- 9-slice centres line up. Corner/edge art is 4x the design size.
----------------------------------------------------------------------
local function id(n: number): string
	return "rbxassetid://" .. tostring(n)
end

Theme.Images = {
	-- the school crest (owner's logo): the PBR relief for big moments, the flat 2D art for small icons
	Crest = id(76710547383945),
	CrestFlat = id(140163448311226),

	-- ornate panel frame: corners (224x224) + tiling edges (64x80 / 80x64)
	-- (all ornament is baked PBR metal: GGX key + rim light, AO, roughness/grime maps)
	CornerTL = id(112650166334448),
	CornerTR = id(102205882194944),
	CornerBL = id(106328863635498),
	CornerBR = id(137277096785516),
	EdgeT = id(121594488844958),
	EdgeB = id(103345821669147),
	EdgeL = id(116603076543192),
	EdgeR = id(109715570722447),

	-- 9-slice frames
	FrameThin = id(87222448211212), -- 128x128, slice 32 (rows, buttons, plates)
	FrameSlot = id(103947306840076), -- 192x192, slice 48 (item slots: bracket corners)
	FrameOrnate = id(87271797482858), -- 512x512, slice 128 (legacy single-image frame)
	BarFrame = id(95638582827971), -- 1024x128, caps 160 (legacy single-image bar)
	Shadow = id(80916333065698), -- 128x128 soft shadow, slice 40

	-- health bar pieces (64x64 design caps, 256px)
	BarCapL = id(113574580178332),
	BarCapR = id(87151520587600),

	-- fills and backgrounds
	PanelBg = id(79365591227813), -- 512 slate, chalk smudges, inner edge shadow (greyscale)
	SlotBg = id(135071894070220), -- 128 recessed slot well
	BarFill = id(112499259139264), -- 512x96 veined fill with gloss, tiles horizontally
	OrbFill = id(120716841893865), -- 256 glassy disc
	OrbRing = id(98807642343746), -- 256 clock-face ring with iron spikes
	Glow = id(117234203443052), -- 256 soft radial glow

	-- ornaments and icons
	Divider = id(129260634559358), -- 512x48
	Knob = id(88681703347014), -- 64 pierced diamond knob (sliders, toggles, meter caps)
	Pip = id(119752817385216), -- 64 solid diamond (stat pips)
	-- (icon set start) the icons that replaced the seal everywhere but the rarity gem (docs/Icon-Set.md,
	-- art/ui/hud/make_seal_icons.py). A key still on the seal's id is waiting for its upload.
	IconNoteInfo = id(77613518052785),
	IconNoteGood = id(93992879141730),
	IconNoteWarning = id(80040895263905),
	IconNoteBad = id(137562229037984),
	IconNoteMilestone = id(74775991945568),
	IconBannerLevelUp = id(100133540737696),
	IconBannerPurchase = id(71454509965270),
	IconBannerEvolved = id(73742479839492),
	IconBannerQuestNew = id(122595062904024),
	IconBannerQuestStep = id(117098613614202),
	IconBannerQuestDone = id(122871790396806),
	IconBannerQuestFailed = id(134685504926951),
	IconBannerFullMoon = id(78088229372954),
	IconBannerNewMoon = id(103320978789077),
	IconBannerCrimsonMoon = id(75115162497853),
	IconBannerBlueMoon = id(76905808578312),
	IconBannerRecord = id(78077364515054),
	IconNpcOffer = id(118658855836011),
	IconNpcTurnIn = id(110237942427954),
	IconNpcRetry = id(88260882124914),
	IconNpcActive = id(129335219160355),
	IconArrivalCrest = id(123508946459581),
	IconClockDial = id(127412964613422),
	IconDiscoverFlag = id(91048384274144),
	IconWaypointMark = id(89748005322968),
	IconDuelRing = id(108727308046919),
	IconSportShoot = id(76745650268241),
	IconSportPass = id(137622831456885),
	IconSportMove = id(126597146216980),
	IconSportEuro = id(112719422027180),
	IconSoccerKick = id(89435755096067),
	IconSoccerPass = id(98331994577399),
	IconSoccerDribble = id(109101630613551),
	IconSoccerTackle = id(104596198141425),
	IconSoccerFeint = id(121973890802648),
	IconSoccerRush = id(98452152216830),
	IconFootballThrow = id(76567307609509),
	IconFootballDive = id(81289815485551),
	IconFootballJuke = id(114061612913293),
	IconFootballHit = id(75203170674408),
	IconFootballSnap = id(86141496970922),
	IconGradeSeal = id(135112626845007),
	IconCoinYen = id(120561881777483),
	IconCardBack = id(89094280984199),
	IconHexRelic = id(116121653547952),
	IconHexAltar = id(132786489933965),
	IconCryptRune = id(113544269547191),
	-- (icon set end)
	Seal = id(130174890638243), -- 512 PBR wax seal, greyscale so ImageColor3 tints it (art/ui/hud/make_seal_pbr.py; was 119862801131834)
	Bell = id(113108812763552), -- 256 cracked skull-bell (danger)
	IconCandle = id(94954840696752), -- The Vigil
	IconDrop = id(120790040119219), -- The Crimson Court / Vampire
	IconNib = id(111653815043223), -- Human / student
	IconCross = id(139095929919543), -- Priest
	IconReport = id(122522265193174), -- 512 report card with an A+ and a wax seal (1.40: the phone's Report Card app; art/ui/hud/make_report_icon.py)
	-- (1.40) the phone's app icons, one per app (art/ui/hud/make_app_icons.py), same family as IconReport
	IconAppGazette = id(111034691557863),
	IconAppTimetable = id(122221944731404),
	IconAppGroup = id(137880925403828),
	IconAppCliques = id(130786823066506),
	IconAppTexts = id(118492365675940),
	IconAppStyle = id(112501139977785),
	IconAppOptions = id(96119055967160),
	IconAppWisp = id(90538413644836),
	IconAppHex = id(87971445986117),
	IconAppCrypt = id(132034319909967),
	IconAppWallet = id(120605023273384),
	IconAppRadio = id(76492020196435),
	IconAppContacts = id(97462922632891),
	IconAppCamera = id(130136184826884),
	ColorWheel = id(106950714273914), -- 512 hue/saturation wheel (ColorPicker)
}

-- (1.45) the Ink Club seer's tarot deck (Controllers.Gui.Fortune; art/ui/hud/make_tarot_cards.py), 600x1024 full colour
Theme.FortuneCards = {
	Back = id(87643887150581),
	Tower = id(129962336422381),
	Fool = id(77595359364753),
	Moon = id(96875840981623),
	Seeker = id(87434866892871),
	Feast = id(130416203982260),
	Crown = id(80080080797051),
	Scholar = id(122009644258686),
}

-- (1.47) substitute days' minigame art (Controllers.Gui.Activities CandleVigil / SeanceSequence, the lesson intro's game
-- icons; art/ui/hud/make_substitute_games.py). The candle overlays' wick tip is at (128, 208) of 256, the body's at (131.4, 80.4)
Theme.SubGames = {
	SigilMoon_idle = id(98813729363393), SigilMoon_lit = id(105446567743918),
	SigilEye_idle = id(72602499134480), SigilEye_lit = id(122066575291130),
	SigilKey_idle = id(72941519275790), SigilKey_lit = id(122284119183898),
	SigilRaven_idle = id(80313624551932), SigilRaven_lit = id(76073386422334),
	SigilSkullBell_idle = id(107451145437327), SigilSkullBell_lit = id(123493172004482),
	SigilStar_idle = id(89043593051563), SigilStar_lit = id(72457572906132),
	CandleBody = id(90454674182579), CandleFlame = id(89964890342300), CandleGutter = id(120029435100167), CandleSmoke = id(95902486659019),
	GamePopQuiz = id(74869266128375), GameLabMix = id(100460872583196), GameWordScramble = id(126445335242922),
	GameMatchThePast = id(129345459175764), GameCandleVigil = id(135211879073434), GameSeanceSequence = id(71554415848107),
}

Theme.Slices = {
	FrameThin = { Center = Rect.new(32, 32, 96, 96), Scale = 0.5 },
	FrameSlot = { Center = Rect.new(48, 48, 144, 144), Scale = 0.4 },
	FrameOrnate = { Center = Rect.new(128, 128, 384, 384), Scale = 0.45 },
	BarFrame = { Center = Rect.new(160, 48, 864, 80), Scale = 0.5 },
	Shadow = { Center = Rect.new(40, 40, 88, 88), Scale = 1 },
}

----------------------------------------------------------------------
-- Motion
----------------------------------------------------------------------
Theme.Tween = {
	Fast = TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
	Med = TweenInfo.new(0.25, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
	Slow = TweenInfo.new(0.6, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut),
}

-- full-colour icons: shown untinted (ImageColor3 white) by Toast, Moments, Compass
Theme.Baked = { IconNoteInfo = true, IconNoteGood = true, IconNoteWarning = true, IconNoteBad = true, IconNoteMilestone = true, IconBannerLevelUp = true, IconBannerPurchase = true, IconBannerEvolved = true, IconBannerQuestNew = true, IconBannerQuestStep = true, IconBannerQuestDone = true, IconBannerQuestFailed = true, IconBannerFullMoon = true, IconBannerNewMoon = true, IconBannerCrimsonMoon = true, IconBannerBlueMoon = true, IconBannerRecord = true, IconNpcOffer = true, IconNpcTurnIn = true, IconNpcRetry = true, IconNpcActive = true, IconArrivalCrest = true, IconClockDial = true, IconDiscoverFlag = true, IconWaypointMark = true, IconDuelRing = true, IconSportShoot = true, IconSportPass = true, IconSportMove = true, IconSportEuro = true, IconSoccerKick = true, IconSoccerPass = true, IconSoccerDribble = true, IconSoccerTackle = true, IconSoccerFeint = true, IconSoccerRush = true, IconFootballThrow = true, IconFootballDive = true, IconFootballJuke = true, IconFootballHit = true, IconFootballSnap = true, IconCoinYen = true, IconCardBack = true, IconHexRelic = true, IconCryptRune = true }

-- Helper: faction palette by key ("Vigil" | "Court" | nil)
function Theme.Faction(key: string?)
	return Theme.Factions[key or "None"] or Theme.Factions.None
end

return Theme
