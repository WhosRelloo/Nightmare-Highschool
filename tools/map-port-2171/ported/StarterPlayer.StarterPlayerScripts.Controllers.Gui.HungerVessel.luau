--[[
	HungerVessel (client). Controllers.Gui.HungerVessel   (Hunger 1.0: docs/Hunger-and-Body-Concept.md, UI 1)
	The hunger meter: a race reliquary on the left cap of the Thornrose health bar (KitHud.Bottom), with an enamel
	plate under it naming the band in the race's own words (Config.Body.Words).

	Reads the player attributes Hunger and HungerBand (set by Services.Features.Body) and its Event remote
	("Ate", "Fed", "Band", "Race"). The server decides every number; this only draws them.

	Layers (bottom to top): Glow (the race colour's halo), Back (the vessel spent), Fill (the contents brimming, shown
	up to the level), Surface (the liquid's lit edge), Motes, Frost (Hungry and Starving), then the Plate.
	  Rise: Human, Priest, Vampire, Ghoul: the fill climbs from the bottom; a UIGradient's hard edge is the level, and it
	        tilts as you run (the slosh, on a damped spring).
	  Wipe: Werewolf: the moon fills left to right like a phase.
	  Fade: Wraith: the wisp brightens.
	Motion (one RenderStepped loop, nothing tweened but the one-shots):
	  idle: the surface breathes 1 px on a 2.4 s cycle; motes, steam or embers drift up; a highlight slides over the
	        glass every 6 s; the Vampire's heart beats (0.8 Hz, 1 Hz at night).
	  eat:  a mote in the race colour arcs into the vessel's top (0.35 s), a splash ring flares, the level eases up,
	        "+14" drifts up in the title font. A race that can't eat it gets "Ash." / "Nothing." instead.
	  band: the plate turns over (0.3 s) to the new word.
	  Hungry: a 2 px "growl" shake about every 40 s; frost creeps in.
	  Starving: the halo pulses with a 0.9 Hz heartbeat and a soft vignette darkens the screen's edges.
	  Reduce Flashing (NHReducedFlash): pulses become a steady glow.
	  Rest: while Fed or better and nothing changes for 20 s, it fades to 55%; any change wakes it.
	Stand-in: until Config.Body.Art has ids, the vessel is drawn from frames (a glass jar in an iron frame).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)

local Player = Players.LocalPlayer
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Body`))

local Shared = {}
local Local = {}

-- KitHud's layout (Controllers.Gui.KitHud: BAR_W, BAR_H, BAR_Y)
local BAR_W, BAR_H, BAR_Y = 600, 50, 2
local VW, VH = 76, 114          -- the vessel on screen (the art is narrower and taller: set in Build)
local PLATE_W, PLATE_H = 84, 18   -- (subtle pass) the plate shows only on a change, a hover, or when hungry
local PAD_TOP, PAD_SIDE = 30, 40

local GLOW = Kit.Theme.Images and Kit.Theme.Images.Glow or `rbxassetid://117234203443052`
local TITLE = (function() -- the theme's title font may be a Font or an Enum.Font
	local F = Kit.Theme.Fonts and Kit.Theme.Fonts.Title
	if typeof(F) == `Font` then return F end
	if typeof(F) == `EnumItem` then return Font.fromEnum(F) end
	return Font.fromEnum(Enum.Font.Fantasy)
end)()
local INK = Color3.fromRGB(14, 11, 16)
local BRASS = Color3.fromRGB(214, 170, 96)
local IRON = Color3.fromRGB(46, 44, 48)

local Ui = nil :: any
local Remotes = nil :: any
local Shown = 0.7        -- the drawn level (0-1), easing toward the real one
local Target = 0.7
local Tilt, TiltV = 0, 0 -- the slosh spring
local LastChange = 0
local NextGrowl = 0
local Race = `Human`

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function art(Id: number?): string?
	return if typeof(Id) == `number` and Id > 0 then `rbxassetid://{Id}` else nil
end

local function reduced(): boolean
	return Player:GetAttribute(`NHReducedFlash`) == true
end

local function colour(): Color3
	return Config.Colours[Race] or Config.Colours.Human
end

local function band(): string
	return Player:GetAttribute(`HungerBand`) or Config.Band((Player:GetAttribute(`Hunger`) or 70))
end

---| build |---

-- the contents' rectangle inside the vessel (fractions), where Fill is shown
function Local.ContentsRect(StandIn: boolean)
	if StandIn then return { X0 = 0.2; X1 = 0.8; Y0 = 0.3; Y1 = 0.86 } end
	local F = Config.ArtFill or {}
	return { X0 = F.Left or 0.3; X1 = F.Right or 0.7; Y0 = F.Top or 0.44; Y1 = F.Bottom or 0.82 }
end

function Local.Build(Bottom: Frame)
	local A = Config.Art[Race] or {}
	local StandIn = art(A.Back) == nil or art(A.Fill) == nil
	if StandIn then VW, VH = 46, 68 else VH = 92 VW = math.floor(VH * (Config.ArtAspect or 0.48) + 0.5) end
	local R = Local.ContentsRect(StandIn)
	local C = colour()

	-- the group is padded (PAD_TOP above, PAD_SIDE each side) so the drifting numbers and the arcing mote stay inside it:
	-- a CanvasGroup clips what's outside. The vessel's right edge sits 4 px left of the bar, centred on it.
	local Root = new(`CanvasGroup`, {
		Name = `HungerVessel`; BackgroundTransparency = 1; ZIndex = 3;
		AnchorPoint = Vector2.new(1, 0); Size = UDim2.fromOffset(VW + 2 * PAD_SIDE, PAD_TOP + VH + 2 + PLATE_H + 12);
		Position = UDim2.new(0.5, -BAR_W / 2 - 2 + PAD_SIDE, 0, BAR_Y + BAR_H / 2 - VH / 2 - PAD_TOP);
	}, Bottom)
	local Body = new(`Frame`, { Name = `Body`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.new(0.5, 0, 0, PAD_TOP); Size = UDim2.fromOffset(VW, VH) }, Root)

	local Glow = new(`ImageLabel`, { Name = `Glow`; Image = art(A.Glow) or GLOW; ImageColor3 = C; ImageTransparency = 0.7;
		BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale((R.X0 + R.X1) / 2, (R.Y0 + R.Y1) / 2); Size = UDim2.fromScale(1.5, 1.1); ZIndex = 1 }, Body)
	if art(A.Glow) then -- the baked halo shares the vessel's frame: centred on it, a little larger
		Glow.Position = UDim2.fromScale(0.5, 0.5)
		Glow.Size = UDim2.fromScale(1.25, 1.1)
	end

	local Back, Fill, FillHost
	local GradRect = R -- where the contents are inside Fill (for the gradient); R stays the contents inside Body
	if StandIn then
		-- an iron-framed glass jar under a pointed cap
		Back = new(`Frame`, { Name = `Back`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Body)
		local Jar = new(`Frame`, { Name = `Jar`; BackgroundColor3 = Color3.fromRGB(20, 16, 22); BackgroundTransparency = 0.15;
			Position = UDim2.fromScale(R.X0 - 0.04, R.Y0 - 0.03); Size = UDim2.fromScale(R.X1 - R.X0 + 0.08, R.Y1 - R.Y0 + 0.06); ZIndex = 2 }, Back)
		new(`UICorner`, { CornerRadius = UDim.new(0.18, 0) }, Jar)
		new(`UIStroke`, { Color = IRON; Thickness = 2 }, Jar)
		local Cap = new(`Frame`, { Name = `Cap`; BackgroundColor3 = IRON; AnchorPoint = Vector2.new(0.5, 0.5); Rotation = 45;
			Position = UDim2.fromScale(0.5, R.Y0 - 0.06); Size = UDim2.fromOffset(16, 16); ZIndex = 1 }, Back)
		new(`UIStroke`, { Color = BRASS; Thickness = 2 }, Cap)
		local Foot = new(`Frame`, { Name = `Foot`; BackgroundColor3 = IRON; AnchorPoint = Vector2.new(0.5, 0);
			Position = UDim2.fromScale(0.5, R.Y1 + 0.02); Size = UDim2.fromScale(0.86, 0.08); ZIndex = 2 }, Back)
		new(`UICorner`, { CornerRadius = UDim.new(0.4, 0) }, Foot)
		new(`UIStroke`, { Color = BRASS; Thickness = 1.5 }, Foot)
		FillHost = new(`Frame`, { Name = `FillHost`; BackgroundTransparency = 1; ClipsDescendants = false;
			Position = UDim2.fromScale(R.X0, R.Y0); Size = UDim2.fromScale(R.X1 - R.X0, R.Y1 - R.Y0); ZIndex = 3 }, Body)
		Fill = new(`Frame`, { Name = `Fill`; BackgroundColor3 = C; Size = UDim2.fromScale(1, 1); ZIndex = 3 }, FillHost)
		new(`UICorner`, { CornerRadius = UDim.new(0.16, 0) }, Fill)
		GradRect = { X0 = 0; X1 = 1; Y0 = 0; Y1 = 1 } -- the fill frame IS the contents
	else
		Back = new(`ImageLabel`, { Name = `Back`; Image = art(A.Back); BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 2 }, Body)
		FillHost = Body
		Fill = new(`ImageLabel`, { Name = `Fill`; Image = art(A.Fill); BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ZIndex = 3 }, Body)
	end
	-- one UIGradient per object: the level's, which also shades the stand-in's fill (lit at the surface, dark below)
	local Grad = new(`UIGradient`, { Name = `Level` }, Fill)
	if StandIn then Grad.Color = ColorSequence.new(C:Lerp(INK, 0.45), C:Lerp(Color3.new(1, 1, 1), 0.25)) end
	if Config.FillMode[Race] == `Fade` then Grad.Enabled = false end

	-- the lit edge of the liquid (Rise only)
	local Surface = new(`Frame`, { Name = `Surface`; BackgroundColor3 = C:Lerp(Color3.new(1, 1, 1), 0.6); BackgroundTransparency = 0.15;
		AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.new(0, 0, 0, 2); ZIndex = 4; BorderSizePixel = 0;
		Visible = Config.FillMode[Race] == `Rise` }, Body)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.15, 0.2),
		NumberSequenceKeypoint.new(0.85, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, Surface)

	-- a highlight that slides over the glass
	local Sheen = new(`Frame`, { Name = `Sheen`; BackgroundColor3 = Color3.new(1, 1, 1); BackgroundTransparency = 0.82; Rotation = 18;
		AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.new(0, 6, R.Y1 - R.Y0 + 0.1, 0); ZIndex = 5; BorderSizePixel = 0 }, Body)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.2), NumberSequenceKeypoint.new(1, 1) }); Rotation = 90 }, Sheen)

	local Motes = new(`Frame`, { Name = `Motes`; BackgroundTransparency = 1; Position = UDim2.fromScale(R.X0, R.Y0);
		Size = UDim2.fromScale(R.X1 - R.X0, R.Y1 - R.Y0); ZIndex = 5; ClipsDescendants = true }, Body)
	if FillHost ~= Body then Motes.Position = FillHost.Position Motes.Size = FillHost.Size end

	local FrostId = A.Frost or Config.Art.Frost
	local Frost = new(`ImageLabel`, { Name = `Frost`; Image = art(FrostId) or GLOW; BackgroundTransparency = 1; ImageTransparency = 1;
		ImageColor3 = if art(FrostId) then Color3.new(1, 1, 1) else Color3.fromRGB(200, 220, 255);
		Size = UDim2.fromScale(1, 1); ZIndex = 6 }, Body)

	-- the band plate
	local PlateGroup = new(`CanvasGroup`, { Name = `PlateGroup`; BackgroundTransparency = 1; GroupTransparency = 1; ZIndex = 7;
		Size = UDim2.fromScale(1, 1) }, Root)
	local Plate = new(`ImageLabel`, { Name = `Plate`; BackgroundColor3 = INK; BackgroundTransparency = if art(Config.Art.Plate) then 1 else 0.05;
		Image = art(Config.Art.Plate) or ``; ScaleType = Enum.ScaleType.Slice;
		SliceCenter = Rect.new(table.unpack(Config.PlateSlice or { 36, 30, 449, 90 }));
		SliceScale = PLATE_H / ((Config.PlateSize or { 485, 120 })[2]); AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, PAD_TOP + VH + 2);
		Size = UDim2.fromOffset(PLATE_W, PLATE_H); ZIndex = 7 }, PlateGroup)
	if not art(Config.Art.Plate) then
		new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Plate)
		new(`UIStroke`, { Color = BRASS; Thickness = 1.5; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, Plate)
	end
	local PlateScale = new(`UIScale`, {}, Plate)
	local Word = new(`TextLabel`, { Name = `Word`; BackgroundTransparency = 1; FontFace = TITLE; TextScaled = true; Text = ``;
		TextColor3 = C:Lerp(Color3.new(1, 1, 1), 0.35); TextStrokeColor3 = INK; TextStrokeTransparency = 0.4;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.52); Size = UDim2.fromScale(0.8, 0.62); ZIndex = 8 }, Plate)

	-- the screen-edge vignette (Starving)
	local Gui = Bottom:FindFirstAncestorOfClass(`ScreenGui`)
	local VigGui = Player.PlayerGui:FindFirstChild(`NHHungerVignette`) or new(`ScreenGui`, { Name = `NHHungerVignette`; IgnoreGuiInset = true;
		ResetOnSpawn = false; DisplayOrder = 0; Enabled = true }, Player.PlayerGui)
	VigGui:ClearAllChildren()
	local Vig = new(`Frame`, { Name = `Vignette`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, VigGui)
	for I, Spec in { { 0, 0, 1, 0.16, 90 }, { 0, 0.84, 1, 0.16, -90 }, { 0, 0, 0.12, 1, 0 }, { 0.88, 0, 0.12, 1, 180 } } do
		local E = new(`Frame`, { Name = `Edge{I}`; BackgroundColor3 = Color3.fromRGB(8, 4, 6); BorderSizePixel = 0;
			Position = UDim2.fromScale(Spec[1], Spec[2]); Size = UDim2.fromScale(Spec[3], Spec[4]) }, Vig)
		new(`UIGradient`, { Rotation = Spec[5]; Transparency = NumberSequence.new(0, 1) }, E)
	end

	-- hover: the number and the band
	local Hover = new(`TextLabel`, { Name = `Hover`; BackgroundColor3 = INK; BackgroundTransparency = 0.1; FontFace = TITLE; TextSize = 13;
		TextColor3 = Color3.fromRGB(236, 224, 200); Text = ``; Visible = false; AutomaticSize = Enum.AutomaticSize.X;
		AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 0, PAD_TOP - 4); Size = UDim2.fromOffset(0, 20); ZIndex = 9 }, Root)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 8); PaddingRight = UDim.new(0, 8) }, Hover)
	new(`UICorner`, { CornerRadius = UDim.new(0, 5) }, Hover)
	new(`UIStroke`, { Color = BRASS; Thickness = 1; ApplyStrokeMode = Enum.ApplyStrokeMode.Border }, Hover)
	Body.MouseEnter:Connect(function() Hover.Visible = true Local.Wake() end)
	Body.MouseLeave:Connect(function() Hover.Visible = false end)

	Ui = { Root = Root; Body = Body; Glow = Glow; Back = Back; Fill = Fill; Grad = Grad; Surface = Surface; Sheen = Sheen;
		Motes = Motes; Frost = Frost; Plate = Plate; PlateGroup = PlateGroup; FlipAt = os.clock(); PlateScale = PlateScale; Word = Word; Vig = Vig; Hover = Hover; Rect = R; GradRect = GradRect;
		StandIn = StandIn; Gui = Gui; MoteT = 0 }
	Word.Text = Config.Word(Race, band())
end

---| the level |---

-- the gradient that shows the fill up to L (0-1) inside the contents rect
function Local.ApplyLevel(L: number, TiltDeg: number)
	local Mode = Config.FillMode[Race] or `Rise`
	local R = Ui.GradRect
	local BR = Ui.Rect
	if Mode == `Fade` then
		Ui.Fill.BackgroundTransparency = if Ui.StandIn then 1 - (0.15 + 0.85 * L) else 1
		if not Ui.StandIn then Ui.Fill.ImageTransparency = 1 - (0.08 + 0.92 * L ^ 0.8) end
		return
	end
	local T, Soft
	if Mode == `Wipe` then
		Ui.Grad.Rotation = 0
		T = R.X0 + (R.X1 - R.X0) * L
		Soft = 0.035
	else
		Ui.Grad.Rotation = -90 + TiltDeg
		T = (1 - R.Y1) + (R.Y1 - R.Y0) * L -- measured from the bottom
		Soft = 0.006
	end
	local A = math.clamp(T - Soft, 0.001, 0.997)
	local B = math.clamp(T + Soft, A + 0.001, 0.998)
	if L <= 0.001 then
		Ui.Grad.Transparency = NumberSequence.new(1)
	elseif L >= 0.999 then
		Ui.Grad.Transparency = NumberSequence.new(0)
	else
		Ui.Grad.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(A, 0),
			NumberSequenceKeypoint.new(B, 1), NumberSequenceKeypoint.new(1, 1) })
	end
	if Mode == `Rise` then
		local Y = BR.Y1 - (BR.Y1 - BR.Y0) * L
		Ui.Surface.Visible = L > 0.02 and L < 0.995
		Ui.Surface.Position = UDim2.new((BR.X0 + BR.X1) / 2, 0, Y, math.sin(os.clock() * math.pi * 2 / 2.4))
		Ui.Surface.Size = UDim2.new(BR.X1 - BR.X0, -4, 0, 2)
		Ui.Surface.Rotation = -TiltDeg
	end
end

---| motion |---

function Local.Wake()
	LastChange = os.clock()
end

function Local.Step(Dt: number)
	if not (Ui and Ui.Root.Parent) then return end
	local Now = os.clock()
	local B = band()
	-- ease toward the real level: about 1.6 s to cover a meal, faster for small moves
	Shown += (Target - Shown) * math.min(1, Dt * 2.2)
	-- the slosh: a damped spring pushed by sideways speed
	local Want = 0
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local Cam = workspace.CurrentCamera
	if Root and Cam then
		local V = Root.AssemblyLinearVelocity
		Want = math.clamp(V:Dot(Cam.CFrame.RightVector) / 40, -1, 1) * 9
	end
	TiltV += ((Want - Tilt) * 38 - TiltV * 7) * Dt
	Tilt += TiltV * Dt
	if Config.FillMode[Race] ~= `Rise` then Tilt = 0 end
	Local.ApplyLevel(Shown, Tilt)
	-- the halo: brighter when fed; Starving pulses with a heartbeat; the Vampire's heart beats always
	local C = colour()
	local Base = 0.9 - 0.16 * Shown
	local Pulse = 0
	if B == `Starving` and not reduced() then
		Pulse = (math.sin(Now * math.pi * 2 * 0.9) * 0.5 + 0.5) * 0.25
	elseif Race == `Vampire` and not reduced() then
		local Hz = if (game:GetService(`Lighting`).ClockTime >= 20 or game:GetService(`Lighting`).ClockTime < 6) then 1 else 0.8
		local Ph = (Now * Hz) % 1
		Pulse = (math.exp(-Ph * 14) + 0.6 * math.exp(-math.max(0, Ph - 0.18) * 14) * (if Ph > 0.18 then 1 else 0)) * 0.22 * Shown
	end
	Ui.Glow.ImageTransparency = math.clamp(Base - Pulse, 0.25, 0.95)
	Ui.Glow.ImageColor3 = if B == `Starving` then C:Lerp(Color3.fromRGB(255, 40, 40), 0.35) else C
	-- the sheen crosses the glass every 6 s
	local Sh = (Now % 6) / 6
	local R = Ui.Rect
	Ui.Sheen.Visible = Sh < 0.35
	Ui.Sheen.Position = UDim2.fromScale(R.X0 + (R.X1 - R.X0) * (Sh / 0.35), (R.Y0 + R.Y1) / 2)
	-- frost
	local FrostT = if B == `Starving` then 0.35 elseif B == `Hungry` then 0.65 else 1
	Ui.Frost.ImageTransparency += (FrostT - Ui.Frost.ImageTransparency) * math.min(1, Dt * 1.5)
	-- the vignette
	Ui.Vig.Visible = (Ui.Gui == nil or Ui.Gui.Enabled) and Player:GetAttribute(`InMainMenu`) ~= true
	local VigT = if B == `Starving` then (if reduced() then 0.72 else 0.7 + 0.06 * math.sin(Now * math.pi * 2 * 0.9)) else 1
	for _, E in Ui.Vig:GetChildren() do
		local G = E:FindFirstChildOfClass(`UIGradient`)
		if G then G.Transparency = NumberSequence.new(VigT, 1) end
	end
	-- the growl
	if B == `Hungry` or B == `Starving` then
		if NextGrowl == 0 then NextGrowl = Now + 6 end
		if Now >= NextGrowl then
			NextGrowl = Now + (if B == `Starving` then 25 else 40)
			Local.Shake()
		end
	else
		NextGrowl = 0
	end
	-- motes, steam and embers drift up (about 2 a second, fewer when spent)
	Ui.MoteT += Dt
	if Ui.MoteT > 0.9 / math.max(0.25, Shown) then
		Ui.MoteT = 0
		Local.Mote()
	end
	-- rest
	local Resting = (B == `Fed` or B == `Full` or B == `Stuffed`) and Now - LastChange > 12 and not Ui.Hover.Visible
	local GT = if Resting then 0.55 else 0
	Ui.Root.GroupTransparency += (GT - Ui.Root.GroupTransparency) * math.min(1, Dt * 3)
	-- the plate: on a band change (4 s), on hover, and while Hungry or Starving; otherwise it's tucked away
	local PlateOn = Ui.Hover.Visible or B == `Hungry` or B == `Starving` or Now - Ui.FlipAt < 4
	local PT = if PlateOn then 0 else 1
	Ui.PlateGroup.GroupTransparency += (PT - Ui.PlateGroup.GroupTransparency) * math.min(1, Dt * (if PlateOn then 8 else 2.5))
	-- the hover text
	if Ui.Hover.Visible then
		Ui.Hover.Text = `{Config.Word(Race, B)} · {math.floor((Player:GetAttribute(`Hunger`) or 0) + 0.5)} / 100`
	end
end

function Local.Mote()
	if Config.FillMode[Race] == `Wipe` then return end
	local C = colour()
	local M = new(`ImageLabel`, { Name = `Mote`; Image = art(Config.Art.Mote) or GLOW; BackgroundTransparency = 1; ImageColor3 = C:Lerp(Color3.new(1, 1, 1), 0.4);
		ImageTransparency = 0.3; AnchorPoint = Vector2.new(0.5, 0.5); ZIndex = 5;
		Position = UDim2.fromScale(math.random(15, 85) / 100, 1 - math.random() * Shown * 0.6); Size = UDim2.fromOffset(3, 3) }, Ui.Motes)
	local Top = 1 - Shown
	local T = TweenService:Create(M, TweenInfo.new(1.6 + math.random() * 0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.Out),
		{ Position = UDim2.fromScale(M.Position.X.Scale + (math.random() - 0.5) * 0.2, math.max(0, Top - 0.05)); ImageTransparency = 1 })
	T:Play()
	T.Completed:Once(function() M:Destroy() end)
end

function Local.Shake()
	if not Ui then return end
	local Body = Ui.Body
	local Start = os.clock()
	task.spawn(function()
		while os.clock() - Start < 0.3 and Body.Parent do
			local K = 1 - (os.clock() - Start) / 0.3
			Body.Position = UDim2.new(0.5, math.random(-1, 1) * K, 0, PAD_TOP)
			RunService.RenderStepped:Wait()
		end
		Body.Position = UDim2.new(0.5, 0, 0, PAD_TOP)
	end)
end

-- a mote arcs into the vessel's top, a splash flares, the number drifts up
function Local.Eat(Amount: number, Kind: string?)
	if not Ui then return end
	Local.Wake()
	local C = colour()
	local R = Ui.Rect
	local Body = Ui.Body
	local TopY = R.Y0
	local Bead = new(`ImageLabel`, { Name = `Bead`; Image = GLOW; BackgroundTransparency = 1; ImageColor3 = C; AnchorPoint = Vector2.new(0.5, 0.5);
		Size = UDim2.fromOffset(12, 12); Position = UDim2.new(1.6, 0, 0.95, 0); ZIndex = 9 }, Body)
	local Start = os.clock()
	task.spawn(function()
		while Bead.Parent do
			local T = math.min(1, (os.clock() - Start) / 0.35)
			local X = 1.6 + (0.5 - 1.6) * T
			local Y = 0.95 + (TopY - 0.95) * T - math.sin(T * math.pi) * 0.45
			Bead.Position = UDim2.fromScale(X, Y)
			Bead.Size = UDim2.fromOffset(12 - 5 * T, 12 - 5 * T)
			if T >= 1 then break end
			RunService.RenderStepped:Wait()
		end
		Bead:Destroy()
		if not Body.Parent then return end
		-- the splash ring: the baked ring sprite when uploaded, else a stroked ellipse
		local SplashY = R.Y1 - (R.Y1 - R.Y0) * Shown
		if art(Config.Art.Splash) then
			local Ring = new(`ImageLabel`, { Name = `Splash`; Image = art(Config.Art.Splash); BackgroundTransparency = 1;
				ImageColor3 = C:Lerp(Color3.new(1, 1, 1), 0.5); AnchorPoint = Vector2.new(0.5, 0.5);
				Position = UDim2.fromScale(0.5, SplashY); Size = UDim2.fromOffset(8, 3); ZIndex = 9 }, Body)
			local Tw = TweenService:Create(Ring, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
				{ Size = UDim2.fromOffset(VW * 0.8, 10); ImageTransparency = 1 })
			Tw:Play()
			Tw.Completed:Once(function() Ring:Destroy() end)
		else
			local Ring = new(`Frame`, { Name = `Splash`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
				Position = UDim2.fromScale(0.5, SplashY); Size = UDim2.fromOffset(10, 4); ZIndex = 9 }, Body)
			new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Ring)
			local Stroke = new(`UIStroke`, { Color = C:Lerp(Color3.new(1, 1, 1), 0.5); Thickness = 2 }, Ring)
			TweenService:Create(Ring, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromOffset(VW * 0.7, 12) }):Play()
			local Tw = TweenService:Create(Stroke, TweenInfo.new(0.45), { Transparency = 1 })
			Tw:Play()
			Tw.Completed:Once(function() Ring:Destroy() end)
		end
		if not reduced() then
			Ui.Glow.ImageTransparency = 0.2
		end
		-- the number
		local Text = if Amount > 0 then `+{math.floor(Amount + 0.5)}`
			elseif Race == `Ghoul` then `Ash.` elseif Race == `Wraith` then `Nothing.` else `+0`
		local L = new(`TextLabel`, { Name = `Gain`; BackgroundTransparency = 1; FontFace = TITLE; TextSize = if Kind == `Fed` then 17 else 14;
			Text = Text; TextColor3 = if Amount > 0 then C:Lerp(Color3.new(1, 1, 1), 0.3) else Color3.fromRGB(150, 146, 140);
			TextStrokeColor3 = INK; TextStrokeTransparency = 0.3; AnchorPoint = Vector2.new(0.5, 1);
			Position = UDim2.new(0.5, 0, 0, PAD_TOP - 2); Size = UDim2.fromOffset(80, 24); ZIndex = 10 }, Ui.Root)
		local Up = TweenService:Create(L, TweenInfo.new(1.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out),
			{ Position = UDim2.new(0.5, 0, 0, PAD_TOP - 24); TextTransparency = 1; TextStrokeTransparency = 1 })
		Up:Play()
		Up.Completed:Once(function() L:Destroy() end)
	end)
end

-- the plate turns over to the new word
function Local.Flip(Band: string)
	if not Ui then return end
	Local.Wake()
	Ui.FlipAt = os.clock()
	local S = Ui.PlateScale
	local Word = Ui.Word
	task.spawn(function()
		local Start = os.clock()
		local Swapped = false
		while os.clock() - Start < 0.3 do
			local T = (os.clock() - Start) / 0.3
			S.Scale = 0.85 + 0.15 * math.abs(math.cos(T * math.pi))
			Word.Size = UDim2.fromScale(0.8, 0.62 * math.abs(math.cos(T * math.pi)))
			if T >= 0.5 and not Swapped then
				Swapped = true
				Word.Text = Config.Word(Race, Band)
			end
			RunService.RenderStepped:Wait()
		end
		S.Scale = 1
		Word.Size = UDim2.fromScale(0.8, 0.62)
		Word.Text = Config.Word(Race, Band)
	end)
end

---| wiring |---

function Local.Mount()
	local PG = Player:WaitForChild(`PlayerGui`)
	local Hud = PG:WaitForChild(`KitHud`, 120)
	local Bottom = Hud and Hud:WaitForChild(`Bottom`, 30)
	if not Bottom then return end
	if Ui and Ui.Root then Ui.Root:Destroy() end
	Race = Player:GetAttribute(`Race`) or `Human`
	if not Config.Races[Race] then Race = `Human` end
	task.spawn(Local.Preload)
	Local.Build(Bottom)
	Target = (Player:GetAttribute(`Hunger`) or 70) / 100
	Shown = Target
	Local.Wake()
end

-- load your race's vessel (and the shared sprites) up front, so the HUD never shows it half-loaded
function Local.Preload()
	local Ids = {}
	local function add(Id) if art(Id) then table.insert(Ids, art(Id)) end end
	local A = Config.Art[Race] or {}
	add(A.Back) add(A.Fill) add(A.Glow)
	add(Config.Art.Frost) add(Config.Art.Plate) add(Config.Art.Splash) add(Config.Art.Mote)
	if #Ids > 0 then
		pcall(function() game:GetService(`ContentProvider`):PreloadAsync(Ids) end)
	end
end

function Shared.OnStart()
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHBody`, 60)
		Local.Mount()
		Player:GetAttributeChangedSignal(`Hunger`):Connect(function()
			local H = Player:GetAttribute(`Hunger`)
			if typeof(H) == `number` then
				-- ticks of decay don't wake it; only a real change of a point or more does
				if math.abs(H / 100 - Target) >= 0.01 then Local.Wake() end
				Target = H / 100
			end
		end)
		Player:GetAttributeChangedSignal(`HungerBand`):Connect(function()
			local B = Player:GetAttribute(`HungerBand`)
			if typeof(B) == `string` then Local.Flip(B) end
		end)
		Player:GetAttributeChangedSignal(`Race`):Connect(function() task.defer(Local.Mount) end)
		if F then
			Remotes = { Get = F:WaitForChild(`Get`); Event = F:WaitForChild(`Event`) }
			Remotes.Event.OnClientEvent:Connect(function(Kind, D)
				if (Kind == `Ate` or Kind == `Fed`) and typeof(D) == `table` then
					Local.Eat(tonumber(D.Amount) or 0, Kind)
				end
			end)
		end
		-- the HUD is rebuilt on some respawns and slot loads: follow it
		Player:WaitForChild(`PlayerGui`).ChildAdded:Connect(function(C)
			if C.Name == `KitHud` then task.defer(Local.Mount) end
		end)
		RunService.RenderStepped:Connect(function(Dt) Local.Step(Dt) end)
	end)
end

-- (Studio tests) read-only peeks
function Shared.Debug()
	return { Shown = Shown; Target = Target; Tilt = Tilt; Race = Race; StandIn = Ui and Ui.StandIn;
		Word = Ui and Ui.Word.Text; Mounted = Ui ~= nil and Ui.Root.Parent ~= nil }
end
Shared._Local = Local

return Shared
