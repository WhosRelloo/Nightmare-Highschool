--[[
	PromptUi (client): the Nightmare Highschool look for every ProximityPrompt.  (2.38, Quiet Corners QC2)
	Spec: docs/superpowers/specs/2026-11-21-quiet-corners-ui-design.md §3, §9. Rules: ReplicatedStorage.Functions.QuietCorners.
	Art: ReplicatedStorage.Config.QuietCornersArt (PromptCap<Race>, PromptCapFill, PromptTag<Race>, PromptPip<Race>).
	Prompts switch to Style = Custom on THIS client only (the server's prompts are untouched), which
	hides Roblox's default popup; a billboard is drawn instead:
	  (2.38) the nearest prompt: a PromptCap<Race> key cap (56) whose PromptCapFill rises in candle-gold while you hold
	         (the Well clip grows 0 -> 1 over HoldDuration), and a PromptTag<Race> 9-slice tag beside it that grows to fit
	         the action (22 px bold) and the object (20 px). Every other shown prompt draws only a PromptPip<Race> (26).
	  (2.38) nearest = QC.Nearest over the shown prompts' adornee distances to the character's root, every 0.1 s.
	  (2.38) no art uploaded yet (ids 0): today's FrameSlot look, with the text raised to 22 / 20 and the tag fitted.
	  (2.38) the trims follow the local player's Race attribute and re-skin when it changes.
	Touch / mouse: hold the key cap. Keyboard and gamepad input are still handled by ProximityPromptService (E stays E).
	Opt a prompt out with the attribute KeepDefaultStyle = true.
	Sounds: a key click when a hold begins, a bell ping when it triggers (Effects volume).
	Rejected: when the server refuses the action, the fill turns crimson and drains, the cap shakes
	(not with Reduce Motion) and the action line reads "✗ <reason>" for a moment.
	  Server:  Prompt:SetAttribute("NHRejected", `{player.UserId}|{reason}|{os.clock()}`)   (only that player sees it)
	  Client:  PromptUi.Reject(Prompt, Reason?)
	(2.38) Studio probe (HudState.Probe): "Prompts"() -> one entry per shown prompt
	  { Name, Nearest, Cap, Tag, Pip, Key, Action, ActionSize, ObjectSize, Fits }. Check: tools/quietcorners/checks/qc_prompts.lua
]]

---| Services |---

local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TextService = game:GetService(`TextService`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Colors = Kit.Theme.Colors
local Fonts = Kit.Theme.Fonts
local QC = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`QuietCorners`)) -- (2.38)
local Art = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`QuietCornersArt`)) -- (2.38)

local Player = Players.LocalPlayer

-- (2.38) design px (spec §3, plan R6)
local CAP = 56
local TAG_X = 50
local HEIGHT = 64
local PIP = 26
local ACTION_SIZE = 22
local OBJECT_SIZE = 20
-- (2.38) ink on paper, measured for 4.5:1 on the tag's paper (spec §9)
local INK = Color3.fromRGB(40, 22, 16)
local INK_DIM = Color3.fromRGB(48, 30, 22)
local INK_RED = Color3.fromRGB(96, 10, 16)
local TAG_PAPER = Color3.fromRGB(170, 156, 134)
local CAP_METAL = Color3.fromRGB(46, 41, 40)

local function BoxString(B: { number }): string return `{B[1]},{B[2]},{B[3]},{B[4]}` end
local TAG_BOX = (Art.Boxes and Art.Boxes.PromptTag) or { 0.11, 0.08, 0.90, 0.92 }
local CAP_BOX = (Art.Boxes and Art.Boxes.PromptCap) or { 0.12, 0.15, 0.88, 0.85 }

local Local = {}
local Shared = {}

local Shown = {} :: { [ProximityPrompt]: any }

function Local.Adopt(Item: Instance)
	if Item:IsA(`ProximityPrompt`) and not Item:GetAttribute(`KeepDefaultStyle`) then
		Item.Style = Enum.ProximityPromptStyle.Custom
	end
end

function Local.Reduced(): boolean
	return Player:GetAttribute(`NHReducedMotion`) == true or Kit.ReducedMotion() == true
end

function Local.Race(): string return QC.Race(Player:GetAttribute(`Race`)) end -- (2.38)

-- (2.38) the art for this race, or nil = the kit fallback
function Local.Images()
	local Race = Local.Race()
	return {
		Cap = QC.Image(Art, `PromptCap`, Race);
		Fill = QC.Image(Art, `PromptCapFill`);
		Tag = QC.Image(Art, `PromptTag`, Race);
		Pip = QC.Image(Art, `PromptPip`, Race);
	}
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

function Local.Where(Adornee: Instance?): Vector3?
	if Adornee == nil then return nil end
	if Adornee:IsA(`BasePart`) then return Adornee.Position end
	if Adornee:IsA(`Attachment`) then return Adornee.WorldPosition end
	return nil
end

function Local.Width(Text: string, Size: number, Font: Enum.Font): number
	return TextService:GetTextSize(Text, Size, Font, Vector2.new(2000, 100)).X
end

-- (2.38) a plain text line (no stroke, no emboss: ink on paper)
function Local.Label(Props: { [string]: any }): TextLabel
	local L = Instance.new(`TextLabel`)
	L.BackgroundTransparency = 1
	L.BorderSizePixel = 0
	L.TextScaled = false
	L.TextWrapped = false
	L.TextXAlignment = Enum.TextXAlignment.Left
	L.TextYAlignment = Enum.TextYAlignment.Center
	L.TextTruncate = Enum.TextTruncate.AtEnd
	for K, V in Props do
		if K ~= `Parent` then (L :: any)[K] = V end
	end
	L.Parent = Props.Parent
	return L
end

function Local.Build(Prompt: ProximityPrompt, InputType: Enum.ProximityPromptInputType)
	local Conns = {}
	local Img = Local.Images()
	local Mode = { Cap = Img.Cap ~= nil; Fill = Img.Cap ~= nil and Img.Fill ~= nil; Tag = Img.Tag ~= nil; Pip = Img.Pip ~= nil }
	local Entry = { Prompt = Prompt; InputType = InputType; Conns = Conns; Mode = Mode; Nearest = nil :: boolean? }

	local Board = Instance.new(`BillboardGui`)
	Board.Name = `NHPrompt`
	Board.AlwaysOnTop = true
	Board.LightInfluence = 0
	Board.ResetOnSpawn = false
	Board.Active = true
	Board.Size = UDim2.fromOffset(TAG_X + 320, HEIGHT)
	Board.Adornee = Local.Adornee(Prompt)
	Entry.Board = Board

	local Scale = Instance.new(`UIScale`)
	Scale.Scale = if Local.Reduced() then 1 else 0.85
	Scale.Parent = Board

	-- (2.38) the key cap: PromptCap<Race>, 56 x 56 at (0, 4); the fallback is today's ink cap with its FrameSlot rim.
	local Cap = Instance.new(`ImageButton`)
	Cap.Name = `Key`
	Cap.AutoButtonColor = false
	Cap.Size = UDim2.fromOffset(CAP, CAP)
	Cap.Position = UDim2.fromOffset(0, (HEIGHT - CAP) / 2)
	Cap.BorderSizePixel = 0
	Cap.ZIndex = 3
	Cap:SetAttribute(`QcBox`, BoxString(CAP_BOX))
	if Mode.Cap then
		Cap.Image = Img.Cap :: string
		Cap.BackgroundTransparency = 1
		Cap:SetAttribute(`QcBg`, CAP_METAL)
	else
		Cap.Image = ``
		Cap.BackgroundColor3 = Colors.Ink
		Cap.BackgroundTransparency = 0.05
	end
	Cap.Parent = Board

	-- (2.38) the Well: a transparent clip anchored at the cap's bottom; its height goes 0 -> 1 over HoldDuration and reveals the Fill.
	local Inset = if Mode.Cap then 0 else 4
	local Well = Instance.new(`Frame`)
	Well.Name = `Well`
	Well.BackgroundTransparency = 1
	Well.BorderSizePixel = 0
	Well.ClipsDescendants = true
	Well.AnchorPoint = Vector2.new(0, 1)
	Well.Position = UDim2.new(0, Inset, 1, -Inset)
	Well.ZIndex = 4
	Well.Parent = Cap
	local function WellSize(H: number): UDim2 return UDim2.new(1, -2 * Inset, H, -2 * Inset * H) end
	Well.Size = WellSize(0)

	local Fill: GuiObject
	local FillGrad: UIGradient? = nil
	if Mode.Fill then
		local F = Instance.new(`ImageLabel`)
		F.Image = Img.Fill :: string
		F.ImageColor3 = Colors.Gold
		F.BackgroundTransparency = 1
		Fill = F
	else
		local F = Instance.new(`Frame`)
		F.BackgroundColor3 = Colors.Gold
		F.BackgroundTransparency = 0.35
		local G = Instance.new(`UIGradient`)
		G.Rotation = 90
		G.Color = ColorSequence.new(Colors.Gold, Colors.GoldDeep)
		G.Parent = F
		FillGrad = G
		Fill = F
	end
	Fill.Name = `Fill`
	Fill.BorderSizePixel = 0
	Fill.AnchorPoint = Vector2.new(0, 1)
	Fill.Position = UDim2.fromScale(0, 1)
	Fill.Size = UDim2.fromOffset(CAP - 2 * Inset, CAP - 2 * Inset) -- full cap box; the Well's clip reveals it bottom-up
	Fill.ZIndex = 4
	Fill.Parent = Well
	local function FillColor(C: Color3)
		if Fill:IsA(`ImageLabel`) then Fill.ImageColor3 = C else Fill.BackgroundColor3 = C end
		if FillGrad then FillGrad.Enabled = C == Colors.Gold end
	end

	if not Mode.Cap then
		Kit.Slice(`FrameSlot`, Colors.Gold:Lerp(Colors.Iron, 0.3), { SliceScale = 0.45, ZIndex = 5, Parent = Cap })
	end
	local KeyLabel = Local.KeyText(Prompt, InputType)
	local Key = Kit.Text({
		Name = `KeyText`; Text = KeyLabel; Font = Fonts.Title; TextSize = QC.KeySize(KeyLabel); -- (2.38) 22 / 20
		TextXAlignment = Enum.TextXAlignment.Center; TextYAlignment = Enum.TextYAlignment.Center; TextColor3 = Colors.Gold;
		Position = UDim2.fromScale(CAP_BOX[1], CAP_BOX[2]); Size = UDim2.fromScale(CAP_BOX[3] - CAP_BOX[1], CAP_BOX[4] - CAP_BOX[2]);
		ZIndex = 6; Parent = Cap;
	})
	Kit.Emboss(Key, Color3.fromRGB(150, 110, 60), 1.4)

	-- (2.38) the tag: PromptTag<Race> 9-slice at (50, 0), (TagWidth, 64). Fallback: today's ink plate with its FrameSlot rim.
	local Tag: GuiObject
	if Mode.Tag then
		local T = Instance.new(`ImageLabel`)
		T.Image = Img.Tag :: string
		T.ScaleType = Enum.ScaleType.Slice
		T.SliceCenter = (Art.Slices and Art.Slices.PromptTag) or Rect.new(80, 16, 560, 112)
		T.SliceScale = 0.5
		T.BackgroundTransparency = 1
		T:SetAttribute(`QcBg`, TAG_PAPER)
		Tag = T
	else
		local T = Instance.new(`ImageLabel`)
		T.Image = ``
		T.BackgroundColor3 = Colors.Ink
		T.BackgroundTransparency = 0.12
		Kit.Slice(`FrameSlot`, Colors.RowFrame, { SliceScale = 0.4, ZIndex = 2, Parent = T })
		Tag = T
	end
	Tag.Name = `Text`
	Tag.BorderSizePixel = 0
	Tag.Position = UDim2.fromOffset(TAG_X, 0)
	Tag.Size = UDim2.fromOffset(320, HEIGHT)
	Tag.ZIndex = 1
	Tag:SetAttribute(`QcBox`, BoxString(TAG_BOX))
	Tag.Parent = Board

	local ActionColor = if Mode.Tag then INK else Colors.Text
	local ObjectColor = if Mode.Tag then INK_DIM else Colors.TextDim
	local Action = Local.Label({
		Name = `Action`; Font = Fonts.Title; TextSize = ACTION_SIZE; TextColor3 = ActionColor; ZIndex = 3; Parent = Tag;
	})
	local Object = Local.Label({
		Name = `Object`; Font = Fonts.Body; TextSize = OBJECT_SIZE; TextColor3 = ObjectColor; ZIndex = 3; Parent = Tag;
	})
	if not Mode.Tag then Kit.Emboss(Action, Color3.fromRGB(160, 150, 140), 1.3) end

	-- (2.38) the pip: the only piece a non-nearest prompt shows
	local Pip: ImageLabel
	if Mode.Pip then
		Pip = Instance.new(`ImageLabel`)
		Pip.Image = Img.Pip :: string
		Pip.BackgroundTransparency = 1
	else
		Pip = Kit.Image(`Glow`, { ImageColor3 = Colors.Gold })
	end
	Pip.Name = `Pip`
	Pip.BackgroundTransparency = 1
	Pip.AnchorPoint = Vector2.new(0.5, 0.5)
	Pip.Position = UDim2.fromScale(0.5, 0.5)
	Pip.Size = UDim2.fromOffset(PIP, PIP)
	Pip.ImageTransparency = 0.15
	Pip.ZIndex = 2
	Pip.Visible = false
	Pip.Parent = Board

	Entry.Cap, Entry.Key, Entry.Tag, Entry.Pip, Entry.Action, Entry.Object, Entry.Well = Cap, Key, Tag, Pip, Action, Object, Well

	local function Refresh()
		local HasObject = Prompt.ObjectText ~= ``
		Object.Text = Prompt.ObjectText
		Object.Visible = HasObject
		Action.Text = Prompt.ActionText
		local TextW = math.max(Local.Width(Prompt.ActionText, ACTION_SIZE, Fonts.Title), if HasObject then Local.Width(Prompt.ObjectText, OBJECT_SIZE, Fonts.Body) else 0)
		local TagW = QC.TagWidth(TextW) -- (2.38) the text box is 0.11 .. 0.90 of the tag
		local X0 = math.ceil(TAG_BOX[1] * TagW) + 4
		local X1 = math.floor(TAG_BOX[3] * TagW)
		Action.Position = UDim2.fromOffset(X0, if HasObject then 21 - 13 else 32 - 13) -- centred at y 21, or 32 alone
		Action.Size = UDim2.fromOffset(X1 - X0, 26)
		Object.Position = UDim2.fromOffset(X0, 45 - 12) -- centred at y 45
		Object.Size = UDim2.fromOffset(X1 - X0, 24)
		Tag.Size = UDim2.fromOffset(TagW, HEIGHT)
		local W = TAG_X + TagW
		Board.Size = UDim2.fromOffset(W, HEIGHT)
		Board.SizeOffset = Vector2.new(Prompt.UIOffset.X / W, Prompt.UIOffset.Y / HEIGHT)
	end
	Refresh()
	Entry.Refresh = Refresh
	table.insert(Conns, Prompt:GetPropertyChangedSignal(`ActionText`):Connect(Refresh))
	table.insert(Conns, Prompt:GetPropertyChangedSignal(`ObjectText`):Connect(Refresh))
	table.insert(Conns, Prompt:GetPropertyChangedSignal(`UIOffset`):Connect(Refresh))

	-- Hold progress (2.38: the Well rises, Linear, over HoldDuration)
	local FillTween = nil
	local function ResetFill()
		if FillTween then FillTween:Cancel(); FillTween = nil end
		Well.Size = WellSize(0)
	end
	table.insert(Conns, Prompt.PromptButtonHoldBegan:Connect(function()
		ResetFill()
		if Prompt.HoldDuration > 0 then
			Kit.PlaySound(`Tick`)
			FillTween = TweenService:Create(Well, TweenInfo.new(Prompt.HoldDuration, Enum.EasingStyle.Linear), { Size = WellSize(1) })
			FillTween:Play()
		end
	end))
	table.insert(Conns, Prompt.PromptButtonHoldEnded:Connect(ResetFill))
	table.insert(Conns, Prompt.Triggered:Connect(function()
		Kit.PlaySound(`Confirm`)
		if FillTween then FillTween:Cancel(); FillTween = nil end
		Well.Size = WellSize(1)
		if not Local.Reduced() then
			Scale.Scale = 1.12
			TweenService:Create(Scale, TweenInfo.new(0.25, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 }):Play()
		end
		task.delay(0.2, ResetFill)
	end))

	-- Rejected: crimson fill, drain, a small shake and the reason, then back to normal.
	local RejectToken = 0
	local function Reject(Reason: string?)
		RejectToken += 1
		local My = RejectToken
		Kit.PlaySound(`Reject`)
		ResetFill()
		FillColor(Colors.Crimson) -- (2.38) the Fill's tint goes crimson
		Well.Size = WellSize(1)
		FillTween = TweenService:Create(Well, TweenInfo.new(0.45, Enum.EasingStyle.Quad, Enum.EasingDirection.In), { Size = WellSize(0) })
		FillTween:Play()
		Key.TextColor3 = Colors.Crimson
		Action.Text = `\u{2717} {if Reason and Reason ~= `` then Reason else `Not now`}`
		Action.TextColor3 = if Mode.Tag then INK_RED else Color3.fromRGB(232, 120, 110)
		-- (2.38) the reason may be longer than the action: widen the tag to fit it
		local TagW = QC.TagWidth(math.max(Local.Width(Action.Text, ACTION_SIZE, Fonts.Title), if Prompt.ObjectText ~= `` then Local.Width(Prompt.ObjectText, OBJECT_SIZE, Fonts.Body) else 0))
		local X0 = math.ceil(TAG_BOX[1] * TagW) + 4
		Action.Size = UDim2.fromOffset(math.floor(TAG_BOX[3] * TagW) - X0, 26)
		Object.Size = Action.Size - UDim2.fromOffset(0, 2)
		Action.Position = UDim2.fromOffset(X0, Action.Position.Y.Offset)
		Object.Position = UDim2.fromOffset(X0, Object.Position.Y.Offset)
		Tag.Size = UDim2.fromOffset(TagW, HEIGHT)
		Board.Size = UDim2.fromOffset(TAG_X + TagW, HEIGHT)
		Board.SizeOffset = Vector2.new(Prompt.UIOffset.X / (TAG_X + TagW), Prompt.UIOffset.Y / HEIGHT)
		if not Local.Reduced() then
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
			FillColor(Colors.Gold)
			Key.TextColor3 = Colors.Gold
			Action.TextColor3 = ActionColor
			Cap.Rotation = 0
			Refresh()
		end)
	end
	Entry.Reject = Reject
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

	-- (2.38) nearest-only: the nearest shows the cap and the tag; the others only the pip
	function Entry.SetNearest(Near: boolean)
		if Entry.Nearest == Near then return end
		Entry.Nearest = Near
		Cap.Visible = Near
		Tag.Visible = Near
		Pip.Visible = not Near
	end
	Entry.SetNearest(true)

	-- (2.38) re-skin in place for a new Race (the caller rebuilds when a piece switches between art and fallback)
	function Entry.Skin(): boolean
		local New = Local.Images()
		if (New.Cap ~= nil) ~= Mode.Cap or (New.Cap ~= nil and New.Fill ~= nil) ~= Mode.Fill or (New.Tag ~= nil) ~= Mode.Tag or (New.Pip ~= nil) ~= Mode.Pip then
			return false
		end
		if Mode.Cap then Cap.Image = New.Cap :: string end
		if Mode.Tag then (Tag :: ImageLabel).Image = New.Tag :: string end
		if Mode.Pip then Pip.Image = New.Pip :: string end
		return true
	end

	Board.Parent = Player:WaitForChild(`PlayerGui`)
	if Scale.Scale ~= 1 then
		TweenService:Create(Scale, TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Scale = 1 }):Play()
	end
	return Entry
end

function Local.Destroy(Entry)
	for _, Connection in Entry.Conns do Connection:Disconnect() end
	Entry.Board:Destroy()
end

-- (2.38) which shown prompt is nearest the character's root (the camera when there's no character)
function Local.UpdateNearest()
	local C = Player.Character
	local Root = C and C:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	local From = if Root then Root.Position elseif workspace.CurrentCamera then workspace.CurrentCamera.CFrame.Position else nil
	if From == nil then return end
	local Dists = {}
	for Prompt, Entry in Shown do
		local At = Local.Where(Entry.Board.Adornee)
		if At then Dists[Prompt] = (At - From).Magnitude end
	end
	local Best = QC.Nearest(Dists)
	for Prompt, Entry in Shown do
		Entry.SetNearest(Best == nil or Prompt == Best)
	end
end

function Local.Show(Prompt: ProximityPrompt, InputType: Enum.ProximityPromptInputType)
	if Shown[Prompt] then Local.Destroy(Shown[Prompt]) end
	Shown[Prompt] = Local.Build(Prompt, InputType)
	Local.UpdateNearest()
end

-- (2.38) Race changed: swap the trims, or rebuild a prompt whose pieces switch between art and fallback
function Local.Reskin()
	for Prompt, Entry in Shown do
		if not Entry.Skin() then Local.Show(Prompt, Entry.InputType) end
	end
	Local.UpdateNearest()
end

-- (2.38) Studio probe for tools/quietcorners/checks/qc_prompts.lua
function Local.ProbePrompts()
	local List = {}
	for Prompt, Entry in Shown do
		table.insert(List, {
			Name = Prompt.ActionText;
			Nearest = Entry.Nearest == true;
			Cap = Entry.Cap.Visible;
			Tag = Entry.Tag.Visible;
			Pip = Entry.Pip.Visible;
			Key = Entry.Key.Text;
			Action = Entry.Action.Text;
			ActionSize = Entry.Action.TextSize;
			ObjectSize = Entry.Object.TextSize;
			Fits = Entry.Action.TextFits and Entry.Object.TextFits;
		})
	end
	return List
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
		Local.Show(Prompt, InputType)
	end)
	ProximityPromptService.PromptHidden:Connect(function(Prompt)
		local Entry = Shown[Prompt]
		if Entry then
			Shown[Prompt] = nil
			Local.Destroy(Entry)
			Local.UpdateNearest()
		end
	end)

	-- (2.38) nearest-only, every 0.1 s
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Acc += Dt
		if Acc < 0.1 then return end
		Acc = 0
		if next(Shown) ~= nil then Local.UpdateNearest() end
	end)

	-- (2.38) re-skin on Race
	Player:GetAttributeChangedSignal(`Race`):Connect(Local.Reskin)

	-- (2.38) the probe, through HudState (required lazily: HudState may start after us)
	task.spawn(function()
		local Module = script.Parent:WaitForChild(`HudState`, 10)
		if not Module then return end
		local Ok, Hud = pcall(require, Module)
		if Ok and type(Hud) == `table` and Hud.Probe then Hud.Probe(`Prompts`, Local.ProbePrompts) end
	end)
end

return Shared
