--[[
	PromptUi (client): the Nightmare Highschool look for every ProximityPrompt.
	Prompts switch to Style = Custom on THIS client only (the server's prompts are untouched), which
	hides Roblox's default popup; an engraved billboard is drawn instead: a key cap that fills with
	candle-gold while you hold, plus the object and action text. Touch / mouse: hold the key cap.
	Keyboard and gamepad input are still handled by ProximityPromptService (E stays E).
	Opt a prompt out with the attribute KeepDefaultStyle = true.
	Sounds: a key click when a hold begins, a bell ping when it triggers (Effects volume).
	Rejected: when the server refuses the action, the cap flashes red, the fill drains, the cap shakes
	(not with Reduce Motion) and the action line reads "✗ <reason>" for a moment.
	  Server:  Prompt:SetAttribute("NHRejected", `{player.UserId}|{reason}|{os.clock()}`)   (only that player sees it)
	  Client:  PromptUi.Reject(Prompt, Reason?)
]]

---| Services |---

local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local TextService = game:GetService(`TextService`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Colors = Kit.Theme.Colors
local Fonts = Kit.Theme.Fonts

local Player = Players.LocalPlayer
local CAP = 54
local HEIGHT = 58

local Local = {}
local Shared = {}

local Shown = {} :: { [ProximityPrompt]: any }

function Local.Adopt(Item: Instance)
	if Item:IsA(`ProximityPrompt`) and not Item:GetAttribute(`KeepDefaultStyle`) then
		Item.Style = Enum.ProximityPromptStyle.Custom
	end
end

function Local.KeyText(Prompt: ProximityPrompt, InputType: Enum.ProximityPromptInputType): string
	if InputType == Enum.ProximityPromptInputType.Gamepad then return Kit.KeyName(Prompt.GamepadKeyCode) end
	if InputType == Enum.ProximityPromptInputType.Touch then return `TAP` end
	return Kit.KeyName(Prompt.KeyboardKeyCode)
end

function Local.Adornee(Prompt: ProximityPrompt): Instance?
	local Parent = Prompt.Parent
	if Parent and (Parent:IsA(`BasePart`) or Parent:IsA(`Attachment`)) then return Parent end
	if Parent and Parent:IsA(`Model`) then return Parent.PrimaryPart or Parent:FindFirstChildWhichIsA(`BasePart`, true) end
	return nil
end

function Local.Width(Text: string, Size: number, Font: Enum.Font): number
	return TextService:GetTextSize(Text, Size, Font, Vector2.new(2000, 100)).X
end

function Local.Build(Prompt: ProximityPrompt, InputType: Enum.ProximityPromptInputType)
	local Conns = {}
	local Board = Instance.new(`BillboardGui`)
	Board.Name = `NHPrompt`
	Board.AlwaysOnTop = true
	Board.LightInfluence = 0
	Board.ResetOnSpawn = false
	Board.Active = true
	Board.Size = UDim2.fromOffset(420, HEIGHT + 8)
	Board.SizeOffset = Vector2.new(Prompt.UIOffset.X / 420, Prompt.UIOffset.Y / (HEIGHT + 8))
	Board.Adornee = Local.Adornee(Prompt)

	local Scale = Instance.new(`UIScale`)
	Scale.Scale = 0.85
	Scale.Parent = Board

	local Row = Instance.new(`Frame`)
	Row.Name = `Row`
	Row.BackgroundTransparency = 1
	Row.Size = UDim2.fromScale(1, 1)
	Row.Parent = Board
	local Layout = Instance.new(`UIListLayout`)
	Layout.FillDirection = Enum.FillDirection.Horizontal
	Layout.HorizontalAlignment = Enum.HorizontalAlignment.Center
	Layout.VerticalAlignment = Enum.VerticalAlignment.Center
	Layout.Padding = UDim.new(0, 8)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Parent = Row

	-- Key cap: bracket-cornered iron cap; wax-gold fill rises while held.
	local Cap = Instance.new(`TextButton`)
	Cap.Name = `Key`
	Cap.Text = ``
	Cap.AutoButtonColor = false
	Cap.LayoutOrder = 1
	Cap.Size = UDim2.fromOffset(CAP, CAP)
	Cap.BackgroundColor3 = Colors.Ink
	Cap.BackgroundTransparency = 0.05
	Cap.BorderSizePixel = 0
	Cap.Parent = Row
	local Well = Instance.new(`Frame`)
	Well.Name = `Well`
	Well.BackgroundTransparency = 1
	Well.ClipsDescendants = true
	Well.Position = UDim2.fromOffset(4, 4)
	Well.Size = UDim2.new(1, -8, 1, -8)
	Well.ZIndex = 2
	Well.Parent = Cap
	local Fill = Instance.new(`Frame`)
	Fill.Name = `Fill`
	Fill.AnchorPoint = Vector2.new(0, 1)
	Fill.Position = UDim2.fromScale(0, 1)
	Fill.Size = UDim2.fromScale(1, 0)
	Fill.BackgroundColor3 = Colors.Gold
	Fill.BackgroundTransparency = 0.35
	Fill.BorderSizePixel = 0
	Fill.ZIndex = 2
	Fill.Parent = Well
	local FillGrad = Instance.new(`UIGradient`)
	FillGrad.Rotation = 90
	FillGrad.Color = ColorSequence.new(Colors.Gold, Colors.GoldDeep)
	FillGrad.Parent = Fill
	Kit.Slice(`FrameSlot`, Colors.Gold:Lerp(Colors.Iron, 0.3), { SliceScale = 0.45, ZIndex = 4, Parent = Cap })
	local KeyLabel = Local.KeyText(Prompt, InputType)
	local Key = Kit.Text({
		Name = `KeyText`; Text = KeyLabel; Font = Fonts.Title; TextSize = if #KeyLabel > 2 then 14 else 24;
		TextXAlignment = Enum.TextXAlignment.Center; TextColor3 = Colors.Gold; ZIndex = 5; Parent = Cap;
	})
	Kit.Emboss(Key, Color3.fromRGB(150, 110, 60), 1.4)

	-- Text plate (sized to its text so it hugs the words).
	local Plate = Instance.new(`Frame`)
	Plate.Name = `Text`
	Plate.LayoutOrder = 2
	Plate.BackgroundColor3 = Colors.Ink
	Plate.BackgroundTransparency = 0.12
	Plate.BorderSizePixel = 0
	Plate.Parent = Row
	Kit.Slice(`FrameSlot`, Colors.RowFrame, { SliceScale = 0.4, ZIndex = 4, Parent = Plate })
	local Object = Kit.Text({
		Name = `Object`; TextSize = 17; TextColor3 = Colors.TextDim; Position = UDim2.fromOffset(14, 6);
		Size = UDim2.new(1, -28, 0, 18); TextTruncate = Enum.TextTruncate.AtEnd; ZIndex = 5; Parent = Plate;
	})
	local Action = Kit.Text({
		Name = `Action`; Font = Fonts.Title; TextSize = 19; Position = UDim2.fromOffset(14, 24);
		Size = UDim2.new(1, -28, 0, 26); TextTruncate = Enum.TextTruncate.AtEnd; ZIndex = 5; Parent = Plate;
	})
	Kit.Emboss(Action, Color3.fromRGB(160, 150, 140), 1.3)

	local function Refresh()
		local HasObject = Prompt.ObjectText ~= ``
		Object.Text = Prompt.ObjectText
		Object.Visible = HasObject
		Action.Text = Prompt.ActionText
		Action.Position = UDim2.fromOffset(14, if HasObject then 24 else 15)
		local W = math.max(Local.Width(Prompt.ActionText, 19, Fonts.Title), HasObject and Local.Width(Prompt.ObjectText, 15, Fonts.Body) or 0)
		Plate.Size = UDim2.fromOffset(math.clamp(W + 34, 110, 340), HEIGHT - 6)
	end
	Refresh()
	table.insert(Conns, Prompt:GetPropertyChangedSignal(`ActionText`):Connect(Refresh))
	table.insert(Conns, Prompt:GetPropertyChangedSignal(`ObjectText`):Connect(Refresh))

	-- Hold progress
	local FillTween = nil
	local function ResetFill()
		if FillTween then FillTween:Cancel(); FillTween = nil end
		Fill.Size = UDim2.fromScale(1, 0)
	end
	table.insert(Conns, Prompt.PromptButtonHoldBegan:Connect(function()
		ResetFill()
		if Prompt.HoldDuration > 0 then Kit.PlaySound(`Tick`) end
		if Prompt.HoldDuration > 0 then
			FillTween = TweenService:Create(Fill, TweenInfo.new(Prompt.HoldDuration, Enum.EasingStyle.Linear), { Size = UDim2.fromScale(1, 1) })
			FillTween:Play()
		end
	end))
	table.insert(Conns, Prompt.PromptButtonHoldEnded:Connect(ResetFill))
	table.insert(Conns, Prompt.Triggered:Connect(function()
		Kit.PlaySound(`Confirm`)
		Fill.Size = UDim2.fromScale(1, 1)
		Scale.Scale = 1.12
		TweenService:Create(Scale, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		task.delay(0.2, ResetFill)
	end))

	-- Rejected: red flash, drain, a small shake and the reason, then back to normal.
	local RejectToken = 0
	local function Reject(Reason: string?)
		RejectToken += 1
		local My = RejectToken
		Kit.PlaySound(`Reject`)
		ResetFill()
		Fill.BackgroundColor3 = Colors.Crimson
		FillGrad.Enabled = false
		Fill.Size = UDim2.fromScale(1, 1)
		TweenService:Create(Fill, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Size = UDim2.fromScale(1, 0) }):Play()
		Key.TextColor3 = Colors.Crimson
		Action.Text = `\u{2717} {if Reason and Reason ~= `` then Reason else `Not now`}`
		Action.TextColor3 = Color3.fromRGB(232, 120, 110)
		if not Kit.ReducedMotion() then
			task.spawn(function()
				for _, R in { -7, 6, -4, 2, 0 } do
					if My ~= RejectToken then return end
					Cap.Rotation = R
					task.wait(0.045)
				end
			end)
		end
		task.delay(1.6, function()
			if My ~= RejectToken or not Board.Parent then return end
			Fill.BackgroundColor3 = Colors.Gold
			FillGrad.Enabled = true
			Key.TextColor3 = Colors.Gold
			Action.TextColor3 = Colors.Text
			Cap.Rotation = 0
			Refresh()
		end)
	end
	table.insert(Conns, Prompt:GetAttributeChangedSignal(`NHRejected`):Connect(function()
		local Value = Prompt:GetAttribute(`NHRejected`)
		if type(Value) ~= `string` then return end
		local Who, Reason = string.match(Value, `^(%d+)|([^|]*)`)
		if tonumber(Who) == Player.UserId then Reject(Reason) end
	end))

	-- Touch / mouse: holding the key cap drives the prompt.
	table.insert(Conns, Cap.InputBegan:Connect(function(Input)
		local T = Input.UserInputType
		if T == Enum.UserInputType.Touch or T == Enum.UserInputType.MouseButton1 then
			Prompt:InputHoldBegin()
		end
	end))
	table.insert(Conns, Cap.InputEnded:Connect(function(Input)
		local T = Input.UserInputType
		if T == Enum.UserInputType.Touch or T == Enum.UserInputType.MouseButton1 then
			Prompt:InputHoldEnd()
		end
	end))

	Board.Parent = Player:WaitForChild(`PlayerGui`)
	TweenService:Create(Scale, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	return { Board = Board; Conns = Conns; Reject = Reject }
end

function Local.Destroy(Entry)
	for _, Connection in Entry.Conns do Connection:Disconnect() end
	Entry.Board:Destroy()
end

-- Show the rejected state on a prompt that's on screen (client code that refuses an action itself).
function Shared.Reject(Prompt: ProximityPrompt, Reason: string?)
	local Entry = Shown[Prompt]
	if Entry and Entry.Reject then Entry.Reject(Reason) end
end

function Shared.OnStart()
	for _, Item in workspace:GetDescendants() do Local.Adopt(Item) end
	workspace.DescendantAdded:Connect(Local.Adopt)

	ProximityPromptService.PromptShown:Connect(function(Prompt, InputType)
		if Prompt.Style ~= Enum.ProximityPromptStyle.Custom then return end
		if Shown[Prompt] then Local.Destroy(Shown[Prompt]) end
		Shown[Prompt] = Local.Build(Prompt, InputType)
	end)
	ProximityPromptService.PromptHidden:Connect(function(Prompt)
		local Entry = Shown[Prompt]
		if Entry then
			Shown[Prompt] = nil
			Local.Destroy(Entry)
		end
	end)
end

return Shared
