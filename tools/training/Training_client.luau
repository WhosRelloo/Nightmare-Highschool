--[[
	Training (client). Controllers.Gui.Training   (training minigames, phase 1: 2026-11-11; docs/Training.md)
	The gym stations' minigame: a ring shrinks onto the brass mark of a gauge; press on the mark.
	  Press   Space, A or R2 on a pad, a click or tap on the gauge, or the PRESS button (touch)
	  Leave   Q, B on a pad, or the Leave button
	The server (Services.Features.Training) seats you, rolls the set's seed and scores the presses this sends; this
	only draws. Art: Config.Training.Art (the group import of art/group-upload-training); until an id is filled in, kit
	stand-ins draw instead. Reduce Motion: no shakes, squash, sweeps or orbit; fades and plain fills.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local ContextActionService = game:GetService(`ContextActionService`)
local GuiService = game:GetService(`GuiService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Training`))
local CameraLease = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`CameraLease`))
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts

local Player = Players.LocalPlayer
local Shared = {}
local Local = {}

local GOLD, BRASS, CHALK, BONE, DIM, INK = C.Gold, Color3.fromRGB(214, 160, 82), C.Chalk, C.Text, C.TextDim, C.Ink
local CRIMSON, CRIMSON_DEEP, EMBER = C.Crimson, C.CrimsonDeep, Color3.fromRGB(255, 136, 60)
local RATE_COLOR = { Perfect = Color3.fromRGB(246, 218, 132); Great = Color3.fromRGB(226, 176, 92); Good = CHALK;
	Miss = Color3.fromRGB(150, 142, 138); Feint = Color3.fromRGB(200, 120, 110); Stray = Color3.fromRGB(150, 142, 138) }
local RATE_WORD = { Perfect = `PERFECT`; Great = `GREAT`; Good = `GOOD`; Miss = `MISS`; Feint = `FEINT!`; Stray = `TOO SOON` }
local RATE_ART = { Perfect = `TrainRatePerfect`; Great = `TrainRateGreat`; Good = `TrainRateGood`; Miss = `TrainRateMiss`; Feint = `TrainRateMiss`; Stray = `TrainRateMiss` }

local GAUGE = 380                 -- design px
local MARK_R = 190 / 1024         -- the mark's radius as a share of the gauge
local START_R = 430 / 1024
local RING_R = 470 / 1024         -- the ring's radius inside its own sprite

local Remotes: Folder? = nil
local Gui: ScreenGui? = nil
local Ui = {} :: { [string]: any }
local Session = nil :: any       -- while seated at a station
local SetRun = nil :: any        -- while a set runs

---| art |---

local function art(Name: string): string?
	local Ids = Config.Art or {}
	local N = Ids[Name]
	if typeof(N) == `number` and N > 0 then return `rbxassetid://{N}` end
	return nil
end
local STAND_IN = {
	TrainGauge = Theme.Images.OrbRing; TrainRing = Theme.Images.OrbRing; TrainRingFake = Theme.Images.OrbRing;
	TrainRingHeavy = Theme.Images.OrbRing; TrainMarkGlow = Theme.Images.Glow; TrainRatePerfect = Theme.Images.Seal;
	TrainRateGreat = Theme.Images.Pip; TrainRateGood = Theme.Images.Knob; TrainRateMiss = Theme.Images.Knob;
	TrainBadgeStreak = Theme.Images.IconCandle; TrainBadgeBest = Theme.Images.Seal; TrainBadgeDaily = Theme.Images.Knob;
	TrainIconSore = Theme.Images.Pip; TrainGear = Theme.Images.OrbRing; TrainNeedle = Theme.Images.Pip;
	TrainIconArms = Theme.Images.Seal; TrainIconTorso = Theme.Images.Seal; TrainIconLegs = Theme.Images.Seal;
	TrainStationPushUp = Theme.Images.Seal; TrainStationPullUp = Theme.Images.Seal; TrainStationSitUp = Theme.Images.Seal;
	TrainStationSquat = Theme.Images.Seal; TrainFlame = (Theme.SubGames and Theme.SubGames.CandleFlame) or Theme.Images.Glow;
}
-- colour-baked art draws white-tinted; a stand-in is tinted so it still reads
local function img(Name: string, Props: { [string]: any }, Tint: Color3?)
	local Real = art(Name)
	local L = Instance.new(Props.ClassName or `ImageLabel`)
	L.BackgroundTransparency = 1
	L.Image = Real or STAND_IN[Name] or Theme.Images.Glow
	L.ImageColor3 = if Real then Color3.new(1, 1, 1) else (Tint or GOLD)
	L.ScaleType = Enum.ScaleType.Fit
	for K, V in Props do if K ~= `ClassName` then (L :: any)[K] = V end end
	L:SetAttribute(`Art`, Name)
	L:SetAttribute(`StandIn`, Real == nil)
	return L
end

local function reduced(): boolean return Kit.ReducedMotion() end
local function shakeScale(): number
	local S = Player:GetAttribute(`NHShakeScale`)
	return if typeof(S) == `number` then math.clamp(S, 0, 1) else 1
end
local function tween(O: Instance, T: number, Props, Style: Enum.EasingStyle?, Dir: Enum.EasingDirection?)
	local Tw = TweenService:Create(O, TweenInfo.new(T, Style or Enum.EasingStyle.Quint, Dir or Enum.EasingDirection.Out), Props)
	Tw:Play()
	return Tw
end
local function text(Props)
	local L = Kit.Text(Props)
	return L
end

---| the HUD |---

function Local.Build()
	if Gui then Gui:Destroy() end
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHTraining`
	G.ResetOnSpawn = false
	G.IgnoreGuiInset = true
	G.DisplayOrder = 30
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	Kit.AutoScale(G)
	Gui = G
	Ui = {}
	local Root = Instance.new(`Frame`)
	Root.Name = `Root`
	Root.BackgroundTransparency = 1
	Root.Size = UDim2.fromScale(1, 1)
	Root.Parent = G
	Ui.Root = Root

	-- the set plate (top centre): station medallion, exercise, area level, reps, streak and Fresh chips
	local Plate = Instance.new(`Frame`)
	Plate.Name = `SetPlate`
	Plate.AnchorPoint = Vector2.new(0.5, 0)
	Plate.Position = UDim2.new(0.5, 0, 0, 28)
	Plate.Size = UDim2.fromOffset(680, 104)
	Plate.BackgroundTransparency = 1
	Plate.Parent = Root
	local PlateArt = art(`TrainPlate`)
	if PlateArt then
		local Bg = Instance.new(`ImageLabel`)
		Bg.Name = `Art`
		Bg.BackgroundTransparency = 1
		Bg.Image = PlateArt
		Bg.ScaleType = Enum.ScaleType.Slice
		Bg.SliceCenter = Rect.new(64, 64, 704, 128)
		Bg.SliceScale = 0.5
		Bg.Size = UDim2.fromScale(1, 1)
		Bg.Parent = Plate
	else
		Kit.Decorate(Plate, { ornament = `thin`, bgTransparency = 0.12 })
	end
	Ui.PlateIcon = img(`TrainStationPushUp`, { Name = `Icon`; Position = UDim2.fromOffset(14, 12); Size = UDim2.fromOffset(80, 80); ZIndex = 3; Parent = Plate })
	Ui.PlateTitle = text({ Name = `Title`; Text = `PUSH-UPS`; Font = Fonts.Title; TextSize = 30; TextColor3 = GOLD;
		Position = UDim2.fromOffset(108, 14); Size = UDim2.fromOffset(330, 36); ZIndex = 3; Parent = Plate })
	Kit.Emboss(Ui.PlateTitle, Color3.fromRGB(150, 112, 50))
	Ui.PlateSub = text({ Name = `Sub`; Text = `Arms  Lv 0`; Font = Fonts.Body; TextSize = 21; TextColor3 = BONE;
		Position = UDim2.fromOffset(108, 54); Size = UDim2.fromOffset(330, 28); ZIndex = 3; Parent = Plate })
	Ui.PlateReps = text({ Name = `Reps`; Text = ``; Font = Fonts.Title; TextSize = 28; TextColor3 = BONE; TextXAlignment = Enum.TextXAlignment.Right;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -20, 0, 14); Size = UDim2.fromOffset(220, 34); ZIndex = 3; Parent = Plate })
	local Chips = Instance.new(`Frame`)
	Chips.Name = `Chips`
	Chips.BackgroundTransparency = 1
	Chips.AnchorPoint = Vector2.new(1, 0)
	Chips.Position = UDim2.new(1, -18, 0, 56)
	Chips.Size = UDim2.fromOffset(300, 32)
	Chips.ZIndex = 3
	Chips.Parent = Plate
	local CL = Instance.new(`UIListLayout`)
	CL.FillDirection = Enum.FillDirection.Horizontal
	CL.HorizontalAlignment = Enum.HorizontalAlignment.Right
	CL.Padding = UDim.new(0, 14)
	CL.Parent = Chips
	local function chip(Name: string, ArtName: string, Tint: Color3)
		local F = Instance.new(`Frame`)
		F.Name = Name
		F.BackgroundTransparency = 1
		F.AutomaticSize = Enum.AutomaticSize.X
		F.Size = UDim2.fromOffset(0, 32)
		F.ZIndex = 3
		F.Parent = Chips
		local I = img(ArtName, { Name = `Icon`; Size = UDim2.fromOffset(32, 32); ZIndex = 4; Parent = F }, Tint)
		local T = text({ Name = `Text`; Text = ``; Font = Fonts.Body; TextSize = 19; TextColor3 = BONE; AutomaticSize = Enum.AutomaticSize.X;
			Position = UDim2.fromOffset(36, 0); Size = UDim2.fromOffset(0, 32); ZIndex = 4; Parent = F })
		local Pad = Instance.new(`UIPadding`)
		Pad.PaddingRight = UDim.new(0, 2)
		Pad.Parent = F
		return F, I, T
	end
	Ui.StreakChip, Ui.StreakIcon, Ui.StreakText = chip(`Streak`, `TrainBadgeStreak`, GOLD)
	Ui.FreshChip, Ui.FreshIcon, Ui.FreshText = chip(`Fresh`, `TrainBadgeDaily`, CHALK)
	Ui.SoreChip, Ui.SoreIcon, Ui.SoreText = chip(`Sore`, `TrainIconSore`, Color3.fromRGB(200, 92, 92))
	Ui.SoreText.TextColor3 = Color3.fromRGB(226, 140, 132)

	-- the next-change bar (under the plate): molten brass poured into a black-iron channel
	local Bar = Instance.new(`Frame`)
	Bar.Name = `NextBar`
	Bar.AnchorPoint = Vector2.new(0.5, 0)
	Bar.Position = UDim2.new(0.5, 20, 0, 176)
	Bar.Size = UDim2.fromOffset(600, 36)
	Bar.BackgroundTransparency = 1
	Bar.Parent = Root
	Ui.Bar = Bar
	Ui.BarIcon = img(`TrainIconArms`, { Name = `Crest`; AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(0, -10, 0.5, 0); Size = UDim2.fromOffset(52, 52); ZIndex = 4; Parent = Bar })
	Ui.BarCaption = text({ Name = `Caption`; Text = ``; Font = Fonts.Body; TextSize = 21; TextColor3 = BONE;
		Position = UDim2.fromOffset(0, -30); Size = UDim2.new(1, 0, 0, 26); Parent = Bar })
	Ui.BarNote = text({ Name = `Note`; Text = ``; Font = Fonts.Body; TextSize = 17; TextColor3 = DIM; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.new(0, 0, 1, 2); Size = UDim2.new(1, 0, 0, 22); Parent = Bar })
	local Channel = Instance.new(`Frame`)
	Channel.Name = `Channel`
	Channel.BackgroundColor3 = INK
	Channel.BorderSizePixel = 0
	Channel.ClipsDescendants = true
	Channel.Position = UDim2.fromOffset(18, 11)
	Channel.Size = UDim2.new(1, -36, 0, 14)
	Channel.ZIndex = 2
	Channel.Parent = Bar
	local Fill = Instance.new(`Frame`)
	Fill.Name = `Fill`
	Fill.BackgroundColor3 = Color3.new(1, 1, 1)
	Fill.BorderSizePixel = 0
	Fill.Size = UDim2.fromScale(0, 1)
	Fill.ZIndex = 2
	Fill.Parent = Channel
	local FG = Instance.new(`UIGradient`)
	FG.Name = `Molten`
	FG.Color = ColorSequence.new({
		ColorSequenceKeypoint.new(0, Color3.fromRGB(150, 88, 30)), ColorSequenceKeypoint.new(0.35, Color3.fromRGB(226, 160, 70)),
		ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 222, 140)), ColorSequenceKeypoint.new(0.65, Color3.fromRGB(226, 160, 70)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(150, 88, 30)) })
	FG.Parent = Fill
	local FillArt = art(`TrainBarFill`)
	if FillArt then
		-- the poured brass itself (tiles across; the flow scrolls it) under a soft travelling glint
		Fill.BackgroundTransparency = 1
		local Tile = Instance.new(`ImageLabel`)
		Tile.Name = `Brass`
		Tile.BackgroundTransparency = 1
		Tile.Image = FillArt
		Tile.ScaleType = Enum.ScaleType.Tile
		Tile.TileSize = UDim2.fromOffset(112, 14)
		Tile.Size = UDim2.new(1, 112, 1, 0)
		Tile.ZIndex = 2
		Tile.Parent = Fill
		Ui.BarTile = Tile
		FG.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(220, 200, 180)), ColorSequenceKeypoint.new(0.5, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(1, Color3.fromRGB(220, 200, 180)) })
		FG.Parent = Tile
	end
	local Lip = Instance.new(`ImageLabel`)  -- the hot leading edge of the pour
	Lip.Name = `Lip`
	Lip.BackgroundTransparency = 1
	Lip.Image = Theme.Images.Glow
	Lip.ImageColor3 = Color3.fromRGB(255, 200, 110)
	Lip.AnchorPoint = Vector2.new(0.5, 0.5)
	Lip.Position = UDim2.fromScale(1, 0.5)
	Lip.Size = UDim2.fromOffset(34, 34)
	Lip.ZIndex = 3
	Lip.Parent = Fill
	Ui.BarFill, Ui.BarFlow, Ui.BarLip = Fill, FG, Lip
	local FrameArt = art(`TrainBarFrame`)
	if FrameArt then
		local Fr = Instance.new(`ImageLabel`)
		Fr.Name = `Frame`
		Fr.BackgroundTransparency = 1
		Fr.Image = FrameArt
		Fr.Size = UDim2.fromScale(1, 1)
		Fr.ZIndex = 4
		Fr.Parent = Bar
	else
		local St = Instance.new(`UIStroke`)
		St.Color = Color3.fromRGB(110, 104, 116)
		St.Thickness = 2
		St.Parent = Channel
	end
	Ui.Ghost = Instance.new(`Frame`)  -- the XP a set just added, shown brighter before the pour settles
	Ui.Ghost.Name = `Gain`
	Ui.Ghost.BackgroundColor3 = Color3.fromRGB(255, 236, 170)
	Ui.Ghost.BackgroundTransparency = 1
	Ui.Ghost.BorderSizePixel = 0
	Ui.Ghost.ZIndex = 2
	Ui.Ghost.Parent = Channel

	-- the gauge (right of centre; the camera frames you on the left)
	local GaugeRoot = Instance.new(`Frame`)
	GaugeRoot.Name = `Gauge`
	GaugeRoot.AnchorPoint = Vector2.new(0.5, 0.5)
	GaugeRoot.Position = UDim2.new(0.66, 0, 0.47, 0)
	GaugeRoot.Size = UDim2.fromOffset(GAUGE, GAUGE)
	GaugeRoot.BackgroundTransparency = 1
	GaugeRoot.Parent = Root
	Ui.Gauge = GaugeRoot
	local GScale = Instance.new(`UIScale`)
	GScale.Parent = GaugeRoot
	Ui.GaugeScale = GScale
	local Dial = img(`TrainGauge`, { ClassName = `ImageButton`; Name = `Dial`; AutoButtonColor = false; Size = UDim2.fromScale(1, 1); ZIndex = 2; Parent = GaugeRoot }, Color3.fromRGB(176, 128, 62))
	Ui.Dial = Dial
	if Dial:GetAttribute(`StandIn`) then
		-- a stand-in face and mark until the art is imported
		local Face = Instance.new(`Frame`)
		Face.Name = `Face`
		Face.AnchorPoint = Vector2.new(0.5, 0.5)
		Face.Position = UDim2.fromScale(0.5, 0.5)
		Face.Size = UDim2.fromScale(0.86, 0.86)
		Face.BackgroundColor3 = Color3.fromRGB(20, 14, 18)
		Face.ZIndex = 1
		Face.Parent = GaugeRoot
		local Cr = Instance.new(`UICorner`) Cr.CornerRadius = UDim.new(0.5, 0) Cr.Parent = Face
		local Mark = Instance.new(`Frame`)
		Mark.Name = `Mark`
		Mark.AnchorPoint = Vector2.new(0.5, 0.5)
		Mark.Position = UDim2.fromScale(0.5, 0.5)
		Mark.Size = UDim2.fromScale(MARK_R * 2, MARK_R * 2)
		Mark.BackgroundTransparency = 1
		Mark.ZIndex = 3
		Mark.Parent = GaugeRoot
		local Cm = Instance.new(`UICorner`) Cm.CornerRadius = UDim.new(0.5, 0) Cm.Parent = Mark
		local Sm = Instance.new(`UIStroke`) Sm.Color = CRIMSON Sm.Thickness = 6 Sm.Parent = Mark
	end
	Ui.MarkGlow = img(`TrainMarkGlow`, { Name = `MarkGlow`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(1, 1); ImageTransparency = 1; ZIndex = 4; Parent = GaugeRoot }, GOLD)
	Ui.MarkGlow.ImageColor3 = GOLD
	-- the needle sweeps as each ring closes in
	Ui.Needle = img(`TrainNeedle`, { Name = `Needle`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(0.62, 0.62); ZIndex = 6; Parent = GaugeRoot }, Color3.fromRGB(120, 140, 190))
	if Ui.Needle:GetAttribute(`StandIn`) then Ui.Needle.Visible = false end
	Ui.AreaIcon = img(`TrainIconArms`, { Name = `Area`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(0.2, 0.2); ZIndex = 7; Parent = GaugeRoot })
	Ui.RingLayer = Instance.new(`Frame`)
	Ui.RingLayer.Name = `Rings`
	Ui.RingLayer.BackgroundTransparency = 1
	Ui.RingLayer.Size = UDim2.fromScale(1, 1)
	Ui.RingLayer.ZIndex = 5
	Ui.RingLayer.Parent = GaugeRoot
	-- the dimming candles (tier III+ distraction)
	Ui.Dim = Instance.new(`Frame`)
	Ui.Dim.Name = `Gutter`
	Ui.Dim.AnchorPoint = Vector2.new(0.5, 0.5)
	Ui.Dim.Position = UDim2.fromScale(0.5, 0.5)
	Ui.Dim.Size = UDim2.fromScale(0.88, 0.88)
	Ui.Dim.BackgroundColor3 = Color3.new(0, 0, 0)
	Ui.Dim.BackgroundTransparency = 1
	Ui.Dim.ZIndex = 8
	Ui.Dim.Parent = GaugeRoot
	local DC = Instance.new(`UICorner`) DC.CornerRadius = UDim.new(0.5, 0) DC.Parent = Ui.Dim

	-- combo (above the gauge): the number punches, a candle flame flickers behind it, hotter on long streaks
	local Combo = Instance.new(`Frame`)
	Combo.Name = `Combo`
	Combo.AnchorPoint = Vector2.new(0.5, 1)
	Combo.Position = UDim2.new(0.5, 0, 0, -6)
	Combo.Size = UDim2.fromOffset(240, 96)
	Combo.BackgroundTransparency = 1
	Combo.Parent = GaugeRoot
	Ui.ComboRoot = Combo
	Ui.ComboFlame = img(`TrainFlame`, { Name = `Flame`; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -18);
		Size = UDim2.fromOffset(90, 120); ImageTransparency = 1; ZIndex = 2; Parent = Combo }, EMBER)
	Ui.ComboNum = text({ Name = `Num`; Text = ``; Font = Fonts.Title; TextSize = 64; TextColor3 = GOLD; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromOffset(240, 66); ZIndex = 3; Parent = Combo })
	Ui.ComboNum.TextStrokeTransparency = 0.4
	Ui.ComboWord = text({ Name = `Word`; Text = ``; Font = Fonts.Title; TextSize = 17; TextColor3 = BONE; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 66); Size = UDim2.fromOffset(240, 22); ZIndex = 3; Parent = Combo })
	local CS = Instance.new(`UIScale`) CS.Parent = Combo
	Ui.ComboScale = CS

	-- the rating stamp (right of the gauge)
	local Rate = Instance.new(`Frame`)
	Rate.Name = `Rating`
	Rate.AnchorPoint = Vector2.new(1, 0.5)
	Rate.Position = UDim2.new(0, -40, 0.3, 0)
	Rate.Size = UDim2.fromOffset(280, 80)
	Rate.BackgroundTransparency = 1
	Rate.Parent = GaugeRoot
	Ui.Rate = Rate
	Ui.RateMark = img(`TrainRatePerfect`, { Name = `Mark`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.fromOffset(76, 76); ImageTransparency = 1; ZIndex = 3; Parent = Rate })
	Ui.RateWord = text({ Name = `Word`; Text = ``; Font = Fonts.Title; TextSize = 36; TextColor3 = GOLD; TextTransparency = 1; TextXAlignment = Enum.TextXAlignment.Right;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -84, 0, 16); Size = UDim2.fromOffset(200, 44); ZIndex = 3; Parent = Rate })
	Ui.RateWord.TextStrokeTransparency = 1
	local RS = Instance.new(`UIScale`) RS.Parent = Rate
	Ui.RateScale = RS

	-- the prompt under the gauge: a key cap with this device's buttons
	local Key = Instance.new(`Frame`)
	Key.Name = `Prompt`
	Key.AnchorPoint = Vector2.new(0.5, 0)
	Key.Position = UDim2.new(0.5, 0, 1, 14)
	Key.Size = UDim2.fromOffset(280, 60)
	Key.BackgroundTransparency = 1
	Key.Parent = GaugeRoot
	local KeyArt = art(`TrainKey`)
	if KeyArt then
		local K = Instance.new(`ImageLabel`)
		K.BackgroundTransparency = 1
		K.Image = KeyArt
		K.ScaleType = Enum.ScaleType.Slice
		K.SliceCenter = Rect.new(40, 40, 216, 88)
		K.SliceScale = 0.5
		K.Size = UDim2.fromScale(1, 1)
		K.Parent = Key
	else
		Kit.Decorate(Key, { ornament = `thin`, bgTransparency = 0.1 })
	end
	Ui.KeyText = text({ Name = `Text`; Text = ``; Font = Fonts.Title; TextSize = 22; TextColor3 = BONE; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.fromScale(1, 1); ZIndex = 3; Parent = Key })
	Ui.Key = Key
	Ui.Hint = text({ Name = `Hint`; Text = `Press on the brass mark  ·  let cracked rings pass  ·  HOLD: keep holding`; Font = Fonts.Body;
		TextSize = 17; TextColor3 = DIM; TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 1, 82); Size = UDim2.fromOffset(620, 22); Parent = GaugeRoot })

	-- HOLD: a brass gear grinds round while the grind bar fills
	local Hold = Instance.new(`Frame`)
	Hold.Name = `Hold`
	Hold.AnchorPoint = Vector2.new(0.5, 0)
	Hold.Position = UDim2.new(0.5, 0, 1, 14)
	Hold.Size = UDim2.fromOffset(320, 60)
	Hold.BackgroundTransparency = 1
	Hold.Visible = false
	Hold.ZIndex = 5
	Hold.Parent = GaugeRoot
	Ui.Hold = Hold
	Ui.Gear = img(`TrainGear`, { Name = `Gear`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromOffset(30, 30); Size = UDim2.fromOffset(60, 60); ZIndex = 7; Parent = Hold }, BRASS)
	local _, HoldBar = Kit.Bar({ color = CRIMSON; caption = `HOLD`; height = 26; Position = UDim2.fromOffset(66, 17); Size = UDim2.fromOffset(250, 26); Parent = Hold })
	Ui.HoldBar = HoldBar

	-- stamina (burnout and tier IV+ sets), left of the gauge
	local _, Stam = Kit.VerticalMeter({ value = 1; color = C.Stamina; label = `STAMINA`; AnchorPoint = Vector2.new(1, 0.5);
		Position = UDim2.new(0, -26, 0.5, 0); Size = UDim2.fromOffset(28, 300); Parent = GaugeRoot })
	Ui.Stamina = Stam
	Stam.Root.Visible = false

	-- the count-in and the centre callouts
	Ui.Count = text({ Name = `Count`; Text = ``; Font = Fonts.Title; TextSize = 120; TextColor3 = GOLD; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(400, 140); ZIndex = 9; TextTransparency = 1; Parent = GaugeRoot })
	Ui.Count.TextStrokeTransparency = 0.3

	-- touch: a big PRESS button in the thumb zone; Leave top right
	local Press = img(`TrainRing`, { ClassName = `ImageButton`; Name = `TouchPress`; AutoButtonColor = false; AnchorPoint = Vector2.new(1, 1);
		Position = UDim2.new(1, -40, 1, -150); Size = UDim2.fromOffset(170, 170); Visible = false; Parent = Root }, GOLD)
	text({ Name = `Label`; Text = `PRESS`; Font = Fonts.Title; TextSize = 30; TextColor3 = GOLD; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1); Parent = Press })
	Ui.TouchPress = Press
	local LeaveRoot, LeaveApi = Kit.Button({ text = `Leave`; style = `ghost`; onClick = function() Local.Leave() end;
		AnchorPoint = Vector2.new(0, 0); Position = UDim2.new(0.5, 352, 0, 56); Size = UDim2.fromOffset(150, 48); Parent = Root })
	Ui.LeaveButton = LeaveRoot
	Ui.LeaveApi = LeaveApi

	-- particles drawn in the UI (sparks and chalk off the mark, embers in the banner)
	Ui.Fx = Instance.new(`Frame`)
	Ui.Fx.Name = `Fx`
	Ui.Fx.BackgroundTransparency = 1
	Ui.Fx.Size = UDim2.fromScale(1, 1)
	Ui.Fx.ZIndex = 20
	Ui.Fx.Parent = Root

	-- cards (start, results, tutorial) and the step-up banner
	Ui.CardLayer = Instance.new(`Frame`)
	Ui.CardLayer.Name = `Cards`
	Ui.CardLayer.BackgroundTransparency = 1
	Ui.CardLayer.Size = UDim2.fromScale(1, 1)
	Ui.CardLayer.ZIndex = 30
	Ui.CardLayer.Parent = Root

	G.Parent = Player:WaitForChild(`PlayerGui`)
	Local.Shimmers()
end

-- idle shine sweeps across the icons and badges, every few seconds
function Local.Shimmers()
	task.spawn(function()
		while Gui and Gui.Parent do
			task.wait(math.random(40, 70) / 10)
			if Gui and Gui.Enabled and not reduced() then
				for _, I in { Ui.PlateIcon, Ui.AreaIcon, Ui.StreakIcon, Ui.BarIcon } do
					if I and I.Parent and I.Visible then Local.Sweep(I) task.wait(0.25) end
				end
			end
		end
	end)
	-- the streak candle and the combo flame flicker (smooth noise, never snaps)
	local T0 = os.clock()
	local Conn
	Conn = RunService.RenderStepped:Connect(function()
		if not (Gui and Gui.Parent) then Conn:Disconnect() return end
		if not Gui.Enabled then return end
		local T = os.clock() - T0
		local F = math.noise(T * 3.1, 0.3) * 0.5 + math.noise(T * 7.7, 1.7) * 0.25
		if Ui.StreakIcon and not reduced() then
			Ui.StreakIcon.Rotation = F * 4
		end
		if Ui.ComboFlame and art(`TrainFlame`) then
			local Fr = math.floor(T * 16) % 16
			Ui.ComboFlame.ImageRectSize = Vector2.new(256, 256)
			Ui.ComboFlame.ImageRectOffset = Vector2.new((Fr % 4) * 256, math.floor(Fr / 4) * 256)
		end
		if Ui.ComboFlame and Ui.ComboFlame.ImageTransparency < 0.99 then
			local Heat = math.clamp((Ui.ComboHeat or 0), 0, 1)
			local Base = 0.35 - 0.25 * Heat
			Ui.ComboFlame.ImageTransparency = math.clamp(Base + F * 0.25, 0, 0.95)
			Ui.ComboFlame.Size = UDim2.fromOffset(90 + 40 * Heat + F * 10, 120 + 70 * Heat + F * 18)
			Ui.ComboFlame.ImageColor3 = EMBER:Lerp(Color3.fromRGB(255, 230, 150), 0.4 + F * 0.3)
		end
		-- the molten fill flows
		if Ui.BarFlow then Ui.BarFlow.Offset = Vector2.new(((T * 0.35) % 2) - 1, 0) end
		if Ui.BarTile and not reduced() then Ui.BarTile.Position = UDim2.fromOffset(-((T * 30) % 112), 0) end
		if Ui.BarLip then Ui.BarLip.ImageTransparency = 0.25 + F * 0.3 end
	end)
end

function Local.Sweep(I: GuiObject)
	local G = I:FindFirstChild(`NHShine`) :: UIGradient?
	if not G then
		G = Instance.new(`UIGradient`)
		G.Name = `NHShine`
		G.Rotation = 25
		G.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)), ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 244, 214)), ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)) })
		G.Parent = I
	end
	G.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.42, 0), NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(0.58, 0), NumberSequenceKeypoint.new(1, 0) })
	-- the band is a brighter colour key travelling across
	G.Offset = Vector2.new(-1, 0)
	local Tw = tween(G, 0.7, { Offset = Vector2.new(1, 0) }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
	Tw.Completed:Connect(function() if G.Parent then G.Offset = Vector2.new(-1, 0) end end)
end

---| little UI particles |---

function Local.Particles(At: Vector2, Count: number, Opts)
	if not (Ui.Fx and Ui.Fx.Parent) then return end
	local Reduced = reduced()
	if Reduced then Count = math.ceil(Count / 3) end
	for _ = 1, Count do
		local P = Instance.new(`ImageLabel`)
		P.BackgroundTransparency = 1
		P.Image = Opts.Image or Theme.Images.Glow
		P.ImageColor3 = Opts.Color or GOLD
		P.AnchorPoint = Vector2.new(0.5, 0.5)
		local S = math.random(Opts.MinSize or 8, Opts.MaxSize or 18)
		P.Size = UDim2.fromOffset(S, S)
		P.Position = UDim2.fromOffset(At.X, At.Y)
		P.ZIndex = 21
		P.Parent = Ui.Fx
		local A = math.random() * math.pi * 2
		local V = math.random(Opts.MinSpeed or 80, Opts.MaxSpeed or 220) * (if Reduced then 0.4 else 1)
		local Life = (Opts.Life or 0.6) * (0.7 + math.random() * 0.6)
		local Dx, Dy = math.cos(A) * V * Life, math.sin(A) * V * Life + (Opts.Rise or 0) * Life
		tween(P, Life, { Position = UDim2.fromOffset(At.X + Dx, At.Y + Dy); ImageTransparency = 1; Size = UDim2.fromOffset(S * (Opts.Grow or 0.4), S * (Opts.Grow or 0.4)) }, Enum.EasingStyle.Quad)
		task.delay(Life + 0.05, function() P:Destroy() end)
	end
end

-- the gauge's centre in the Fx layer's own offsets (design px: the Fx frame is inside the auto-scaled root)
function Local.GaugeCentre(): Vector2
	local Scale = (Gui and Gui:FindFirstChild(`NHAutoScale`) :: UIScale?)
	local S = if Scale then Scale.Scale else 1
	local P = Ui.Gauge.AbsolutePosition + Ui.Gauge.AbsoluteSize / 2 - Ui.Fx.AbsolutePosition
	return P / S
end

---| text helpers |---

local function inputKind(): string
	local K = Kit.InputKind()
	if K == `Keyboard` and Kit.TouchOnly() then return `Touch` end
	return K
end
local function keysText(): string
	local Kind = inputKind()
	if Kind == `Touch` then return `TAP THE GAUGE` end
	if Kind == `Gamepad` then return `{Kit.KeyName(`ButtonA`)}  or  {Kit.KeyName(`ButtonR2`)}` end
	return `SPACE  or  CLICK`
end
local function leaveText(): string
	local Kind = inputKind()
	if Kind == `Gamepad` then return `Leave ({Kit.KeyName(`ButtonB`)})` end
	if Kind == `Touch` then return `Leave` end
	return `Leave (Q)`
end
local function pct(X: number): string return `{math.floor(X * 100 + 0.5)}%` end

function Local.StatLine(Area: string, Level: number): string
	local Ok, Prog = pcall(require, ReplicatedStorage.Config.Progression)
	local Per = Ok and Prog.Training and Prog.Training[Area]
	if not Per or Level <= 0 then return `` end
	local Bits = {}
	if Per.DamageDealt then table.insert(Bits, `+{string.format(`%.1f`, Per.DamageDealt * Level * 100)}% damage`) end
	if Per.MaxHealth then table.insert(Bits, `+{math.floor(Per.MaxHealth * Level)} health`) end
	if Per.PostureGain then table.insert(Bits, `{string.format(`%.1f`, Per.PostureGain * Level * 100)}% posture`) end
	if Per.SprintSpeed then table.insert(Bits, `+{string.format(`%.1f`, Per.SprintSpeed * Level * 100)}% sprint`) end
	return `Lv {Level}: ` .. table.concat(Bits, `, `)
end

-- the area panel bits that both the HUD and the cards show
function Local.ApplyState(State)
	if not (Session and State) then return end
	Session.State = State
	local Def = Config.Stations[Session.Station]
	local A = State.Areas[Def.Area]
	Ui.PlateIcon.Image = art(Def.Icon) or STAND_IN[Def.Icon]
	Ui.PlateTitle.Text = string.upper(Def.Name)
	Ui.PlateSub.Text = `{Def.Area}  Lv {A.Level}  ·  Tier {A.Tier}`
	Ui.AreaIcon.Image = art(Config.AreaInfo[Def.Area].Icon) or STAND_IN[Config.AreaInfo[Def.Area].Icon]
	Ui.BarIcon.Image = Ui.AreaIcon.Image
	Ui.StreakChip.Visible = (State.Streak or 0) > 0 and State.StreakAlive
	Ui.StreakText.Text = `{State.Streak} day{if State.Streak == 1 then `` else `s`}`
	Ui.FreshChip.Visible = A.Fresh
	Ui.FreshText.Text = `Fresh ×{Config.FreshMult}`
	Ui.SoreChip.Visible = A.Sore >= 1
	Ui.SoreText.Text = `Sore {math.floor(A.Sore)}%`
	Local.SetBar(A, false)
end

function Local.RepsToStep(A): number?
	if not A.ToStep then return nil end
	local Tier = Config.TierFor(A.Level)
	local Per = 2 * Tier.Xp * 1.15 * A.SoreMult * (if A.Fresh then Config.FreshMult else 1)
	return math.max(1, math.ceil(A.ToStep / Per))
end

function Local.SetBar(A, Pour: boolean)
	local F = math.clamp(A.Xp / math.max(1, A.ToNext), 0, 1)
	if A.Level >= Config.MaxLevel then F = 1 end
	local N = Local.RepsToStep(A)
	local Def = Config.Stations[Session.Station]
	if N then
		Ui.BarCaption.Text = `{string.upper(Def.Area)}  ·  next change in ~{N} reps` .. (if A.NextBody then `  ({A.NextBody})` else ``)
	elseif A.Level >= Config.MaxLevel then
		Ui.BarCaption.Text = `{string.upper(Def.Area)}  ·  peak`
	else
		Ui.BarCaption.Text = `{string.upper(Def.Area)}  ·  Lv {A.Level}  ·  {A.Xp} / {A.ToNext}`
	end
	Ui.BarNote.Text = Local.StatLine(Def.Area, A.Level)
	if Pour and not reduced() then
		tween(Ui.BarFill, 1.1, { Size = UDim2.fromScale(F, 1) }, Enum.EasingStyle.Quad, Enum.EasingDirection.InOut)
		task.spawn(function()   -- molten drips off the lip while it pours
			for _ = 1, 8 do
				if not (Ui.BarLip and Ui.BarLip.Parent) then return end
				local P = Ui.BarLip.AbsolutePosition + Ui.BarLip.AbsoluteSize / 2 - Ui.Fx.AbsolutePosition
				local Scale = Gui and Gui:FindFirstChild(`NHAutoScale`) :: UIScale?
				Local.Particles(P / (if Scale then Scale.Scale else 1), 3, { Color = Color3.fromRGB(255, 190, 90); MinSpeed = 20; MaxSpeed = 70; Rise = 90; Life = 0.5; MinSize = 4; MaxSize = 9 })
				task.wait(0.13)
			end
		end)
	else
		Ui.BarFill.Size = UDim2.fromScale(F, 1)
	end
end

---| cards |---

function Local.ClearCards()
	for _, C0 in Ui.CardLayer:GetChildren() do C0:Destroy() end
	Ui.CardButtons = nil
end

function Local.Card(W: number, H: number, Title: string?)
	Local.ClearCards()
	local Root, Api = Kit.Panel({ title = Title; maxSize = Vector2.new(W, H); AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.new(0.27, 0, 0.55, 0); Size = UDim2.fromOffset(W, H); Parent = Ui.CardLayer })
	if not reduced() then
		local S = Instance.new(`UIScale`) S.Scale = 0.92 S.Parent = Root
		tween(S, 0.28, { Scale = 1 }, Enum.EasingStyle.Back)
	end
	Kit.FadeIn(Root, 0.2)
	return Root, Api.Content
end

function Local.Row(Parent: Instance, Y: number, Label: string, Value: string, Color: Color3?)
	text({ Text = Label; Font = Fonts.Body; TextSize = 20; TextColor3 = DIM; Position = UDim2.fromOffset(0, Y); Size = UDim2.new(0.55, 0, 0, 26); Parent = Parent })
	return text({ Text = Value; Font = Fonts.Title; TextSize = 20; TextColor3 = Color or BONE; TextXAlignment = Enum.TextXAlignment.Right;
		Position = UDim2.new(0.45, 0, 0, Y); Size = UDim2.new(0.55, 0, 0, 26); Parent = Parent })
end

function Local.Buttons(Parent: Instance, Y: number, Main: string, OnMain: () -> (), OnLeave: () -> ())
	local W = 200
	local Kind = inputKind()
	local MainKey = if Kind == `Gamepad` then ` ({Kit.KeyName(`ButtonA`)})` elseif Kind == `Touch` then `` else ` (Space)`
	local _, A = Kit.Button({ text = Main .. MainKey; style = `gold`; onClick = OnMain; Position = UDim2.fromOffset(0, Y); Size = UDim2.fromOffset(W + 30, 52); Parent = Parent })
	local _, B = Kit.Button({ text = leaveText(); onClick = OnLeave; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, Y); Size = UDim2.fromOffset(W - 20, 52); Parent = Parent })
	Ui.CardButtons = { Main = OnMain; Leave = OnLeave }
	pcall(function() if Kind == `Gamepad` then GuiService.SelectedObject = A.Root end end)
	return A, B
end

function Local.StartCard()
	if not Session then return end
	local State = Session.State
	local Def = Config.Stations[Session.Station]
	local A = State.Areas[Def.Area]
	local Card, Body = Local.Card(560, 470, string.upper(Def.Name))
	img(Def.Icon, { Position = UDim2.fromOffset(0, 6); Size = UDim2.fromOffset(110, 110); Parent = Body })
	local T = text({ Text = `Trains your {string.upper(Def.Area)}`; Font = Fonts.Title; TextSize = 26; TextColor3 = GOLD; Position = UDim2.fromOffset(126, 10); Size = UDim2.new(1, -126, 0, 32); Parent = Body })
	Kit.Emboss(T, Color3.fromRGB(150, 112, 50))
	text({ Text = `Level {A.Level}  ·  Tier {A.Tier}  ·  {A.Body}`; Font = Fonts.Body; TextSize = 20; TextColor3 = BONE; Position = UDim2.fromOffset(126, 46); Size = UDim2.new(1, -126, 0, 26); Parent = Body })
	local N = Local.RepsToStep(A)
	text({ Text = if N then `Next body change in ~{N} reps` .. (if A.NextBody then ` ({A.NextBody})` else ``) else (if A.Level >= Config.MaxLevel then `At its peak` else `Steps III and IV are coming`);
		Font = Fonts.Body; TextSize = 19; TextColor3 = DIM; TextWrapped = true; Position = UDim2.fromOffset(126, 76); Size = UDim2.new(1, -126, 0, 44); Parent = Body })
	local _, B = Kit.Bar({ color = BRASS; caption = `{A.Xp} / {A.ToNext}`; height = 22; Position = UDim2.fromOffset(0, 128); Size = UDim2.new(1, 0, 0, 22); Parent = Body })
	B:Set(math.clamp(A.Xp / math.max(1, A.ToNext), 0, 1))
	local Best = State.Best and State.Best[Session.Station]
	local Y = 166
	Local.Row(Body, Y, `Personal best`, if Best then `{Best.Score}  ·  combo {Best.Combo}` else `none yet`, if Best then GOLD else DIM)
	Local.Row(Body, Y + 30, `Training streak`, if State.StreakAlive and State.Streak > 0 then `{State.Streak} day{if State.Streak == 1 then `` else `s`} (+{pct(math.min(Config.StreakCap, Config.StreakPer * State.Streak))} XP)` else `start one today`)
	Local.Row(Body, Y + 60, `Fresh bonus`, if A.Fresh then `×{Config.FreshMult} on your first {Def.Area} set today` else `used today`, if A.Fresh then CHALK else DIM)
	Local.Row(Body, Y + 90, `Soreness`, if A.Sore >= 1 then `{math.floor(A.Sore)}%  (XP ×{string.format(`%.2f`, A.SoreMult)})` else `fresh muscles`, if A.Sore >= 30 then Color3.fromRGB(226, 140, 132) else BONE)
	Local.Row(Body, Y + 120, `Today`, `{A.DayXp} / {A.Cap} XP`)
	if A.Sore >= 40 then
		text({ Text = `Your {string.lower(Def.Area)} are sore: train another area for full XP.`; Font = Fonts.Body; TextSize = 18; TextColor3 = Color3.fromRGB(226, 140, 132);
			Position = UDim2.fromOffset(0, Y + 150); Size = UDim2.new(1, 0, 0, 24); Parent = Body })
	end
	Local.Buttons(Body, 362, `Begin set`, function() Local.Begin() end, function() Local.Leave() end)
	Local.Mode(`Card`)
end

-- three skippable first-time cards
function Local.Tutorial(OnDone: () -> ())
	local Pages = {
		{ Title = `THE RING AND THE MARK`; Art = `TrainRing`; Text = `A ring shrinks onto the brass mark. Press when it lies on the mark.\n{keysText()}.\nPerfect, Great or Good builds your combo, and every rep moves your body.` };
		{ Title = `FEINTS AND HOLDS`; Art = `TrainRingFake`; Text = `A cracked ring is a feint: let it pass, or your combo breaks.\nA leather-bound HOLD ring is a heavy rep: press on the mark and keep holding until the gear stops. It's worth double.` };
		{ Title = `BUILD YOUR BODY`; Art = `TrainIconArms`; Text = `Sets give that area XP. At levels 5 and 10 it changes, live.\nThe first set of each area each day is Fresh (×2). Sore muscles give less, so rotate arms, torso and legs.` };
	}
	local I = 1
	local function show()
		local P = Pages[I]
		local _, Body = Local.Card(600, 400, P.Title)
		img(P.Art, { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 0); Size = UDim2.fromOffset(130, 130); Parent = Body })
		text({ Text = P.Text; Font = Fonts.Body; TextSize = 21; TextColor3 = BONE; TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Center;
			TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(0, 142); Size = UDim2.new(1, 0, 0, 140); Parent = Body })
		text({ Text = `{I} / {#Pages}`; Font = Fonts.Title; TextSize = 17; TextColor3 = DIM; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 270); Size = UDim2.new(1, 0, 0, 20); Parent = Body })
		local Kind = inputKind()
		local _, Next = Kit.Button({ text = (if I < #Pages then `Next` else `Got it`) .. (if Kind == `Gamepad` then ` ({Kit.KeyName(`ButtonA`)})` elseif Kind == `Touch` then `` else ` (Space)`); style = `gold`;
			onClick = function() if I < #Pages then I += 1 show() else OnDone() end end; Position = UDim2.fromOffset(0, 300); Size = UDim2.fromOffset(250, 50); Parent = Body })
		Kit.Button({ text = `Skip`; style = `ghost`; onClick = OnDone; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 300); Size = UDim2.fromOffset(150, 50); Parent = Body })
		Ui.CardButtons = { Main = function() if I < #Pages then I += 1 show() else OnDone() end end; Leave = OnDone }
		pcall(function() if Kind == `Gamepad` then GuiService.SelectedObject = Next.Root end end)
	end
	show()
	Local.Mode(`Card`)
end

function Local.ResultCard(R)
	local Def = Config.Stations[Session.Station]
	local _, Body = Local.Card(560, 500, if R.Ok then (if R.Ended then `SPENT!` else `SET COMPLETE`) else `SET REFUSED`)
	if not R.Ok then
		text({ Text = R.Message or `That set didn't count.`; Font = Fonts.Body; TextSize = 22; TextColor3 = BONE; TextWrapped = true; Size = UDim2.new(1, 0, 0, 80); Parent = Body })
		Local.Buttons(Body, 392, `Again`, function() Local.Begin() end, function() Local.Leave() end)
		return
	end
	-- the counts, one stamp each
	local X = 0
	for _, K in { `Perfect`, `Great`, `Good`, `Miss` } do
		local N = (R.Counts[K] or 0) + (if K == `Miss` then (R.Counts.Feint or 0) + (R.Counts.Stray or 0) else 0)
		local F = Instance.new(`Frame`)
		F.BackgroundTransparency = 1
		F.Position = UDim2.fromOffset(X, 0)
		F.Size = UDim2.fromOffset(124, 96)
		F.Parent = Body
		img(RATE_ART[K], { AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 0); Size = UDim2.fromOffset(52, 52); Parent = F }, RATE_COLOR[K])
		text({ Text = `{N}`; Font = Fonts.Title; TextSize = 26; TextColor3 = RATE_COLOR[K]; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 52); Size = UDim2.new(1, 0, 0, 28); Parent = F })
		text({ Text = string.upper(K); Font = Fonts.Title; TextSize = 14; TextColor3 = DIM; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 78); Size = UDim2.new(1, 0, 0, 16); Parent = F })
		X += 128
	end
	local Y = 108
	Local.Row(Body, Y, `Best combo`, `{R.BestCombo}`, GOLD)
	Local.Row(Body, Y + 28, `Score`, `{R.Score}`)
	local Bits = { `{R.Base} base` }
	if R.Fresh then table.insert(Bits, `Fresh ×{Config.FreshMult}`) end
	if R.StreakBonus > 0 then table.insert(Bits, `streak +{pct(R.StreakBonus)}`) end
	if R.SoreMult < 0.995 then table.insert(Bits, `sore ×{string.format(`%.2f`, R.SoreMult)}`) end
	if R.Burnout then table.insert(Bits, `burnout ×{Config.Burnout.Xp}`) end
	local XpL = Local.Row(Body, Y + 56, `{Def.Area} XP`, `+0`, GOLD)
	text({ Text = table.concat(Bits, `  ·  `) .. (if R.Capped then `  ·  daily cap reached` else ``); Font = Fonts.Body; TextSize = 17; TextColor3 = DIM;
		Position = UDim2.fromOffset(0, Y + 84); Size = UDim2.new(1, 0, 0, 22); Parent = Body })
	local A = R.State and R.State.Areas[R.Area]
	if A then
		text({ Text = `Level {R.Level}` .. (if R.Level > R.OldLevel then `  (up from {R.OldLevel})` else ``); Font = Fonts.Title; TextSize = 20; TextColor3 = if R.Level > R.OldLevel then GOLD else BONE;
			Position = UDim2.fromOffset(0, Y + 114); Size = UDim2.new(1, 0, 0, 24); Parent = Body })
		local _, B = Kit.Bar({ color = BRASS; caption = `{A.Xp} / {A.ToNext}`; height = 22; Position = UDim2.fromOffset(0, Y + 142); Size = UDim2.new(1, 0, 0, 22); Parent = Body })
		B:Set(0)
		task.delay(0.25, function() B:Set(math.clamp(A.Xp / math.max(1, A.ToNext), 0, 1)) end)
	end
	if R.Streak and R.StreakUp then
		Local.Row(Body, Y + 174, `Training streak`, `{R.Streak} day{if R.Streak == 1 then `` else `s`}` .. (if R.Yen then `  ·  +{R.Yen} Yen` else ``), GOLD)
	end
	if R.NewBest then
		local Stamp = img(`TrainBadgeBest`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(1, -56, 0, 318); Size = UDim2.fromOffset(92, 92); ZIndex = 12; Parent = Body }, GOLD)
		local Word = text({ Text = `NEW BEST`; Font = Fonts.Title; TextSize = 18; TextColor3 = GOLD; TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0);
			Position = UDim2.new(1, -56, 0, 362); Size = UDim2.fromOffset(120, 22); ZIndex = 12; Parent = Body })
		if not reduced() then
			local S = Instance.new(`UIScale`) S.Scale = 1.6 S.Parent = Stamp
			task.delay(0.5, function() tween(S, 0.3, { Scale = 1 }, Enum.EasingStyle.Back) Kit.PlaySound(`Stamp`, 0.8, 1.1) end)
		end
		Local.Sweep(Stamp)
		_ = Word
	end
	-- count the XP up
	task.spawn(function()
		local N = R.Xp
		local T0 = os.clock()
		while os.clock() - T0 < 0.8 and XpL.Parent do
			XpL.Text = `+{math.floor(N * (os.clock() - T0) / 0.8)}`
			task.wait()
		end
		if XpL.Parent then XpL.Text = `+{N}` end
	end)
	Local.Buttons(Body, 402, `Again`, function() Local.Begin() end, function() Local.Leave() end)
end

---| modes |---

function Local.Mode(M: string)
	if not Session then return end
	Session.Mode = M
	local Set = M == `Set`
	Ui.Gauge.Visible = Set
	Ui.Key.Visible = Set
	Ui.Hint.Visible = Set
	Ui.ComboRoot.Visible = Set
	Ui.Rate.Visible = Set
	Ui.TouchPress.Visible = Set and inputKind() == `Touch`
	Ui.CardLayer.Visible = M == `Card`
	Ui.Gauge.Position = if M == `Card` then UDim2.new(0.74, 0, 0.5, 0) else UDim2.new(0.66, 0, 0.47, 0)
	Ui.GaugeScale.Scale = if M == `Card` then 0.82 else 1
	Ui.LeaveApi:SetText(leaveText())
	Ui.KeyText.Text = keysText()
end

---| the set |---

function Local.Begin()
	if not Session or SetRun or Session.Busy then return end
	Session.Busy = true
	Local.ClearCards()
	local R = Remotes.Begin:InvokeServer()
	Session.Busy = false
	if not Session then return end
	if not (R and R.Ok) then
		Local.ResultCard({ Ok = false; Message = R and R.Message or `Couldn't start the set.` })
		return
	end
	local PlanT = Config.Plan(R.Seed, R.Level)
	local Start = os.clock()
	SetRun = { Plan = PlanT; Level = R.Level; Tier = Config.TierFor(R.Level); Start = Start; Presses = {}; Held = nil;
		Rings = {}; Next = 1; Combo = 0; Results = {}; Stamina = 100; Done = false; Area = R.Area }
	Local.Mode(`Set`)
	Ui.ComboNum.Text = ``
	Ui.ComboWord.Text = ``
	Ui.ComboHeat = 0
	Ui.ComboFlame.ImageTransparency = 1
	Ui.PlateReps.Text = `Rep 0 / {#PlanT.Rings}`
	Ui.Stamina.Root.Visible = PlanT.Stamina
	Ui.Stamina:Set(1, true)
	if PlanT.Burnout then
		Local.Callout(`BURNOUT`, CRIMSON, `as many as you can before your stamina runs out`)
	end
	-- the 3-2-1
	task.spawn(function()
		for I = 3, 1, -1 do
			if not SetRun then return end
			Ui.Count.Text = tostring(I)
			Ui.Count.TextTransparency = 0
			Ui.Count.TextColor3 = GOLD
			Kit.PlaySound(`Tick`, 1, 1 + (3 - I) * 0.08)
			if not reduced() then
				local S = Ui.Count:FindFirstChildOfClass(`UIScale`) or Instance.new(`UIScale`)
				S.Parent = Ui.Count
				S.Scale = 1.5
				tween(S, 0.35, { Scale = 1 }, Enum.EasingStyle.Back)
			end
			tween(Ui.Count, 0.9, { TextTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
			task.wait(1)
		end
	end)
	Local.Run()
end

function Local.Callout(Big: string, Color: Color3, Small: string?)
	local L = text({ Text = Big; Font = Fonts.Title; TextSize = 54; TextColor3 = Color; TextXAlignment = Enum.TextXAlignment.Center;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.3, 0); Size = UDim2.fromOffset(700, 64); ZIndex = 25; Parent = Ui.Root })
	L.TextStrokeTransparency = 0.3
	if Small then
		text({ Text = Small; Font = Fonts.Body; TextSize = 20; TextColor3 = BONE; TextXAlignment = Enum.TextXAlignment.Center;
			Position = UDim2.new(0, 0, 1, 0); Size = UDim2.new(1, 0, 0, 24); ZIndex = 25; Parent = L })
	end
	task.delay(2.0, function() Kit.FadeOut(L, 0.4) task.delay(0.45, function() L:Destroy() end) end)
end

-- one ring sprite (plus its trail of fading echoes)
function Local.NewRing(Ring)
	local Name = if Ring.Kind == `Fake` then `TrainRingFake` elseif Ring.Kind == `Heavy` then `TrainRingHeavy` else `TrainRing`
	local Tint = if Ring.Kind == `Fake` then Color3.fromRGB(130, 124, 126) elseif Ring.Kind == `Heavy` then CRIMSON else GOLD
	local function one(Tr: number)
		local I = img(Name, { Name = `Ring`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
			Size = UDim2.fromScale(1, 1); ImageTransparency = Tr; ZIndex = 5; Parent = Ui.RingLayer }, Tint)
		if I:GetAttribute(`StandIn`) then
			-- a crisp stroke ring until the art is in
			I.Image = ``
			local Cr = Instance.new(`UICorner`) Cr.CornerRadius = UDim.new(0.5, 0) Cr.Parent = I
			local St = Instance.new(`UIStroke`) St.Color = Tint St.Thickness = if Ring.Kind == `Heavy` then 9 else 5 St.Transparency = Tr St.Parent = I
			if Ring.Kind == `Fake` then St.LineJoinMode = Enum.LineJoinMode.Miter St.Thickness = 3 end
		end
		return I
	end
	local Main = one(0)
	local Trail = {}
	if not reduced() then
		for K = 1, 3 do table.insert(Trail, one(0.55 + K * 0.12)) end
	end
	local Label
	if Ring.Kind == `Heavy` then
		Label = text({ Text = `HOLD`; Font = Fonts.Title; TextSize = 18; TextColor3 = CRIMSON; TextXAlignment = Enum.TextXAlignment.Center;
			AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromOffset(100, 22); ZIndex = 6; Parent = Main })
	end
	return { Ring = Ring; Main = Main; Trail = Trail; Label = Label; Broken = false }
end

local function setRingSize(I: GuiObject, R: number)
	-- R: the ring's radius as a share of the gauge -> the sprite size
	local S = if I:GetAttribute(`StandIn`) then R * 2 else R / RING_R
	I.Size = UDim2.fromScale(S, S)
end

function Local.Run()
	local Run = SetRun
	local Tier = Run.Tier
	local Approach = Tier.Approach
	local Conn
	local LastFlicker = 0
	Conn = RunService.RenderStepped:Connect(function()
		if SetRun ~= Run or not Session then Conn:Disconnect() return end
		local T = os.clock() - Run.Start
		-- spawn rings as their travel begins
		while Run.Next <= #Run.Plan.Rings and Run.Plan.Rings[Run.Next].T - Approach - 0.05 <= T do
			local Ring = Run.Plan.Rings[Run.Next]
			Ring.I = Run.Next
			table.insert(Run.Rings, Local.NewRing(Ring))
			Run.Next += 1
		end
		local Lead = nil
		for Idx = #Run.Rings, 1, -1 do
			local V = Run.Rings[Idx]
			local P = 1 - (V.Ring.T - T) / Approach          -- 0 at the bezel, 1 on the mark
			local R = START_R + (MARK_R - START_R) * P
			if V.Ring.Kind == `Fake` and P >= Config.FakeBreakAt and not V.Broken then
				V.Broken = true
				Local.Shatter(V)
			end
			if not V.Broken then
				setRingSize(V.Main, math.max(0.02, R))
				V.Main.ImageTransparency = if P < 0.1 then 1 - P * 10 else 0
				for K, E in V.Trail do
					local Pk = P - K * 0.045
					setRingSize(E, math.max(0.02, START_R + (MARK_R - START_R) * Pk))
					E.ImageTransparency = math.clamp(0.5 + K * 0.15 + (if Pk < 0.1 then 1 - Pk * 10 else 0), 0, 1)
				end
				if not Lead and not V.Done then Lead = P end
			end
			-- past its window with no press: a miss (feints just fade)
			if not V.Done and T > V.Ring.T + Tier.Good + 0.02 then
				V.Done = true
				if V.Ring.Kind ~= `Fake` and not V.Hit then Local.Rated(V, `Miss`) end
				Local.FadeRing(V)
				table.remove(Run.Rings, Idx)
			end
		end
		-- the needle sweeps with the leading ring, and rests with a gentle sway between rings
		if Ui.Needle.Visible then
			local Target = if Lead then -120 + 240 * math.clamp(Lead, 0, 1.08) else -120 + math.sin(T * 1.3) * 4
			Ui.Needle.Rotation += (Target - Ui.Needle.Rotation) * (if reduced() then 1 else 0.35)
		end
		-- HOLD: the gear grinds and the bar fills while you hold
		if Run.Held then
			local H = Run.Held
			local F = math.clamp((T - H.T) / math.max(0.05, H.Hold), 0, 1)
			Ui.HoldBar:Set(F, if F >= 1 then `RELEASE` else `HOLD`)
			Ui.Gear.Rotation += (if reduced() then 2 else 9) * (1 - F * 0.6)
			if F >= 1 and not H.Full then
				H.Full = true
				Kit.PlaySound(`Confirm`, 0.6, 1.2)
				Ui.HoldBar:SetColor(GOLD)
			end
		end
		-- candles gutter (tier III+): the gauge dims for a moment
		if Tier.Flicker and not reduced() and T - LastFlicker > 4 and math.random() < 0.01 then
			LastFlicker = T
			Ui.Dim.BackgroundTransparency = 0.45
			tween(Ui.Dim, 0.9, { BackgroundTransparency = 1 }, Enum.EasingStyle.Sine)
		end
		-- the set ends after the last ring's window (or when stamina runs out)
		if (Run.Next > #Run.Plan.Rings and #Run.Rings == 0 and not Run.Held) or Run.Spent then
			Conn:Disconnect()
			Local.Finish(Run)
		end
	end)
end

function Local.FadeRing(V)
	for _, I in { V.Main, table.unpack(V.Trail) } do
		local St = I:FindFirstChildOfClass(`UIStroke`)
		if St then tween(St, 0.2, { Transparency = 1 }) end
		tween(I, 0.2, { ImageTransparency = 1 })
		task.delay(0.22, function() I:Destroy() end)
	end
end

function Local.Shatter(V)
	-- the feint cracks apart: shards fly off the ring
	local C0 = Local.GaugeCentre()
	local Rpx = (START_R + (MARK_R - START_R) * Config.FakeBreakAt) * GAUGE
	for K = 1, (if reduced() then 3 else 9) do
		local A = K / 9 * math.pi * 2
		Local.Particles(C0 + Vector2.new(math.cos(A), math.sin(A)) * Rpx, 1, { Image = Theme.Images.Pip; Color = Color3.fromRGB(140, 134, 136); MinSpeed = 60; MaxSpeed = 140; Life = 0.45; MinSize = 10; MaxSize = 16; Grow = 0.2 })
	end
	Local.FadeRing(V)
	Kit.PlaySound(`Reject`, 0.35, 1.4)
end

-- a press (keyboard, pad, click or tap)
function Local.Press(Down: boolean)
	if not SetRun then
		if Down and Session and Session.Mode == `Card` and Ui.CardButtons then Ui.CardButtons.Main() end
		return
	end
	local Run = SetRun
	local T = os.clock() - Run.Start
	if not Down then
		if Run.Held then
			local H = Run.Held
			Run.Held = nil
			H.Entry.R = T
			Ui.Hold.Visible = false
			Ui.Key.Visible = true
			if T - H.T < H.Hold - 0.05 then
				Local.Rated(H.V, `Miss`)
				Local.Callout(`LET GO TOO SOON`, Color3.fromRGB(200, 120, 110))
			else
				Local.Rated(H.V, H.Kind)
			end
		end
		return
	end
	if Run.Held then return end
	if #Run.Presses > 0 and T - Run.Presses[#Run.Presses].T < Config.Check.MinPressGap then return end
	local Entry = { T = T }
	table.insert(Run.Presses, Entry)
	-- the nearest live ring inside its Good window takes the press
	local Best, BestD = nil, nil
	for _, V in Run.Rings do
		if not V.Done and not V.Hit then
			local D = T - V.Ring.T
			if math.abs(D) <= Run.Tier.Good and (BestD == nil or math.abs(D) < math.abs(BestD)) then Best, BestD = V, D end
		end
	end
	if not Best then
		Local.Rated(nil, `Stray`)
		return
	end
	Best.Hit = true
	if Best.Ring.Kind == `Fake` then
		Best.Done = true
		Local.Rated(Best, `Feint`)
		if not Best.Broken then Best.Broken = true Local.Shatter(Best) end
		return
	end
	local A = math.abs(BestD)
	local Kind = if A <= Run.Tier.Perfect then `Perfect` elseif A <= Run.Tier.Great then `Great` else `Good`
	Best.Done = true
	Local.FadeRing(Best)
	for I, V in Run.Rings do if V == Best then table.remove(Run.Rings, I) break end end
	if Best.Ring.Kind == `Heavy` then
		Run.Held = { T = T; Hold = Best.Ring.Hold; V = Best; Kind = Kind; Entry = Entry }
		Ui.Hold.Visible = true
		Ui.Key.Visible = false
		Ui.HoldBar:SetColor(CRIMSON)
		Ui.HoldBar:Set(0, `HOLD`)
		Local.Rep(Kind, true)
		return
	end
	Local.Rated(Best, Kind)
end

-- feedback for one rated ring (or a stray press)
function Local.Rated(V, Kind: string)
	local Run = SetRun
	if not Run then return end
	local Good = Kind == `Perfect` or Kind == `Great` or Kind == `Good`
	if Good then
		Run.Combo += 1
		if not (V and V.Ring.Kind == `Heavy`) then Local.Rep(Kind, false) end
	else
		if Run.Combo >= 5 then Kit.PlaySound(`Reject`, 0.5, 0.9) end
		Run.Combo = 0
	end
	-- the reps counter, the stamina, the combo
	local Done = 0
	for _, R in Run.Results do if R ~= `Stray` then Done += 1 end end
	table.insert(Run.Results, Kind)
	if Kind ~= `Stray` then Done += 1 end
	Ui.PlateReps.Text = `Rep {math.min(Done, #Run.Plan.Rings)} / {#Run.Plan.Rings}`
	if Run.Plan.Stamina then
		local Rules = if Run.Plan.Burnout then Config.Burnout.Stamina else Config.SetStamina
		Run.Stamina = math.min(100, Run.Stamina + (Rules[Kind] or 0))
		Ui.Stamina:Set(math.max(0, Run.Stamina) / 100)
		if Run.Stamina <= 0 and not Run.Spent then
			Run.Spent = true
			Local.Callout(`SPENT`, CRIMSON)
		end
	end
	Local.Combo(Run.Combo)
	Local.Stamp(Kind)
end

function Local.Combo(N: number)
	if N < 2 then
		if Ui.ComboNum.Text ~= `` then
			tween(Ui.ComboNum, 0.25, { TextTransparency = 1 })
			tween(Ui.ComboFlame, 0.25, { ImageTransparency = 1 })
			task.delay(0.26, function() if SetRun and SetRun.Combo < 2 then Ui.ComboNum.Text = `` Ui.ComboWord.Text = `` Ui.ComboNum.TextTransparency = 0 end end)
		end
		Ui.ComboHeat = 0
		return
	end
	Ui.ComboNum.Text = `×{N}`
	Ui.ComboNum.TextTransparency = 0
	Ui.ComboWord.Text = if N >= 20 then `UNSTOPPABLE` elseif N >= 10 then `ON FIRE` else `COMBO`
	Ui.ComboHeat = math.clamp((N - 3) / 17, 0, 1)
	Ui.ComboNum.TextColor3 = GOLD:Lerp(EMBER, Ui.ComboHeat * 0.6)
	if Ui.ComboFlame.ImageTransparency > 0.98 then Ui.ComboFlame.ImageTransparency = 0.6 end
	if not reduced() then
		Ui.ComboScale.Scale = 1.25 + 0.15 * Ui.ComboHeat
		tween(Ui.ComboScale, 0.22, { Scale = 1 }, Enum.EasingStyle.Back)
		if N >= 10 then   -- long streaks shake the number
			task.spawn(function()
				for _ = 1, 5 do
					Ui.ComboNum.Position = UDim2.new(0.5, math.random(-3, 3), 0, math.random(-2, 2))
					task.wait(0.03)
				end
				Ui.ComboNum.Position = UDim2.fromScale(0.5, 0)
			end)
		end
	end
	if N % 10 == 0 then Kit.PlaySound(`Confirm`, 0.8, 1 + math.min(N, 40) / 80) end
end

function Local.Stamp(Kind: string)
	local Col = RATE_COLOR[Kind]
	Ui.RateMark.Image = art(RATE_ART[Kind]) or STAND_IN[RATE_ART[Kind]]
	if Ui.RateMark:GetAttribute(`StandIn`) then Ui.RateMark.ImageColor3 = Col end
	Ui.RateWord.Text = RATE_WORD[Kind]
	Ui.RateWord.TextColor3 = Col
	Ui.RateWord.TextTransparency = 0
	Ui.RateMark.ImageTransparency = 0
	if not reduced() then
		-- stamp in: big, then a squash, then settle
		Ui.RateScale.Scale = 1.55
		local Tw = tween(Ui.RateScale, 0.09, { Scale = 0.9 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		Tw.Completed:Connect(function() tween(Ui.RateScale, 0.16, { Scale = 1 }, Enum.EasingStyle.Back) end)
		Ui.RateWord.Size = UDim2.fromOffset(240, 34)
		tween(Ui.RateWord, 0.2, { Size = UDim2.fromOffset(200, 44) }, Enum.EasingStyle.Back)
	end
	local Token = (Ui.RateToken or 0) + 1
	Ui.RateToken = Token
	task.delay(0.55, function()
		if Ui.RateToken ~= Token then return end
		tween(Ui.RateWord, 0.3, { TextTransparency = 1 })
		tween(Ui.RateMark, 0.3, { ImageTransparency = 1 })
	end)
	-- the mark flashes in the rating's colour
	Ui.MarkGlow.ImageColor3 = Col
	Ui.MarkGlow.ImageTransparency = if Kind == `Perfect` then 0 elseif Kind == `Great` then 0.25 elseif Kind == `Good` then 0.5 else 0.75
	tween(Ui.MarkGlow, 0.4, { ImageTransparency = 1 }, Enum.EasingStyle.Quad)
	if Kind == `Perfect` then
		local C0 = Local.GaugeCentre()
		local Rpx = MARK_R * GAUGE
		for K = 1, 14 do
			local A = K / 14 * math.pi * 2
			Local.Particles(C0 + Vector2.new(math.cos(A), math.sin(A)) * Rpx, 1, { Color = Color3.fromRGB(255, 214, 120); MinSpeed = 120; MaxSpeed = 260; Life = 0.5; MinSize = 6; MaxSize = 12; Grow = 0.2 })
		end
		Local.Particles(C0, 6, { Image = Theme.Images.Glow; Color = CHALK; MinSpeed = 30; MaxSpeed = 90; Life = 0.9; MinSize = 40; MaxSize = 70; Grow = 1.6; Rise = -40 })
	end
end

-- a rep: the animation, the sound, a camera bump, chalk dust on Perfect
function Local.Rep(Kind: string, Heavy: boolean)
	local S = Session
	if not S then return end
	local Pitch = if Kind == `Perfect` then 1.18 elseif Kind == `Great` then 1.06 else 0.94
	Kit.PlaySound(`Stamp`, if Heavy then 1.0 else 0.75, Pitch * (if Heavy then 0.8 else 1))
	if Kind == `Perfect` then Kit.PlaySound(`Confirm`, 0.5, 1.35) end
	Local.PlayRep()
	if not reduced() then S.Bump = (if Kind == `Perfect` then 0.22 elseif Kind == `Great` then 0.14 else 0.08) * shakeScale() end
	if Kind == `Perfect` then Local.ChalkDust() end
end

function Local.ChalkDust()
	local Char = Player.Character
	if not Char then return end
	local Ok, Fx = pcall(function() return require(script.Parent.Parent:WaitForChild(`Fx`)) end)
	if not Ok then return end
	local Def = Config.Stations[Session.Station]
	for _, N in Config.AreaInfo[Def.Area].Parts do
		local P = Char:FindFirstChild(N) :: BasePart?
		if P then
			local At = if Def.Area == `Legs` then P.Position - P.CFrame.UpVector * 0.9 else P.Position - P.CFrame.UpVector * 0.9
			pcall(Fx.Burst, At, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(228, 226, 216); Count = 5; Size = 0.5;
				Speed = NumberRange.new(0.8, 2.2); Lifetime = NumberRange.new(0.5, 0.9); LightEmission = 0; Accel = Vector3.new(0, -1.5, 0); Spread = 70 })
		end
	end
end

function Local.Finish(Run)
	if SetRun ~= Run then return end
	SetRun = nil
	Ui.Hold.Visible = false
	for _, V in Run.Rings do Local.FadeRing(V) end
	local Presses = {}
	for _, P in Run.Presses do table.insert(Presses, { T = P.T; R = P.R }) end
	-- a hold still down when the set ends: count its release now
	if RunService:IsStudio() then   -- (Studio tests) each press against its nearest ring, for the play-test log
		local Off = {}
		for _, P in Presses do
			local Best
			for _, Ring in Run.Plan.Rings do if not Best or math.abs(P.T - Ring.T) < math.abs(Best) then Best = P.T - Ring.T end end
			table.insert(Off, string.format(`%.3f`, Best or 0))
		end
		Player:SetAttribute(`NHTrainLast`, table.concat(Off, `,`))
	end
	local R = Remotes.Submit:InvokeServer(Presses)
	if not Session then return end
	R = R or { Ok = false; Message = `No answer from the school.` }
	if R.Ok and R.State then Session.State = R.State end
	Local.Mode(`Card`)
	Local.ResultCard(R)
	if R.Ok and R.State then
		Local.ApplyState(R.State)
		Local.SetBar(R.State.Areas[R.Area], true)
	end
	if R.Ok and R.StepUp then task.delay(0.4, function() Local.StepUp(R.StepUp, true) end) end
end

---| the milestone: a body step-up |---

local STEP_NUMERAL = { `I`, `II`, `III`, `IV` }
function Local.StepUp(D, Mine: boolean)
	if Mine and Ui.Root then
		-- the big banner: a plate that unfurls, the area crest stamps in, embers rise
		local B = Instance.new(`Frame`)
		B.Name = `StepBanner`
		B.AnchorPoint = Vector2.new(0.5, 0.5)
		B.Position = UDim2.fromScale(0.66, 0.72)
		B.Size = UDim2.fromOffset(760, 150)
		B.BackgroundTransparency = 1
		B.ZIndex = 40
		B.Parent = Ui.Root
		local PlateArt = art(`TrainPlate`)
		if PlateArt then
			local Bg = Instance.new(`ImageLabel`) Bg.BackgroundTransparency = 1 Bg.Image = PlateArt Bg.ScaleType = Enum.ScaleType.Slice
			Bg.SliceCenter = Rect.new(64, 64, 704, 128) Bg.SliceScale = 0.5 Bg.Size = UDim2.fromScale(1, 1) Bg.ZIndex = 40 Bg.Parent = B
		else
			Kit.Decorate(B, { ornamentScale = 0.6, bgTransparency = 0.05, frameColor = GOLD })
		end
		local Icon = img(Config.AreaInfo[D.Area].Icon, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0, 80, 0.5, 0); Size = UDim2.fromOffset(124, 124); ZIndex = 42; Parent = B })
		local T1 = text({ Text = `YOUR {string.upper(D.Area)} GREW`; Font = Fonts.Title; TextSize = 40; TextColor3 = GOLD; Position = UDim2.fromOffset(160, 26); Size = UDim2.fromOffset(580, 48); ZIndex = 42; Parent = B })
		Kit.Emboss(T1, Color3.fromRGB(150, 112, 50))
		text({ Text = `Step {STEP_NUMERAL[D.Step] or D.Step}  ·  {D.Body}`; Font = Fonts.Body; TextSize = 24; TextColor3 = BONE; Position = UDim2.fromOffset(160, 82); Size = UDim2.fromOffset(580, 32); ZIndex = 42; Parent = B })
		local S = Instance.new(`UIScale`) S.Parent = B
		if not reduced() then
			S.Scale = 0.2
			tween(S, 0.45, { Scale = 1 }, Enum.EasingStyle.Back)
			local IS = Instance.new(`UIScale`) IS.Scale = 1.8 IS.Parent = Icon
			task.delay(0.3, function() tween(IS, 0.3, { Scale = 1 }, Enum.EasingStyle.Back) Kit.PlaySound(`Stamp`, 1, 0.9) end)
			task.spawn(function()
				for _ = 1, 10 do
					if not B.Parent then return end
					local P = B.AbsolutePosition + B.AbsoluteSize * Vector2.new(math.random(), 1) - Ui.Fx.AbsolutePosition
					local Sc = Gui and Gui:FindFirstChild(`NHAutoScale`) :: UIScale?
					Local.Particles(P / (if Sc then Sc.Scale else 1), 3, { Image = Theme.Images.Glow; Color = Color3.fromRGB(255, 150, 70); MinSpeed = 10; MaxSpeed = 50; Rise = -180; Life = 1.2; MinSize = 6; MaxSize = 12; Grow = 0.3 })
					task.wait(0.12)
				end
			end)
		end
		Kit.FadeIn(B, 0.25)
		Local.Sweep(Icon)
		pcall(function()
			local Sound = Instance.new(`Sound`)
			Sound.SoundId = `rbxassetid://9113584435`   -- the brass hand bell (Moments' Bell)
			Sound.Volume = 0.32
			Sound.Parent = workspace.CurrentCamera
			Sound:Play()
			task.delay(3, function() Sound:Destroy() end)
		end)
		task.delay(3.6, function() Kit.FadeOut(B, 0.5) task.delay(0.55, function() B:Destroy() end) end)
	end
	-- in the world (everyone near sees it): the flex and an ember and chalk burst on that area
	local P = Players:GetPlayerByUserId(D.UserId or Player.UserId)
	local Char = P and P.Character
	if not Char then return end
	-- your own: step off the exercise pose for the flex (not while hanging from the bar), then back to it
	local S = Session
	local Def = S and Config.Stations[S.Station]
	if P == Player and S and Def and not Def.Hang and not reduced() then
		if S.Idle then S.Idle:Stop(0.2) end
		if S.Rep then S.Rep:Stop(0.2) end
		task.delay(1.9, function()
			if Session ~= S then return end
			if S.IdleFromRep and S.Rep then S.Rep:Play(0.25, 1, 0) S.Rep.TimePosition = 0
			elseif S.Idle then S.Idle:Play(0.25) end
		end)
		task.wait(0.2)
	elseif P == Player and Def and Def.Hang then
		Local.Flex(Char, D.Area, true, true)   -- the burst only: your hands stay on the bar
		return
	end
	Local.Flex(Char, D.Area, P == Player)
end

function Local.Flex(Char: Model, Area: string, Mine: boolean, BurstOnly: boolean?)
	local Ok, Fx = pcall(function() return require(script.Parent.Parent:WaitForChild(`Fx`)) end)
	if Ok then
		for _, N in Config.AreaInfo[Area].Parts do
			local P = Char:FindFirstChild(N) :: BasePart?
			if P and (Mine or Fx.Near(P.Position, 80)) then
				pcall(Fx.Burst, P.Position, { Texture = Fx.Tex.Ember; Color = Color3.fromRGB(255, 150, 70); Count = 18; Size = 0.35; Speed = NumberRange.new(2, 5);
					Lifetime = NumberRange.new(0.8, 1.5); Accel = Vector3.new(0, 3, 0); Spread = 180 })
				pcall(Fx.Burst, P.Position, { Texture = Fx.Tex.Smoke; Flipbook = `Grid4x4`; Color = Color3.fromRGB(228, 226, 216); Count = 8; Size = 0.9;
					Speed = NumberRange.new(1, 3); Lifetime = NumberRange.new(0.7, 1.2); LightEmission = 0; Spread = 180 })
				pcall(Fx.Light, P.Position, Color3.fromRGB(255, 170, 90), 1.6, 10, 1.2)
			end
		end
	end
	if reduced() or BurstOnly or Char:GetAttribute(`NHTraining`) == `PullUp` then return end
	-- the flex: both arms thrown up and out for a held beat, then back. Drawn locally on each client over whatever
	-- is playing (the shoulders' Transform, set after the animator each step), so everyone near sees it.
	local Torso = Char:FindFirstChild(`Torso`)
	local RS = Torso and Torso:FindFirstChild(`Right Shoulder`) :: Motor6D?
	local LS = Torso and Torso:FindFirstChild(`Left Shoulder`) :: Motor6D?
	if not (RS and LS) or Char:GetAttribute(`NHFlexing`) then return end
	Char:SetAttribute(`NHFlexing`, true)
	local RUp = CFrame.Angles(math.rad(-120), 0, math.rad(8))
	local LUp = CFrame.Angles(math.rad(-120), 0, math.rad(-8))
	local T0 = os.clock()
	local Conn
	Conn = RunService.PreSimulation:Connect(function()
		local T = os.clock() - T0
		if T > 1.7 or not Char.Parent then
			Conn:Disconnect()
			Char:SetAttribute(`NHFlexing`, nil)
			return
		end
		local W = if T < 0.25 then T / 0.25 elseif T > 1.4 then 1 - (T - 1.4) / 0.3 else 1
		W = math.sin(math.clamp(W, 0, 1) * math.pi / 2)
		RS.Transform = RS.Transform:Lerp(RUp, W)
		LS.Transform = LS.Transform:Lerp(LUp, W)
	end)
end

---| the station: seated, animated, framed |---

function Local.Track(Id: number?, Looped: boolean, Priority: Enum.AnimationPriority): AnimationTrack?
	if not Id then return nil end
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return nil end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{Id}`
	local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return nil end
	T.Looped = Looped
	T.Priority = Priority
	return T
end

function Local.PlayRep()
	local S = Session
	if not (S and S.Rep) then return end
	local Gap = if SetRun then SetRun.Tier.Gap else 1
	local Speed = if S.Rep.Length > 0 then math.max(1, S.Rep.Length / (Gap * 0.92)) else 1
	if S.IdleFromRep then
		S.Rep.TimePosition = 0
		S.Rep:AdjustSpeed(Speed)
		S.RepUntil = os.clock() + S.Rep.Length / Speed
	else
		S.Rep:Play(0.08, 1, Speed)
	end
end

function Local.Enter(D)
	if Session then Local.Teardown() end
	local Def = Config.Stations[D.Station]
	if not Def then return end
	if not Gui then Local.Build() end
	Session = { Station = D.Station; State = D.State; Mode = `Card`; IdleFromRep = Def.IdleFromRep == true }
	local S = Session
	Gui.Enabled = true
	Local.ApplyState(D.State)
	-- animations: the idle loops; the rep plays once per rep
	if Def.IdleFromRep then
		S.Rep = Local.Track(Def.Rep, true, Enum.AnimationPriority.Action2)
		if S.Rep then S.Rep:Play(0.2, 1, 0) end    -- held on its first frame between reps
	else
		S.Idle = Local.Track(Def.Idle, true, Enum.AnimationPriority.Action)
		S.Rep = Local.Track(Def.Rep, false, Enum.AnimationPriority.Action2)
		if S.Idle then S.Idle:Play(0.25) end
	end
	-- no jumping off the station by accident (Space is the press)
	local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
	if Hum then
		S.Hum = Hum
		S.JumpWas = Hum:GetStateEnabled(Enum.HumanoidStateType.Jumping)
		Hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, false)
	end
	ContextActionService:BindActionAtPriority(`NHTrainPress`, function(_, State, Input)
		if UserInputService:GetFocusedTextBox() then return Enum.ContextActionResult.Pass end
		if State == Enum.UserInputState.Begin then Local.Press(true)
		elseif State == Enum.UserInputState.End then Local.Press(false) end
		return Enum.ContextActionResult.Sink
	end, false, 3100, Enum.KeyCode.Space, Enum.KeyCode.ButtonA, Enum.KeyCode.ButtonR2)
	ContextActionService:BindActionAtPriority(`NHTrainLeave`, function(_, State)
		if UserInputService:GetFocusedTextBox() then return Enum.ContextActionResult.Pass end
		if State == Enum.UserInputState.Begin then
			if Session and Session.Mode == `Card` and Ui.CardButtons then Ui.CardButtons.Leave() else Local.Leave() end
		end
		return Enum.ContextActionResult.Sink
	end, false, 3100, Enum.KeyCode.Q, Enum.KeyCode.ButtonB)
	-- clicks and taps on the gauge or the PRESS button
	S.Conns = {}
	for _, B in { Ui.Dial, Ui.TouchPress } do
		table.insert(S.Conns, B.InputBegan:Connect(function(I)
			if I.UserInputType == Enum.UserInputType.MouseButton1 or I.UserInputType == Enum.UserInputType.Touch then Local.Press(true) end
		end))
		table.insert(S.Conns, B.InputEnded:Connect(function(I)
			if I.UserInputType == Enum.UserInputType.MouseButton1 or I.UserInputType == Enum.UserInputType.Touch then Local.Press(false) end
		end))
	end
	-- the sit-up hold: after a rep plays out, stop it on the first frame again
	table.insert(S.Conns, RunService.Heartbeat:Connect(function()
		if S.IdleFromRep and S.Rep and S.RepUntil and os.clock() >= S.RepUntil then
			S.RepUntil = nil
			S.Rep.TimePosition = 0
			S.Rep:AdjustSpeed(0)
		end
	end))
	Local.Camera()
	task.delay(0.9, Local.Settle)
	task.delay(2.2, Local.Settle)
	if D.State and not D.State.Tut then
		Local.Tutorial(function()
			Remotes.Tutorial:FireServer()
			if Session and Session.State then Session.State.Tut = true end
			Local.StartCard()
		end)
	else
		Local.StartCard()
	end
end

-- rest the posed body on the mat (or the hands on the bar): measure, and let the server move the anchored root
function Local.Settle()
	local S = Session
	local Char = Player.Character
	if not (S and Char) then return end
	local Def = Config.Stations[S.Station]
	local Station
	for _, M in game:GetService(`CollectionService`):GetTagged(`NHTrainStation`) do
		if M:GetAttribute(`Station`) == S.Station and (M:GetPivot().Position - Char:GetPivot().Position).Magnitude < 14 then Station = M end
	end
	local Low, High = math.huge, -math.huge
	local Parts = if Def.Hang then { `Left Arm`, `Right Arm` } else { `Torso`, `Left Leg`, `Right Leg`, `Left Arm`, `Right Arm`, `Head` }
	for _, N in Parts do
		local P = Char:FindFirstChild(N) :: BasePart?
		if P then
			local Cf, Sz = P.CFrame, P.Size / 2
			for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
				local V = (Cf * Vector3.new(X * Sz.X, Y * Sz.Y, Z * Sz.Z)).Y
				Low, High = math.min(Low, V), math.max(High, V)
			end end end
		end
	end
	local Dy
	if Def.Hang then
		local Grip = Station and Station:GetAttribute(`GripY`)
		if typeof(Grip) == `number` then Dy = Grip - (High - 0.15) end
	else
		local Floor = Station and Station:GetAttribute(`FloorY`)
		if typeof(Floor) == `number` and Low < math.huge then Dy = Floor - Low end
	end
	if Dy and math.abs(Dy) > 0.04 then Remotes.Settle:FireServer(Dy) end
end

function Local.Camera()
	local S = Session
	if not CameraLease.Take(`Training`, function() return Session == S end, function() end) then return end
	local Cam = workspace.CurrentCamera
	local T0 = os.clock()
	local Bump = 0
	table.insert(S.Conns, RunService.RenderStepped:Connect(function(Dt)
		if Session ~= S or not CameraLease.IsTop(`Training`) then return end
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		if not Root then return end
		local CF = Root.CFrame
		local T = os.clock() - T0
		local Orbit = if reduced() then 0 else math.sin(T * 0.5) * math.rad(5)
		-- from the student's right side, a little in front; the student sits left of centre (the gauge is right)
		local A0 = math.rad(28) + Orbit                -- 28 degrees round from the student's side toward the front
		local SideK = (Config.Stations[S.Station] and Config.Stations[S.Station].CamSide) or 1   -- -1: from the left (a wall or stands on the right)
		local Dir = (CF.RightVector * math.cos(A0) * SideK + CF.LookVector * math.sin(A0)).Unit
		local Torso = Player.Character:FindFirstChild(`Torso`) :: BasePart?
		local Mid = if Torso then Torso.Position else CF.Position
		local CamRight = Dir:Cross(Vector3.yAxis).Unit * -1
		local Want = if S.Mode == `Card` then -2.2 else 3.4   -- the card sits left; in a set the gauge sits right
		S.AimOff = (S.AimOff or Want) + (Want - (S.AimOff or Want)) * math.min(1, Dt * 4)
		local Aim = Mid + CamRight * S.AimOff + Vector3.new(0, 0.3, 0)
		if S.Bump and S.Bump > 0 then Bump = math.max(Bump, S.Bump) S.Bump = 0 end
		Bump = math.max(0, Bump - Dt * 1.4)
		local Dist = 12 - Bump * 3
		do -- never through a wall or the stands: come in to just short of what's in the way
			local Rp = RaycastParams.new()
			Rp.FilterType = Enum.RaycastFilterType.Exclude
			Rp.FilterDescendantsInstances = { Player.Character, workspace:FindFirstChild(`NHTraining`) :: Instance }
			local Hit = workspace:Raycast(Mid + Vector3.new(0, 1, 0), (Dir * Dist + Vector3.new(0, 2.2, 0)), Rp)
			if Hit then Dist = math.max(3.5, (Hit.Position - Mid).Magnitude - 0.6) end
		end
		local Pos = Mid + Dir * Dist + Vector3.new(0, 3.2, 0)
		Cam.CFrame = CFrame.lookAt(Pos, Aim + Vector3.new(0, Bump * 0.5, 0))
		Cam.FieldOfView = 50
	end))
end

function Local.Leave()
	if not Session then return end
	SetRun = nil
	Remotes.Leave:FireServer()
end

function Local.Teardown()
	local S = Session
	Session = nil
	SetRun = nil
	if not S then return end
	for _, C0 in S.Conns or {} do pcall(function() C0:Disconnect() end) end
	ContextActionService:UnbindAction(`NHTrainPress`)
	ContextActionService:UnbindAction(`NHTrainLeave`)
	if S.Idle then S.Idle:Stop(0.3) end
	if S.Rep then S.Rep:Stop(0.3) end
	if S.Hum and S.Hum.Parent then S.Hum:SetStateEnabled(Enum.HumanoidStateType.Jumping, S.JumpWas ~= false) end
	CameraLease.Release(`Training`)
	if Gui then
		Local.ClearCards()
		for _, C0 in Ui.RingLayer:GetChildren() do C0:Destroy() end
		Gui.Enabled = false
	end
end

---| start |---

function Shared.OnStart()
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHTraining`, 60)
		if not F then return end
		Remotes = {
			Get = F:WaitForChild(`Get`); Begin = F:WaitForChild(`Begin`); Submit = F:WaitForChild(`Submit`);
			Leave = F:WaitForChild(`Leave`); Tutorial = F:WaitForChild(`Tutorial`); Settle = F:WaitForChild(`Settle`); Event = F:WaitForChild(`Event`);
		}
		Remotes.Event.OnClientEvent:Connect(function(Kind, D)
			if Kind == `Enter` then Local.Enter(D)
			elseif Kind == `Left` then Local.Teardown()
			elseif Kind == `State` and D then Local.ApplyState(D.State) end
		end)
		-- other students' (and your own) step-ups in the world
		pcall(function()
			local Fx = require(script.Parent.Parent:WaitForChild(`Fx`))
			Fx.On(`TrainStep`, function(D)
				if typeof(D) ~= `table` then return end
				if D.UserId == Player.UserId and not D.Test then return end   -- your own plays from the results (with the banner)
				Local.StepUp(D, D.UserId == Player.UserId)
			end)
		end)
		Player.CharacterAdded:Connect(function() if Session then Local.Teardown() end end)
		pcall(function()
			Kit.InputKindChanged.Event:Connect(function()
				if Session and Ui.KeyText then Ui.KeyText.Text = keysText() Ui.LeaveApi:SetText(leaveText()) Ui.TouchPress.Visible = Session.Mode == `Set` and inputKind() == `Touch` end
			end)
		end)
	end)
end

-- (Studio tests) read-only peeks
function Shared.Debug()
	return { Session = Session and { Station = Session.Station; Mode = Session.Mode } or nil; Running = SetRun ~= nil;
		Presses = SetRun and #SetRun.Presses or 0; Combo = SetRun and SetRun.Combo or 0 }
end
Shared._Local = Local

return Shared
