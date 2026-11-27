--[[
	Class activities (client)

	Chalkboard-style lesson screen: intro card with 3-2-1, the minigame (child modules of this
	script, one per activity type), a lesson timer, and a graded result sheet with a red-ink stamp.
	The server decides everything that matters (questions, judging, grade, rewards); this only draws
	and sends inputs. Every game works with mouse/touch as well as keys, and with a controller: its buttons are selected
	with the D-pad and pressed with A (Controllers.Gui.GamepadControls treats the lesson as a menu; NHPadFirst marks where
	the selection starts, "Leave lesson" is never picked first). B is Shared.PadBack: the game's own back (renderer:PadBack),
	or closing the report card. Renderers get Api.Pad() / Api.KeyName / Api.PadText / Api.InputKindChanged for hints.

	Renderer interface (child ModuleScripts):
		Renderer.new(Content: Frame, Payload, Api) -> object with :Update(Payload) and :Destroy()
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local StarterGui = game:GetService(`StarterGui`)
local TweenService = game:GetService(`TweenService`)
local GuiService = game:GetService(`GuiService`)

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit (board frame)

local Player = Players.LocalPlayer

local Theme = {
	Board = Color3.fromRGB(34, 60, 46);
	BoardDark = Color3.fromRGB(24, 44, 34);
	Wood = Color3.fromRGB(112, 74, 42);
	Chalk = Color3.fromRGB(238, 241, 232);
	ChalkDim = Color3.fromRGB(170, 185, 170);
	ChalkYellow = Color3.fromRGB(250, 222, 120);
	ChalkBlue = Color3.fromRGB(150, 200, 255);
	ChalkPink = Color3.fromRGB(255, 160, 185);
	ChalkGreen = Color3.fromRGB(150, 235, 160);
	Good = Color3.fromRGB(120, 220, 130);
	Bad = Color3.fromRGB(255, 110, 100);
	Paper = Color3.fromRGB(250, 244, 225);
	Ink = Color3.fromRGB(40, 40, 60);
	RedInk = Color3.fromRGB(205, 35, 35);
	-- kit typography: the kit's title face on the board, its book face for everything secondary
	TitleFont = Kit.Theme.Fonts.Title;
	ChalkFont = Kit.Theme.Fonts.Title;
	HandFont = Kit.Theme.Fonts.Body;
	-- kit colours for framing
	Gold = Kit.Theme.Colors.Gold;
	Iron = Kit.Theme.Colors.Iron;
	Frame = Kit.Theme.Colors.Gold:Lerp(Kit.Theme.Colors.Iron, 0.55);
	Crimson = Kit.Theme.Colors.Crimson;
	SealImage = (function()
		local Id = Kit.Theme.Images.IconCardBack -- the memory card back (it was the kit seal)
		return if typeof(Id) == `number` then `rbxassetid://{Id}` else tostring(Id or ``)
	end)();
}

local Local = {}
local Shared = {}

Shared.Theme = Theme

local Current = nil -- active lesson

---| UI helpers (also used by renderers) |---

function Shared.Label(Parent: Instance, Props: { [string]: any }): TextLabel
	local Label = Instance.new(`TextLabel`)
	Label.BackgroundTransparency = 1
	Label.Font = Theme.ChalkFont
	Label.TextColor3 = Theme.Chalk
	Label.TextScaled = true
	Label.Text = ``
	for Key, Value in Props do (Label :: any)[Key] = Value end
	Label.Parent = Parent
	return Label
end

-- Kit slot: dark well, iron-gold FrameSlot border, soft top light. Hover: gold frame and a slight
-- lift; press: sinks. Games still tint BackgroundColor3 / TextColor3 for their states.
function Shared.Button(Parent: Instance, Text: string, Props: { [string]: any }?): TextButton
	local Button = Instance.new(`TextButton`)
	Button.AutoButtonColor = false
	Button.BackgroundColor3 = Theme.BoardDark
	Button.BorderSizePixel = 0
	Button.Font = Theme.ChalkFont
	Button.TextColor3 = Theme.Chalk
	Button.TextScaled = true
	Button.Text = Text

	local Corner = Instance.new(`UICorner`)
	Corner.CornerRadius = UDim.new(0, 4)
	Corner.Parent = Button

	local Light = Instance.new(`UIGradient`)
	Light.Rotation = 90
	Light.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(196, 196, 196))
	Light.Parent = Button

	local Edge = Kit.Slice(`FrameSlot`, Theme.Frame, { SliceScale = 0.36, Parent = Button })
	if Edge then
		Edge.Name = `Edge`
		-- undo the button's text padding (left/right 6%, top/bottom 12%) so the frame covers the whole button
		Edge.Size = UDim2.fromScale(1 / 0.88, 1 / 0.76)
		Edge.Position = UDim2.fromScale(-0.06 / 0.88, -0.12 / 0.76)
	end
	local Stroke = { Transparency = 0 } -- (kept for the hover code below)

	Button.Activated:Connect(function() Kit.PlaySound(`Tick`, 0.45, 1.4) end) -- chalk tap

	local Padding = Instance.new(`UIPadding`)
	Padding.PaddingTop = UDim.new(0.12, 0)
	Padding.PaddingBottom = UDim.new(0.12, 0)
	Padding.PaddingLeft = UDim.new(0.06, 0)
	Padding.PaddingRight = UDim.new(0.06, 0)
	Padding.Parent = Button

	local Scale = Instance.new(`UIScale`)
	Scale.Parent = Button
	local Hover = false
	local function Lift(To: number)
		if Kit.ReducedMotion() then Scale.Scale = 1 return end
		TweenService:Create(Scale, TweenInfo.new(0.12, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = To }):Play()
	end
	Button.MouseEnter:Connect(function()
		Hover = true
		if Edge then Edge.ImageColor3 = Theme.Gold end
		Lift(1.035)
	end)
	Button.MouseLeave:Connect(function()
		Hover = false
		if Edge then Edge.ImageColor3 = Theme.Frame end
		Lift(1)
	end)
	Button.MouseButton1Down:Connect(function() Lift(0.95) end)
	Button.MouseButton1Up:Connect(function() Lift(if Hover then 1.035 else 1) end)
	_ = Stroke

	for Key, Value in Props or {} do (Button :: any)[Key] = Value end
	Button.Parent = Parent
	return Button
end

-- Quick scale "pop" for feedback.
function Shared.Pop(Object: GuiObject, Amount: number?)
	local Scale = Object:FindFirstChildOfClass(`UIScale`) or Instance.new(`UIScale`)
	Scale.Parent = Object
	Scale.Scale = Amount or 1.25
	TweenService:Create(Scale, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
end

---| Lesson screen |---

function Local.BuildScreen(Message)
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `Lesson`
	Gui.ResetOnSpawn = false
	Gui.IgnoreGuiInset = true
	Gui.DisplayOrder = 20

	local Dim = Instance.new(`Frame`)
	Dim.Name = `Dim`
	Dim:SetAttribute(`NHNotPanel`, true) -- (GamepadControls: the board is the panel)
	Dim.Size = UDim2.fromScale(1, 1)
	Dim.BackgroundColor3 = Color3.new(0, 0, 0)
	Dim.BackgroundTransparency = 0.45
	Dim.Parent = Gui

	local Board = Instance.new(`Frame`)
	Board.Name = `Board`
	Board.AnchorPoint = Vector2.new(0.5, 0.5)
	Board.Position = UDim2.fromScale(0.5, 0.5)
	Board.Size = UDim2.fromScale(0.92, 0.86)
	Board.BackgroundColor3 = Theme.Board
	Board.Parent = Gui

	local Limit = Instance.new(`UISizeConstraint`)
	Limit.MaxSize = Vector2.new(960, 640)
	Limit.Parent = Board

	-- NH kit frame: iron ornament + slate texture tinted chalkboard green (replaces the wood stroke).
	Kit.Decorate(Board, { ornamentScale = 0.8; bgColor = Color3.fromRGB(84, 132, 104) })

	-- Header: the lesson's name on a gold kit plate hanging from the frame, subject and level under it
	local TitlePlate, TitleApi = Kit.Plate({
		Name = `TitlePlate`; text = string.upper(tostring(Message.Title or ``)); autoWidth = true;
		color = Theme.Gold; textSize = 26; frameColor = Theme.Gold:Lerp(Theme.Iron, 0.3);
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0, 4); Size = UDim2.fromOffset(0, 46);
		Parent = Board;
	})
	local Title = TitleApi.Label
	Kit.Emboss(Title, Color3.fromRGB(150, 118, 70), 1.3)
	local Sub = Shared.Label(Board, {
		Name = `Subtitle`; Font = Theme.HandFont; TextColor3 = Theme.ChalkDim;
		Position = UDim2.fromScale(0.25, 0.068); Size = UDim2.fromScale(0.5, 0.042);
		Text = (if Message.Study then `Night Study  ·  ` else ``) .. `{Message.Subject}  ·  Level {Message.Level}` .. (if Message.Practice then `  ·  practice (already passed this period)` else ``)
			.. (if Message.Substitute then `  ·  Substitute: {Message.Substitute.Name}, {Message.Substitute.Rule}` else ``); -- (1.47)
	})
	local MaxSub = Instance.new(`UITextSizeConstraint`)
	MaxSub.MaxTextSize = 20
	MaxSub.Parent = Sub

	-- Score (left) and the lesson clock (right) on kit plates
	local function HeaderPlate(Name: string, Anchor: number, X: number)
		local Root, PlateApi = Kit.Plate({
			Name = Name; text = ``; color = Theme.Gold; frameColor = Theme.Frame;
			AnchorPoint = Vector2.new(Anchor, 0); Position = UDim2.fromScale(X, 0.04); Size = UDim2.fromScale(0.2, 0.072);
			Parent = Board;
		})
		local Label = PlateApi.Label
		Label.Size = UDim2.fromScale(1, 1)
		Label.TextScaled = true
		local Max = Instance.new(`UITextSizeConstraint`)
		Max.MaxTextSize = 24
		Max.Parent = Label
		local Pad = Instance.new(`UIPadding`)
		Pad.PaddingTop, Pad.PaddingBottom = UDim.new(0.18, 0), UDim.new(0.14, 0)
		Pad.Parent = Label
		return Root, Label
	end
	local ScorePlate, Score = HeaderPlate(`ScorePlate`, 0, 0.04)
	Score.TextColor3 = Theme.Chalk
	Score.Text = `Score: \u{2013}`
	local ClockPlate, Timer = HeaderPlate(`ClockPlate`, 1, 0.96)
	Timer.Size = UDim2.new(1, -28, 1, 0)
	Timer.Position = UDim2.fromOffset(26, 0)
	local Limit0 = tonumber(Message.TimeLimit) or 60
	Timer.Text = string.format(`%d:%02d`, Limit0 // 60, Limit0 % 60)
	local Candle = Instance.new(`ImageLabel`) -- the kit's candle: the lesson burning down
	Candle.Name = `Candle`
	Candle.BackgroundTransparency = 1
	local CandleId = Kit.Theme.Images.IconCandle
	Candle.Image = if typeof(CandleId) == `number` then `rbxassetid://{CandleId}` else tostring(CandleId or ``)
	Candle.ImageColor3 = Theme.Gold
	Candle.AnchorPoint = Vector2.new(0, 0.5)
	Candle.Position = UDim2.new(0, 10, 0.5, 0)
	Candle.Size = UDim2.fromScale(0.6, 0.6)
	Candle.ZIndex = 12
	local CandleAspect = Instance.new(`UIAspectRatioConstraint`)
	CandleAspect.DominantAxis = Enum.DominantAxis.Height
	CandleAspect.Parent = Candle
	Candle.Parent = ClockPlate

	-- the lesson's time, burning down under the header (gold, crimson for the last 10 s)
	local TimeBar = Instance.new(`Frame`)
	TimeBar.Name = `TimeBar`
	TimeBar.BackgroundColor3 = Kit.Theme.Colors.Ink
	TimeBar.BorderSizePixel = 0
	TimeBar.Position = UDim2.fromScale(0.04, 0.128)
	TimeBar.Size = UDim2.fromScale(0.92, 0.012)
	TimeBar.Parent = Board
	local TimeStroke = Instance.new(`UIStroke`)
	TimeStroke.Color = Theme.Frame
	TimeStroke.Thickness = 1
	TimeStroke.Parent = TimeBar
	local TimeFill = Instance.new(`Frame`)
	TimeFill.Name = `Fill`
	TimeFill.BorderSizePixel = 0
	TimeFill.BackgroundColor3 = Theme.Gold
	TimeFill.Size = UDim2.fromScale(1, 1)
	TimeFill.Parent = TimeBar
	local TimeShade = Instance.new(`UIGradient`)
	TimeShade.Rotation = 90
	TimeShade.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(160, 160, 160))
	TimeShade.Parent = TimeFill

	local Content = Instance.new(`Frame`)
	Content.Name = `Content`
	Content.BackgroundTransparency = 1
	Content.Position = UDim2.fromScale(0.03, 0.17)
	Content.Size = UDim2.fromScale(0.94, 0.72)
	Content.ClipsDescendants = true
	Content.Parent = Board

	local Quit = Shared.Button(Board, `Leave lesson`, {
		Name = `Quit`; Font = Theme.HandFont; TextColor3 = Theme.ChalkDim;
		AnchorPoint = Vector2.new(1, 1); Position = UDim2.fromScale(0.955, 0.955); Size = UDim2.fromScale(0.17, 0.06);
	})
	Quit:SetAttribute(`NHPadSkip`, true) -- a controller never starts on it (one press of A would end the lesson)

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	return { Gui = Gui; Board = Board; Title = Title; Sub = Sub; Score = Score; Timer = Timer; Content = Content; Quit = Quit; TimeFill = TimeFill }
end

function Local.Shake(Board: GuiObject)
	-- follows Settings > Camera Shake (0% = off); Reduce Motion halves it
	local Scale = Player:GetAttribute(`NHShakeScale`)
	Scale = if type(Scale) == `number` then Scale else 1
	if Player:GetAttribute(`NHReducedMotion`) then Scale *= 0.5 end
	if Scale <= 0 then return end
	local Base = UDim2.fromScale(0.5, 0.5)
	task.spawn(function()
		for I = 1, 6 do
			Board.Position = Base + UDim2.fromOffset(math.round(math.random(-8, 8) * Scale), math.round(math.random(-5, 5) * Scale))
			task.wait(0.03)
		end
		Board.Position = Base
	end)
end

-- A thin kit progress bar (per-question timers). Returns the track and the fill; games size and tint the fill.
function Local.Bar(Parent: Instance, Props: { [string]: any }): (Frame, Frame)
	local Back = Instance.new(`Frame`)
	Back.Name = `Bar`
	Back.BackgroundColor3 = Kit.Theme.Colors.Ink
	Back.BorderSizePixel = 0
	for Key, Value in Props do (Back :: any)[Key] = Value end
	local Corner = Instance.new(`UICorner`)
	Corner.CornerRadius = UDim.new(1, 0)
	Corner.Parent = Back
	local Stroke = Instance.new(`UIStroke`)
	Stroke.Color = Theme.Frame
	Stroke.Thickness = 1
	Stroke.Parent = Back
	local Fill = Instance.new(`Frame`)
	Fill.Name = `Fill`
	Fill.BorderSizePixel = 0
	Fill.BackgroundColor3 = Theme.Gold
	Fill.Size = UDim2.fromScale(1, 1)
	Fill.Parent = Back
	local FillCorner = Instance.new(`UICorner`)
	FillCorner.CornerRadius = UDim.new(1, 0)
	FillCorner.Parent = Fill
	local Shade = Instance.new(`UIGradient`)
	Shade.Rotation = 90
	Shade.Color = ColorSequence.new(Color3.new(1, 1, 1), Color3.fromRGB(150, 150, 150))
	Shade.Parent = Fill
	Back.Parent = Parent
	return Back, Fill
end

---| Juice (sounds, bursts, BOOM) |---

-- Kinds: Correct (rises with N, the streak), Perfect, Good, Wrong, Boom, Grade
function Local.Sound(Kind: string, N: number?)
	if Kind == `Correct` then
		Kit.PlaySound(`Confirm`, 0.9, 1.15 + 0.06 * math.min(N or 0, 8))
	elseif Kind == `Perfect` then
		Kit.PlaySound(`Confirm`, 0.75, 1.3 + 0.03 * math.min(N or 0, 10))
	elseif Kind == `Good` then
		Kit.PlaySound(`Confirm`, 0.5, 1.1)
	elseif Kind == `Wrong` then
		Kit.PlaySound(`Stamp`, 0.9, 0.7)
	elseif Kind == `Boom` then
		Kit.PlaySound(`Boom`)
	elseif Kind == `Grade` then
		Kit.PlaySound(`Stamp`)
	end
end

-- A check / cross glyph pops off the element (meaning is never colour-only), with chalk dust.
function Local.Burst(Target: GuiObject?, Good: boolean)
	if not (Target and Target.Parent) then return end
	local Calm = Kit.ReducedMotion()
	local Glyph = Instance.new(`TextLabel`)
	Glyph.Name = `Glyph`
	Glyph.BackgroundTransparency = 1
	Glyph.AnchorPoint = Vector2.new(0.5, 0.5)
	Glyph.Position = UDim2.fromScale(0.92, 0.1)
	Glyph.Size = UDim2.fromOffset(34, 34)
	Glyph.Font = Theme.TitleFont
	Glyph.TextScaled = true
	Glyph.Text = if Good then `\u{2713}` else `\u{2717}`
	Glyph.TextColor3 = if Good then Theme.ChalkGreen else Theme.Bad
	Glyph.TextStrokeTransparency = 0.4
	Glyph.ZIndex = (Target.ZIndex or 1) + 5
	Glyph.Parent = Target
	if not Calm then Shared.Pop(Glyph, 1.6) end
	task.delay(0.45, function()
		if Glyph.Parent then
			TweenService:Create(Glyph, TweenInfo.new(0.35, Enum.EasingStyle.Sine), { TextTransparency = 1, TextStrokeTransparency = 1 }):Play()
		end
	end)
	task.delay(0.9, function() Glyph:Destroy() end)
	if Calm then return end
	for I = 1, 6 do
		local Dust = Instance.new(`Frame`)
		Dust.BorderSizePixel = 0
		Dust.AnchorPoint = Vector2.new(0.5, 0.5)
		Dust.Position = UDim2.fromScale(0.5, 0.5)
		Dust.Size = UDim2.fromOffset(5, 5)
		Dust.BackgroundColor3 = if Good then Theme.Chalk else Color3.fromRGB(200, 170, 170)
		Dust.BackgroundTransparency = 0.2
		Dust.ZIndex = (Target.ZIndex or 1) + 4
		local Round = Instance.new(`UICorner`)
		Round.CornerRadius = UDim.new(1, 0)
		Round.Parent = Dust
		Dust.Parent = Target
		local Angle = (I / 6) * math.pi * 2 + math.random() * 0.6
		local Dist = 30 + math.random() * 30
		TweenService:Create(Dust, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
			Position = UDim2.new(0.5, math.cos(Angle) * Dist, 0.5, math.sin(Angle) * Dist);
			BackgroundTransparency = 1;
		}):Play()
		task.delay(0.5, function() Dust:Destroy() end)
	end
end

-- The beaker goes off: a quick flash (soft with Reduce Flashing) and a green smoke puff.
function Local.Boom(Board: GuiObject?)
	Local.Sound(`Boom`)
	if not (Board and Board.Parent) then return end
	local Flash = Instance.new(`Frame`)
	Flash.Name = `BoomFlash`
	Flash.BorderSizePixel = 0
	Flash.Size = UDim2.fromScale(1, 1)
	Flash.BackgroundColor3 = Color3.fromRGB(220, 255, 210)
	Flash.BackgroundTransparency = if Kit.ReducedFlash() then 0.75 else 0.35
	Flash.ZIndex = 50
	Flash.Parent = Board
	TweenService:Create(Flash, TweenInfo.new(0.3, Enum.EasingStyle.Sine), { BackgroundTransparency = 1 }):Play()
	task.delay(0.35, function() Flash:Destroy() end)
	local Calm = Kit.ReducedMotion()
	local Glow = Kit.Theme.Images and Kit.Theme.Images.Glow
	for I = 1, 7 do
		local Puff = Instance.new(`ImageLabel`)
		Puff.Name = `Smoke`
		Puff.BackgroundTransparency = 1
		Puff.Image = if typeof(Glow) == `number` then `rbxassetid://{Glow}` else tostring(Glow or ``)
		Puff.ImageColor3 = Color3.fromRGB(110, 190, 90):Lerp(Color3.fromRGB(60, 120, 50), math.random())
		Puff.ImageTransparency = 0.25
		Puff.AnchorPoint = Vector2.new(0.5, 0.5)
		local X, Y = 0.72 + (math.random() - 0.5) * 0.18, 0.55 + (math.random() - 0.5) * 0.2
		Puff.Position = UDim2.fromScale(X, Y)
		Puff.Size = UDim2.fromScale(0.05, 0.08)
		Puff.ZIndex = 49
		Puff.Parent = Board
		local Goal = { Size = UDim2.fromScale(0.22 + math.random() * 0.1, 0.34 + math.random() * 0.12); ImageTransparency = 1 }
		if not Calm then Goal.Position = UDim2.fromScale(X + (math.random() - 0.5) * 0.12, Y - 0.08 - math.random() * 0.1) end
		TweenService:Create(Puff, TweenInfo.new(1.1 + math.random() * 0.4, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), Goal):Play()
		task.delay(1.6, function() Puff:Destroy() end)
	end
end

-- The grade slams onto the sheet: overshoot, stamp sound, an ink splat; A gets a gold shimmer, F a red scribble.
function Local.StampGrade(Sheet: GuiObject, Stamp: TextLabel, Grade: string)
	Local.Sound(`Grade`)
	local Calm = Kit.ReducedMotion()
	if Calm then
		Kit.FadeIn(Stamp, 0.25)
	else
		local Scale = Stamp:FindFirstChildOfClass(`UIScale`) or Instance.new(`UIScale`)
		Scale.Scale = 1.6
		Scale.Parent = Stamp
		TweenService:Create(Scale, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
	-- wax / ink splat around the seal, in the seal's colour
	local Host = Stamp.Parent or Sheet
	local InkColor = Stamp:GetAttribute(`InkColor`) or Theme.RedInk
	for I = 1, 7 do
		local Dot = Instance.new(`Frame`)
		Dot.BorderSizePixel = 0
		Dot.BackgroundColor3 = InkColor
		Dot.BackgroundTransparency = 0.15
		Dot.AnchorPoint = Vector2.new(0.5, 0.5)
		local Angle = math.random() * math.pi * 2
		local R = 0.46 + math.random() * 0.1
		Dot.Position = UDim2.fromScale(0.5 + math.cos(Angle) * R, 0.5 + math.sin(Angle) * R)
		local Size = 4 + math.random(0, 7)
		Dot.Size = UDim2.fromOffset(Size, Size)
		local Round = Instance.new(`UICorner`)
		Round.CornerRadius = UDim.new(1, 0)
		Round.Parent = Dot
		Dot.Parent = Host
	end
	local First = string.sub(Grade or ``, 1, 1)
	if First == `A` and not Calm then
		local Gradient = Instance.new(`UIGradient`)
		Gradient.Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
			ColorSequenceKeypoint.new(0.4, Color3.new(1, 1, 1)),
			ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 214, 110)),
			ColorSequenceKeypoint.new(0.6, Color3.new(1, 1, 1)),
			ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)),
		})
		Gradient.Offset = Vector2.new(-1, 0)
		Gradient.Parent = Stamp
		task.delay(0.25, function()
			if not Gradient.Parent then return end
			local Sweep = TweenService:Create(Gradient, TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Offset = Vector2.new(1, 0) })
			Sweep.Completed:Connect(function() Gradient:Destroy() end)
			Sweep:Play()
		end)
	elseif First == `F` then
		for I, Rot in { -18, 12 } do
			local Line = Instance.new(`Frame`)
			Line.Name = `Scribble`
			Line.BorderSizePixel = 0
			Line.BackgroundColor3 = Theme.RedInk
			Line.AnchorPoint = Vector2.new(0, 0.5)
			Line.Position = UDim2.fromScale(0.08, 0.42 + I * 0.07)
			Line.Size = UDim2.new(if Calm then 0.84 else 0, 0, 0, 4)
			Line.Rotation = Rot
			Line.ZIndex = Stamp.ZIndex + 2
			Line.Parent = Host
			if not Calm then
				task.delay(0.15 + I * 0.12, function()
					TweenService:Create(Line, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { Size = UDim2.new(0.84, 0, 0, 4) }):Play()
				end)
			end
		end
	end
end

function Local.Close()
	local Lesson = Current
	if not Lesson then return end
	Current = nil

	if Lesson.Renderer then pcall(function() Lesson.Renderer:Destroy() end) end
	if Lesson.TimerConnection then Lesson.TimerConnection:Disconnect() end
	if Lesson.Screen then Lesson.Screen.Gui:Destroy() end
	-- Keep the core backpack off when the NH KitHud hotbar replaces it.
	local KitHotbar = Player:FindFirstChild(`PlayerGui`) and Player.PlayerGui:FindFirstChild(`KitHud`)
	pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, KitHotbar == nil) end)
end

function Local.Open(Message)
	Local.Close()

	local RendererModule = script:FindFirstChild(Message.Activity)
	if not RendererModule then
		warn(`[Activities] no renderer for {Message.Activity}`)
		return
	end

	-- Number keys would otherwise equip backpack tools.
	pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false) end)

	-- The server's game clock starts Intro seconds after it sent this message. Anchor the
	-- client's clock to when the message arrived (not to when the screen finished building),
	-- so timing games line up with the server's judge.
	local GameStartClock = os.clock() + (Message.Intro or 3)

	local Screen = Local.BuildScreen(Message)
	local Lesson = { Id = Message.Id; Screen = Screen; Renderer = nil; Ended = false; Bench = Message.Bench == true }
	Current = Lesson

	local Api = {
		Theme = Theme;
		Label = Shared.Label;
		Button = Shared.Button;
		Pop = Shared.Pop;
		Send = function(Action: string, Data: any)
			if Current == Lesson and not Lesson.Ended then
				Packets.ActivityAction:Fire({ Id = Lesson.Id; Action = Action; Data = Data })
			end
		end;
		SetScore = function(Text: string) Screen.Score.Text = Text end;
		Shake = function() Local.Shake(Screen.Board) end;
		Sound = function(Kind: string, N: number?) Local.Sound(Kind, N) end; -- Correct / Perfect / Good / Wrong
		Burst = function(Target: GuiObject?, Good: boolean) Local.Burst(Target, Good) end; -- glyph + chalk dust
		Boom = function() Local.Boom(Screen.Board) end;
		Bar = function(Parent: Instance, Props: { [string]: any }) return Local.Bar(Parent, Props) end; -- kit progress bar -> Back, Fill
		Frame = function(Object: GuiObject, Color: Color3?) -- kit thin frame around any panel
			return Kit.Slice(`FrameThin`, Color or Theme.Frame, { SliceScale = 0.3, Parent = Object })
		end;
		GameStartClock = GameStartClock; -- os.clock() at which the server's game clock hit 0
		-- controller hints
		Pad = function(): boolean return Kit.InputKind() == `Gamepad` end;
		KeyName = Kit.KeyName;
		PadText = Kit.PadText;
		InputKindChanged = Kit.InputKindChanged;
		-- (Electives) a full-screen renderer draws its own clock: hand it a label and the timer writes there too
		SetTimerLabel = function(L: TextLabel?) Lesson.TimerLabel = L end;
		Bench = Lesson.Bench;
	}

	Screen.Quit.Activated:Connect(function()
		Api.Send(`Quit`, nil)
	end)

	-- (Electives) Bench lessons open on the renderer's own intro (Anatomy: a specimen docket and a candle count) in place
	-- of the chalkboard; Leave lesson moves to the bottom-left at once and takes the renderer's skin
	local Docket = nil
	if Lesson.Bench then
		local okM, Mod = pcall(require, RendererModule)
		if okM and type(Mod) == `table` and Mod.Docket then
			local okD, Dk = pcall(Mod.Docket, Screen, Message)
			if okD and Dk then
				Docket = Dk
				Screen.Board.Visible = false
				local Dim0 = Screen.Gui:FindFirstChild(`Dim`)
				if Dim0 then Dim0.Visible = false end
				Screen.QuitHome = { Parent = Screen.Quit.Parent; Position = Screen.Quit.Position; AnchorPoint = Screen.Quit.AnchorPoint; Size = Screen.Quit.Size }
				Screen.Quit.AnchorPoint = Vector2.new(0, 1)
				Screen.Quit.Position = UDim2.new(0, 18, 1, -14)
				Screen.Quit.Size = UDim2.fromOffset(170, 44)
				Screen.Quit.ZIndex = 20
				Screen.Quit.Parent = Screen.Gui
				if Mod.SkinQuit then pcall(Mod.SkinQuit, Screen.Quit) end
			else
				warn(`[Activities] {Message.Activity} docket failed: {Dk}`)
			end
		end
	end

	-- Intro: the tagline, then 3-2-1 stamped into the HUD's gold orb (with a tick each second)
	local Intro = Shared.Label(Screen.Content, {
		Font = Theme.HandFont; TextColor3 = Theme.Chalk; Size = UDim2.fromScale(0.8, 0.13); Position = UDim2.fromScale(0.1, 0.1);
		Text = Message.Tagline;
	})
	local IntroMax = Instance.new(`UITextSizeConstraint`)
	IntroMax.MaxTextSize = 30
	IntroMax.Parent = Intro
	local Orb = Instance.new(`Frame`)
	Orb.Name = `CountOrb`
	Orb.BackgroundTransparency = 1
	Orb.AnchorPoint = Vector2.new(0.5, 0.5)
	Orb.Position = UDim2.fromScale(0.5, 0.58)
	Orb.Size = UDim2.fromScale(0.5, 0.5)
	local OrbAspect = Instance.new(`UIAspectRatioConstraint`)
	OrbAspect.DominantAxis = Enum.DominantAxis.Height
	OrbAspect.Parent = Orb
	Orb.Parent = Screen.Content
	for _, Part in { { `OrbFill`, Kit.Theme.Colors.Ink, 0.14 }, { `OrbRing`, Theme.Gold, 0 } } do
		local Img = Instance.new(`ImageLabel`)
		Img.Name = Part[1]
		Img.BackgroundTransparency = 1
		local Id = Kit.Theme.Images[Part[1]]
		Img.Image = if typeof(Id) == `number` then `rbxassetid://{Id}` else tostring(Id or ``)
		Img.ImageColor3 = Part[2]
		Img.AnchorPoint = Vector2.new(0.5, 0.5)
		Img.Position = UDim2.fromScale(0.5, 0.5)
		Img.Size = UDim2.fromScale(1 - Part[3], 1 - Part[3])
		Img.Parent = Orb
	end
	-- (1.47) the game's own icon beside the countdown (UI.Theme SubGames Game<Name>; art/ui/hud/make_substitute_games.py)
	local ICON = { MathQuiz = `GamePopQuiz`; LabRhythm = `GameLabMix`; WordScramble = `GameWordScramble`; MemoryMatch = `GameMatchThePast`;
		CandleVigil = `GameCandleVigil`; SeanceSequence = `GameSeanceSequence` }
	local IconId = Kit.Theme.SubGames and Kit.Theme.SubGames[ICON[Message.Activity] or ``]
	if IconId then
		local Icon = Instance.new(`ImageLabel`)
		Icon.Name = `GameIcon`
		Icon.BackgroundTransparency = 1
		Icon.Image = if typeof(IconId) == `number` then `rbxassetid://{IconId}` else tostring(IconId)
		Icon.ScaleType = Enum.ScaleType.Fit
		Icon.AnchorPoint = Vector2.new(0.5, 0.5)
		Icon.Position = UDim2.fromScale(0.2, 0.58)
		Icon.Size = UDim2.fromScale(0.3, 0.4)
		local IA = Instance.new(`UIAspectRatioConstraint`)
		IA.Parent = Icon
		Icon.Parent = Screen.Content
		if not Kit.ReducedMotion() then Shared.Pop(Icon, 1.15) end
		Lesson.Icon = Icon
	end
	local Count = Shared.Label(Orb, {
		Font = Theme.TitleFont; TextColor3 = Theme.Gold; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.52); Size = UDim2.fromScale(0.55, 0.55); ZIndex = 3;
	})

	if Docket then -- the docket carries the tagline and the count
		Intro.Visible = false
		Orb.Visible = false
		if Lesson.Icon then Lesson.Icon.Visible = false end
		Lesson.Docket = Docket
	end

	local Started = os.clock()
	task.spawn(function()
		local Intro_ = Message.Intro or 3
		while Current == Lesson and not Lesson.Ended and os.clock() < GameStartClock - 0.15 do
			local Left = math.ceil(Intro_ - (os.clock() - Started))
			if Count.Text ~= tostring(Left) then
				Count.Text = tostring(Left)
				Kit.PlaySound(`Tick`, 0.5, 1.1)
				if Docket then
					pcall(function() Docket:Count(math.clamp(Left, 1, 3)) end)
				elseif not Kit.ReducedMotion() then Shared.Pop(Orb, 1.25) end
			end
			task.wait()
		end
		if Current ~= Lesson or Lesson.Ended then return end -- cancelled during the countdown: keep "Lesson cancelled" up
		Intro:Destroy()
		Orb:Destroy()
		if Lesson.Icon then Lesson.Icon:Destroy() Lesson.Icon = nil end
		if Docket then pcall(function() Docket:Leave() end) Lesson.Docket = nil end

		-- (Electives) Bench mode: the renderer gets the whole screen; the chalk board steps aside and
		-- only Quit stays, bottom-left. ShowResult brings the board back for the report card.
		local Target = Screen.Content
		if Lesson.Bench then
			local BenchContent = Instance.new(`Frame`)
			BenchContent.Name = `BenchContent`
			BenchContent.BackgroundTransparency = 1
			BenchContent.Size = UDim2.fromScale(1, 1)
			BenchContent.ZIndex = 2
			BenchContent.Parent = Screen.Gui
			Screen.BenchContent = BenchContent
			Screen.Board.Visible = false
			local Dim = Screen.Gui:FindFirstChild(`Dim`)
			if Dim then Dim.Visible = false end
			if not Screen.QuitHome then -- (the docket intro moved it already)
				Screen.QuitHome = { Parent = Screen.Quit.Parent; Position = Screen.Quit.Position; AnchorPoint = Screen.Quit.AnchorPoint; Size = Screen.Quit.Size }
				Screen.Quit.AnchorPoint = Vector2.new(0, 1)
				Screen.Quit.Position = UDim2.new(0, 18, 1, -14)
				Screen.Quit.Size = UDim2.fromOffset(150, 34)
				Screen.Quit.ZIndex = 20
				Screen.Quit.Parent = Screen.Gui
			end
			Target = BenchContent
		end

		local Ok, Renderer = pcall(function()
			return require(RendererModule).new(Target, Message.Payload, Api)
		end)
		if not Ok then
			warn(`[Activities] renderer {Message.Activity} failed: {Renderer}`)
			Api.Send(`Quit`, nil)
			return
		end
		if Current ~= Lesson or Lesson.Ended then -- cancelled while the renderer was being built
			pcall(function() Renderer:Destroy() end)
			return
		end
		Lesson.Renderer = Renderer
		if Lesson.PendingResult then
			Local.ShowResult(Lesson.PendingResult)
			return
		end

		local GameStart = os.clock()
		local BaseColor = Screen.Timer.TextColor3
		local LastSecond = nil
		Lesson.TimerConnection = RunService.Heartbeat:Connect(function()
			local Total = Message.TimeLimit or 60
			local Left = math.max(0, Total - (os.clock() - GameStart))
			Screen.Timer.Text = string.format(`%d:%02d`, Left // 60, math.floor(Left % 60))
			if Lesson.TimerLabel and Lesson.TimerLabel.Parent then
				Lesson.TimerLabel.Text = Screen.Timer.Text
				Lesson.TimerLabel.TextColor3 = if Left <= 10 then Theme.Crimson else Theme.Gold
			end
			if Screen.TimeFill then
				Screen.TimeFill.Size = UDim2.fromScale(math.clamp(Left / Total, 0, 1), 1)
				Screen.TimeFill.BackgroundColor3 = if Left <= 10 then Theme.Crimson else Theme.Gold
			end
			-- the last 10 seconds: the timer turns red and pulses every second (ticks for the last 5)
			local Second = math.ceil(Left)
			if Second ~= LastSecond then
				LastSecond = Second
				if Second <= 10 and Second > 0 then
					Screen.Timer.TextColor3 = Theme.Bad
					if not Kit.ReducedMotion() then Shared.Pop(Screen.Timer, 1.18) end
					if Second <= 5 then Kit.PlaySound(`Tick`, 0.35, 0.9) end
				else
					Screen.Timer.TextColor3 = BaseColor
				end
			end
		end)
	end)
end

function Local.ShowResult(Message)
	local Lesson = Current
	if not Lesson or Message.Id ~= Lesson.Id then return end
	if not Lesson.Renderer and not Message.Cancelled then
		Lesson.PendingResult = Message -- still on the intro; show after
		return
	end
	Lesson.Ended = true

	if Lesson.Renderer then pcall(function() Lesson.Renderer:Destroy() end); Lesson.Renderer = nil end
	if Lesson.TimerConnection then Lesson.TimerConnection:Disconnect(); Lesson.TimerConnection = nil end

	local Content = Lesson.Screen.Content
	for _, Child in Content:GetChildren() do Child:Destroy() end
	Lesson.Screen.Quit.Visible = false
	if Lesson.Docket then -- (Electives) ended on the docket intro: the board comes back for the message
		pcall(function() Lesson.Docket:Destroy() end)
		Lesson.Docket = nil
		Lesson.Screen.Board.Visible = true
		local Dim0 = Lesson.Screen.Gui:FindFirstChild(`Dim`)
		if Dim0 then Dim0.Visible = true end
	end
	if Lesson.Screen.BenchContent then -- (Electives) back from the full-screen bench to the board for the report card
		Lesson.Screen.BenchContent:Destroy()
		Lesson.Screen.BenchContent = nil
		Lesson.TimerLabel = nil
		Lesson.Screen.Board.Visible = true
		local Dim = Lesson.Screen.Gui:FindFirstChild(`Dim`)
		if Dim then Dim.Visible = true end
		local Home = Lesson.Screen.QuitHome
		if Home then
			Lesson.Screen.Quit.Parent = Home.Parent
			Lesson.Screen.Quit.Position = Home.Position
			Lesson.Screen.Quit.AnchorPoint = Home.AnchorPoint
			Lesson.Screen.Quit.Size = Home.Size
		end
	end

	if Message.Cancelled then
		Shared.Label(Content, {
			Font = Theme.HandFont; Size = UDim2.fromScale(1, 0.2); Position = UDim2.fromScale(0, 0.35);
			Text = `Lesson cancelled. {Message.Message or ``}`;
		})
		task.delay(2.5, function() if Current == Lesson then Local.Close() end end)
		return
	end

	-- (2026-11-26) Report card: its own ivory sheet on the dimmed screen (the chalk board steps aside), a crimson crest
	-- band, the grade pressed into a wax seal, the score counting up, the grade's breakdown as bars when the game
	-- sends one, what it means, and the teacher's remark in hand. Every class uses it.
	local Paper = Color3.fromRGB(240, 232, 214)
	local PaperEdge = Color3.fromRGB(206, 192, 164)
	local Ink = Color3.fromRGB(44, 34, 30)
	local InkDim = Color3.fromRGB(112, 96, 82)
	local InkRed = Color3.fromRGB(146, 28, 36)
	local InkGreen = Color3.fromRGB(46, 112, 64)
	local InkGold = Color3.fromRGB(150, 104, 30)
	local Track = Color3.fromRGB(214, 202, 180)
	local GradeColors = {
		A = Color3.fromRGB(196, 150, 60); B = Color3.fromRGB(78, 108, 160); C = Color3.fromRGB(110, 100, 90);
		D = Color3.fromRGB(176, 104, 50); F = InkRed;
	}
	local GradeColor = GradeColors[string.sub(tostring(Message.Grade or ``), 1, 1)] or GradeColors.A
	local Calm = Kit.ReducedMotion()
	Lesson.Screen.Board.Visible = false

	local function label(Parent: Instance, Props, Max: number?): TextLabel
		local L = Shared.Label(Parent, Props)
		if Max then
			local C = Instance.new(`UITextSizeConstraint`)
			C.MaxTextSize = Max
			C.Parent = L
		end
		return L
	end
	local function frame(Parent: Instance, Props): Frame
		local F = Instance.new(`Frame`)
		F.BorderSizePixel = 0
		for K, V in Props do (F :: any)[K] = V end
		F.Parent = Parent
		return F
	end
	local function stroke(Parent: Instance, Color: Color3, Thick: number, Transp: number)
		local S = Instance.new(`UIStroke`)
		S.Color, S.Thickness, S.Transparency = Color, Thick, Transp
		S.Parent = Parent
		return S
	end

	-- a dark backdrop over the rest of the HUD
	local Backdrop = frame(Lesson.Screen.Gui, { Name = `ReportBackdrop`; Size = UDim2.new(1, 0, 1, 60); Position = UDim2.fromOffset(0, -60);
		BackgroundColor3 = Color3.fromRGB(8, 6, 8); BackgroundTransparency = if Calm then 0.35 else 1; ZIndex = 1 })
	if not Calm then TweenService:Create(Backdrop, TweenInfo.new(0.3), { BackgroundTransparency = 0.35 }):Play() end
	-- the sheet and its shadow ride in one CanvasGroup, so the slide, the tilt and the fade move them together
	local Holder = Instance.new(`CanvasGroup`)
	Holder.Name = `ReportCard`
	Holder.BackgroundTransparency = 1
	Holder.AnchorPoint = Vector2.new(0.5, 0.5)
	Holder.Position = UDim2.fromScale(0.5, 0.5)
	Holder.Size = UDim2.fromScale(0.64, 0.86)
	Holder.ZIndex = 30
	Holder.Parent = Lesson.Screen.Gui
	local Aspect = Instance.new(`UIAspectRatioConstraint`)
	Aspect.AspectRatio = 1.45
	Aspect.Parent = Holder
	frame(Holder, { Name = `Shadow`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 5, 0.5, 8); Size = UDim2.new(0.94, 0, 0.94, 0);
		BackgroundColor3 = Color3.new(0, 0, 0); BackgroundTransparency = 0.5; ZIndex = 29 })
	local Sheet = frame(Holder, { Name = `Sheet`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromScale(0.94, 0.94); BackgroundColor3 = Paper; ZIndex = 30 })
	local Grain = Instance.new(`UIGradient`)
	Grain.Rotation = 115
	Grain.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 252, 244)), ColorSequenceKeypoint.new(0.55, Color3.new(1, 1, 1)),
		ColorSequenceKeypoint.new(1, Color3.fromRGB(226, 214, 190)) })
	Grain.Parent = Sheet
	stroke(Sheet, PaperEdge, 2, 0)
	-- a double crimson rule inside the edge
	stroke(frame(Sheet, { Name = `Rule`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(1, -22, 1, -22);
		BackgroundTransparency = 1; ZIndex = 31 }), InkRed, 2, 0.15)
	stroke(frame(Sheet, { Name = `Rule2`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(1, -32, 1, -32);
		BackgroundTransparency = 1; ZIndex = 31 }), InkRed, 1, 0.45)

	-- the crest band
	local Band = frame(Sheet, { Name = `Band`; Position = UDim2.new(0, 16, 0, 16); Size = UDim2.new(1, -32, 0.17, 0); BackgroundColor3 = Color3.fromRGB(92, 18, 26); ZIndex = 32 })
	local BandShade = Instance.new(`UIGradient`)
	BandShade.Rotation = 90
	BandShade.Color = ColorSequence.new(Color3.fromRGB(255, 255, 255), Color3.fromRGB(170, 150, 150))
	BandShade.Parent = Band
	local Cream = Color3.fromRGB(236, 220, 200)
	label(Band, { Font = Theme.TitleFont; TextColor3 = Color3.fromRGB(240, 214, 150); Text = `NIGHTMARE HIGHSCHOOL`; ZIndex = 33;
		Position = UDim2.fromScale(0.04, 0.1); Size = UDim2.fromScale(0.6, 0.36); TextXAlignment = Enum.TextXAlignment.Left }, 26)
	label(Band, { Font = Theme.HandFont; TextColor3 = Cream; ZIndex = 33; TextXAlignment = Enum.TextXAlignment.Left;
		Text = `Report Card  \u{00B7}  {Message.Subject or ``}  \u{00B7}  {Message.Title or ``}` .. (if Message.Level then `  \u{00B7}  Level {Message.Level}` else ``);
		Position = UDim2.fromScale(0.04, 0.52); Size = UDim2.fromScale(0.75, 0.32) }, 20)
	label(Band, { Font = Theme.HandFont; TextColor3 = Cream; ZIndex = 33; TextXAlignment = Enum.TextXAlignment.Right;
		Text = if Message.Practice then `PRACTICE` elseif Message.Study then `NIGHT STUDY` else `GRADED`;
		Position = UDim2.fromScale(0.7, 0.14); Size = UDim2.fromScale(0.26, 0.3) }, 18)

	-- the grade, pressed into a wax seal tinted by the grade
	local SealHolder = frame(Sheet, { Name = `GradeSeal`; BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.22, 0.5); Size = UDim2.fromScale(0.3, 0.44); ZIndex = 32 })
	local SealAspect = Instance.new(`UIAspectRatioConstraint`)
	SealAspect.DominantAxis = Enum.DominantAxis.Height
	SealAspect.Parent = SealHolder
	local Seal = Instance.new(`ImageLabel`)
	Seal.Name = `Seal`
	Seal.BackgroundTransparency = 1
	local SealId = Kit.Theme.Images.IconGradeSeal
	Seal.Image = if typeof(SealId) == `number` then `rbxassetid://{SealId}` else tostring(SealId or ``)
	Seal.ImageColor3 = GradeColor
	Seal.Size = UDim2.fromScale(1, 1)
	Seal.ZIndex = 33
	Seal.Parent = SealHolder
	local Stamp = Shared.Label(SealHolder, {
		Name = `Grade`; Font = Theme.TitleFont; TextColor3 = Color3.fromRGB(255, 246, 228); Rotation = -10;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.52); Size = UDim2.fromScale(0.6, 0.5); ZIndex = 35;
		TextStrokeTransparency = 0.25; TextStrokeColor3 = Color3.new(0, 0, 0);
		Text = Message.Grade;
	})
	Stamp:SetAttribute(`InkColor`, GradeColor)
	Stamp.Visible = false
	label(Sheet, { Font = Theme.HandFont; TextColor3 = InkDim; Text = `final grade`; ZIndex = 32;
		Position = UDim2.fromScale(0.07, 0.75); Size = UDim2.fromScale(0.3, 0.05) }, 18)

	-- the score, counting up, and its bar
	local Right = 0.42
	local ScoreText = label(Sheet, { Font = Theme.TitleFont; TextColor3 = Ink; TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 32;
		Position = UDim2.fromScale(Right, 0.24); Size = UDim2.fromScale(0.5, 0.1); Text = `Score  0%` }, 42)
	local ScoreBack, ScoreFill = Local.Bar(Sheet, { Position = UDim2.fromScale(Right, 0.355); Size = UDim2.fromScale(0.5, 0.026); ZIndex = 32 })
	ScoreBack.BackgroundColor3 = Track
	ScoreFill.BackgroundColor3 = GradeColor
	ScoreFill.ZIndex = 33
	ScoreFill.Size = UDim2.fromScale(0, 1)
	local Percent = tonumber(Message.Percent) or 0

	-- the breakdown (games that send one: Anatomy's accuracy / process / time)
	local Y = 0.41
	local Rows = {}
	if typeof(Message.Breakdown) == `table` then
		local Order = { `Accuracy`, `Process`, `Time` }
		local Known = { Accuracy = true; Process = true; Time = true }
		for K in Message.Breakdown do if not Known[K] then table.insert(Order, K) end end
		for _, K in Order do
			local V = tonumber(Message.Breakdown[K])
			if V then
				V = math.clamp(V, 0, 1)
				label(Sheet, { Font = Theme.HandFont; TextColor3 = Ink; TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 32;
					Position = UDim2.fromScale(Right, Y); Size = UDim2.fromScale(0.15, 0.045); Text = tostring(K) }, 18)
				local Back, Fill = Local.Bar(Sheet, { Position = UDim2.fromScale(Right + 0.16, Y + 0.016); Size = UDim2.fromScale(0.27, 0.016); ZIndex = 32 })
				Back.BackgroundColor3 = Track
				Fill.BackgroundColor3 = InkGold
				Fill.ZIndex = 33
				Fill.Size = UDim2.fromScale(0, 1)
				label(Sheet, { Font = Theme.HandFont; TextColor3 = InkDim; TextXAlignment = Enum.TextXAlignment.Right; ZIndex = 32;
					Position = UDim2.fromScale(Right + 0.43, Y); Size = UDim2.fromScale(0.07, 0.045); Text = `{math.floor(V * 100 + 0.5)}%` }, 18)
				table.insert(Rows, { Fill = Fill; V = V })
				Y += 0.055
			end
		end
		Y += 0.015
	end

	-- what it means (with a mark, never colour-only)
	local Lines = {}
	if Message.Study then
		table.insert(Lines, { if Message.Passed then `\u{2713} Study session: passed` else `\u{2022} Study session: keep at it`, if Message.Passed then InkGreen else Ink })
		table.insert(Lines, { Message.Extra or `No standing this time.`, InkDim })
	elseif Message.Practice then
		table.insert(Lines, { `\u{2022} Practice round: no rewards.`, InkDim })
	elseif Message.Passed then
		table.insert(Lines, { `\u{2713} Passed`, InkGreen })
		if Message.Yen and Message.Yen > 0 then table.insert(Lines, { `+\u{00A5}{Message.Yen}`, InkGold }) end
		if Message.LevelUp then table.insert(Lines, { `Level {Message.Level} unlocked!`, InkGold }) end
	else
		table.insert(Lines, { `\u{2717} Failed: you can retry this period.`, InkRed })
	end
	if Message.SubNote then table.insert(Lines, { Message.SubNote, InkGold }) end -- (1.47) the substitute's pay rule
	if Message.Reason == `Bell` then table.insert(Lines, { `(The bell rang.)`, InkDim }) end
	for Index, Entry in Lines do
		label(Sheet, { Font = Theme.HandFont; TextColor3 = Entry[2]; TextXAlignment = Enum.TextXAlignment.Left; ZIndex = 32;
			Position = UDim2.fromScale(Right, Y + (Index - 1) * 0.058); Size = UDim2.fromScale(0.5, 0.05); Text = Entry[1] }, 22)
	end

	-- the teacher's remark, in hand, over a rule
	frame(Sheet, { Name = `RemarkRule`; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.fromScale(0.5, 0.8); Size = UDim2.new(0.84, 0, 0, 1);
		BackgroundColor3 = PaperEdge; ZIndex = 32 })
	label(Sheet, { Font = Theme.HandFont; TextColor3 = InkDim; ZIndex = 32; Position = UDim2.fromScale(0.08, 0.82); Size = UDim2.fromScale(0.6, 0.075);
		TextXAlignment = Enum.TextXAlignment.Left;
		Text = `\u{201C}{Message.Line or ``}\u{201D}` .. (if Message.Substitute then `  \u{2014} {Message.Substitute}` else ``) }, 20) -- (1.47)

	local Done = Shared.Button(Sheet, `Close`, {
		Font = Theme.TitleFont; TextColor3 = Theme.Gold; AnchorPoint = Vector2.new(1, 1); Position = UDim2.fromScale(0.93, 0.94); Size = UDim2.fromScale(0.18, 0.085); ZIndex = 34;
	})
	Done.Activated:Connect(function() if Current == Lesson then Local.Close() end end)
	Done:SetAttribute(`NHPadFirst`, true)
	if GuiService.SelectedObject then task.defer(function() if Done.Parent then GuiService.SelectedObject = Done end end) end

	-- the reveal: the sheet slides up and settles, then the seal is pressed, the score counts and the bars fill
	if not Calm then
		local Scale = Instance.new(`UIScale`)
		Scale.Scale = 0.96
		Scale.Parent = Holder
		Holder.Position = UDim2.fromScale(0.5, 0.62)
		Holder.Rotation = -2.5
		Holder.GroupTransparency = 1
		local Info = TweenInfo.new(0.45, Enum.EasingStyle.Back, Enum.EasingDirection.Out)
		TweenService:Create(Holder, Info, { Position = UDim2.fromScale(0.5, 0.5); Rotation = 0 }):Play()
		TweenService:Create(Holder, TweenInfo.new(0.25), { GroupTransparency = 0 }):Play()
		TweenService:Create(Scale, Info, { Scale = 1 }):Play()
	end
	task.delay(if Calm then 0 else 0.4, function()
		if not Sheet.Parent then return end
		Stamp.Visible = true
		Local.StampGrade(SealHolder, Stamp, Message.Grade)
		local T = if Calm then 0.01 else 0.8
		local Count = Instance.new(`NumberValue`)
		Count.Changed:Connect(function(v) ScoreText.Text = `Score  {math.floor(v + 0.5)}%` end)
		TweenService:Create(Count, TweenInfo.new(T, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Value = Percent }):Play()
		TweenService:Create(ScoreFill, TweenInfo.new(T, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromScale(math.clamp(Percent / 100, 0, 1), 1) }):Play()
		task.delay(T + 0.1, function() ScoreText.Text = `Score  {Percent}%` Count:Destroy() end)
		for i, R in Rows do
			task.delay(if Calm then 0 else 0.25 + i * 0.15, function()
				if R.Fill.Parent then
					TweenService:Create(R.Fill, TweenInfo.new(if Calm then 0.01 else 0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromScale(R.V, 1) }):Play()
				end
			end)
		end
	end)
	task.delay(10, function() if Current == Lesson then Local.Close() end end)
end

-- B on a controller: the game's own back (an undo), or closing the report card
function Shared.PadBack()
	local Lesson = Current
	if not Lesson then return end
	if Lesson.Ended then Local.Close() return end
	local R = Lesson.Renderer
	if R and R.PadBack then pcall(R.PadBack, R) end
end

function Shared.IsOpen(): boolean
	return Current ~= nil
end

function Shared.OnStart()
	-- (1.47) fetch the substitutes' minigame art up front, so a game's icon is there for its 5-second intro
	task.spawn(function()
		local List = {}
		for _, Id in Kit.Theme.SubGames or {} do table.insert(List, if typeof(Id) == `number` then `rbxassetid://{Id}` else tostring(Id)) end
		pcall(function() game:GetService(`ContentProvider`):PreloadAsync(List) end)
	end)
	-- (Anatomy) warm the bench's models a little after joining, so a first lesson does not wait on its meshes and maps
	task.delay(15, function()
		local Bench = script:FindFirstChild(`AnatomyBench`)
		if Bench then pcall(function() require(Bench).Preload() end) end
	end)
	local function OnEvent(Message)
		if typeof(Message) ~= `table` then return end

		if Message.Type == `Start` then
			Local.Open(Message)
		elseif Message.Type == `Update` then
			if Current and Message.Id == Current.Id and Current.Renderer then
				local Ok, Err = pcall(function() Current.Renderer:Update(Message.Payload) end)
				if not Ok then warn(`[Activities] update error: {Err}`) end
			end
		elseif Message.Type == `Result` then
			Local.ShowResult(Message)
		end
	end
	Packets.ActivityEvent.OnClientEvent:Connect(OnEvent)
	-- Studio tests (Studio/tests/ps5_lesson.luau): show a lesson with made-up content; the server never hears of it
	if RunService:IsStudio() then
		local Test = Instance.new(`BindableEvent`)
		Test.Name = `NHActivityTest`
		Test.Event:Connect(OnEvent)
		Test.Parent = Player:WaitForChild(`PlayerGui`)
	end

	Player.CharacterRemoving:Connect(function()
		Local.Close()
	end)
end

return Shared
