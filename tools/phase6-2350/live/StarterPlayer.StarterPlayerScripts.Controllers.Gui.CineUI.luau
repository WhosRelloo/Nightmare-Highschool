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
     (2.35.0) FadeHud(On, Seconds) (seamless cuts: no bars, the HUD fades), Dip(Seconds, AtBlack?) (seamless skip)
     (2.25.0) PromptShow(P, Opts), PromptHit(), PromptMeter(f), PromptHold(down), PromptHide(Outcome?), GradeCard(G, Perfects, Prompts, s)
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

-- (2.35.0) Fade (seconds, seamless cuts): a ScreenGui whose top level holds CanvasGroups (the UI kit's panels) fades
-- them out and is switched off at the end; any other GUI, and the core GUI, toggles at the midpoint. Without Fade
-- everything goes at once (the cut veils to black first).
local HudToken = 0
local CanvasWas = {} :: { [CanvasGroup]: number }
-- a faded restore still in flight: what each GUI / core setting goes back to (a new hide uses these as the originals,
-- not the half-restored state)
local PendingGui = {} :: { [Instance]: boolean }
local PendingCore: { [any]: any }? = nil

local function topGroups(G: Instance): { CanvasGroup }
	local Out = {}
	for _, Ch in G:GetChildren() do if Ch:IsA(`CanvasGroup`) then table.insert(Out, Ch) end end
	return Out
end

local function coreOff()
	if PendingCore then
		for K, V in PendingCore do SavedCore[K] = V end
		PendingCore = nil
	end
	for _, T in CORE do
		if SavedCore[T] ~= nil then pcall(StarterGui.SetCoreGuiEnabled, StarterGui, T, false) continue end
		local Ok, V = pcall(StarterGui.GetCoreGuiEnabled, StarterGui, T)
		SavedCore[T] = if Ok then V else true
		pcall(StarterGui.SetCoreGuiEnabled, StarterGui, T, false)
	end
	pcall(function()
		if SavedCore.ChatWindow == nil then SavedCore.ChatWindow = TextChatService.ChatWindowConfiguration.Enabled end
		if SavedCore.ChatInput == nil then SavedCore.ChatInput = TextChatService.ChatInputBarConfiguration.Enabled end
		TextChatService.ChatWindowConfiguration.Enabled = false
		TextChatService.ChatInputBarConfiguration.Enabled = false
	end)
end

local function coreBack()
	for T, V in SavedCore do
		if typeof(T) == `EnumItem` then pcall(StarterGui.SetCoreGuiEnabled, StarterGui, T, V) end
	end
	pcall(function()
		if SavedCore.ChatWindow ~= nil then TextChatService.ChatWindowConfiguration.Enabled = SavedCore.ChatWindow end
		if SavedCore.ChatInput ~= nil then TextChatService.ChatInputBarConfiguration.Enabled = SavedCore.ChatInput end
	end)
	table.clear(SavedCore)
end

function Local.HideOthers(Fade: number?)
	HudToken += 1
	local Token = HudToken
	local F = if Fade and Fade > 0 and not reduced() then Fade else 0
	local PG = Player:WaitForChild(`PlayerGui`)
	local function hide(G: Instance, Now: boolean?)
		if G == Ui.Gui or not G:IsA(`LayerCollector`) or Hidden[G] ~= nil then return end
		if PendingGui[G] ~= nil then Hidden[G] = PendingGui[G] PendingGui[G] = nil else Hidden[G] = (G :: any).Enabled end
		if F <= 0 or Now or not Hidden[G] then (G :: any).Enabled = false return end
		local Groups = topGroups(G)
		for _, CG in Groups do
			if CanvasWas[CG] == nil then CanvasWas[CG] = CG.GroupTransparency end
			tween(CG, F, { GroupTransparency = 1 }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
		end
		task.delay(if #Groups > 0 then F else F / 2, function()
			if Token == HudToken and Hidden[G] ~= nil and G.Parent then (G :: any).Enabled = false end
		end)
	end
	for _, G in PG:GetChildren() do hide(G) end
	table.clear(PendingGui)
	table.insert(Conns, PG.ChildAdded:Connect(function(G) if On then task.defer(function() if On then hide(G, true) end end) end end))
	if F > 0 then
		task.delay(F / 2, function() if Token == HudToken then coreOff() end end)
	else
		coreOff()
	end
end

function Local.RestoreOthers(Fade: number?)
	HudToken += 1
	local Token = HudToken
	local F = if Fade and Fade > 0 and not reduced() then Fade else 0
	for _, Cn in Conns do Cn:Disconnect() end
	table.clear(Conns)
	for G, Was in Hidden do
		if not G.Parent then continue end
		local Groups = topGroups(G)
		if F > 0 and Was and #Groups > 0 then
			pcall(function() (G :: any).Enabled = true end)
			for _, CG in Groups do
				local To = CanvasWas[CG] or 0
				tween(CG, F, { GroupTransparency = To }, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut)
			end
		elseif F > 0 and Was then
			PendingGui[G] = true
			task.delay(F / 2, function()
				if Token == HudToken and PendingGui[G] then
					PendingGui[G] = nil
					if G.Parent then pcall(function() (G :: any).Enabled = true end) end
				end
			end)
		else
			for _, CG in Groups do if CanvasWas[CG] then CG.GroupTransparency = CanvasWas[CG] end end
			pcall(function() (G :: any).Enabled = Was end)
		end
	end
	table.clear(Hidden)
	table.clear(CanvasWas)
	if F > 0 and next(SavedCore) then
		PendingCore = table.clone(SavedCore)
		table.clear(SavedCore)
		task.delay(F / 2, function()
			if Token ~= HudToken or not PendingCore then return end
			for K, V in PendingCore do SavedCore[K] = V end
			PendingCore = nil
			coreBack()
		end)
	else
		coreBack()
	end
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
	Ui.Bars = true
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
	local Rest = if Ui.Bars == false then UDim2.new(0.5, 0, 1, -24) else UDim2.new(0.5, 0, 1 - barShare(), -14)
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

---| prompts (2.25.0): drawn from the kit's seal, panel and frame art |---

local VERDICT = { Perfect = `PERFECT`; Good = `GOOD`; Miss = `MISS`; Win = `BROKE FREE`; Lose = `TOO SLOW`; Hit = `PERFECT`; Right = `DODGED`; Wrong = `MISSED` }
local GOOD_OUTCOME = { Perfect = true; Good = true; Win = true; Hit = true; Right = true }
local CRIMSON = Color3.fromRGB(200, 40, 60)

local function keyGlyph(Touch: boolean): string
	if Touch then return `TAP` end
	if UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled then return `A` end
	return `E`
end

local function sealButton(Name: string, Parent: Instance, Pos: UDim2, Size: number, Text: string, TextBase: number)
	local S = new(`ImageButton`, { Name = Name; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Wax; AutoButtonColor = false;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = Pos; Size = UDim2.fromOffset(Size, Size); ZIndex = 52 }, Parent)
	new(`TextLabel`, { Name = `Glyph`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; Text = Text; TextColor3 = C.Gold;
		TextSize = textSize(TextBase); Size = UDim2.fromScale(1, 1); ZIndex = 53 }, S)
	return S
end

local function tapWired(B: GuiButton, OnTap: (boolean) -> ())
	B.InputBegan:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.Touch or I.UserInputType == Enum.UserInputType.MouseButton1 then OnTap(true) end
	end)
	B.InputEnded:Connect(function(I)
		if I.UserInputType == Enum.UserInputType.Touch or I.UserInputType == Enum.UserInputType.MouseButton1 then OnTap(false) end
	end)
end

function Shared.PromptShow(P, Opts)
	if not Ui then Local.Build() end
	Ui.Gui.Enabled = true
	if Ui.Prompt then Ui.Prompt:Destroy() end
	local L = new(`CanvasGroup`, { Name = `Prompt`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.6); Size = UDim2.fromOffset(560, 300); GroupTransparency = 1; ZIndex = 50 }, Ui.Gui)
	Ui.Prompt = L
	local Parts = {}
	Ui.PromptParts = Parts
	local Kind = P.kind
	local Label = new(`TextLabel`, { Name = `Label`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextColor3 = C.Chalk; Text = ``;
		TextSize = textSize(22); AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.8); Size = UDim2.new(1, 0, 0, 34); ZIndex = 52 }, L)
	Parts.Label = Label
	if Kind == `Press` or Kind == `Mash` or Kind == `Hold` then
		local Key = sealButton(`Key`, L, UDim2.fromScale(0.5, 0.4), 108, keyGlyph(Opts.Touch), 30)
		Parts.Key = Key
		tapWired(Key, Opts.OnTap)
		Label.Text = if Kind == `Mash` then `MASH` elseif Kind == `Hold` then `HOLD, RELEASE ON THE SEAL` else (P.label or `NOW`)
		if Kind == `Press` or Kind == `Hold` then
			-- a faint seal where the closing seal lands; the closing seal shrinks onto it on the beat (Press) or, once the
			-- key is held, at the release mark (Hold)
			new(`ImageLabel`, { Name = `Zone`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Gold; ImageTransparency = 0.8;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = Key.Position; Size = UDim2.fromOffset(124, 124); ZIndex = 51 }, L)
			local Ring = new(`ImageLabel`, { Name = `Ring`; BackgroundTransparency = 1; Image = Img.Seal; ImageColor3 = C.Gold; ImageTransparency = 0.5;
				AnchorPoint = Vector2.new(0.5, 0.5); Position = Key.Position; Size = UDim2.fromOffset(264, 264); ZIndex = 51 }, L)
			Parts.Ring = Ring
			Parts.RingAt = if Kind == `Press` then (P.beat or 0.6) else (P.zoneAt or 1)
			if Kind == `Press` then tween(Ring, Parts.RingAt, { Size = UDim2.fromOffset(124, 124) }, Enum.EasingStyle.Linear) end
		else
			local Bar = new(`ImageLabel`, { Name = `Meter`; Image = Img.PanelBg; ImageColor3 = C.PanelTint; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.2;
				BorderSizePixel = 0; ScaleType = Enum.ScaleType.Stretch; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.93);
				Size = UDim2.fromOffset(340, 20); ZIndex = 52 }, L)
			Parts.Fill = new(`ImageLabel`, { Name = `Fill`; Image = Img.PanelBg; ImageColor3 = C.Gold; BackgroundTransparency = 1;
				ScaleType = Enum.ScaleType.Stretch; Size = UDim2.fromScale(0, 1); ZIndex = 53 }, Bar)
			Kit.Slice(`FrameThin`, C.GoldDeep, { Name = `Rim`; SliceScale = 0.2; ZIndex = 54; Parent = Bar })
		end
	elseif Kind == `Direction` then
		local Options = P.options or {}
		local KEY = { Left = `A`; Right = `D`; Up = `W`; Down = `S` }
		for I, Dir in Options do
			local X = (I - 0.5) / #Options
			local Glyph = if Opts.Touch then string.upper(Dir) else KEY[Dir] or Dir
			local S = sealButton(`Dir_{Dir}`, L, UDim2.fromScale(X, 0.4), 96, Glyph, if Opts.Touch then 20 else 30)
			S.Activated:Connect(function() Opts.OnPick(Dir) end)
			new(`TextLabel`, { Name = `Word`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; Text = string.upper(Dir); TextColor3 = C.Chalk;
				TextSize = textSize(20); AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 4); Size = UDim2.fromOffset(120, 24); ZIndex = 53 }, S)
		end
		Label.Text = P.label or `DODGE`
	elseif Kind == `Choice` then
		local Options = P.options or {}
		for I, O in Options do
			local B = Kit.Button({ text = `{I}   {O.text}`; style = `default`; onClick = function() Opts.OnPick(O.id) end;
				Size = UDim2.fromOffset(500, 50); Parent = L })
			B.AnchorPoint = Vector2.new(0.5, 0)
			B.Position = UDim2.new(0.5, 0, 0, 10 + (I - 1) * 58)
			B.ZIndex = 52
		end
		Label.Position = UDim2.fromScale(0.5, 0.86)
		Label.Text = ``
		local Bar = new(`ImageLabel`, { Name = `Timer`; Image = Img.PanelBg; ImageColor3 = C.Gold; BackgroundTransparency = 1; ScaleType = Enum.ScaleType.Stretch;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.95); Size = UDim2.fromOffset(500, 6); ZIndex = 52 }, L)
		tween(Bar, P.dur or 5, { Size = UDim2.fromOffset(0, 6) }, Enum.EasingStyle.Linear)
	end
	local Reduced = Opts.Reduced or reduced()
	if Reduced then L.GroupTransparency = 0 else
		local Sc = new(`UIScale`, { Scale = 0.9 }, L)
		tween(Sc, 0.14, { Scale = 1 }, Enum.EasingStyle.Back)
		tween(L, 0.12, { GroupTransparency = 0 })
	end
end

function Shared.PromptHit()
	local Parts = Ui and Ui.PromptParts
	pcall(Kit.PlaySound, `Stamp`, 0.4)
	local Key = Parts and Parts.Key
	if Key and not reduced() then
		Key.Size = UDim2.fromOffset(124, 124)
		tween(Key, 0.18, { Size = UDim2.fromOffset(108, 108) }, Enum.EasingStyle.Back)
	end
end

function Shared.PromptMeter(Fraction: number)
	local Fill = Ui and Ui.PromptParts and Ui.PromptParts.Fill
	if Fill then Fill.Size = UDim2.fromScale(math.clamp(Fraction, 0, 1), 1) end
end

function Shared.PromptHold(Down: boolean)
	local Parts = Ui and Ui.PromptParts
	if Down and Parts and Parts.Ring then
		tween(Parts.Ring, Parts.RingAt, { Size = UDim2.fromOffset(124, 124) }, Enum.EasingStyle.Linear)
	end
end

function Shared.PromptHide(Outcome: string?)
	if not (Ui and Ui.Prompt) then return end
	local L = Ui.Prompt
	Ui.Prompt = nil
	local Label = Ui.PromptParts and Ui.PromptParts.Label
	if Outcome and Label and VERDICT[Outcome] then
		Label.Text = VERDICT[Outcome]
		Label.TextColor3 = if GOOD_OUTCOME[Outcome] then C.Gold else CRIMSON
		task.delay(0.35, function() tween(L, 0.3, { GroupTransparency = 1 }) end)
		task.delay(0.8, function() L:Destroy() end)
	else
		L:Destroy()
	end
end

function Shared.GradeCard(Grade: string, Perfects: number, Prompts: number, Seconds: number)
	local Sub = if Prompts > 0 then `{Perfects} of {Prompts} perfect` else nil
	Shared.Card(`GRADE {Grade}`, Sub, Seconds)
end

function Shared.Hide(Seconds: number?)
	if not Ui then return end
	if Ui.Prompt then Ui.Prompt:Destroy() Ui.Prompt = nil end
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

-- (2.35.0) seamless cuts: no bars; the rest of the HUD fades out and back in (spec §2.1 / §4.1). The cut's own pieces
-- (subtitles, card, skip, prompts) still show; Off puts everything back like Hide, faded.
function Shared.FadeHud(Show: boolean, Seconds: number)
	if not Ui then Local.Build() end
	if Show then
		On = true
		Local.HideOthers(Seconds)
		Ui.Gui.Enabled = true
		Ui.Group = false
		Ui.Voted = false
		Ui.Bars = false
		Ui.Top.Size = UDim2.fromScale(1, 0)
		Ui.Bottom.Size = UDim2.fromScale(1, 0)
		Ui.Sub.Position = UDim2.new(0.5, 0, 1, -24)
		Ui.Sub.GroupTransparency = 1
		Ui.Card.GroupTransparency = 1
	else
		if Ui.Prompt then Ui.Prompt:Destroy() Ui.Prompt = nil end
		On = false
		Ui.Skip.Visible = false
		tween(Ui.Sub, 0.2, { GroupTransparency = 1 })
		tween(Ui.Card, 0.2, { GroupTransparency = 1 })
		Local.RestoreOthers(Seconds)
		task.delay(Seconds + 0.05, function()
			if not On and Ui and Ui.Veil.BackgroundTransparency >= 0.99 then Ui.Gui.Enabled = false end
		end)
	end
end

-- (2.35.0) the one black in a seamless cut: skip's jump to the end state (spec §2.3). AtBlack (optional) runs while the
-- screen is fully black (the actor placed, the camera handed back), then the veil lifts.
function Shared.Dip(Seconds: number, AtBlack: (() -> ())?)
	if not Ui then Local.Build() end
	Ui.Gui.Enabled = true
	Shared.Veil(1, Seconds / 2)
	task.wait(Seconds / 2)
	Ui.Veil.BackgroundTransparency = 0
	if AtBlack then
		local Ok, Err = pcall(AtBlack)
		if not Ok then warn(`[CineUI] Dip: {Err}`) end
	end
	Shared.Veil(0, Seconds / 2)
end

function Shared.IsOn(): boolean return On end

function Shared.OnStart()
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if not On then return end
		if Input.KeyCode == Enum.KeyCode.Escape or Input.KeyCode == Enum.KeyCode.ButtonB then Local.FireSkip() end
	end)
end

return Shared
