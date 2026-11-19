local Report = {}
local Items = {}
table.insert(Items, { Path = {"StarterPlayer", "StarterPlayerScripts", "Controllers", "Gui", "StatsPanel"}; Source = [==[
--[[
	The Permanent Record (client). Controllers.Gui.StatsPanel   (M, or the top bar's Record button)  (2.32, remade)

	The school's dossier on you (docs/expansion/14-Progression-and-Identity.md §4), in its own PBR art
	(Config.RecordArt, baked by art/ui/hud/make_record_ui.py). The cover is your race's: Human, Priest, Vampire,
	Werewolf, Ghoul or Wraith, each with its own leather, tooling, corners and a slow ambient effect.

	Organised the same way on every page: an index tab per section down the left; on the page, a title, one line saying
	what the page shows, then sections (an icon, a heading, a rule) of rows (the label left, the value right, a hint under
	it when there's something to say, pips where a rank has steps). Anything not earned yet says how to earn it.
	  Student      your report card: name, race, level and EXP, points, Might / Grit / Wits with +1, your abilities and
	               where your bonuses come from (Progression.Sheet, as before)
	  Academics, Attendance & Conduct, Athletics, Combat, Factions & Cliques    Services.Player.Record.FileFor
	  Paths        five path cards (tier, pips, the next tier and what it needs) and your titles (Equip)
	  Honours      the 30 honours by group: struck medals, the ones to earn pressed into the page, secrets sealed
	  Entries      the Notable Entries log
	Animated: the book lifts open, pages turn between tabs, gilt glints, new honours stamp in, the cover breathes.
	Data: ReplicatedStorage.NHProgress (Get / Spend / Updated / File). API: Toggle(on?), IsOpen(), Open(tab)
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TweenService = game:GetService(`TweenService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Config = require(ReplicatedStorage.Config.Progression)
local Art = require(ReplicatedStorage.Config:WaitForChild(`RecordArt`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local Fonts = Theme.Fonts

local Shared = {}
local Local = {}
local Ui = nil
local Sheet = nil
local File = nil
local FileAt = 0
local Tab = `Student`
local Busy = false
local SeenHonours = nil :: { [string]: boolean }? -- this session: what the last look showed (new ones stamp in)

-- ink on parchment, gilt on leather
local INK = Color3.fromRGB(42, 28, 18)
local SEPIA = Color3.fromRGB(108, 80, 56)
local CRIMSON = Color3.fromRGB(138, 26, 31)
local GOOD = Color3.fromRGB(38, 96, 48)
local BAD = Color3.fromRGB(150, 30, 30)
local GILT = Color3.fromRGB(242, 217, 160)
local CREAM = Color3.fromRGB(251, 239, 214)
local ICON_INK = Color3.fromRGB(96, 58, 30)

local W, H = 1280, 760
local SECTIONS = {
	{ Id = `Student`; Name = `Student` }, { Id = `Academics`; Name = `Academics` }, { Id = `Attendance`; Name = `Attendance` },
	{ Id = `Athletics`; Name = `Athletics` }, { Id = `Combat`; Name = `Combat` }, { Id = `Factions`; Name = `Factions` },
	{ Id = `Paths`; Name = `Paths` }, { Id = `Honours`; Name = `Honours` }, { Id = `Entries`; Name = `Entries` },
}
local PATH_ICON = { Academic = `Academics`; Social = `Social`; Combat = `Combat`; Athletic = `Athletics`; Supernatural = `Supernatural` }
local STAT_ICON = { Might = `Might`; Grit = `Grit`; Wits = `Wits` }

---| little helpers |---

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end
local function tween(I: Instance, T: number, Goal, Style: Enum.EasingStyle?, Dir: Enum.EasingDirection?)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Style or Enum.EasingStyle.Quad, Dir or Enum.EasingDirection.Out), Goal)
	Tw:Play()
	return Tw
end
local function img(Name: string, Props, Parent: Instance?)
	local I = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Art.Id(Name) or ``; ScaleType = Enum.ScaleType.Stretch }, Parent)
	for K, V in Props or {} do I[K] = V end
	return I
end
local function sliced(I, Kind: string)
	local S = Art.Slices[Kind]
	I.ScaleType = Enum.ScaleType.Slice
	I.SliceCenter = S[1]
	I.SliceScale = S[2]
	return I
end
local function icon(Name: string, Size: number, Color: Color3, Props, Parent: Instance?)
	local I = img(`Icon{Name}`, { ImageColor3 = Color; Size = UDim2.fromOffset(Size, Size); ScaleType = Enum.ScaleType.Fit }, Parent)
	for K, V in Props or {} do I[K] = V end
	return I
end
local function text(Parent: Instance, Str: string, Size: number, Props)
	local T = new(`TextLabel`, { BackgroundTransparency = 1; Text = Str; TextSize = Size; Font = Fonts.Body; TextColor3 = INK; RichText = true;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Center; TextTruncate = Enum.TextTruncate.AtEnd }, Parent)
	for K, V in Props or {} do T[K] = V end
	return T
end
local function tone(T: string?): Color3
	return if T == `good` then GOOD elseif T == `bad` then BAD elseif T == `dim` then SEPIA else INK
end
local function sound(Name: string) pcall(Kit.PlaySound, Name) end

function Local.Remote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHProgress`)
	return F and F:FindFirstChild(Name)
end
function Local.Race(): string
	local R = Player:GetAttribute(`NHRecordRace`) or Player:GetAttribute(`Race`) -- (NHRecordRace: a preview, from tests)
	return if typeof(R) == `string` and Art[`Cover{R}`] ~= nil then R else `Human`
end

---| the book |---

function Local.Build()
	local G = new(`ScreenGui`, { Name = `NHReportCard`; ResetOnSpawn = false; DisplayOrder = 12; ZIndexBehavior = Enum.ZIndexBehavior.Sibling; Enabled = false },
		Player:WaitForChild(`PlayerGui`))
	local Dim = new(`Frame`, { Name = `Dim`; BackgroundColor3 = Color3.new(0, 0, 0); BackgroundTransparency = 1; Size = UDim2.new(1, 0, 1, 80);
		Position = UDim2.fromOffset(0, -60); BorderSizePixel = 0 }, G)
	local Holder = new(`Frame`, { Name = `Holder`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(W, H) }, G)
	Kit.AutoScale(G)
	local Book = new(`Frame`, { Name = `Book`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Holder)
	local Scale = new(`UIScale`, { Scale = 1 }, Book)
	local Cover = img(`CoverHuman`, { Name = `Cover`; Size = UDim2.fromScale(1, 1) }, Book)
	local Ambience = new(`Frame`, { Name = `Ambience`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1); ClipsDescendants = true }, Book)
	-- the nameplate, with a glint that sweeps across it now and then
	local Plate = sliced(img(`PlateHuman`, { Name = `Plate`; Position = UDim2.fromOffset(58, 30); Size = UDim2.fromOffset(440, 74); ClipsDescendants = true }, Book), `Plate`)
	local PlateText = text(Plate, `PERMANENT RECORD`, 28, { Font = Fonts.Title; TextColor3 = Color3.fromRGB(34, 24, 16); Position = UDim2.fromOffset(34, 0); Size = UDim2.new(1, -68, 1, 0) })
	local PlateStroke = new(`UIStroke`, { Color = Color3.new(0, 0, 0); Thickness = 1.5; Transparency = 1 }, PlateText)
	local Glint = img(`Glint`, { Name = `Glint`; ImageTransparency = 0.25; Size = UDim2.new(0, 160, 1, 0); Position = UDim2.new(-0.5, 0, 0, 0) }, Plate)
	-- the student's name and standing, in the band between the nameplate and the emblem, lined up with the plate
	local Who = text(Book, ``, 34, { Font = Fonts.Title; TextColor3 = GILT; Position = UDim2.fromOffset(524, 28); Size = UDim2.fromOffset(470, 40) })
	new(`UIStroke`, { Color = Color3.fromRGB(20, 10, 6); Thickness = 2; Transparency = 0.25 }, Who)
	local WhoSub = text(Book, ``, 19, { Font = Fonts.Title; TextColor3 = Color3.fromRGB(236, 214, 170); Position = UDim2.fromOffset(526, 70); Size = UDim2.fromOffset(470, 26) })
	new(`UIStroke`, { Color = Color3.fromRGB(20, 10, 6); Thickness = 1.5; Transparency = 0.35 }, WhoSub)
	-- close: an iron ring with a gilt boss
	local Close = new(`ImageButton`, { Name = `Close`; BackgroundTransparency = 1; Image = Art.Id(`Close`) or ``; AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -22, 0, 22); Size = UDim2.fromOffset(56, 56) }, Book)
	icon(`Close`, 26, Color3.fromRGB(52, 32, 14), { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5) }, Close)
	Close.Activated:Connect(function() Shared.Toggle(false) end)
	-- the index tabs
	local Rail = new(`Frame`, { Name = `Rail`; BackgroundTransparency = 1; Position = UDim2.fromOffset(30, 128); Size = UDim2.fromOffset(268, 600) }, Book)
	local Tabs = {}
	for I, S in SECTIONS do
		local B = new(`ImageButton`, { Name = S.Id; BackgroundTransparency = 1; AutoButtonColor = false; Image = Art.Id(`Tab{S.Id}`) or ``;
			Position = UDim2.fromOffset(0, (I - 1) * 66); Size = UDim2.fromOffset(234, 60) }, Rail)
		sliced(B, `Tab`)
		icon(S.Id, 30, Color3.fromRGB(255, 226, 160), { AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 22, 0.5, -1) }, B)
		text(B, S.Name, 21, { Font = Fonts.Title; TextColor3 = CREAM; Position = UDim2.fromOffset(62, 0); Size = UDim2.new(1, -86, 1, -2) })
		B.MouseEnter:Connect(function() if Tab ~= S.Id then tween(B, 0.12, { Position = UDim2.fromOffset(8, (I - 1) * 66) }) end end)
		B.MouseLeave:Connect(function() if Tab ~= S.Id then tween(B, 0.12, { Position = UDim2.fromOffset(0, (I - 1) * 66) }) end end)
		B.Activated:Connect(function() Shared.Open(S.Id) end)
		Tabs[S.Id] = { Button = B; Index = I }
	end
	-- the page: parchment, its writing in a canvas group so a page turn can fade it
	local Page = sliced(img(`Page`, { Name = `Page`; Position = UDim2.fromOffset(290, 116); Size = UDim2.fromOffset(964, 618) }, Book), `Page`)
	local Content = new(`CanvasGroup`, { Name = `Content`; BackgroundTransparency = 1; Position = UDim2.fromOffset(54, 26); Size = UDim2.new(1, -86, 1, -48) }, Page)
	local Turn = sliced(img(`Page`, { Name = `Turn`; ImageTransparency = 1; ZIndex = 5; Size = UDim2.new(0.12, 0, 1, 0); Position = UDim2.fromScale(1, 0) }, Page), `Page`)
	Ui = { Gui = G; Dim = Dim; Holder = Holder; Book = Book; Scale = Scale; Cover = Cover; Ambience = Ambience; Plate = Plate; Glint = Glint;
		Who = Who; WhoSub = WhoSub; PlateText = PlateText; PlateStroke = PlateStroke; Tabs = Tabs; Page = Page; Content = Content; Turn = Turn; Race = nil }
	Local.Animate()
end

-- the cover and nameplate for your race, and its ambient effect
function Local.Dress()
	local Race = Local.Race()
	if Ui.Race == Race then return end
	Ui.Race = Race
	Ui.Cover.Image = Art.Id(`Cover{Race}`) or ``
	Ui.Plate.Image = Art.Id(`Plate{Race}`) or ``
	local Dark = Race == `Werewolf` or Race == `Vampire` -- (iron and blackened silver plates)
	Ui.PlateText.TextColor3 = if Dark then CREAM else Color3.fromRGB(34, 24, 16)
	Ui.PlateStroke.Transparency = if Dark then 0.35 else 1
	for _, Ch in Ui.Ambience:GetChildren() do Ch:Destroy() end
	Local.Ambience(Race)
end

-- each race's cover breathes in its own way (Theme.Images.Glow, tweened: a few images, no per-frame work)
function Local.Ambience(Race: string)
	local A = Ui.Ambience
	local Glow = Theme.Images.Glow
	local function glow(Color: Color3, Pos: UDim2, Size: number, T: number)
		return new(`ImageLabel`, { BackgroundTransparency = 1; Image = Glow; ImageColor3 = Color; ImageTransparency = T; AnchorPoint = Vector2.new(0.5, 0.5);
			Position = Pos; Size = UDim2.fromOffset(Size, Size) }, A)
	end
	local function loop(I: Instance, T: number, Goal)
		TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), Goal):Play()
	end
	local Emblem = UDim2.fromOffset(W - 244, 70) -- where the cover's tooled emblem sits
	if Race == `Human` then -- a candle's warmth on the emblem, flickering
		local G1 = glow(Color3.fromRGB(255, 170, 80), Emblem, 170, 0.55)
		task.spawn(function()
			while G1.Parent do
				tween(G1, 0.12, { ImageTransparency = 0.45 + math.random() * 0.25; Size = UDim2.fromOffset(160 + math.random(0, 24), 160 + math.random(0, 24)) })
				task.wait(0.12 + math.random() * 0.1)
			end
		end)
	elseif Race == `Priest` then -- a slow golden shimmer across the vellum
		local Band = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(255, 226, 150); BackgroundTransparency = 0.8; BorderSizePixel = 0; Size = UDim2.new(0, 220, 2, 0);
			Rotation = 18; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(-0.2, 0, 0.5, 0) }, A)
		new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(1, 1) }) }, Band)
		task.spawn(function()
			while Band.Parent do
				Band.Position = UDim2.new(-0.2, 0, 0.5, 0)
				tween(Band, 5, { Position = UDim2.new(1.2, 0, 0.5, 0) }, Enum.EasingStyle.Sine).Completed:Wait()
				task.wait(3)
			end
		end)
		loop(glow(Color3.fromRGB(255, 220, 140), Emblem, 210, 0.6), 2.4, { ImageTransparency = 0.35 })
	elseif Race == `Vampire` then -- the garnets in the corners pulse like a slow heartbeat
		for _, P in { UDim2.fromOffset(37, 37), UDim2.fromOffset(W - 37, 37), UDim2.fromOffset(37, H - 37), UDim2.fromOffset(W - 37, H - 37) } do
			loop(glow(Color3.fromRGB(220, 20, 40), P, 70, 0.75), 1.4, { ImageTransparency = 0.25; Size = UDim2.fromOffset(92, 92) })
		end
	elseif Race == `Werewolf` then -- moonlight drifts over the hide
		loop(glow(Color3.fromRGB(190, 210, 255), UDim2.fromOffset(W * 0.3, H * 0.2), 700, 0.82), 7, { Position = UDim2.fromOffset(W * 0.7, H * 0.35); ImageTransparency = 0.72 })
		loop(glow(Color3.fromRGB(235, 240, 255), Emblem, 150, 0.6), 3, { ImageTransparency = 0.3 })
	elseif Race == `Ghoul` then -- grave wisps rise along the edges
		task.spawn(function()
			while A.Parent and Ui and Ui.Race == `Ghoul` do
				if Ui.Gui.Enabled then
					local X = if math.random() < 0.5 then math.random(20, 110) else math.random(W - 110, W - 20)
					local Wisp = glow(Color3.fromRGB(120, 210, 120), UDim2.fromOffset(X, H - 20), math.random(40, 70), 0.55)
					tween(Wisp, 4, { Position = UDim2.fromOffset(X + math.random(-30, 30), H - 260); ImageTransparency = 1 }, Enum.EasingStyle.Sine)
					task.delay(4.1, function() Wisp:Destroy() end)
				end
				task.wait(0.9)
			end
		end)
	elseif Race == `Wraith` then -- the silver tooling breathes with a cold light
		for _, P in { UDim2.fromOffset(W / 2, 48), UDim2.fromOffset(W / 2, H - 48), UDim2.fromOffset(48, H / 2), UDim2.fromOffset(W - 48, H / 2) } do
			local G1 = glow(Color3.fromRGB(150, 200, 255), P, 300, 0.85)
			G1.Size = if P.X.Offset == W / 2 then UDim2.fromOffset(W, 120) else UDim2.fromOffset(120, H)
			loop(G1, 3.2, { ImageTransparency = 0.65 })
		end
		loop(glow(Color3.fromRGB(170, 215, 255), Emblem, 180, 0.55), 2.6, { ImageTransparency = 0.25 })
	end
end

-- the glint across the nameplate, now and then
function Local.Animate()
	task.spawn(function()
		while Ui do
			task.wait(5 + math.random() * 3)
			if Ui and Ui.Gui.Enabled then
				Ui.Glint.Position = UDim2.new(-0.5, 0, 0, 0)
				tween(Ui.Glint, 0.9, { Position = UDim2.new(1.2, 0, 0, 0) }, Enum.EasingStyle.Sine)
			end
		end
	end)
end

function Local.MarkTabs()
	for Id, T in Ui.Tabs do
		local On = Id == Tab
		T.Button.Image = Art.Id(if On then `TabOn{Id}` else `Tab{Id}`) or ``
		T.Button.ZIndex = if On then 3 else 2
		tween(T.Button, 0.16, { Position = UDim2.fromOffset(if On then 16 else 0, (T.Index - 1) * 66); Size = UDim2.fromOffset(if On then 252 else 234, 60) })
	end
end

---| the page |---

function Local.Clear()
	for _, Ch in Ui.Content:GetChildren() do Ch:Destroy() end
end

-- the page's head: its title, one line on what it shows, and a crimson rule
function Local.Head(Title: string, Blurb: string)
	text(Ui.Content, Title, 34, { Font = Fonts.Title; Size = UDim2.new(1, 0, 0, 40) })
	text(Ui.Content, Blurb, 17, { TextColor3 = SEPIA; Position = UDim2.fromOffset(2, 42); Size = UDim2.new(1, -4, 0, 20) })
	new(`Frame`, { BackgroundColor3 = CRIMSON; BackgroundTransparency = 0.35; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 70); Size = UDim2.new(1, 0, 0, 2) }, Ui.Content)
	local Body = new(`ScrollingFrame`, { Name = `Body`; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(0, 82); Size = UDim2.new(1, 0, 1, -82);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 5; ScrollBarImageColor3 = SEPIA; ScrollingDirection = Enum.ScrollingDirection.Y }, Ui.Content)
	new(`UIPadding`, { PaddingRight = UDim.new(0, 12); PaddingBottom = UDim.new(0, 12) }, Body)
	return Body
end

local function list(Parent: Instance, Pad: number?)
	new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, Pad or 4) }, Parent)
end

-- a section: an icon, a heading in crimson capitals, a rule
function Local.Heading(Parent: Instance, Title: string, Icon: string?, Order: number)
	local F = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 36); LayoutOrder = Order }, Parent)
	if Icon then icon(Icon, 22, CRIMSON, { Position = UDim2.fromOffset(2, 8) }, F) end
	text(F, string.upper(Title), 15, { Font = Fonts.Title; TextColor3 = CRIMSON; Position = UDim2.fromOffset(if Icon then 32 else 2, 6); Size = UDim2.new(1, -40, 0, 22) })
	new(`Frame`, { BackgroundColor3 = SEPIA; BackgroundTransparency = 0.6; BorderSizePixel = 0; Position = UDim2.new(0, 0, 1, -2); Size = UDim2.new(1, 0, 0, 1) }, F)
	return F
end

-- a row: the label left, the value right (tinted by tone), pips just left of the value, a hint underneath
function Local.Row(Parent: Instance, R, Order: number, Alt: boolean)
	local Tall = R.Hint ~= nil and R.Hint ~= ``
	local F = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(120, 80, 40); BackgroundTransparency = if Alt then 0.93 else 1; BorderSizePixel = 0;
		Size = UDim2.new(1, 0, 0, if Tall then 50 else 32); LayoutOrder = Order }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, F)
	text(F, R.L, 18, { Position = UDim2.fromOffset(10, 5); Size = UDim2.new(0.5, -10, 0, 22); TextColor3 = if R.Tone == `dim` then SEPIA else INK })
	local ValueW = if R.Pips then 130 else 260
	text(F, R.V or ``, 18, { Font = Fonts.Title; TextColor3 = tone(R.Tone); TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -10, 0, 5); Size = UDim2.fromOffset(ValueW, 22) })
	if R.Pips then
		local N, Of = R.Pips[1], R.Pips[2]
		for I = 1, Of do
			img(if I <= N then `PipOn` else `Pip`, { AnchorPoint = Vector2.new(1, 0); Size = UDim2.fromOffset(18, 18);
				Position = UDim2.new(1, -(10 + ValueW + 10 + (Of - I) * 22), 0, 7) }, F)
		end
	end
	if Tall then
		text(F, R.Hint, 15, { TextColor3 = SEPIA; Position = UDim2.fromOffset(12, 27); Size = UDim2.new(1, -24, 0, 19) })
	end
	return F
end

function Local.Sections(Body: Instance, Sections)
	list(Body, 2)
	local Order = 0
	for _, S in Sections do
		Order += 1
		Local.Heading(Body, S.H, S.Icon, Order)
		for I, R in S.Rows do
			Order += 1
			Local.Row(Body, R, Order, I % 2 == 0)
		end
		Order += 1
		new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 8); LayoutOrder = Order }, Body)
	end
end

---| Student (the report card, on the page) |---

function Local.Pct(V: number?, Invert: boolean?): (string, string?)
	V = V or 0
	if Invert then V = -V end
	if math.abs(V) < 1e-4 then return `\u{2014}`, `dim` end
	local P = math.abs(V) * 100
	local Num = if P < 9.95 and math.abs(P - math.floor(P + 0.5)) > 0.05 then string.format(`%.1f`, P) else tostring(math.floor(P + 0.5))
	return `{if V > 0 then `+` else `\u{2212}`}{Num}%`, if V > 0 then `good` else `bad`
end

function Local.Spend(StatId: string)
	if Busy then return end
	local R = Local.Remote(`Spend`)
	if not R then return end
	Busy = true
	local Ok, Done, New = pcall(R.InvokeServer, R, StatId, 1)
	Busy = false
	if Ok and Done and typeof(New) == `table` then
		Sheet = New
		sound(`Confirm`)
		Local.Render(true)
	else
		sound(`Reject`)
	end
end

function Local.Student()
	local S = Sheet
	local Rec = S.Record or {}
	local Body = Local.Head(`Student`, `Your report card: who you are, your level, your stats and what they give you.`)
	-- left: the card
	local Card = sliced(img(`Card`, { Size = UDim2.fromOffset(400, 500) }, Body), `Card`)
	local Name = (Rec.Name ~= `` and Rec.Name) or Player.DisplayName
	text(Card, Name, 26, { Font = Fonts.Title; Position = UDim2.fromOffset(26, 18); Size = UDim2.new(1, -52, 0, 30) })
	local R = S.RaceInfo
	local RaceLine = if R then `{R.Sub ~= `` and R.Sub or R.Race}  \u{00B7}  {R.TierName or `Tier {R.Tier}`}` else (S.Race or `Human`)
	text(Card, string.upper(RaceLine), 14, { Font = Fonts.Title; TextColor3 = CRIMSON; Position = UDim2.fromOffset(26, 50); Size = UDim2.new(1, -52, 0, 18) })
	text(Card, `Level`, 15, { TextColor3 = SEPIA; Position = UDim2.fromOffset(26, 76); Size = UDim2.fromOffset(80, 18) })
	text(Card, tostring(S.Level), 40, { Font = Fonts.Title; Position = UDim2.fromOffset(26, 92); Size = UDim2.fromOffset(84, 44) })
	local Bar = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(220, 200, 165); BorderSizePixel = 0; Position = UDim2.fromOffset(112, 104); Size = UDim2.new(1, -140, 0, 22) }, Card)
	new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Bar)
	new(`UIStroke`, { Color = SEPIA; Transparency = 0.3; Thickness = 1.5 }, Bar)
	local Frac = if S.Next > 0 then S.Exp / S.Next else 1
	local Fill = new(`Frame`, { BackgroundColor3 = Color3.new(1, 1, 1); BorderSizePixel = 0; Size = UDim2.fromScale(0, 1) }, Bar)
	new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Fill)
	new(`UIGradient`, { Color = ColorSequence.new(Color3.fromRGB(176, 36, 42), Color3.fromRGB(120, 18, 26)) }, Fill)
	tween(Fill, 0.6, { Size = UDim2.fromScale(math.clamp(Frac, 0, 1), 1) }, Enum.EasingStyle.Quart)
	text(Bar, if S.Next > 0 then `{S.Exp} / {S.Next} EXP` else `MAX LEVEL`, 14, { Font = Fonts.Title; TextColor3 = if Frac > 0.55 then CREAM else INK;
		TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.fromScale(1, 1); ZIndex = 2 })
	text(Card, if S.Points > 0 then `<b>{S.Points}</b> point{if S.Points == 1 then `` else `s`} to spend` else `No points to spend \u{00B7} {Config.PointsPerLevel} each level`, 16,
		{ TextColor3 = if S.Points > 0 then CRIMSON else SEPIA; Position = UDim2.fromOffset(26, 136); Size = UDim2.new(1, -52, 0, 20) })
	local Y = 168
	for _, St in Config.Stats do
		local Val = S.Stats[St.Id] or 0
		new(`Frame`, { BackgroundColor3 = SEPIA; BackgroundTransparency = 0.7; BorderSizePixel = 0; Position = UDim2.fromOffset(26, Y - 6); Size = UDim2.new(1, -52, 0, 1) }, Card)
		icon(STAT_ICON[St.Id] or `Student`, 38, ICON_INK, { Position = UDim2.fromOffset(26, Y + 6) }, Card)
		text(Card, St.Name, 21, { Font = Fonts.Title; Position = UDim2.fromOffset(74, Y); Size = UDim2.fromOffset(140, 26) })
		text(Card, `{Val} / {Config.MaxStat}`, 17, { Font = Fonts.Title; TextColor3 = CRIMSON; Position = UDim2.fromOffset(212, Y + 2); Size = UDim2.fromOffset(70, 22) })
		text(Card, Config.Describe(St.Per), 14, { TextColor3 = GOOD; TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextYAlignment = Enum.TextYAlignment.Top;
			Position = UDim2.fromOffset(74, Y + 28); Size = UDim2.new(1, -190, 0, 50) })
		local Can = S.Points > 0 and Val < Config.MaxStat
		local Plus = new(`ImageButton`, { BackgroundTransparency = 1; Image = Art.Id(if Can then `Button` else `Ink`) or ``; AnchorPoint = Vector2.new(1, 0);
			Position = UDim2.new(1, -24, 0, Y + 8); Size = UDim2.fromOffset(78, 42); AutoButtonColor = Can }, Card)
		sliced(Plus, `Button`)
		icon(`Plus`, 22, if Can then CREAM else Color3.fromRGB(150, 130, 100), { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5) }, Plus)
		if Can then
			local StatId = St.Id
			Plus.Activated:Connect(function()
				tween(Plus, 0.06, { Size = UDim2.fromOffset(72, 38) }).Completed:Connect(function() tween(Plus, 0.12, { Size = UDim2.fromOffset(78, 42) }, Enum.EasingStyle.Back) end)
				Local.Spend(StatId)
			end)
		end
		Y += 108
	end
	-- right: abilities and where they come from
	local Right = new(`ScrollingFrame`, { BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(420, 0); Size = UDim2.new(1, -420, 0, 500);
		CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y; ScrollBarThickness = 5; ScrollBarImageColor3 = SEPIA }, Body)
	new(`UIPadding`, { PaddingRight = UDim.new(0, 10) }, Right)
	local E = S.Effects or {}
	local function r(L, Key, Invert) local V, T = Local.Pct(E[Key], Invert) return { L = L; V = V; Tone = T } end
	local Health = 100 + math.floor(E.MaxHealth or 0)
	local Sources = {}
	local function src(L, T, Bad) if T and T ~= `` then table.insert(Sources, { L = L; V = ``; Hint = T; Tone = if Bad then `bad` else nil }) end end
	if S.Clan then src(`Clan {S.Clan}`, S.ClanText) end
	if R then
		src(if R.Passive ~= `` then R.Passive else `Race`, R.Strengths)
		if R.Drawbacks and R.Drawbacks ~= `` then src(`Drawback`, R.Drawbacks, true) end
	end
	for _, Tr in S.Traits or {} do src(Tr.Name, Tr.Text) end
	src(`Gear`, S.GearText)
	src(`Snack`, S.SnackText)
	if #Sources == 0 then Sources = { { L = `Nothing yet`; V = ``; Tone = `dim`; Hint = `A clan, your race's tiers, traits, gear and snacks all add bonuses.` } } end
	Local.Sections(Right, {
		{ H = `In a fight`; Icon = `Combat`; Rows = { { L = `Max health`; V = tostring(Health); Tone = if Health > 100 then `good` else nil }, r(`Damage`, `DamageDealt`),
			r(`Toughness`, `DamageTaken`, true), r(`Guard`, `PostureGain`, true), r(`Night power`, `NightPower`), r(`Stealth`, `Stealth`, true) } };
		{ H = `EXP bonuses`; Icon = `Paths`; Rows = { r(`All EXP`, `AllExp`), r(`Class`, `ClassExp`), r(`Quest`, `QuestExp`), r(`Combat`, `CombatExp`), r(`Social`, `SocialExp`) } };
		{ H = `Where it comes from`; Icon = `Student`; Rows = Sources };
	})
end

---| Paths |---

function Local.Paths(T)
	local Body = Local.Head(T.Title, T.Blurb)
	list(Body, 6)
	local Grid = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = 1 }, Body)
	new(`UIGridLayout`, { CellSize = UDim2.new(0.5, -8, 0, 164); CellPadding = UDim2.fromOffset(12, 8); SortOrder = Enum.SortOrder.LayoutOrder }, Grid)
	for I, C in T.Cards do
		local Card = sliced(img(`Card`, { LayoutOrder = I }, Grid), `Card`)
		icon(PATH_ICON[C.Path] or `Paths`, 40, CRIMSON, { Position = UDim2.fromOffset(22, 20) }, Card)
		text(Card, C.Path, 22, { Font = Fonts.Title; Position = UDim2.fromOffset(72, 16); Size = UDim2.new(1, -96, 0, 26) })
		text(Card, C.Name, 18, { Font = Fonts.Title; TextColor3 = CRIMSON; Position = UDim2.fromOffset(72, 42); Size = UDim2.new(1, -96, 0, 22) })
		for P = 1, C.Of do
			img(if P <= C.Tier then `PipOn` else `Pip`, { Size = UDim2.fromOffset(20, 20); Position = UDim2.fromOffset(72 + (P - 1) * 24, 70) }, Card)
		end
		if C.Next then
			text(Card, `Next: <b>{C.Next}</b>`, 16, { TextColor3 = SEPIA; Position = UDim2.fromOffset(22, 98); Size = UDim2.new(1, -44, 0, 18) })
			text(Card, if #C.Missing > 0 then `Needs: {table.concat(C.Missing, ` \u{00B7} `)}` else `Ready: it arrives on your next check.`, 15,
				{ TextColor3 = SEPIA; TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextYAlignment = Enum.TextYAlignment.Top;
					Position = UDim2.fromOffset(22, 118); Size = UDim2.new(1, -44, 0, 36) })
		else
			text(Card, `The top of this path.`, 15, { TextColor3 = GOOD; Font = Fonts.Title; Position = UDim2.fromOffset(22, 100); Size = UDim2.new(1, -44, 0, 18) })
		end
	end
	Local.Heading(Body, `Titles`, `Honours`, 2)
	local Wrap = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = 3 }, Body)
	if #T.Titles == 0 then
		text(Wrap, `No titles yet. Every path tier earns one.`, 15, { TextColor3 = SEPIA; Size = UDim2.new(1, 0, 0, 30) })
		return
	end
	new(`UIGridLayout`, { CellSize = UDim2.fromOffset(204, 44); CellPadding = UDim2.fromOffset(10, 8); SortOrder = Enum.SortOrder.LayoutOrder }, Wrap)
	for I, Title in T.Titles do
		local On = Title == T.Equipped
		local B = new(`ImageButton`, { BackgroundTransparency = 1; Image = Art.Id(if On then `Button` else `Ink`) or ``; LayoutOrder = I }, Wrap)
		sliced(B, `Button`)
		text(B, (if On then `\u{2713} ` else ``) .. Title, 15, { Font = Fonts.Title; TextColor3 = if On then CREAM else GILT; TextXAlignment = Enum.TextXAlignment.Center;
			Size = UDim2.new(1, -24, 1, -2); Position = UDim2.fromOffset(12, 0) })
		B.Activated:Connect(function()
			pcall(function() require(ReplicatedStorage.Remotes.Packets).SocialAction:Fire({ Action = `EquipTitle`; Title = if On then `` else Title }) end)
			sound(`Confirm`)
			T.Equipped = if On then `` else Title
			Local.Render(true)
		end)
	end
end

---| Honours |---

function Local.Honours(T)
	local Body = Local.Head(T.Title, T.Blurb)
	list(Body, 4)
	local Order = 0
	local Fresh = {}
	for _, G in T.Groups do
		Order += 1
		Local.Heading(Body, G.Name, G.Icon, Order)
		Order += 1
		local Grid = new(`Frame`, { BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Order }, Body)
		new(`UIGridLayout`, { CellSize = UDim2.fromOffset(160, 176); CellPadding = UDim2.fromOffset(8, 4); SortOrder = Enum.SortOrder.LayoutOrder }, Grid)
		for I, Hn in G.Items do
			local Cell = new(`Frame`, { BackgroundTransparency = 1; LayoutOrder = I }, Grid)
			local M = img(if Hn.Secret then `Envelope` elseif Hn.Earned then `Medal` else `MedalDim`, { AnchorPoint = Vector2.new(0.5, 0);
				Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromOffset(96, 96) }, Cell)
			if Hn.Earned then
				icon(G.Icon, 30, Color3.fromRGB(70, 40, 12), { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.61) }, M)
			elseif not Hn.Secret then
				icon(G.Icon, 28, SEPIA, { ImageTransparency = 0.55; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.61) }, M)
			end
			text(Cell, Hn.Name, 15, { Font = Fonts.Title; TextColor3 = if Hn.Earned then INK else SEPIA; TextXAlignment = Enum.TextXAlignment.Center;
				Position = UDim2.fromOffset(0, 98); Size = UDim2.new(1, 0, 0, 20) })
			text(Cell, Hn.Text, 13, { TextColor3 = SEPIA; TextWrapped = true; TextTruncate = Enum.TextTruncate.None; TextXAlignment = Enum.TextXAlignment.Center;
				TextYAlignment = Enum.TextYAlignment.Top; Position = UDim2.fromOffset(4, 120); Size = UDim2.new(1, -8, 0, 48) })
			if Hn.Earned and SeenHonours and not SeenHonours[Hn.Id] then table.insert(Fresh, M) end
		end
	end
	SeenHonours = SeenHonours or {}
	for _, G in T.Groups do for _, Hn in G.Items do if Hn.Earned then SeenHonours[Hn.Id] = true end end end
	-- new since the last look: struck in, one after another
	for I, M in Fresh do
		M.Size = UDim2.fromOffset(170, 170)
		M.Rotation = -14
		M.ImageTransparency = 1
		task.delay(0.35 + (I - 1) * 0.3, function()
			tween(M, 0.22, { Size = UDim2.fromOffset(96, 96); Rotation = 0; ImageTransparency = 0 }, Enum.EasingStyle.Back)
			sound(`Confirm`)
		end)
	end
end

---| Entries |---

function Local.Entries(T)
	local Body = Local.Head(T.Title, T.Blurb)
	list(Body, 2)
	if #T.List == 0 then
		Local.Row(Body, { L = `Nothing on file yet.`; V = ``; Tone = `dim`; Hint = `The school is watching. Earn a tier or an honour and it will be written here.` }, 1, false)
		return
	end
	for I, E in T.List do
		local F = new(`Frame`, { BackgroundColor3 = Color3.fromRGB(120, 80, 40); BackgroundTransparency = if I % 2 == 0 then 0.93 else 1; BorderSizePixel = 0;
			Size = UDim2.new(1, 0, 0, 34); LayoutOrder = I }, Body)
		new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, F)
		text(F, string.upper(if E.When ~= `` then E.When else `On file`), 14, { Font = Enum.Font.Code; TextColor3 = CRIMSON; Position = UDim2.fromOffset(10, 0); Size = UDim2.fromOffset(170, 34) })
		text(F, E.Text, 17, { Position = UDim2.fromOffset(186, 0); Size = UDim2.new(1, -196, 1, 0) })
	end
end

---| rendering and page turns |---

function Local.Fetch(Force: boolean?)
	if not Force and File and os.clock() - FileAt < 2 then return end
	local R = Local.Remote(`File`)
	if not R then return end
	local Ok, F = pcall(R.InvokeServer, R)
	if Ok and typeof(F) == `table` then File, FileAt = F, os.clock() end
end

function Local.Draw()
	Local.Clear()
	if Tab == `Student` then
		if Sheet then Local.Student() end
		return
	end
	Local.Fetch()
	local T = File and File[Tab]
	if not T then
		Local.Head(`One moment`, `The office is fetching your file.`)
		return
	end
	if Tab == `Paths` then Local.Paths(T)
	elseif Tab == `Honours` then Local.Honours(T)
	elseif Tab == `Entries` then Local.Entries(T)
	else Local.Sections(Local.Head(T.Title, T.Blurb), T.Sections) end
end

-- Quiet = redraw in place (after a spend, an equip, an update); otherwise the page turns
function Local.Render(Quiet: boolean?)
	if not (Ui and Sheet) then return end
	Local.Dress()
	local Rec = Sheet.Record or {}
	Ui.Who.Text = (Rec.Name ~= `` and Rec.Name) or Player.DisplayName
	local R = Sheet.RaceInfo
	Ui.WhoSub.Text = string.upper(if R then `{if R.Sub ~= `` and R.Sub ~= R.Race then R.Sub .. `  \u{00B7}  ` else ``}{R.Race}  \u{00B7}  Level {Sheet.Level}` else `Level {Sheet.Level}`)
	Local.MarkTabs()
	if Quiet then
		local Body = Ui.Content:FindFirstChild(`Body`)
		local Pos = Body and Body.CanvasPosition
		Local.Draw()
		local NewBody = Ui.Content:FindFirstChild(`Body`)
		if Pos and NewBody then NewBody.CanvasPosition = Pos end
		return
	end
	local C = Ui.Content
	-- the page turns: the old writing slides away, a page edge sweeps across, the new writing settles in
	tween(C, 0.1, { GroupTransparency = 1; Position = UDim2.fromOffset(30, 26) })
	Ui.Turn.ImageTransparency = 0.1
	Ui.Turn.Position = UDim2.fromScale(0.92, 0)
	tween(Ui.Turn, 0.26, { Position = UDim2.fromScale(-0.02, 0); ImageTransparency = 1 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
	task.delay(0.1, function()
		if not Ui then return end
		Local.Draw()
		C.Position = UDim2.fromOffset(78, 26)
		tween(C, 0.2, { GroupTransparency = 0; Position = UDim2.fromOffset(54, 26) })
	end)
end

function Shared.Open(Id: string)
	if Tab == Id then return end
	Tab = Id
	sound(`Tick`)
	Local.Render()
end

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Gui.Enabled end

function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Gui.Enabled end
	if On and Player:GetAttribute(`InMainMenu`) == true then return end
	if On then
		if Ui.Gui.Enabled then return end
		local R = Local.Remote(`Get`)
		if R then
			local Ok, S = pcall(R.InvokeServer, R)
			if Ok and typeof(S) == `table` then Sheet = S end
		end
		if not Sheet then return end
		Local.Fetch(true)
		Ui.Gui.Enabled = true
		Local.Render(true)
		-- the book lifts open
		Ui.Scale.Scale = 0.9
		Ui.Book.Position = UDim2.fromOffset(0, 40)
		Ui.Dim.BackgroundTransparency = 1
		tween(Ui.Scale, 0.32, { Scale = 1 }, Enum.EasingStyle.Back)
		tween(Ui.Book, 0.28, { Position = UDim2.fromOffset(0, 0) }, Enum.EasingStyle.Quart)
		tween(Ui.Dim, 0.25, { BackgroundTransparency = 0.45 })
		Ui.Content.GroupTransparency = 1
		task.delay(0.12, function() if Ui then tween(Ui.Content, 0.25, { GroupTransparency = 0 }) end end)
		sound(`Tick`)
	else
		if not Ui.Gui.Enabled then return end
		tween(Ui.Scale, 0.16, { Scale = 0.94 }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		tween(Ui.Book, 0.16, { Position = UDim2.fromOffset(0, 30) }, Enum.EasingStyle.Quad, Enum.EasingDirection.In)
		tween(Ui.Dim, 0.16, { BackgroundTransparency = 1 })
		task.delay(0.17, function() if Ui then Ui.Gui.Enabled = false end end)
	end
end

-- tests: point the art at local files, or look at another race's cover
function Shared.UseArt(Map) for K, V in Map do Art[K] = V end if Ui then Ui.Race = nil end end
function Shared.PreviewRace(Race: string?) Player:SetAttribute(`NHRecordRace`, Race) if Ui then Ui.Race = nil Local.Render(true) end end

function Shared.OnStart()
	task.spawn(function()
		local F = ReplicatedStorage:WaitForChild(`NHProgress`, 30)
		if not F then return end
		F:WaitForChild(`Updated`).OnClientEvent:Connect(function(S)
			if typeof(S) ~= `table` then return end
			Sheet = S
			if Ui and Ui.Gui.Enabled then FileAt = 0 Local.Render(true) end
		end)
	end)
	task.spawn(function()
		while true do
			task.wait(0.5)
			if Ui and Ui.Gui.Enabled and Player:GetAttribute(`InMainMenu`) == true then Ui.Gui.Enabled = false end
		end
	end)
	Player:GetAttributeChangedSignal(`Race`):Connect(function() if Ui and Ui.Gui.Enabled then Local.Dress() end end)
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