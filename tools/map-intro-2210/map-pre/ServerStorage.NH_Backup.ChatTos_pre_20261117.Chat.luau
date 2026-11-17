--[[
	Chat (client, 2.1.0): the NH chat window, in the UI kit's gothic style, in place of Roblox's default chat window
	and input bar.

	- Everything still goes through TextChatService: the bar sends with TextChannel:SendAsync, and the window shows
	  TextChatService.MessageReceived. So the talking faces (Controllers.Character.FaceTalk), the TopBar's unread pip,
	  filtering and chat commands work as before.
	- Roblox's chat window and input bar are switched off (ChatWindowConfiguration / ChatInputBarConfiguration
	  .Enabled = false). Bubbles stay Roblox's (BubbleChatConfiguration), restyled to match the students' bubbles.
	- Press / to talk. Enter sends, Esc leaves the bar (the draft stays). Up / Down bring back what you sent before.
	- While the bar has focus no game key does anything: every keybind checks Packages.Bind.Typing.
	- It fades back to a faint log after a few quiet seconds and comes back on a new message, the mouse, or /.
	- The TopBar's Chat button shows and hides it (Shared.SetShown). The main menu and the cinematic view hide it.

	Studio preview (edit mode, command bar):
		require(game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Chat:Clone()).Preview(game.StarterGui.ChatPreview)
]]

---| Services |---

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextChatService = game:GetService("TextChatService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

---| Modules |---

local Theme = require(ReplicatedStorage:WaitForChild("UI"):WaitForChild("Theme"))
local Kit = require(ReplicatedStorage.UI:WaitForChild("Components"))

local C = Theme.Colors
local rgb = Color3.fromRGB

local WIDTH, HEIGHT = 470, 300 -- design px (1080p); the kit's AutoScale fits it to the screen
local HEADER = 30
local BAR = 44
local BAR_MAX = 100
local TEXT = 19
local MAX_LINES = 120
local MAX_CHARS = 200
local IDLE_AFTER = 10 -- quiet seconds before the window fades back
local SEND_GAP = 0.6 -- the server's own rate limit is stricter; this only stops a held Enter

-- name inks for other players (stable per player); you are always candle gold
local INKS = {
	rgb(222, 224, 214), -- chalk
	rgb(230, 128, 140), -- rose
	rgb(140, 170, 236), -- ink blue
	rgb(140, 196, 146), -- ink green
	rgb(190, 148, 232), -- violet
	rgb(230, 172, 112), -- amber
	rgb(128, 200, 204), -- verdigris
}

local Local = {}
local Shared = {}

local Ui = nil
local State = {
	Shown = true,
	LastActive = os.clock(),
	Hover = false,
	Faded = false,
	History = {} :: { string },
	HistoryAt = 0,
	LastSent = 0,
	EatSlash = nil :: string?,
	Line = 0,
	Touch = false,
}

---| Helpers |---

local function new(Class: string, Props: { [string]: any }?): any
	return Kit.new(Class, Props)
end

local function tween(Inst: Instance, Time: number, Goal: { [string]: any })
	local T = TweenService:Create(Inst, TweenInfo.new(Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), Goal)
	T:Play()
	return T
end

local function hex(Col: Color3): string
	return Col:ToHex()
end

-- for text we write ourselves into a RichText label (names from the server and filtered chat are escaped already)
function Local.Escape(S: string): string
	return (S:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
end

function Local.Trim(S: string): string
	return (S:gsub("^%s+", ""):gsub("%s+$", ""))
end

function Local.Ink(UserId: number): Color3
	local Me = Players.LocalPlayer
	if Me and UserId == Me.UserId then
		return C.Gold
	end
	return INKS[(math.abs(UserId) % #INKS) + 1]
end

function Local.Reduced(): boolean
	local Ok, R = pcall(Kit.ReducedMotion)
	return Ok and R == true
end

---| Building |---

-- Fills a ScreenGui with the chat window. Returns the Ui table. Used live (Shared.OnStart) and by the edit preview.
function Shared.Build(Gui: ScreenGui)
	Gui.ResetOnSpawn = false
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.IgnoreGuiInset = false
	pcall(Kit.AutoScale, Gui)

	local Window, Api = Kit.Panel({
		ornament = "thin",
		bgTransparency = 0.18,
		inset = 12,
		Name = "Window",
		Size = UDim2.fromOffset(WIDTH, HEIGHT),
		Position = UDim2.fromOffset(16, 10),
		Parent = Gui,
	})
	local Decor = Api.Decor
	local Content = Api.Content

	-- header: the channel name, and the key hint (the letter count while typing)
	local Header = new("CanvasGroup", {
		Name = "Header",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, HEADER),
		ZIndex = 8,
		Parent = Content,
	})
	Kit.Image("Knob", {
		Name = "Mark",
		ImageColor3 = C.Gold,
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 2, 0.5, -1),
		Size = UDim2.fromOffset(16, 16),
		ZIndex = 9,
		Parent = Header,
	})
	local Title = Kit.Emboss(Kit.Text({
		Name = "Title",
		Text = "HALLWAY",
		Font = Theme.Fonts.Title,
		TextSize = 19,
		TextColor3 = C.Gold,
		Position = UDim2.fromOffset(26, 0),
		Size = UDim2.new(0.5, 0, 1, 0),
		ZIndex = 9,
		Parent = Header,
	}))
	local Hint = Kit.Text({
		Name = "Hint",
		Text = "Press <b>/</b> to talk",
		TextSize = 16,
		TextColor3 = C.TextDim,
		TextXAlignment = Enum.TextXAlignment.Right,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -4, 0, 0),
		Size = UDim2.new(0.5, 0, 1, 0),
		ZIndex = 9,
		Parent = Header,
	})
	Kit.Image("Divider", {
		Name = "Rule",
		ScaleType = Enum.ScaleType.Stretch,
		ImageColor3 = C.Iron,
		ImageTransparency = 0,
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.new(0.5, 0, 1, 4),
		Size = UDim2.new(1, 0, 0, 12),
		ZIndex = 9,
		Parent = Header,
	})

	-- the log
	local Log = new("ScrollingFrame", {
		Name = "Log",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, HEADER + 6),
		Size = UDim2.new(1, 0, 1, -(HEADER + 6 + BAR + 8)),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = C.GoldDeep,
		ScrollBarImageTransparency = 0.2,
		VerticalScrollBarInset = Enum.ScrollBarInset.ScrollBar,
		ZIndex = 8,
		Parent = Content,
	})
	new("UIListLayout", {
		Padding = UDim.new(0, 3),
		SortOrder = Enum.SortOrder.LayoutOrder,
		-- (Bottom alignment in a scrolling frame lays lines out above the canvas, so the scroll-to-end hid them)
		VerticalAlignment = Enum.VerticalAlignment.Top,
		Parent = Log,
	})
	new("UIPadding", { PaddingRight = UDim.new(0, 6), PaddingBottom = UDim.new(0, 2), Parent = Log })

	-- the bar
	local Bar = new("CanvasGroup", {
		Name = "Bar",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, BAR),
		BackgroundColor3 = C.Ink,
		BackgroundTransparency = 0.12,
		BorderSizePixel = 0,
		ZIndex = 8,
		Parent = Content,
	})
	local Frame = Kit.Slice("FrameThin", C.IronDim, { Name = "Frame", SliceScale = 0.4, ZIndex = 9, Parent = Bar })
	local Quill = Kit.Image("IconNib", {
		Name = "Quill",
		ImageColor3 = C.GoldDeep,
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 10, 0.5, 0),
		Size = UDim2.fromOffset(22, 22),
		ZIndex = 10,
		Parent = Bar,
	})
	local Box = new("TextBox", {
		Name = "Box",
		BackgroundTransparency = 1,
		ClearTextOnFocus = false,
		Font = Theme.Fonts.Body,
		Text = "",
		TextSize = 20,
		TextColor3 = C.Text,
		PlaceholderText = "Press / to talk...",
		PlaceholderColor3 = C.TextFaint,
		TextXAlignment = Enum.TextXAlignment.Left,
		TextYAlignment = Enum.TextYAlignment.Center,
		TextWrapped = true,
		MultiLine = false,
		ClipsDescendants = true,
		Position = UDim2.fromOffset(40, 0),
		Size = UDim2.new(1, -40 - 74, 1, 0),
		ZIndex = 10,
		Parent = Bar,
	})
	local Send = new("TextButton", {
		Name = "Send",
		AutoButtonColor = false,
		BackgroundColor3 = C.Well,
		BackgroundTransparency = 0.1,
		BorderSizePixel = 0,
		Text = "",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -6, 0.5, 0),
		Size = UDim2.fromOffset(62, 32),
		ZIndex = 10,
		Parent = Bar,
	})
	local SendFrame = Kit.Slice("FrameThin", C.GoldDeep, { Name = "Frame", SliceScale = 0.35, ZIndex = 11, Parent = Send })
	Kit.Text({
		Name = "Label",
		Text = "SEND",
		Font = Theme.Fonts.Title,
		TextSize = 16,
		TextColor3 = C.Gold,
		TextXAlignment = Enum.TextXAlignment.Center,
		ZIndex = 12,
		Parent = Send,
	})

	local U = {
		Gui = Gui,
		Window = Window,
		Decor = Decor,
		Background = Decor:FindFirstChild("Background"),
		Border = Decor:FindFirstChild("Ornament"),
		Shadow = Decor:FindFirstChild("Shadow"),
		Header = Header,
		Title = Title,
		Hint = Hint,
		Log = Log,
		Bar = Bar,
		Frame = Frame,
		Quill = Quill,
		Box = Box,
		Send = Send,
		SendFrame = SendFrame,
	}
	return U
end

-- one line in the log. Rich is RichText; Ink colours the diamond
function Local.AddLine(U, Rich: string, Ink: Color3, Italic: boolean?)
	State.Line += 1
	local Log = U.Log
	local AtBottom = Log.CanvasPosition.Y >= Log.AbsoluteCanvasSize.Y - Log.AbsoluteWindowSize.Y - 24
	local Row = new("Frame", {
		Name = "Line",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		LayoutOrder = State.Line,
		ZIndex = 8,
	})
	local Pip = Kit.Image("Pip", {
		Name = "Pip",
		ImageColor3 = Ink,
		Position = UDim2.fromOffset(1, 8),
		Size = UDim2.fromOffset(8, 8),
		ZIndex = 9,
		Parent = Row,
	})
	local Label = Kit.Text({
		Name = "Text",
		Text = if Italic then `<i>{Rich}</i>` else Rich,
		TextSize = TEXT,
		TextWrapped = true,
		TextYAlignment = Enum.TextYAlignment.Top,
		TextStrokeTransparency = 0.45,
		Position = UDim2.fromOffset(15, 0),
		Size = UDim2.new(1, -15, 0, 0),
		AutomaticSize = Enum.AutomaticSize.Y,
		ZIndex = 9,
		Parent = Row,
	})
	Row.Parent = Log
	if not Local.Reduced() then
		Label.TextTransparency = 1
		Pip.ImageTransparency = 1
		tween(Label, 0.18, { TextTransparency = 0 })
		tween(Pip, 0.18, { ImageTransparency = 0 })
	end
	-- keep the newest MAX_LINES
	local Lines = {}
	for _, L in Log:GetChildren() do
		if L.Name == "Line" then table.insert(Lines, L) end
	end
	if #Lines > MAX_LINES then
		table.sort(Lines, function(A, B) return A.LayoutOrder < B.LayoutOrder end)
		for I = 1, #Lines - MAX_LINES do Lines[I]:Destroy() end
	end
	if AtBottom then
		task.defer(function()
			Log.CanvasPosition = Vector2.new(0, 1e7)
		end)
	end
	return Row
end

function Local.Say(U, Name: string, Ink: Color3, Body: string, Tag: string?)
	local After = if Tag then ` <font color="#{hex(C.Mana:Lerp(Color3.new(1, 1, 1), 0.3))}"><i>{Tag}</i></font>` else ""
	return Local.AddLine(U, `<font color="#{hex(Ink)}"><b>{Name}</b></font>{After}   {Body}`, Ink)
end

function Local.System(U, Body: string)
	return Local.AddLine(U, `<font color="#{hex(C.TextDim)}">{Body}</font>`, C.TextFaint, true)
end

---| Look: focus, fade, bar height |---

function Local.Focused(): boolean
	return Ui ~= nil and Ui.Box:IsFocused()
end

function Local.SetFocusLook(U, On: boolean)
	tween(U.Frame, 0.15, { ImageColor3 = if On then C.Gold else C.IronDim })
	tween(U.Quill, 0.15, { ImageColor3 = if On then C.Gold else C.GoldDeep })
	tween(U.Bar, 0.15, { BackgroundTransparency = if On then 0.02 else 0.12 })
end

function Local.UpdateHint(U)
	local N = utf8.len(U.Box.Text) or #U.Box.Text
	if U.Box:IsFocused() and N > 0 then
		local Col = if N >= MAX_CHARS then C.Danger elseif N >= MAX_CHARS - 30 then C.Gold else C.TextDim
		U.Hint.Text = `<font color="#{hex(Col)}">{N}</font> / {MAX_CHARS}`
	elseif U.Box:IsFocused() then
		U.Hint.Text = "<b>Enter</b> sends · <b>Esc</b> leaves"
	elseif State.Touch then
		U.Hint.Text = "Tap the bar to talk"
	else
		U.Hint.Text = "Press <b>/</b> to talk"
	end
end

-- a long note wraps; the bar grows (up to BAR_MAX) and the log gives way
function Local.Resize(U)
	local Want = math.clamp(U.Box.TextBounds.Y / math.max(U.Gui:FindFirstChild("NHAutoScale") and U.Gui.NHAutoScale.Scale or 1, 0.01) + 18, BAR, BAR_MAX)
	if U.Box.Text == "" then Want = BAR end
	U.Bar.Size = UDim2.new(1, 0, 0, Want)
	U.Log.Size = UDim2.new(1, 0, 1, -(HEADER + 6 + Want + 8))
end

function Local.SetFaded(U, Faded: boolean, Instant: boolean?)
	if State.Faded == Faded and not Instant then return end
	State.Faded = Faded
	local T = if Instant or Local.Reduced() then 0.01 else (if Faded then 0.8 else 0.2)
	if U.Background then
		tween(U.Background, T, { ImageTransparency = if Faded then 0.94 else 0.18, BackgroundTransparency = if Faded then 1 else 0.18 })
	end
	if U.Border then
		for _, B in (if U.Border:IsA("ImageLabel") then { U.Border } else U.Border:GetChildren()) do
			if B:IsA("ImageLabel") then tween(B, T, { ImageTransparency = if Faded then 0.8 else 0 }) end
		end
	end
	if U.Shadow then tween(U.Shadow, T, { ImageTransparency = if Faded then 1 else 0.15 }) end
	tween(U.Header, T, { GroupTransparency = if Faded then 0.75 else 0 })
	tween(U.Bar, T, { GroupTransparency = if Faded then 0.6 else 0 })
	U.Log.ScrollBarImageTransparency = if Faded then 1 else 0.2
end

function Local.Wake()
	State.LastActive = os.clock()
	if Ui then Local.SetFaded(Ui, false) end
end

---| Sending |---

function Local.Target(): TextChannel?
	local Cfg = TextChatService:FindFirstChildOfClass("ChatInputBarConfiguration")
	local T = Cfg and Cfg.TargetTextChannel
	if T then return T end
	local Folder = TextChatService:FindFirstChild("TextChannels")
	return Folder and Folder:FindFirstChild("RBXGeneral") :: TextChannel?
end

function Local.Send()
	if not Ui then return end
	local Text = Local.Trim(Ui.Box.Text)
	Ui.Box.Text = ""
	Local.Resize(Ui)
	if Text == "" then return end
	if os.clock() - State.LastSent < SEND_GAP then
		Ui.Box.Text = Text
		return
	end
	State.LastSent = os.clock()
	table.insert(State.History, Text)
	if #State.History > 30 then table.remove(State.History, 1) end
	State.HistoryAt = #State.History + 1
	local Channel = Local.Target()
	if not Channel then
		Local.System(Ui, "The hallway is quiet: chat isn't ready yet.")
		return
	end
	task.spawn(function()
		local Ok, Msg = pcall(Channel.SendAsync, Channel, Text)
		local Status = Ok and Msg and Msg.Status
		if not Ok or (Status and Status ~= Enum.TextChatMessageStatus.Success and Status ~= Enum.TextChatMessageStatus.Sending) then
			local Why = if Status == Enum.TextChatMessageStatus.Floodchecked then "you're talking too fast"
				elseif Status == Enum.TextChatMessageStatus.MessageTooLong then "it's too long"
				elseif Status == Enum.TextChatMessageStatus.TextFilterFailed then "the filter couldn't check it"
				else "something went wrong"
			if Ui then Local.System(Ui, `Your note didn't send: {Why}.`) end
		end
	end)
end

function Local.Focus()
	if not Ui or Players.LocalPlayer:GetAttribute("InMainMenu") == true then return end
	if not State.Shown then Shared.SetShown(true) end
	Local.Wake()
	State.EatSlash = Ui.Box.Text
	Ui.Box:CaptureFocus()
	task.delay(0.15, function() State.EatSlash = nil end)
end

---| Incoming |---

function Local.OnMessage(Msg: TextChatMessage)
	if not Ui then return end
	local Src = Msg.TextSource
	local Chan = Msg.TextChannel
	local ChanName = if Chan then Chan.Name else ""
	if Src then
		local Me = Players.LocalPlayer
		local P = Players:GetPlayerByUserId(Src.UserId)
		-- Roblox's prefix is "<font color=...>Name:</font>": keep the name, drop its colour and colon (we ink it)
		local Name = Local.Trim((string.gsub(Msg.PrefixText, "<[^>]->", "")))
		Name = Local.Trim((string.gsub(Name, ":$", "")))
		if Name == "" then Name = if P then Local.Escape(P.DisplayName) else Local.Escape(Src.Name) end
		local Tag = nil
		if string.sub(ChanName, 1, 10) == "RBXWhisper" and Chan then
			if Me and Src.UserId == Me.UserId then
				local To = "?"
				for _, S in Chan:GetChildren() do
					if S:IsA("TextSource") and S.UserId ~= Me.UserId then
						local Other = Players:GetPlayerByUserId(S.UserId)
						To = Local.Escape(if Other then Other.DisplayName else S.Name)
					end
				end
				Tag = `to {To}:`
			else
				Tag = "whispers:"
			end
		elseif string.sub(ChanName, 1, 7) == "RBXTeam" then
			Tag = "[team]"
		end
		Local.Say(Ui, Name, Local.Ink(Src.UserId), Msg.Text, Tag)
	else
		if Msg.Text == "" then return end
		Local.System(Ui, Msg.Text)
	end
	Local.Wake()
end

---| Bubbles |---

-- player bubbles look like the students' (Controllers.World.NpcLook): ink well, gold rim, bone Garamond.
-- The place's own bubble image (BubbleChatConfiguration.ImageLabel) is a rim: we only tint it. The tail takes
-- BackgroundColor3.
function Local.StyleBubbles()
	local B = TextChatService:FindFirstChildOfClass("BubbleChatConfiguration")
	if not B then return end
	pcall(function()
		B.BackgroundColor3 = C.Well
		B.BackgroundTransparency = 0.12
		B.TextColor3 = C.Text
		B.FontFace = Theme.FontFaces.Body
		B.TextSize = 19
		B.TailVisible = true
	end)
	local function child(Class: string): any
		local X = B:FindFirstChildOfClass(Class)
		if not X then
			X = Instance.new(Class)
			X.Parent = B
		end
		return X
	end
	pcall(function()
		child("UICorner").CornerRadius = UDim.new(0, 6)
		local Pad = child("UIPadding")
		Pad.PaddingLeft, Pad.PaddingRight = UDim.new(0, 10), UDim.new(0, 10)
		Pad.PaddingTop, Pad.PaddingBottom = UDim.new(0, 6), UDim.new(0, 6)
		local G = B:FindFirstChildOfClass("UIGradient")
		if G then
			G.Color = ColorSequence.new(Color3.new(1, 1, 1))
			G.Transparency = NumberSequence.new(0)
		end
		local Img = child("ImageLabel")
		if Img.Image == "" then
			-- NH Combat Test's bubble rim (the Map's config has none)
			Img.Image = "rbxassetid://94961441938931"
			Img.ScaleType = Enum.ScaleType.Slice
			Img.SliceCenter = Rect.new(11, 11, 263, 111)
		end
		Img.ImageColor3 = C.GoldDeep
	end)
end

---| Public |---

function Shared.SetShown(On: boolean)
	State.Shown = On
	if Ui then
		Ui.Window.Visible = On and Players.LocalPlayer:GetAttribute("InMainMenu") ~= true
		if On then Local.Wake() elseif Ui.Box:IsFocused() then Ui.Box:ReleaseFocus(false) end
	end
end

function Shared.IsShown(): boolean
	return State.Shown
end

function Shared.Focus()
	Local.Focus()
end

function Shared.OnStart()
	local Player = Players.LocalPlayer
	-- Roblox's own window and bar make way (the TopBar and the cinematic view switch ours instead)
	pcall(function()
		TextChatService.ChatWindowConfiguration.Enabled = false
		TextChatService.ChatInputBarConfiguration.Enabled = false
	end)
	Local.StyleBubbles()

	local Gui = Instance.new("ScreenGui")
	Gui.Name = "NHChat"
	Gui.DisplayOrder = 3 -- the HUD's layer: panels open above it
	Ui = Shared.Build(Gui)
	Gui.Parent = Player:WaitForChild("PlayerGui")
	local U = Ui
	local OkT, Touch = pcall(Kit.TouchOnly)
	State.Touch = OkT and Touch == true
	if State.Touch then U.Box.PlaceholderText = "Tap to talk..." end

	-- the bar
	U.Box.Focused:Connect(function()
		Local.Wake()
		Local.SetFocusLook(U, true)
		Local.UpdateHint(U)
	end)
	U.Box.FocusLost:Connect(function(Enter)
		Local.SetFocusLook(U, false)
		if Enter then Local.Send() end
		Local.UpdateHint(U)
		State.LastActive = os.clock()
	end)
	U.Box:GetPropertyChangedSignal("Text"):Connect(function()
		local T = U.Box.Text
		-- the / that opened the bar isn't part of the note
		if State.EatSlash and T == State.EatSlash .. "/" then
			State.EatSlash = nil
			U.Box.Text = string.sub(T, 1, -2)
			return
		end
		if (utf8.len(T) or #T) > MAX_CHARS then
			local Cut = utf8.offset(T, MAX_CHARS + 1)
			U.Box.Text = if Cut then string.sub(T, 1, Cut - 1) else string.sub(T, 1, MAX_CHARS)
			return
		end
		Local.UpdateHint(U)
		Local.Resize(U)
	end)
	U.Send.MouseButton1Click:Connect(function()
		Local.Send()
		Local.Wake()
	end)
	U.Send.MouseEnter:Connect(function() tween(U.SendFrame, 0.12, { ImageColor3 = C.Gold }) end)
	U.Send.MouseLeave:Connect(function() tween(U.SendFrame, 0.12, { ImageColor3 = C.GoldDeep }) end)
	U.Window.MouseEnter:Connect(function() State.Hover = true Local.Wake() end)
	U.Window.MouseLeave:Connect(function() State.Hover = false State.LastActive = os.clock() end)

	-- keys: / opens the bar; Up / Down walk back through what you sent
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Input.KeyCode == Enum.KeyCode.Slash then
			if Processed or UserInputService:GetFocusedTextBox() then return end
			if Player:GetAttribute("InMainMenu") == true then return end
			Local.Focus()
			return
		end
		if UserInputService:GetFocusedTextBox() ~= U.Box then return end
		local Step = if Input.KeyCode == Enum.KeyCode.Up then -1 elseif Input.KeyCode == Enum.KeyCode.Down then 1 else 0
		if Step == 0 or #State.History == 0 then return end
		State.HistoryAt = math.clamp(State.HistoryAt + Step, 1, #State.History + 1)
		U.Box.Text = State.History[State.HistoryAt] or ""
		task.defer(function() U.Box.CursorPosition = #U.Box.Text + 1 end)
	end)

	-- incoming
	TextChatService.MessageReceived:Connect(function(Msg)
		local Ok, Err = pcall(Local.OnMessage, Msg)
		if not Ok then warn(`[Chat] {Err}`) end
	end)

	-- the main menu hides it
	Player:GetAttributeChangedSignal("InMainMenu"):Connect(function() Shared.SetShown(State.Shown) end)
	Shared.SetShown(State.Shown)

	-- fade back when quiet
	task.spawn(function()
		while Gui.Parent do
			local Busy = U.Box:IsFocused() or State.Hover or os.clock() - State.LastActive < IDLE_AFTER
			Local.SetFaded(U, not Busy)
			task.wait(0.25)
		end
	end)
	Local.UpdateHint(U)
end

-- Edit-mode mockup: the window with sample lines, a focused bar and a sample bubble.
-- Faded = true shows the quiet look instead (no bubble), lower down the screen.
function Shared.Preview(Gui: ScreenGui, Faded: boolean?)
	for _, X in Gui:GetChildren() do X:Destroy() end
	local U = Shared.Build(Gui)
	if Faded then
		U.Window.Position = UDim2.fromOffset(16, HEIGHT + 60)
	end
	Ui = U
	local function id(N: number) return N end
	Local.System(U, "Welcome to Nightmare Highschool. Mind the halls after dark.")
	Local.Say(U, "Mirela", Local.Ink(id(3)), "anyone know where Room 102 is?")
	Local.Say(U, "Fenwick", Local.Ink(id(5)), "past the chapel stairs, left at the portraits :)")
	Local.Say(U, "Ash", Local.Ink(id(2)), "don't go after the bell... the lights go out", nil)
	Local.Say(U, "Corvin", Local.Ink(id(4)), "meet me by the lockers", "whispers:")
	Local.Say(U, "Testy", C.Gold, "on my way, save me a seat!")
	Local.System(U, "Corvin joined the Crimson Court.")
	U.Box.Text = "who's coming to the seance tonight?"
	Local.SetFocusLook(U, true)
	tween(U.Frame, 0.01, { ImageColor3 = C.Gold })
	U.Hint.Text = `<font color="#{hex(C.TextDim)}">34</font> / {MAX_CHARS}`
	Ui = nil
	if Faded then
		U.Box.Text = ""
		tween(U.Frame, 0.01, { ImageColor3 = C.IronDim })
		tween(U.Quill, 0.01, { ImageColor3 = C.GoldDeep })
		U.Hint.Text = "Press <b>/</b> to talk"
		State.Faded = false
		Local.SetFaded(U, true, true)
		return U
	end
	-- a sample bubble, as it will look over a player's head
	local Bubble = new("Frame", {
		Name = "SampleBubble",
		AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.new(0.5, 0, 0, 120),
		Size = UDim2.fromOffset(0, 40),
		AutomaticSize = Enum.AutomaticSize.X,
		BackgroundColor3 = C.Well,
		BackgroundTransparency = 0.12,
		Parent = Gui,
	})
	new("UICorner", { CornerRadius = UDim.new(0, 6), Parent = Bubble })
	new("UIPadding", { PaddingLeft = UDim.new(0, 12), PaddingRight = UDim.new(0, 12), Parent = Bubble })
	new("UIGradient", { Rotation = 90, Color = ColorSequence.new(Color3.new(1, 1, 1), rgb(190, 186, 196)), Parent = Bubble })
	Kit.Slice("FrameThin", C.GoldDeep, { Name = "Rim", SliceScale = 0.35, Position = UDim2.fromOffset(-12, 0), Size = UDim2.new(1, 24, 1, 0), ZIndex = 4, Parent = Bubble })
	Kit.Text({
		Text = "who's coming to the seance tonight?",
		TextSize = 19,
		TextXAlignment = Enum.TextXAlignment.Center,
		Size = UDim2.new(0, 0, 1, 0),
		AutomaticSize = Enum.AutomaticSize.X,
		ZIndex = 5,
		Parent = Bubble,
	})
	new("ImageLabel", {
		Name = "Tail",
		BackgroundColor3 = C.Well,
		BackgroundTransparency = 0.12,
		BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 1, 0),
		Size = UDim2.fromOffset(12, 12),
		Rotation = 45,
		ZIndex = 1,
		Parent = Bubble,
	})
	return U
end

return Shared
