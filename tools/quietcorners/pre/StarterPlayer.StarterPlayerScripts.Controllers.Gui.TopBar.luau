--[[
	Top bar (client): a slim, on-theme replacement for Roblox's default top bar buttons.

	Roblox's top bar is switched off (StarterGui:SetCore("TopbarEnabled", false)); in its place sits
	one small ink-black plate with a thin gold rim in the top-left corner:
		Menu      opens the game's Settings panel (Controllers.Gui.SettingsMenu). Esc still opens Roblox's menu.
		Chat      shows / hides the chat window; a crimson pip appears when messages arrive while it is hidden.
		Students  opens / closes the Students list, grouped by faction (Controllers.Gui.Students; also Tab).
		Record    your Student Record: level, EXP, stats (Controllers.Gui.Progress; also L).
	It keeps out of the way: after a few seconds without the mouse near the top of the screen it
	fades back to a faint outline, and it comes back when you move to the top or press a bar key.
	If Roblox still draws its own button (some clients always do), the plate sits just to its right
	(GuiService.TopbarInset). The main menu hides it with the rest of the HUD.
]]

---| Services |---

local GuiService = game:GetService(`GuiService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local StarterGui = game:GetService(`StarterGui`)
local TextChatService = game:GetService(`TextChatService`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)

---| Modules |---

local Theme = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Theme`))
local Kit = require(ReplicatedStorage.UI:WaitForChild(`Components`))

local Player = Players.LocalPlayer
local C = Theme.Colors
local IDLE_AFTER = 3.5      -- seconds before the bar fades back
local IDLE_TRANSPARENCY = 0.5
local SIZE = 34             -- button size (pixels at 1080p)

local Local = {}
local Shared = {}

local Ui = nil
local State = { LastActive = os.clock(); ChatOn = true; ListOn = false; Unread = false; Shown = true }

---| Helpers |---

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

local function tween(I: Instance, T: number, Props)
	local Tw = TweenService:Create(I, TweenInfo.new(T, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), Props)
	Tw:Play()
	return Tw
end

function Local.SetCore(Name: string, Value: any)
	task.spawn(function()
		for _ = 1, 40 do
			if pcall(function() StarterGui:SetCore(Name, Value) end) then return end
			task.wait(0.25)
		end
	end)
end

---| Icons (drawn from frames so they tint with the theme) |---

function Local.Bar(Parent: Instance, Y: number, W: number)
	return new(`Frame`, { BackgroundColor3 = C.Text; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, Y); Size = UDim2.fromOffset(W, 2) }, Parent)
end

function Local.MenuIcon(Parent: Instance)
	local Parts = {}
	for I, Y in { -5, 0, 5 } do Parts[I] = Local.Bar(Parent, Y, if I == 2 then 10 else 14) end
	return Parts
end

function Local.ChatIcon(Parent: Instance)
	local Bubble = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, -1); Size = UDim2.fromOffset(16, 11) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Bubble)
	local Stroke = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Bubble)
	local Tail = new(`Frame`, { BackgroundColor3 = C.Text; BorderSizePixel = 0; Rotation = 45; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, -3, 0.5, 6); Size = UDim2.fromOffset(4, 4) }, Parent)
	local Line = Local.Bar(Parent, -1, 8)
	return { Stroke, Tail, Line }
end

function Local.PeopleIcon(Parent: Instance)
	local Head = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, -4); Size = UDim2.fromOffset(7, 7) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Head)
	local S1 = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Head)
	local Body = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0.5, 2); Size = UDim2.fromOffset(13, 6) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, Body)
	local S2 = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Body)
	return { S1, S2 }
end

function Local.BookIcon(Parent: Instance)
	local Cover = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, 0); Size = UDim2.fromOffset(13, 16) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 2) }, Cover)
	local Stroke = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Cover)
	local Spine = new(`Frame`, { BackgroundColor3 = C.Text; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, -3, 0.5, 0); Size = UDim2.fromOffset(2, 14) }, Parent)
	local Line = Local.Bar(Parent, -2, 5)
	Line.Position = UDim2.new(0.5, 2, 0.5, -2)
	local Line2 = Local.Bar(Parent, 2, 5)
	Line2.Position = UDim2.new(0.5, 2, 0.5, 2)
	return { Stroke, Spine, Line, Line2 }
end

-- a locker / chest outline (Locker, G)
function Local.ChestIcon(Parent: Instance)
	local Box = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, 2); Size = UDim2.fromOffset(16, 10) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 2) }, Box)
	local S1 = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Box)
	local Lid = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 0.5, -3); Size = UDim2.fromOffset(16, 6) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, Lid)
	local S2 = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Lid)
	local Lock = new(`Frame`, { BackgroundColor3 = C.Text; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, -1); Size = UDim2.fromOffset(3, 4) }, Parent)
	return { S1, S2, Lock }
end

-- two figures side by side (Study Group, U)
function Local.GroupIcon(Parent: Instance)
	local Parts = {}
	for _, X in { -5, 5 } do
		local Head = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, X, 0.5, -4); Size = UDim2.fromOffset(6, 6) }, Parent)
		new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Head)
		table.insert(Parts, new(`UIStroke`, { Color = C.Text; Thickness = 1.5 }, Head))
		local Body = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, X, 0.5, 1); Size = UDim2.fromOffset(9, 6) }, Parent)
		new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Body)
		table.insert(Parts, new(`UIStroke`, { Color = C.Text; Thickness = 1.5 }, Body))
	end
	return Parts
end

-- a film frame with letterbox bars (Cinematic view, \)
function Local.FilmIcon(Parent: Instance)
	local Frame = new(`Frame`, { BackgroundTransparency = 1; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.new(0.5, 0, 0.5, 0); Size = UDim2.fromOffset(18, 13) }, Parent)
	new(`UICorner`, { CornerRadius = UDim.new(0, 2) }, Frame)
	local S = new(`UIStroke`, { Color = C.Text; Thickness = 1.6 }, Frame)
	local TopBar = Local.Bar(Parent, -3, 12)
	local BottomBar = Local.Bar(Parent, 3, 12)
	return { S, TopBar, BottomBar }
end

function Local.Tint(Parts, Color: Color3)
	for _, P in Parts do
		if P:IsA(`UIStroke`) then P.Color = Color else P.BackgroundColor3 = Color end
	end
end

---| Build |---

function Local.Button(Name: string, Order: number, Draw, Tip: string, OnClick)
	local B = new(`TextButton`, {
		Name = Name; Text = ``; AutoButtonColor = false; BackgroundColor3 = C.Well; BackgroundTransparency = 1;
		Size = UDim2.fromOffset(SIZE, SIZE); LayoutOrder = Order; Selectable = true;
	}, Ui.Row)
	new(`UICorner`, { CornerRadius = UDim.new(0, 4) }, B)
	local Icon = new(`Frame`, { Name = `Icon`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, B)
	local Parts = Draw(Icon)
	local Pip = new(`Frame`, {
		Name = `Pip`; BackgroundColor3 = C.Crimson; BorderSizePixel = 0; Visible = false;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -5, 0, 5); Size = UDim2.fromOffset(7, 7);
	}, B)
	new(`UICorner`, { CornerRadius = UDim.new(1, 0) }, Pip)
	new(`UIStroke`, { Color = C.Ink; Thickness = 1.5 }, Pip)
	local Api = { Root = B; Parts = Parts; Pip = Pip; On = true }
	function Api.Refresh(Hover: boolean?)
		local Col = if Hover then C.Gold elseif Api.On then C.Text else C.TextFaint
		Local.Tint(Parts, Col)
		B.BackgroundTransparency = if Hover then 0.35 else 1
	end
	B.MouseEnter:Connect(function()
		Api.Refresh(true)
		Ui.Tip.Text = Tip
		local S = Ui.Scale.Scale
		Ui.Tip.Position = UDim2.fromOffset((B.AbsolutePosition.X + B.AbsoluteSize.X / 2) / S, Ui.Plate.Position.Y.Offset + SIZE + 16)
		Ui.Tip.Visible = true
		Local.Wake()
		-- (audit) a tap fires MouseEnter but no MouseLeave: on touch take the tip down after a moment so the bar can fade
		local Mine = {}
		Ui.TipToken = Mine
		task.delay(2.5, function()
			if Ui and Ui.TipToken == Mine and UserInputService:GetLastInputType() == Enum.UserInputType.Touch then
				Api.Refresh(false)
				Ui.Tip.Visible = false
			end
		end)
	end)
	B.MouseLeave:Connect(function()
		Api.Refresh(false)
		Ui.Tip.Visible = false
	end)
	B.Activated:Connect(function()
		Local.Wake()
		-- (audit) touch: the tap is done, hide the tip (no MouseLeave will come)
		if UserInputService:GetLastInputType() == Enum.UserInputType.Touch then
			Api.Refresh(false)
			Ui.Tip.Visible = false
		end
		OnClick(Api)
	end)
	Api.Refresh(false)
	return Api
end

function Local.Build()
	local Gui = new(`ScreenGui`, {
		Name = `NHTopBar`; DisplayOrder = 20; ResetOnSpawn = false; IgnoreGuiInset = true;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling;
	}, Player:WaitForChild(`PlayerGui`))
	local Scale = new(`UIScale`, {}, Gui)
	local Group = new(`CanvasGroup`, { Name = `Group`; BackgroundTransparency = 1; Size = UDim2.fromScale(1, 1) }, Gui)
	local Plate = new(`Frame`, {
		Name = `Plate`; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.15; BorderSizePixel = 0;
		AutomaticSize = Enum.AutomaticSize.X; Position = UDim2.fromOffset(12, 10); Size = UDim2.fromOffset(0, SIZE + 8);
	}, Group)
	new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Plate)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.35 }, Plate)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(Color3.fromRGB(40, 32, 40), Color3.fromRGB(14, 10, 14)) }, Plate)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 4); PaddingRight = UDim.new(0, 4); PaddingTop = UDim.new(0, 4); PaddingBottom = UDim.new(0, 4) }, Plate)
	local Row = new(`Frame`, { Name = `Row`; BackgroundTransparency = 1; AutomaticSize = Enum.AutomaticSize.X; Size = UDim2.fromOffset(0, SIZE) }, Plate)
	new(`UIListLayout`, { FillDirection = Enum.FillDirection.Horizontal; Padding = UDim.new(0, 2); SortOrder = Enum.SortOrder.LayoutOrder; VerticalAlignment = Enum.VerticalAlignment.Center }, Row)
	-- a thin crimson underline: the one bit of colour
	local Rule = new(`Frame`, { Name = `Rule`; BackgroundColor3 = C.Crimson; BorderSizePixel = 0; AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, 4); Size = UDim2.new(1, -16, 0, 1) }, Plate)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, Rule)
	local Tip = new(`TextLabel`, {
		Name = `Tip`; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.15; Visible = false; AutomaticSize = Enum.AutomaticSize.X;
		AnchorPoint = Vector2.new(0.5, 0); Size = UDim2.fromOffset(0, 22); Font = Theme.Fonts.Title; TextSize = 15; TextColor3 = C.Text; Text = ``;
	}, Group)
	new(`UIPadding`, { PaddingLeft = UDim.new(0, 8); PaddingRight = UDim.new(0, 8) }, Tip)
	new(`UICorner`, { CornerRadius = UDim.new(0, 3) }, Tip)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.4 }, Tip)

	Ui = { Gui = Gui; Scale = Scale; Group = Group; Plate = Plate; Row = Row; Tip = Tip }
	Ui.Menu = Local.Button(`Menu`, 1, Local.MenuIcon, `Options  [P]`, function() Local.OpenSettings() end)
	Ui.Chat = Local.Button(`Chat`, 2, Local.ChatIcon, `Chat`, function() Shared.SetChat(not State.ChatOn) end)
	Ui.Players = Local.Button(`Players`, 3, Local.PeopleIcon, `Students  [Tab]`, function() Shared.SetPlayerList(not State.ListOn) end)
	Ui.Record = Local.Button(`Record`, 4, Local.BookIcon, `Report Card  [M]`, function()
		local Ok, Progress = pcall(require, script.Parent:FindFirstChild(`Progress`))
		if Ok and typeof(Progress) == `table` then Progress.Toggle() end
	end)
	Ui.Locker = Local.Button(`Locker`, 5, Local.ChestIcon, "Locker  [`]", function()
		local Ok, Mod = pcall(require, script.Parent:FindFirstChild(`Locker`))
		if Ok and typeof(Mod) == `table` then Mod.Toggle() end
	end)
	Ui.Film = Local.Button(`Cinematic`, 7, Local.FilmIcon, `Cinematic view  [\\]`, function()
		local Ok, Mod = pcall(require, script.Parent:FindFirstChild(`Cinematic`))
		if Ok and typeof(Mod) == `table` then Mod.Toggle() end
	end)
	Ui.StudyGroup = Local.Button(`StudyGroup`, 6, Local.GroupIcon, `Study Group  [U]`, function()
		local Ok, Mod = pcall(require, script.Parent:FindFirstChild(`StudyGroup`))
		if Ok and typeof(Mod) == `table` then Mod.Toggle() end
	end)
	Local.Place()
end

-- sit just right of whatever Roblox still draws in the corner, and scale with the screen
function Local.Place()
	if not Ui then return end
	local View = if Kit.Viewport then Kit.Viewport() else (workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1920, 1080))
	Ui.Scale.Scale = math.clamp(View.Y / 1080, 0.8, 1.4)
	local Ok, Inset = pcall(function() return GuiService.TopbarInset end)
	local X = 12
	if Ok and Inset and Inset.Width > 0 then
		-- TopbarInset is the free area; anything left of its Min.X belongs to Roblox
		X = math.max(12, Inset.Min.X / Ui.Scale.Scale + 6)
	end
	Ui.Plate.Position = UDim2.fromOffset(X, 10)
end

---| Actions |---

function Local.OpenSettings()
	local Module = script.Parent:FindFirstChild(`SettingsMenu`)
	local Ok, Settings = pcall(require, Module)
	if Ok and typeof(Settings) == `table` and Settings.Toggle then
		pcall(Settings.Toggle)
	end
end

function Shared.SetChat(On: boolean)
	State.ChatOn = On
	-- (2.1.0) the NH chat window (Controllers.Gui.Chat) in place of Roblox's; Roblox's stays off
	local Ok, Chat = pcall(require, script.Parent:FindFirstChild(`Chat`))
	if Ok and type(Chat) == `table` and Chat.SetShown then
		Chat.SetShown(On)
	else
		pcall(function()
			TextChatService.ChatWindowConfiguration.Enabled = On
			TextChatService.ChatInputBarConfiguration.Enabled = On
		end)
	end
	if On then State.Unread = false end
	if Ui then
		Ui.Chat.On = On
		Ui.Chat.Pip.Visible = State.Unread
		Ui.Chat.Refresh(false)
	end
end

function Local.Students()
	local Module = script.Parent:FindFirstChild(`Students`)
	local Ok, Students = pcall(require, Module)
	return if Ok and typeof(Students) == `table` then Students else nil
end

function Shared.SetPlayerList(On: boolean)
	local Students = Local.Students()
	if Students then
		Students.Toggle(On)
	else
		pcall(function() StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.PlayerList, On) end)
	end
	Local.SyncList(On)
end

function Local.SyncList(On: boolean)
	State.ListOn = On
	if Ui then
		Ui.Players.On = On
		Ui.Players.Refresh(false)
	end
end

function Local.Wake()
	State.LastActive = os.clock()
	if Ui and not State.Shown then
		State.Shown = true
		tween(Ui.Group, 0.25, { GroupTransparency = 0 })
	end
end

---| Start |---

function Shared.OnStart()
	Local.SetCore(`TopbarEnabled`, false)
	Local.Build()
	local Cam = workspace.CurrentCamera
	if Cam then Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(Local.Place) end
	pcall(function() GuiService:GetPropertyChangedSignal(`TopbarInset`):Connect(Local.Place) end)

	-- unread pip while chat is hidden
	pcall(function()
		TextChatService.MessageReceived:Connect(function(Message)
			if State.ChatOn or not Message.TextSource then return end
			State.Unread = true
			if Ui then Ui.Chat.Pip.Visible = true end
		end)
	end)

	-- fade back when not in use; wake when the mouse comes near the top
	UserInputService.InputChanged:Connect(function(Input)
		if Input.UserInputType == Enum.UserInputType.MouseMovement and Input.Position.Y < 90 then Local.Wake() end
	end)
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed then return end
		if Input.KeyCode == Enum.KeyCode.Slash then Shared.SetChat(true) Local.Wake() end
	end)
	-- keep the Students icon in step when the list is toggled with Tab
	task.spawn(function()
		while true do
			task.wait(0.2)
			local Students = Local.Students()
			if Students and Students.IsOpen() ~= State.ListOn then
				Local.SyncList(Students.IsOpen())
				if State.ListOn then Local.Wake() end
			end
		end
	end)
	RunService.Heartbeat:Connect(function()
		if Ui and State.Shown and os.clock() - State.LastActive > IDLE_AFTER and not Ui.Tip.Visible and not State.ListOn then
			State.Shown = false
			tween(Ui.Group, 0.8, { GroupTransparency = IDLE_TRANSPARENCY })
		end
	end)
	Local.Wake()
end

---| Testing |---

function Shared.Debug()
	return { Chat = State.ChatOn; List = State.ListOn; Unread = State.Unread; Shown = State.Shown; X = Ui and Ui.Plate.Position.X.Offset }
end

return Shared
