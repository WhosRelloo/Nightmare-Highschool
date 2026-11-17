--[[
	CineUI (client, Phase 1 / 2.24.0). Controllers.Gui.CineUI: the screen side of a story cut (Controllers.Cine drives it).

	  * The frame: black letterbox bars (thinner on a narrow phone screen) with a film-gate edge: the kit's gold rule and
	    divider art along the inner edge, and the school's brass bell hanging at the top bar's centre. The bell swings
	    when the cut's bell rings (Ring).
	  * Subtitles, bottom third: an ink plate cut from the kit's panel art (PanelBg, FrameThin) with a wax seal in the
	    speaker's colour, the speaker in gold capitals and the line in chalk Garamond. Every spoken line shows: it rises in,
	    types out at reading pace and settles out. The text never goes below 20 px at the kit's AutoScale.
	  * Chapter card: the crest, a letter-spaced title, a divider and a sub-line, breathing in and out (Card).
	  * Skip: a large wax-seal button (Esc, gamepad B or a tap) once the cut may be skipped; in a group cut it's a vote
	    with a pip per viewer ("2 of 3 to skip").
	  * A black veil for fades between the menu, the cut and gameplay (Veil).
	Every other piece of screen UI is switched off while a cut plays and put back as it was afterwards.

	API: Show(Opts), Hide(), Subtitle(Speaker, Text, Seconds, Color?), Card(Title, Sub, Seconds), Veil(Alpha, Seconds),
	     Votes(Votes, Need, Voted), SetSkippable(bool), Ring(), OnSkip(fn)
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local StarterGui = game:GetService(`StarterGui`)
local TextChatService = game:GetService(`TextChatService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local RunService = game:GetService(`RunService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Img = Theme.Images
local CORE = { Enum.CoreGuiType.Chat, Enum.CoreGuiType.PlayerList, Enum.CoreGuiType.EmotesMenu, Enum.CoreGuiType.Backpack }

local Shared = {}
local Local = {}
local Ui = nil
local On = false
local SkipFns = {} :: { () -> () }
local Hidden = {} :: { [Instance]: boolean }
local Conns = {} :: { RBXScriptConnection }
local SavedCore = {}
local SubToken = 0

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do (I :: any)[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function tween(I: Instance, T: number, Props, Style: Enum.EasingStyle?, Dir: Enum.EasingDirection?)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Style or Enum.EasingStyle.Quart, Dir or Enum.EasingDirection.Out), Props)
	Tw:Play()
	return Tw
end

local function reduced(): boolean
	local Ok, R = pcall(Kit.ReducedMotion)
	return Ok and R == true
end

-- the bars' height as a share of the screen: a 2.2:1 frame on 16:9, thinner on narrow (tall) phone screens
local function barShare(): number
	local Cam = workspace.CurrentCamera
	local V = Cam and Cam.ViewportSize or Vector2.new(1920, 1080)
	local Aspect = V.X / math.max(V.Y, 1)
	return if Aspect < 1.5 then 0.06 else 0.11
end

local function textSize(Base: number): number
	local Cam = workspace.CurrentCamera
	local V = Cam and Cam.ViewportSize or Vector2.new(1920, 1080)
	local Scale = math.clamp(V.Y / 1080, 0.6, 1.4)
	return math.max(20, math.floor(Base * Scale + 0.5)) -- doc 04 §7: never below 20 px
end

---| building |---

function Local.Build()
	local G = new(`ScreenGui`, { Name = `NHCineUI`; ResetOnSpawn = false; IgnoreGuiInset = true; DisplayOrder = 1100; Enabled = false;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, Player:WaitForChild(`PlayerGui`))
	G:SetAttribute(`ShowInCinematic`, true)

	-- the veil (fades); under the bars so the frame stays crisp over black
	local Veil = new(`Frame`, { Name = `Veil`; BackgroundColor3 = Color3.new(0, 0, 0); BorderSizePixel = 0; Size = UDim2.fromScale(1, 1);
		BackgroundTransparency = 1; ZIndex = 1 }, G)

	local function bar(Top: boolean)
		local B = new(`Frame`, { Name = if Top then `Top` else `Bottom`; BackgroundColor3 = Color3.new(0, 0, 0); BorderSizePixel = 0;
			AnchorPoint = Vector2.new(0, if Top then 0 else 1); Position = UDim2.fromScale(0, if Top then 0 else 1);
			Size = UDim2.fromScale(1, 0); ZIndex = 5; ClipsDescendants = false }, G)
		-- film-gate edge: the kit's divider art on a gold rule, fading to the sides
		local Rule = new(`Frame`, { Name = `Rule`; BackgroundColor3 = C.Gold; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, if Top then 1 else 0);
			Position = UDim2.fromScale(0.5, if Top then 1 else 0); Size = UDim2.new(0.9, 0, 0, 1); ZIndex = 6 }, B)
		new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.25, 0.45),
			NumberSequenceKeypoint.new(0.5, 0.05), NumberSequenceKeypoint.new(0.75, 0.45), NumberSequenceKeypoint.new(1, 1) }) }, Rule)
		new(`ImageLabel`, { Name = `Divider`; BackgroundTransparency = 1; Image = Img.Divider; ImageColor3 = C.GoldDeep; ImageTransparency = 0.15;
			ScaleType = Enum.ScaleType.Fit; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, if Top then 1 else 0);
			Size = UDim2.fromOffset(260, 18); ZIndex = 7 }, B)
		return B
	end
	local Top, Bottom = bar(true), bar(false)
	-- the brass bell hanging from the top bar (it swings on Ring)
	local BellPivot = new(`Frame`, { Name = `BellPivot`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0);
		Position = UDim2.fromScale(0.5, 1); Size = UDim2.fromOffset(2, 2); ZIndex = 8 }, Top)
	local Bell = new(`ImageLabel`, { Name = `Bell`; BackgroundTransparency = 1; Image = Img.Bell; ImageColor3 = C.Gold;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromOffset(1, -6); Size = UDim2.fromOffset(30, 30); ZIndex = 8 }, BellPivot)

	-- subtitles: an ink plate cut from the kit's panel art, with a wax seal for the speaker
	local Sub = new(`CanvasGroup`, { Name = `Subtitle`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 1);
		Position = UDim2.new(0.5, 0, 1, -20); Size = UDim2.new(0.62, 0, 0, 96); GroupTransparency = 1; ZIndex = 20 }, G)
	new(`UISizeConstraint`, { MinSize = Vector2.new(300, 70); MaxSize = Vector2.new(1100, 160) }, Sub)
	new(`ImageLabel`, { Name = `Plate`; Image = Img.PanelBg; ImageColor3 = C.PanelTint; ImageTransparency = 0.18; BackgroundColor3 = C.Ink;
		BackgroundTransparency = 0.2; BorderSizePixel = 0; ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromScale(1, 1); ZIndex = 20 }, Sub)
	Kit.Slice(`FrameThin`, C.GoldDeep, { Name = `Rim`; SliceScale = 0.3; ImageTransparency = 0.2; ZIndex = 21; Parent = Sub })
	local Seal = new(`ImageLabel`, { Name = `Seal`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Wax;
		AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 14, 0.5, 0); Size = UDim2.fromOffset(40, 40); ZIndex = 22 }, Sub)
	local Speaker = new(`TextLabel`, { Name = `Speaker`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; Text = ``; TextColor3 = C.Gold;
		TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromOffset(66, 10); Size = UDim2.new(1, -86, 0, 24); ZIndex = 22 }, Sub)
	local Line = new(`TextLabel`, { Name = `Line`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; Text = ``; TextColor3 = C.Chalk;
		TextWrapped = true; TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top;
		Position = UDim2.fromOffset(66, 36); Size = UDim2.new(1, -86, 1, -42); ZIndex = 22 }, Sub)

	-- chapter card
	local Card = new(`CanvasGroup`, { Name = `Card`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.46); Size = UDim2.fromOffset(720, 220); GroupTransparency = 1; ZIndex = 30 }, G)
	local CardScale = new(`UIScale`, { Scale = 1 }, Card)
	new(`ImageLabel`, { Name = `Crest`; BackgroundTransparency = 1; Image = Img.Crest; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0); Size = UDim2.fromOffset(78, 78); ZIndex = 30 }, Card)
	local CardTitle = new(`TextLabel`, { Name = `Title`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; Text = ``; TextColor3 = C.Gold;
		TextScaled = true; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromOffset(360, 86); Size = UDim2.fromOffset(700, 52); ZIndex = 30 }, Card)
	new(`UITextSizeConstraint`, { MaxTextSize = 46; MinTextSize = 22 }, CardTitle)
	new(`ImageLabel`, { Name = `Divider`; BackgroundTransparency = 1; Image = Img.Divider; ImageColor3 = C.GoldDeep; ScaleType = Enum.ScaleType.Fit;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromOffset(360, 142); Size = UDim2.fromOffset(340, 20); ZIndex = 30 }, Card)
	local CardSub = new(`TextLabel`, { Name = `Sub`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; Text = ``; TextColor3 = C.Chalk;
		TextSize = 24; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromOffset(360, 166); Size = UDim2.fromOffset(700, 30); ZIndex = 30 }, Card)

	-- skip: a big wax-seal button (a large tap target on phones)
	local Skip = new(`ImageButton`, { Name = `Skip`; BackgroundTransparency = 1; Image = ``; AutoButtonColor = false; AnchorPoint = Vector2.new(1, 1);
		Position = UDim2.new(1, -28, 1, -28); Size = UDim2.fromOffset(190, 64); Visible = false; ZIndex = 40 }, G)
	new(`ImageLabel`, { Name = `Plate`; Image = Img.PanelBg; ImageColor3 = C.PanelTint; ImageTransparency = 0.1; BackgroundColor3 = C.Ink;
		BackgroundTransparency = 0.15; BorderSizePixel = 0; ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromScale(1, 1); ZIndex = 40 }, Skip)
	Kit.Slice(`FrameThin`, C.Gold, { Name = `Rim`; SliceScale = 0.28; ImageTransparency = 0.25; ZIndex = 41; Parent = Skip })
	local SkipSeal = new(`ImageLabel`, { Name = `Seal`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Wax;
		AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 8, 0.5, 0); Size = UDim2.fromOffset(48, 48); ZIndex = 42 }, Skip)
	local SkipText = new(`TextLabel`, { Name = `Text`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; Text = `SKIP`; TextColor3 = C.Gold;
		TextSize = 22; TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromOffset(64, 8); Size = UDim2.new(1, -70, 0, 26); ZIndex = 42 }, Skip)
	local SkipHint = new(`TextLabel`, { Name = `Hint`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; Text = ``; TextColor3 = C.TextDim;
		TextSize = 20; TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.fromOffset(64, 33); Size = UDim2.new(1, -70, 0, 22); ZIndex = 42 }, Skip)
	local Pips = new(`Frame`, { Name = `Pips`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 6);
		Size = UDim2.fromOffset(180, 12); ZIndex = 42 }, Skip)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; HorizontalAlignment = Enum.HorizontalAlignment.Center; Padding = UDim.new(0, 6) }, Pips)
	Skip.MouseEnter:Connect(function() tween(SkipSeal, 0.15, { Size = UDim2.fromOffset(52, 52) }) end)
	Skip.MouseLeave:Connect(function() tween(SkipSeal, 0.15, { Size = UDim2.fromOffset(48, 48) }) end)
	Skip.Activated:Connect(function() Local.FireSkip() end)

	Ui = { Gui = G; Veil = Veil; Top = Top; Bottom = Bottom; Bell = Bell; BellPivot = BellPivot; Sub = Sub; Seal = Seal; Speaker = Speaker;
		Line = Line; Card = Card; CardScale = CardScale; CardTitle = CardTitle; CardSub = CardSub; Skip = Skip; SkipSeal = SkipSeal;
		SkipText = SkipText; SkipHint = SkipHint; Pips = Pips; Group = false; Voted = false }
end

---| everything else off while a cut plays |---

function Local.HideOthers()
	local PG = Player:WaitForChild(`PlayerGui`)
	local function hide(G: Instance)
		if G == Ui.Gui or not G:IsA(`LayerCollector`) or Hidden[G] ~= nil then return end
		Hidden[G] = (G :: any).Enabled
		;(G :: any).Enabled = false
	end
	for _, G in PG:GetChildren() do hide(G) end
	table.insert(Conns, PG.ChildAdded:Connect(function(G) if On then task.defer(function() if On then hide(G) end end) end end))
	for _, T in CORE do
		local Ok, V = pcall(StarterGui.GetCoreGuiEnabled, StarterGui, T)
		SavedCore[T] = if Ok then V else true
		pcall(StarterGui.SetCoreGuiEnabled, StarterGui, T, false)
	end
	pcall(function()
		SavedCore.ChatWindow = TextChatService.ChatWindowConfiguration.Enabled
		SavedCore.ChatInput = TextChatService.ChatInputBarConfiguration.Enabled
		TextChatService.ChatWindowConfiguration.Enabled = false
		TextChatService.ChatInputBarConfiguration.Enabled = false
	end)
end

function Local.RestoreOthers()
	for _, Cn in Conns do Cn:Disconnect() end
	table.clear(Conns)
	for G, Was in Hidden do
		if G.Parent then pcall(function() (G :: any).Enabled = Was end) end
	end
	table.clear(Hidden)
	for T, V in SavedCore do
		if typeof(T) == `EnumItem` then pcall(StarterGui.SetCoreGuiEnabled, StarterGui, T, V) end
	end
	pcall(function()
		if SavedCore.ChatWindow ~= nil then TextChatService.ChatWindowConfiguration.Enabled = SavedCore.ChatWindow end
		if SavedCore.ChatInput ~= nil then TextChatService.ChatInputBarConfiguration.Enabled = SavedCore.ChatInput end
	end)
	table.clear(SavedCore)
end

---| skip input |---

function Local.FireSkip()
	if not (On and Ui and Ui.Skip.Visible) then return end
	if Ui.Group and Ui.Voted then return end
	pcall(Kit.PlaySound, `Stamp`, 0.5)
	if not reduced() then
		Ui.SkipSeal.Rotation = -12
		tween(Ui.SkipSeal, 0.35, { Rotation = 0 }, Enum.EasingStyle.Back)
	end
	for _, Fn in SkipFns do task.spawn(Fn) end
end

---| API |---

function Shared.OnSkip(Fn: () -> ()) table.insert(SkipFns, Fn) end

function Shared.Show(Opts)
	if not Ui then Local.Build() end
	Opts = Opts or {}
	On = true
	Local.HideOthers()
	Ui.Gui.Enabled = true
	Ui.Group = Opts.Group == true
	Ui.Voted = false
	local Share = barShare()
	local T = if reduced() then 0.01 else 0.7
	Ui.Top.Size = UDim2.fromScale(1, 0)
	Ui.Bottom.Size = UDim2.fromScale(1, 0)
	tween(Ui.Top, T, { Size = UDim2.fromScale(1, Share) })
	tween(Ui.Bottom, T, { Size = UDim2.fromScale(1, Share) })
	Ui.Sub.Position = UDim2.new(0.5, 0, 1 - Share, -14)
	Ui.Sub.GroupTransparency = 1
	Ui.Card.GroupTransparency = 1
	Shared.SetSkippable(Opts.Skippable == true or Ui.Group, Opts.Votes, Opts.Need)
end

function Shared.SetSkippable(Can: boolean, Votes: number?, Need: number?)
	if not Ui then return end
	local Pad = UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled
	local Touch = UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled
	Ui.SkipHint.Text = if Pad then `B to skip` elseif Touch then `tap to skip` else `Esc to skip`
	Ui.SkipText.Text = if Ui.Group then `VOTE SKIP` else `SKIP`
	if Can and not Ui.Skip.Visible then
		Ui.Skip.Visible = true
		if not reduced() then
			Ui.Skip.Position = UDim2.new(1, -28, 1, 10)
			tween(Ui.Skip, 0.45, { Position = UDim2.new(1, -28, 1, -28) }, Enum.EasingStyle.Back)
		end
	elseif not Can then
		Ui.Skip.Visible = false
	end
	if Ui.Group then Shared.Votes(Votes or 0, Need or 1, Ui.Voted) end
end

-- group cuts: one pip per vote needed, lit for each vote cast
function Shared.Votes(Votes: number, Need: number, Voted: boolean?)
	if not Ui then return end
	if Voted ~= nil then Ui.Voted = Voted end
	for _, P in Ui.Pips:GetChildren() do if P:IsA(`ImageLabel`) then P:Destroy() end end
	for I = 1, math.max(Need, 1) do
		local Lit = I <= Votes
		local Pip = new(`ImageLabel`, { BackgroundTransparency = 1; Image = Img.Pip; ImageColor3 = if Lit then C.Gold else C.Off;
			Size = UDim2.fromOffset(12, 12); ZIndex = 43 }, Ui.Pips)
		if Lit and not reduced() then Kit.tween(Pip, 0.25, { Size = UDim2.fromOffset(14, 14) }) end
	end
	Ui.SkipHint.Text = `{Votes} of {Need} to skip`
	if Ui.Voted then Ui.SkipText.Text = `VOTED` end
end

function Shared.Subtitle(Speaker: string, Text: string, Seconds: number, Color: Color3?)
	if not Ui then return end
	SubToken += 1
	local Token = SubToken
	local Sz = textSize(26)
	Ui.Line.TextSize = Sz
	Ui.Speaker.TextSize = math.max(20, Sz - 4)
	Ui.Speaker.Text = string.upper(Speaker)
	Ui.Line.Text = Text
	Ui.Seal.ImageColor3 = Color or C.Wax
	Ui.Sub.Size = UDim2.new(0.62, 0, 0, Sz * 2 + 54)
	local Reduced = reduced()
	local Rest = UDim2.new(0.5, 0, 1 - barShare(), -14)
	if Ui.Sub.GroupTransparency > 0.9 then
		Ui.Sub.Position = if Reduced then Rest else Rest + UDim2.fromOffset(0, 10)
		tween(Ui.Sub, 0.3, { GroupTransparency = 0; Position = Rest })
	end
	-- types out at reading pace (about 45 letters a second), never longer than half the line's time
	local N = utf8.len(Text) or #Text
	Ui.Line.MaxVisibleGraphemes = if Reduced then -1 else 0
	if not Reduced then
		local TypeTime = math.min(N / 45, Seconds * 0.5)
		local T0 = os.clock()
		task.spawn(function()
			while Token == SubToken and os.clock() - T0 < TypeTime do
				Ui.Line.MaxVisibleGraphemes = math.floor(N * (os.clock() - T0) / TypeTime)
				RunService.RenderStepped:Wait()
			end
			if Token == SubToken then Ui.Line.MaxVisibleGraphemes = -1 end
		end)
	end
	Ui.Seal.Rotation = if Reduced then 0 else -18
	if not Reduced then tween(Ui.Seal, 0.4, { Rotation = 0 }, Enum.EasingStyle.Back) end
	task.delay(Seconds, function()
		if Token ~= SubToken or not Ui then return end
		tween(Ui.Sub, 0.35, { GroupTransparency = 1 }, Enum.EasingStyle.Sine)
	end)
end

function Shared.ClearSubtitle()
	if not Ui then return end
	SubToken += 1
	tween(Ui.Sub, 0.2, { GroupTransparency = 1 })
end

function Shared.Card(Title: string, Sub: string?, Seconds: number)
	if not Ui then return end
	Ui.CardTitle.Text = Title
	Ui.CardSub.Text = Sub or ``
	local Reduced = reduced()
	Ui.CardScale.Scale = if Reduced then 1 else 0.96
	Ui.Card.GroupTransparency = 1
	tween(Ui.Card, 0.9, { GroupTransparency = 0 }, Enum.EasingStyle.Sine)
	if not Reduced then tween(Ui.CardScale, Seconds, { Scale = 1.03 }, Enum.EasingStyle.Sine) end
	task.delay(math.max(0.5, Seconds - 0.8), function()
		if Ui then tween(Ui.Card, 0.8, { GroupTransparency = 1 }, Enum.EasingStyle.Sine) end
	end)
end

function Shared.Veil(Alpha: number, Seconds: number)
	if not Ui then Local.Build() end
	Ui.Gui.Enabled = true
	if Seconds <= 0 then Ui.Veil.BackgroundTransparency = 1 - Alpha return end
	tween(Ui.Veil, Seconds, { BackgroundTransparency = 1 - Alpha }, Enum.EasingStyle.Sine)
end

-- the bell at the top of the frame swings when the cut's bell rings
function Shared.Ring()
	if not Ui or reduced() then return end
	local P = Ui.BellPivot
	task.spawn(function()
		for I, A in { 22, -16, 10, -6, 3, 0 } do
			tween(P, 0.18 + I * 0.03, { Rotation = A }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut).Completed:Wait()
		end
	end)
end

function Shared.Hide(Seconds: number?)
	if not Ui then return end
	local T = Seconds or 0.45
	On = false
	Ui.Skip.Visible = false
	tween(Ui.Top, T, { Size = UDim2.fromScale(1, 0) }, Enum.EasingStyle.Quart, Enum.EasingDirection.In)
	tween(Ui.Bottom, T, { Size = UDim2.fromScale(1, 0) }, Enum.EasingStyle.Quart, Enum.EasingDirection.In)
	tween(Ui.Sub, 0.2, { GroupTransparency = 1 })
	tween(Ui.Card, 0.2, { GroupTransparency = 1 })
	Local.RestoreOthers()
	task.delay(T + 0.05, function()
		if not On and Ui and Ui.Veil.BackgroundTransparency >= 0.99 then Ui.Gui.Enabled = false end
	end)
end

function Shared.IsOn(): boolean return On end

function Shared.OnStart()
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if not On then return end
		if Input.KeyCode == Enum.KeyCode.Escape or Input.KeyCode == Enum.KeyCode.ButtonB then Local.FireSkip() end
	end)
end

return Shared
