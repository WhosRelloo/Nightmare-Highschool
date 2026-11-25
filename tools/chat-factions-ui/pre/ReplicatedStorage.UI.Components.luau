--!nonstrict
--[[
	Nightmare Highschool UI Kit - Components

	Every builder is  Components.X(opts) -> (root: GuiObject, api: table)
	  * lower-case opts are component data (title, value, onChanged ...)
	  * PascalCase opts are copied onto the root: Name, Size, Position,
	    AnchorPoint, LayoutOrder, Visible, ZIndex, Parent (Parent is set last)
	  * api.Root is the root instance; interactive parts expose :Set / :Get and
	    fire their opts callback. The current value is mirrored to the root's
	    "Value" attribute.

	Sizes are design pixels at 1920x1080. Call Components.AutoScale(screenGui)
	once per ScreenGui so they scale to any screen (touch screens never go
	below Theme.Scale.TouchMin, so 44px rows stay >= 40px).

	See Docs/UI-Kit.md for the full API.
]]

local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local IS_STUDIO = RunService:IsStudio()

local Theme = require(script.Parent:WaitForChild("Theme"))
local Colors, Sizes, Images, Fonts, Slices = Theme.Colors, Theme.Sizes, Theme.Images, Theme.Fonts, Theme.Slices

local Components = {}
Components.Theme = Theme

--------------------------------------------------------------------------
-- helpers
--------------------------------------------------------------------------
local PLACE_KEYS = { "Name", "Position", "AnchorPoint", "Size", "LayoutOrder", "Visible", "ZIndex" }
local CENTER = Enum.TextXAlignment.Center
local LEFT = Enum.TextXAlignment.Left
local RIGHT = Enum.TextXAlignment.Right

local function new(className: string, props: { [string]: any }?, children: { Instance }?)
	local inst = Instance.new(className)
	local parent = nil
	if props then
		for k, v in pairs(props) do
			if k == "Parent" then
				parent = v
			else
				(inst :: any)[k] = v
			end
		end
	end
	if children then
		for _, c in ipairs(children) do
			c.Parent = inst
		end
	end
	if parent then
		inst.Parent = parent
	end
	return inst
end
Components.new = new

local function merge(a, b)
	local out = {}
	for k, v in pairs(a) do
		out[k] = v
	end
	if b then
		for k, v in pairs(b) do
			out[k] = v
		end
	end
	return out
end

local function place(inst, opts)
	for _, k in ipairs(PLACE_KEYS) do
		if opts[k] ~= nil then
			(inst :: any)[k] = opts[k]
		end
	end
	if opts.Parent then
		inst.Parent = opts.Parent
	end
	return inst
end

local function tween(inst, info, goal)
	local t = TweenService:Create(inst, info, goal)
	t:Play()
	return t
end
Components.tween = tween

local function pad(l, r, t, b)
	return new("UIPadding", {
		PaddingLeft = UDim.new(0, l),
		PaddingRight = UDim.new(0, r or l),
		PaddingTop = UDim.new(0, t or l),
		PaddingBottom = UDim.new(0, b or t or l),
	})
end

local function round(px)
	return new("UICorner", { CornerRadius = UDim.new(0, px) })
end

-- TextLabel with kit defaults
local function text(props)
	return new("TextLabel", merge({
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Font = Fonts.Body,
		TextColor3 = Colors.Text,
		TextSize = Sizes.TextBody,
		TextXAlignment = LEFT,
		TextStrokeColor3 = Colors.Shadow,
		TextStrokeTransparency = 0.72,
		RichText = true,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 3,
	}, props))
end
Components.Text = text

-- Engraved title treatment: vertical gradient (multiplies TextColor3) + dark stroke.
local function emboss(label, bottom: Color3?, thickness: number?)
	label.TextStrokeTransparency = 1
	new("UIGradient", {
		Name = "Emboss",
		Rotation = 90,
		Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
			ColorSequenceKeypoint.new(0.45, Color3.fromRGB(236, 230, 222)),
			ColorSequenceKeypoint.new(1, bottom or Color3.fromRGB(140, 128, 118)),
		}),
		Parent = label,
	})
	new("UIStroke", {
		Name = "Engrave",
		Color = Colors.Shadow,
		Thickness = thickness or 1.6,
		Transparency = 0.12,
		ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual,
		Parent = label,
	})
	return label
end
Components.Emboss = emboss

-- Lit-from-the-left depth on a row background (UIGradient only affects its parent).
local function rowDepth(gui)
	new("UIGradient", {
		Name = "Depth",
		Color = ColorSequence.new({
			ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
			ColorSequenceKeypoint.new(0.6, Color3.fromRGB(150, 150, 150)),
			ColorSequenceKeypoint.new(1, Color3.fromRGB(105, 105, 105)),
		}),
		Parent = gui,
	})
end

-- 9-slice image (FrameThin / FrameOrnate / BarFrame / Shadow)
local function slice(key, color, props)
	local s = Slices[key]
	return new("ImageLabel", merge({
		Name = key,
		BackgroundTransparency = 1,
		Image = Images[key],
		ImageColor3 = color or Colors.Iron,
		ScaleType = Enum.ScaleType.Slice,
		SliceCenter = s.Center,
		SliceScale = s.Scale,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 6,
	}, props))
end
Components.Slice = slice

local function image(key, props)
	return new("ImageLabel", merge({
		Name = key,
		BackgroundTransparency = 1,
		Image = Images[key] or key,
		ScaleType = Enum.ScaleType.Fit,
		ZIndex = 4,
	}, props))
end
Components.Image = image

local function isPress(input)
	local t = input.UserInputType
	return t == Enum.UserInputType.MouseButton1 or t == Enum.UserInputType.Touch
end

local function lighten(c: Color3, a: number)
	return c:Lerp(Color3.new(1, 1, 1), a)
end

-- Hover / press feedback for any GuiButton. `frame` is its border image.
local function wireFeedback(button, bg, frame, baseColor, hoverColor)
	local scale = new("UIScale", { Parent = button })
	button.MouseEnter:Connect(function()
		if button:GetAttribute("Disabled") then
			return
		end
		if bg then
			tween(bg, Theme.Tween.Fast, { BackgroundColor3 = Colors.WellHover })
		end
		if frame then
			tween(frame, Theme.Tween.Fast, { ImageColor3 = hoverColor or lighten(baseColor, 0.3) })
		end
	end)
	button.MouseLeave:Connect(function()
		if bg then
			tween(bg, Theme.Tween.Fast, { BackgroundColor3 = bg:GetAttribute("BaseColor") or Colors.Well })
		end
		if frame then
			tween(frame, Theme.Tween.Fast, { ImageColor3 = frame:GetAttribute("BaseColor") or baseColor })
		end
		tween(scale, Theme.Tween.Fast, { Scale = 1 })
	end)
	button.MouseButton1Down:Connect(function()
		if not button:GetAttribute("Disabled") then
			tween(scale, Theme.Tween.Fast, { Scale = 0.96 })
		end
	end)
	button.MouseButton1Up:Connect(function()
		tween(scale, Theme.Tween.Fast, { Scale = 1 })
	end)
end

-- Ornate border: 4 fixed corners + 4 tiled edge strips (gothic arcade).
local function ornateBorder(parent, color, s)
	s = s or 1
	local c, e, t = Sizes.Corner * s, Sizes.Edge * s, Sizes.Tile * s
	local holder = new("Frame", {
		Name = "Ornament",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 6,
		Parent = parent,
	})
	local function img(key, props)
		return new("ImageLabel", merge({
			Name = key,
			Image = Images[key],
			ImageColor3 = color,
			BackgroundTransparency = 1,
			ZIndex = 6,
			Parent = holder,
		}, props))
	end
	local tile = Enum.ScaleType.Tile
	img("EdgeT", { Position = UDim2.fromOffset(c, 0), Size = UDim2.new(1, -2 * c, 0, e), ScaleType = tile, TileSize = UDim2.fromOffset(t, e) })
	img("EdgeB", { AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, c, 1, 0), Size = UDim2.new(1, -2 * c, 0, e), ScaleType = tile, TileSize = UDim2.fromOffset(t, e) })
	img("EdgeL", { Position = UDim2.fromOffset(0, c), Size = UDim2.new(0, e, 1, -2 * c), ScaleType = tile, TileSize = UDim2.fromOffset(e, t) })
	img("EdgeR", { AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, c), Size = UDim2.new(0, e, 1, -2 * c), ScaleType = tile, TileSize = UDim2.fromOffset(e, t) })
	img("CornerTL", { Size = UDim2.fromOffset(c, c) })
	img("CornerTR", { AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), Size = UDim2.fromOffset(c, c) })
	img("CornerBL", { AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.fromOffset(c, c) })
	img("CornerBR", { AnchorPoint = Vector2.new(1, 1), Position = UDim2.fromScale(1, 1), Size = UDim2.fromOffset(c, c) })
	return holder
end

-- Small engraved plate (used by titles, counters, search bar)
local function plate(props, frameColor)
	local p = new("Frame", merge({
		Name = "Plate",
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		ZIndex = 9,
	}, props))
	slice("FrameThin", frameColor or Colors.Iron, { SliceScale = 0.4, ZIndex = 10, Parent = p })
	return p
end

local KEY_NAMES = {
	LeftShift = "Shift", RightShift = "Shift", LeftControl = "Ctrl", RightControl = "Ctrl",
	LeftAlt = "Alt", RightAlt = "Alt", Return = "Enter", Space = "Space", Backspace = "Bksp",
	Zero = "0", One = "1", Two = "2", Three = "3", Four = "4", Five = "5", Six = "6", Seven = "7", Eight = "8", Nine = "9",
	MouseButton1 = "LMB", MouseButton2 = "RMB", MouseButton3 = "MMB",
	DPadUp = "D-pad Up", DPadDown = "D-pad Down", DPadLeft = "D-pad Left", DPadRight = "D-pad Right",
}
-- controller buttons, by the pad in use (Components.PadStyle). PlayStation's touchpad press is Roblox's ButtonSelect.
local PAD_NAMES = {
	Xbox = {
		ButtonA = "A", ButtonB = "B", ButtonX = "X", ButtonY = "Y", ButtonL1 = "LB", ButtonR1 = "RB", ButtonL2 = "LT", ButtonR2 = "RT",
		ButtonL3 = "LS", ButtonR3 = "RS", ButtonSelect = "View", ButtonStart = "Menu",
	},
	PlayStation = {
		ButtonA = "Cross", ButtonB = "Circle", ButtonX = "Square", ButtonY = "Triangle", ButtonL1 = "L1", ButtonR1 = "R1",
		ButtonL2 = "L2", ButtonR2 = "R2", ButtonL3 = "L3", ButtonR3 = "R3", ButtonSelect = "Touchpad", ButtonStart = "Options",
	},
}
Components.PadNames = PAD_NAMES

-- "Xbox" or "PlayStation": the Settings choice (LocalPlayer attribute NHPadStyle, "Auto" by default), else the connected
-- pad (Roblox names ButtonA "ButtonCross" on a PlayStation pad). Studio: ReplicatedStorage NHPadStyleTest forces one.
function Components.PadStyle(): string
	if IS_STUDIO then
		local t = ReplicatedStorage:GetAttribute("NHPadStyleTest")
		if PAD_NAMES[t] then
			return t
		end
	end
	local lp = game:GetService("Players").LocalPlayer
	local pick = lp and lp:GetAttribute("NHPadStyle")
	if PAD_NAMES[pick] then
		return pick
	end
	local ok, s = pcall(function()
		return UserInputService:GetStringForKeyCode(Enum.KeyCode.ButtonA)
	end)
	return (ok and s == "ButtonCross") and "PlayStation" or "Xbox"
end

local function keyName(k)
	if k == nil then
		return "-"
	end
	local n = if typeof(k) == "string" then k else k.Name
	local pad = PAD_NAMES[Components.PadStyle()][n]
	return pad or KEY_NAMES[n] or n
end
Components.KeyName = keyName
-- "{A} to select" -> "A to select" / "Cross to select": {A} {B} {X} {Y} {L1} {R1} {L2} {R2} {L3} {R3} {Select} {Start}
function Components.PadText(s: string): string
	return (string.gsub(s, "{(%w+)}", function(n)
		return keyName("Button" .. n)
	end))
end

-- every controller button, for the quick menu's list and the Settings Controls tab (key code name, what it does)
Components.PadControls = {
	{ "ButtonR2", "Strike (hold)" }, { "ButtonR1", "Heavy" }, { "ButtonL2", "Block (hold)" }, { "ButtonL1", "Feint" },
	{ "ButtonB", "Dodge" }, { "ButtonA", "Jump" }, { "ButtonX", "Interact / draw" }, { "ButtonY", "Carry / drop" },
	{ "ButtonL3", "Run (toggle)" }, { "ButtonR3", "Crouch (tap); hold + strike: uppercut" }, { "DPadUp", "Grip / board" },
	{ "DPadDown", "Race action" }, { "DPadLeft", "Hotbar (with D-pad Right)" }, { "ButtonSelect", "Quick menu" },
}

--------------------------------------------------------------------------
-- Screen: the viewport and the input kind every scale rule reads
--------------------------------------------------------------------------
-- Studio previews: ReplicatedStorage NHPhonePreview (a Vector2) lays every kit screen out as if the viewport were
-- that size, and NHTouchTest treats the session as a touch-only screen (Studio/tests/phone_preview.luau).
function Components.Viewport(): Vector2
	if IS_STUDIO then
		local v = ReplicatedStorage:GetAttribute("NHPhonePreview")
		if typeof(v) == "Vector2" then
			return v
		end
	end
	local cam = workspace.CurrentCamera
	return cam and cam.ViewportSize or Vector2.new(1920, 1080)
end

-- a touch screen whose shorter side is under Theme.Scale.PhoneBelow (phones, not tablets)
function Components.Phone(): boolean
	local vp = Components.Viewport()
	return Components.TouchOnly() and math.min(vp.X, vp.Y) < (Theme.Scale.PhoneBelow or 600)
end

function Components.TouchOnly(): boolean
	if UserInputService.TouchEnabled and not UserInputService.KeyboardEnabled then
		return true
	end
	return IS_STUDIO and ReplicatedStorage:GetAttribute("NHTouchTest") == true
end

-- What the player is using right now: "Gamepad", "Touch" or "Keyboard" (the last input; a console with no keyboard is
-- "Gamepad" before any input). Studio: ReplicatedStorage NHGamepadTest forces "Gamepad". Hints read this and listen to
-- Components.InputKindChanged.
local kindChanged = Instance.new("BindableEvent")
Components.InputKindChanged = kindChanged.Event
function Components.InputKind(): string
	if IS_STUDIO and ReplicatedStorage:GetAttribute("NHGamepadTest") == true then
		return "Gamepad"
	end
	local t = UserInputService:GetLastInputType()
	if string.sub(t.Name, 1, 7) == "Gamepad" then
		return "Gamepad"
	elseif t == Enum.UserInputType.Touch then
		return "Touch"
	elseif t == Enum.UserInputType.Keyboard or string.sub(t.Name, 1, 5) == "Mouse" then
		return "Keyboard"
	end
	if Components.TouchOnly() then
		return "Touch"
	end
	if UserInputService.GamepadEnabled and not UserInputService.KeyboardEnabled then
		return "Gamepad"
	end
	return "Keyboard"
end
if RunService:IsClient() then
	local lastKind = nil
	local function check()
		local k = Components.InputKind()
		if k ~= lastKind then
			lastKind = k
			kindChanged:Fire(k)
		end
	end
	UserInputService.LastInputTypeChanged:Connect(check)
	if IS_STUDIO then
		ReplicatedStorage:GetAttributeChangedSignal("NHGamepadTest"):Connect(check)
	end
	-- a new pad, or the Settings choice of button names: hints listening for the input kind redraw too
	local lastStyle = Components.PadStyle()
	local function styleCheck()
		local s = Components.PadStyle()
		if s ~= lastStyle then
			lastStyle = s
			kindChanged:Fire(Components.InputKind())
		end
	end
	UserInputService.GamepadConnected:Connect(function() task.defer(styleCheck) end)
	if IS_STUDIO then
		ReplicatedStorage:GetAttributeChangedSignal("NHPadStyleTest"):Connect(styleCheck)
	end
	task.spawn(function()
		local lp = game:GetService("Players").LocalPlayer
		if lp then
			lp:GetAttributeChangedSignal("NHPadStyle"):Connect(styleCheck)
		end
	end)
end

-- fires when a preview size is set or cleared (Studio), so screens re-run their layout
Components.PreviewChanged = ReplicatedStorage:GetAttributeChangedSignal("NHPhonePreview")

--------------------------------------------------------------------------
-- AutoScale(screenGui) -> UIScale
--------------------------------------------------------------------------
-- Player UI-scale preference (Settings "UI Scale"), multiplied into every AutoScale.
Components.UserScale = 1
local scaleUpdaters = setmetatable({}, { __mode = "k" })
function Components.SetUserScale(m: number)
	Components.UserScale = math.clamp(m, 0.5, 2)
	for ui, update in pairs(scaleUpdaters) do
		if ui.Parent then
			update()
		end
	end
end

-- opts: min?, max?, touchMin?, curve?, multiplier?, design?, fitHeight? / fitWidth? (design px of the
-- largest panel in this gui: the scale is capped so it always fits), fitMargin? (default 24),
-- phoneScale? (phones only: this exact scale instead of the usual rules; Theme.Scale.PhoneTouchMin otherwise).
-- On phones, big panels (direct children sized in offset px, over 250 tall) are also clamped to the screen at that
-- scale, keeping their text size: their contents should be laid out relative to them (and scroll). The design size is
-- kept in the attribute NHPhoneDesign. A gui opts out with the attribute NHNoPanelClamp.
function Components.AutoScale(gui: Instance, opts)
	opts = opts or {}
	local ui = gui:FindFirstChild("NHAutoScale") or new("UIScale", { Name = "NHAutoScale", Parent = gui })
	local design = opts.design or Theme.Scale.Design
	local conns = {}
	local function update()
		local cam = workspace.CurrentCamera
		if not cam then
			return
		end
		local vp = Components.Viewport()
		local raw = math.min(vp.X / design.X, vp.Y / design.Y)
		-- gentler shrink on small screens (text stays readable), linear growth above 1x
		local s = raw < 1 and raw ^ (opts.curve or Theme.Scale.Curve or 1) or raw
		s = math.clamp(s, opts.min or Theme.Scale.Min, opts.max or Theme.Scale.Max)
		local phone = false
		if Components.TouchOnly() then
			phone = math.min(vp.X, vp.Y) < (Theme.Scale.PhoneBelow or 600)
			s = math.max(s, opts.touchMin or (phone and Theme.Scale.PhoneTouchMin) or Theme.Scale.TouchMin)
			if phone and opts.phoneScale then
				s = opts.phoneScale
			end
		end
		s = s * (opts.multiplier or 1) * Components.UserScale
		-- fit: a panel of this design size must stay inside the visible screen (phones, short windows)
		if opts.fitHeight then
			local inset = (gui:IsA("ScreenGui") and gui.IgnoreGuiInset) and 0 or 58
			s = math.min(s, (vp.Y - inset - (opts.fitMargin or 24)) / opts.fitHeight)
		end
		if opts.fitWidth then
			s = math.min(s, (vp.X - (opts.fitMargin or 24)) / opts.fitWidth)
		end
		ui.Scale = s
		Components.ClampPanels(gui, phone, s, vp)
	end
	scaleUpdaters[ui] = update
	local function hookCamera()
		for _, c in ipairs(conns) do
			c:Disconnect()
		end
		table.clear(conns)
		local cam = workspace.CurrentCamera
		if cam then
			table.insert(conns, cam:GetPropertyChangedSignal("ViewportSize"):Connect(update))
		end
		update()
	end
	-- (audit) disconnected when the gui goes: popups that build and destroy their own ScreenGui used to leave these
	-- running (and holding the dead gui) for the rest of the session
	local camConn = workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(hookCamera)
	gui.Destroying:Connect(function()
		camConn:Disconnect()
		for _, c in ipairs(conns) do c:Disconnect() end
		table.clear(conns)
		scaleUpdaters[ui] = nil
	end)
	if IS_STUDIO then
		Components.PreviewChanged:Connect(update)
	end
	-- panels are usually built after AutoScale is called: clamp them as they arrive
	gui.ChildAdded:Connect(function(child)
		if child:IsA("GuiObject") then
			task.defer(update)
		end
	end)
	hookCamera()
	return ui
end

-- Phones: keep big offset-sized panels inside the screen (see AutoScale). Off phones, give them their design size back.
function Components.ClampPanels(gui: Instance, phone: boolean, s: number, vp: Vector2)
	if gui:GetAttribute("NHNoPanelClamp") then
		return
	end
	local inset = (gui:IsA("ScreenGui") and gui.IgnoreGuiInset) and 0 or 58
	for _, p in gui:GetChildren() do
		if p:IsA("GuiObject") then
			local d = p:GetAttribute("NHPhoneDesign")
			if phone then
				local size = p.Size
				if not d and size.X.Scale == 0 and size.Y.Scale == 0 and size.Y.Offset > 250 then
					d = Vector2.new(size.X.Offset, size.Y.Offset)
					p:SetAttribute("NHPhoneDesign", d)
				end
				if d then
					local w = math.min(d.X, (vp.X - 16) / s)
					local h = math.min(d.Y, (vp.Y - inset - 12) / s)
					p.Size = UDim2.fromOffset(w, h)
				end
			elseif d then
				p.Size = UDim2.fromOffset(d.X, d.Y)
				p:SetAttribute("NHPhoneDesign", nil)
			end
		end
	end
end

-- Keep a panel inside the visible screen without shrinking its text: the panel keeps its design size
-- (attribute DesignSize, Vector2, default = its current offset size) but is clamped to the screen,
-- divided by the gui's NHAutoScale. Its contents should scroll. Used for tall panels on phones and
-- short windows. Change the design size later with panel:SetAttribute("DesignSize", v2).
function Components.FitToScreen(panel: GuiObject, margin: number?)
	margin = margin or 16
	if not panel:GetAttribute("DesignSize") then
		panel:SetAttribute("DesignSize", Vector2.new(panel.Size.X.Offset, panel.Size.Y.Offset))
	end
	local function update()
		local cam = workspace.CurrentCamera
		local gui = panel:FindFirstAncestorWhichIsA("ScreenGui")
		if not (cam and gui) then
			return
		end
		local scaler = gui:FindFirstChild("NHAutoScale")
		local s = scaler and scaler.Scale or 1
		local inset = gui.IgnoreGuiInset and 0 or 58
		local d = panel:GetAttribute("DesignSize")
		local vp = Components.Viewport()
		panel.Size = UDim2.fromOffset(math.min(d.X, (vp.X - margin * 2) / s), math.min(d.Y, (vp.Y - inset - margin * 2) / s))
	end
	local conns = {}
	local function hook()
		for _, cn in ipairs(conns) do
			cn:Disconnect()
		end
		table.clear(conns)
		local cam = workspace.CurrentCamera
		if cam then
			table.insert(conns, cam:GetPropertyChangedSignal("ViewportSize"):Connect(update))
		end
		local gui = panel:FindFirstAncestorWhichIsA("ScreenGui")
		local scaler = gui and gui:FindFirstChild("NHAutoScale")
		if scaler then
			table.insert(conns, scaler:GetPropertyChangedSignal("Scale"):Connect(update))
		end
		update()
	end
	panel:GetAttributeChangedSignal("DesignSize"):Connect(update)
	panel.AncestryChanged:Connect(function()
		task.defer(hook)
	end)
	local camConn = workspace:GetPropertyChangedSignal("CurrentCamera"):Connect(hook)
	panel.Destroying:Connect(function() -- (audit) same leak as AutoScale
		camConn:Disconnect()
		for _, cn in ipairs(conns) do cn:Disconnect() end
		table.clear(conns)
	end)
	hook()
	return update
end

--------------------------------------------------------------------------
-- Divider / SectionHeader
--------------------------------------------------------------------------
function Components.Divider(opts)
	opts = opts or {}
	local root = image("Divider", {
		Name = "Divider",
		ScaleType = Enum.ScaleType.Stretch,
		ImageColor3 = opts.color or Colors.IronDim,
		Size = UDim2.new(1, 0, 0, opts.height or 16),
	})
	place(root, opts)
	return root, { Root = root }
end

function Components.SectionHeader(opts)
	opts = opts or {}
	local root = new("Frame", { Name = "Section", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, opts.height or 34) })
	local lbl = emboss(text({
		Name = "Label",
		Text = string.upper(opts.text or "Section"),
		Font = Fonts.Title,
		TextSize = opts.textSize or Sizes.TextSmall + 2,
		TextColor3 = opts.color or Colors.Gold,
		TextXAlignment = CENTER,
		Size = UDim2.new(1, 0, 1, -10),
		Parent = root,
	}), Color3.fromRGB(150, 118, 70), 1.3)
	image("Divider", {
		ScaleType = Enum.ScaleType.Stretch,
		ImageColor3 = opts.lineColor or Colors.IronDim,
		AnchorPoint = Vector2.new(0.5, 1),
		Position = UDim2.fromScale(0.5, 1),
		Size = UDim2.new(1, 0, 0, 14),
		Parent = root,
	})
	place(root, opts)
	return root, { Root = root, Label = lbl }
end

--------------------------------------------------------------------------
-- Decorate / Panel
--------------------------------------------------------------------------
--[[ Decorate(target, opts) dresses an EXISTING frame as a kit panel without touching its
	 layout or size (works with AutomaticSize and scale sizes). The art goes in a ZIndex-0
	 child "NHDecor"; an optional title plaque sits on the top edge. The target's own content
	 stays in its other children and draws above the decoration.
	 Note: a UIListLayout / UIGridLayout / UIPadding directly in `target` would also move
	 NHDecor - put content in an inner frame in that case.
	 opts: title?, accent? ("Vigil"|"Court"), frameColor?, bgColor?, titleColor?, titleSize?,
	       ornament? ("ornate" | "thin" | "slot" | "none"), ornamentScale?, shadow?,
	       titleFlourishWidth?, bgTransparency? ]]
-- Scale-sized art inside an AutomaticSize frame measures against the frame's PARENT
-- (often the whole screen) and blows the frame up. For auto-sized targets, size the art
-- layer in offsets to the bounds of the target's other (content) children instead.
local TRACK_SKIP = { NHDecor = true, Title = true, TitleFlourish = true }
local function trackContent(target, layer)
	local ax = target.AutomaticSize
	-- Hidden: still reports AbsoluteSize (for the UIScale factor) but adds nothing to auto-size.
	local probe = new("Frame", { Name = "NHProbe", BackgroundTransparency = 1, Visible = false, Size = UDim2.fromOffset(100, 100), Parent = layer })
	local pending = false
	local function refit()
		pending = false
		if not layer.Parent then
			return
		end
		local f = probe.AbsoluteSize.X / 100
		if f <= 0 then
			return
		end
		local tp = target.AbsolutePosition
		local maxX, maxY = 0, 0
		for _, ch in ipairs(target:GetChildren()) do
			if ch:IsA("GuiObject") and ch.Visible and not TRACK_SKIP[ch.Name] then
				maxX = math.max(maxX, ch.AbsolutePosition.X + ch.AbsoluteSize.X - tp.X)
				maxY = math.max(maxY, ch.AbsolutePosition.Y + ch.AbsoluteSize.Y - tp.Y)
			end
		end
		local xs = (ax == Enum.AutomaticSize.Y) and UDim.new(1, 0) or UDim.new(0, maxX / f)
		local ys = (ax == Enum.AutomaticSize.X) and UDim.new(1, 0) or UDim.new(0, maxY / f)
		layer.Size = UDim2.new(xs, ys)
	end
	local function schedule()
		if not pending then
			pending = true
			task.defer(refit)
		end
	end
	local function hook(ch)
		if ch:IsA("GuiObject") and not TRACK_SKIP[ch.Name] then
			ch:GetPropertyChangedSignal("AbsoluteSize"):Connect(schedule)
			ch:GetPropertyChangedSignal("AbsolutePosition"):Connect(schedule)
			ch:GetPropertyChangedSignal("Visible"):Connect(schedule)
		end
	end
	for _, ch in ipairs(target:GetChildren()) do
		hook(ch)
	end
	target.ChildAdded:Connect(function(ch)
		hook(ch)
		schedule()
	end)
	target.ChildRemoved:Connect(schedule)
	target:GetPropertyChangedSignal("AbsolutePosition"):Connect(schedule)
	layer.Size = UDim2.new(ax == Enum.AutomaticSize.Y and UDim.new(1, 0) or UDim.new(0, 0), ax == Enum.AutomaticSize.X and UDim.new(1, 0) or UDim.new(0, 0))
	schedule()
end

function Components.Decorate(target: GuiObject, opts)
	opts = opts or {}
	local faction = Theme.Faction(opts.accent)
	local frameColor = opts.frameColor or (opts.accent and faction.Frame) or Colors.Iron
	local titleColor = opts.titleColor or (opts.accent and faction.Accent) or Colors.Text
	local s = opts.ornamentScale or 1
	local style = opts.ornament or "ornate"
	target.BackgroundTransparency = 1
	for _, d in ipairs(target:GetChildren()) do
		if d:IsA("UICorner") or d:IsA("UIStroke") then
			d:Destroy()
		end
	end
	local old = target:FindFirstChild("NHDecor")
	if old then
		old:Destroy()
	end
	local decor = new("Frame", { Name = "NHDecor", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 0, Parent = target })
	if target.AutomaticSize ~= Enum.AutomaticSize.None then
		trackContent(target, decor)
	end
	if opts.shadow ~= false then
		-- AutomaticSize counts descendants, so the shadow may not overhang an auto-sized edge.
		local ax = target.AutomaticSize
		local autoX = ax == Enum.AutomaticSize.X or ax == Enum.AutomaticSize.XY
		local autoY = ax == Enum.AutomaticSize.Y or ax == Enum.AutomaticSize.XY
		slice("Shadow", Colors.Shadow, {
			Name = "Shadow",
			ImageTransparency = 0.15,
			Position = UDim2.fromOffset(-26, -18),
			Size = UDim2.new(1, autoX and 26 or 52, 1, autoY and 18 or 50),
			SliceScale = 0.7,
			ZIndex = 0,
			Parent = decor,
		})
	end
	local bgInset = (style == "ornate") and math.floor(5 * s) or 2
	local bg = new("ImageLabel", {
		Name = "Background",
		Image = Images.PanelBg,
		ImageColor3 = opts.bgColor or Colors.PanelTint,
		ScaleType = Enum.ScaleType.Stretch,
		BackgroundColor3 = Colors.Base,
		BackgroundTransparency = opts.bgTransparency or 0,
		ImageTransparency = opts.bgTransparency or 0,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(bgInset, bgInset),
		Size = UDim2.new(1, -2 * bgInset, 1, -2 * bgInset),
		ZIndex = 1,
		Parent = decor,
	})
	local border
	if style == "ornate" then
		border = ornateBorder(decor, frameColor, s)
	elseif style == "thin" then
		border = slice("FrameThin", frameColor, { Name = "Ornament", SliceScale = 0.5 * s, Parent = decor })
	elseif style == "slot" then
		border = slice("FrameSlot", frameColor, { Name = "Ornament", SliceScale = 0.4 * s, Parent = decor })
	end
	local titleLabel
	if opts.title then
		local y = (style == "ornate") and math.floor(Sizes.Edge * s / 2) or 0
		image("Divider", {
			Name = "TitleFlourish",
			ScaleType = Enum.ScaleType.Stretch,
			ImageColor3 = frameColor,
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 0, y),
			Size = UDim2.fromOffset(opts.titleFlourishWidth or 300, 26),
			ZIndex = 8,
			Parent = target,
		})
		local p = plate({
			Name = "Title",
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 0, y),
			Size = UDim2.fromOffset(0, 32),
			AutomaticSize = Enum.AutomaticSize.X,
			Parent = target,
		}, frameColor)
		pad(22, 22, 0, 0).Parent = p
		titleLabel = emboss(text({
			Name = "Label",
			Text = opts.title,
			Font = Fonts.Title,
			TextSize = opts.titleSize or Sizes.TextSmall + 3,
			TextColor3 = titleColor,
			TextXAlignment = CENTER,
			AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 32),
			ZIndex = 11,
			Parent = p,
		}))
	end
	local api = { Root = target, Decor = decor, Background = bg, Border = border, TitleLabel = titleLabel }
	function api:SetTitle(t: string)
		if titleLabel then
			titleLabel.Text = t
		end
	end
	function api:SetFrameColor(c: Color3)
		if border then
			for _, d in ipairs(border:IsA("ImageLabel") and { border } or border:GetChildren()) do
				d.ImageColor3 = c
			end
		end
	end
	return decor, api
end

--[[ opts: title?, accent? ("Vigil"|"Court"), frameColor?, bgColor?,
	   ornament? ("ornate" default | "thin" | "slot" | "none"), ornamentScale?, inset?,
	   shadow? (default true), maxSize? Vector2 ]]
function Components.Panel(opts)
	opts = opts or {}
	local s = opts.ornamentScale or 1
	local style = opts.ornament or "ornate"
	local root = new("Frame", { Name = "Panel", BackgroundTransparency = 1, Size = UDim2.fromOffset(480, 360) })
	local _, deco = Components.Decorate(root, opts)
	local inset = opts.inset or ((style == "ornate") and math.floor(Sizes.ContentInset * s) or 14)
	local top = inset + (opts.title and 10 or 0)
	local content = new("Frame", {
		Name = "Content",
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(inset, top),
		Size = UDim2.new(1, -2 * inset, 1, -top - inset),
		ZIndex = 7,
		Parent = root,
	})
	if opts.maxSize then
		new("UISizeConstraint", { MaxSize = opts.maxSize, Parent = root })
	end
	place(root, opts)
	local api = { Root = root, Content = content, Border = deco.Border, TitleLabel = deco.TitleLabel, Decor = deco.Decor }
	function api:SetTitle(t: string)
		deco:SetTitle(t)
	end
	function api:SetFrameColor(c: Color3)
		deco:SetFrameColor(c)
	end
	return root, api
end

-- Engraved plate (title plaques, counters, search bar, HUD chips). Public form of plate().
function Components.Plate(opts)
	opts = opts or {}
	local root = plate({ Name = "Plate", Size = UDim2.fromOffset(160, 32) }, opts.frameColor)
	if opts.text then
		local lbl = text({
			Name = "Label",
			Text = opts.text,
			Font = opts.font or Fonts.Title,
			TextSize = opts.textSize or Sizes.TextSmall,
			TextColor3 = opts.color or Colors.Text,
			TextXAlignment = CENTER,
			ZIndex = 11,
			Parent = root,
		})
		if opts.autoWidth then
			root.AutomaticSize = Enum.AutomaticSize.X
			lbl.AutomaticSize = Enum.AutomaticSize.X
			lbl.Size = UDim2.new(0, 0, 1, 0)
			pad(18, 18, 0, 0).Parent = root
		end
	end
	place(root, opts)
	return root, { Root = root, Label = root:FindFirstChild("Label") }
end

-- Thin labelled progress bar (reputation, standing, EXP...).
-- opts: fraction (0..1), color?, caption?, height?
function Components.Bar(opts)
	opts = opts or {}
	local color = opts.color or Colors.Gold
	local root = new("Frame", { Name = "Bar", BackgroundColor3 = Colors.Ink, BorderSizePixel = 0, Size = UDim2.new(1, 0, 0, opts.height or 20) })
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, Position = UDim2.fromOffset(2, 2), ZIndex = 2, Parent = root })
	local grad = new("UIGradient", { Rotation = 90, Color = ColorSequence.new(lighten(color, 0.2), color:Lerp(Colors.Ink, 0.35)), Parent = fill })
	slice("FrameThin", Colors.IronDim, { SliceScale = 0.25, ZIndex = 4, Parent = root })
	local cap = text({ Name = "Caption", Text = opts.caption or "", Font = Fonts.Title, TextSize = Sizes.TextTiny, TextXAlignment = CENTER, TextStrokeTransparency = 0.2, ZIndex = 5, Parent = root })
	local api = { Root = root }
	function api:Set(f: number, caption: string?)
		fill.Size = UDim2.new(math.clamp(f, 0, 1), -4, 1, -4)
		if caption then
			cap.Text = caption
		end
		root:SetAttribute("Value", f)
	end
	function api:SetColor(c: Color3)
		grad.Color = ColorSequence.new(lighten(c, 0.2), c:Lerp(Colors.Ink, 0.35))
	end
	api:Set(opts.fraction or 0)
	place(root, opts)
	return root, api
end

-- Numbered reply / choice row (dialogue replies, menus).
-- opts: index?, text, color?, onClick(index), height?
function Components.ChoiceRow(opts)
	opts = opts or {}
	local root = new("TextButton", {
		Name = "Choice" .. tostring(opts.index or ""),
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Colors.Well,
		BackgroundTransparency = 0.08,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, opts.height or Sizes.RowHeight),
	})
	root:SetAttribute("BaseColor", Colors.Well)
	rowDepth(root)
	local fr = slice("FrameThin", Colors.RowFrame, { SliceScale = 0.3, Parent = root })
	fr:SetAttribute("BaseColor", Colors.RowFrame)
	local x = 14
	if opts.index then
		text({ Name = "Index", Text = tostring(opts.index) .. ".", Font = Fonts.Title, TextSize = Sizes.TextSmall, TextColor3 = Colors.Gold, Position = UDim2.fromOffset(14, 0), Size = UDim2.new(0, 24, 1, 0), Parent = root })
		x = 40
	end
	local lbl = text({
		Name = "Label",
		Text = opts.text or "...",
		TextSize = Sizes.TextBody - 1,
		TextColor3 = opts.color or Colors.Text,
		Position = UDim2.fromOffset(x, 0),
		Size = UDim2.new(1, -x - 12, 1, 0),
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = root,
	})
	wireFeedback(root, root, fr, Colors.RowFrame, Colors.Gold)
	root.Activated:Connect(function()
		if opts.onClick then
			opts.onClick(opts.index)
		end
	end)
	place(root, opts)
	return root, { Root = root, Label = lbl }
end

-- Notification toast. opts: title, text?, kind? ("Info"|"Good"|"Warning"|"Bad"), color?
Components.ToastColors = {
	Info = Color3.fromRGB(150, 180, 230),
	Good = Colors.Stamina,
	Warning = Colors.Gold,
	Bad = Colors.Crimson,
	Milestone = Color3.fromRGB(236, 196, 104), -- level-up, quest complete, faction join / rank, purchases
}

-- each toast kind's own icon (docs/Icon-Set.md); full-colour art, shown untinted
Components.ToastIcons = {
	Info = "IconNoteInfo",
	Good = "IconNoteGood",
	Warning = "IconNoteWarning",
	Bad = "IconNoteBad",
	Milestone = "IconNoteMilestone",
}

-- UI sounds (Pro Sound Effects, licensed for Roblox). Routed to the Effects volume (Settings).
Components.Sounds = {
	Tick = { Id = "rbxassetid://9120300134", Volume = 0.35 }, -- typewriter key: a prompt hold begins
	Confirm = { Id = "rbxassetid://9114058995", Volume = 0.22, Length = 0.7 }, -- desk bell, first ring only
	Reject = { Id = "rbxassetid://9112997947", Volume = 0.45, Length = 0.6 }, -- knob jiggle: "not now"
	Stamp = { Id = "rbxassetid://9119907907", Volume = 0.5, Length = 0.5 }, -- palm on wood: a seal stamps in
	Boom = { Id = "rbxassetid://2885026620", Volume = 0.3, Length = 1.4 }, -- a lab mixture going off
}
function Components.PlaySound(name: string, volumeScale: number?, speed: number?)
	local def = Components.Sounds[name]
	if not def or not game:GetService("RunService"):IsClient() then
		return nil
	end
	local SoundService = game:GetService("SoundService")
	local snd = Instance.new("Sound")
	snd.Name = "NHUi" .. name
	snd.SoundId = def.Id
	snd.Volume = def.Volume * (volumeScale or 1)
	snd.PlaybackSpeed = speed or 1
	local master = SoundService:FindFirstChild("NH_Master")
	local fx = master and master:FindFirstChild("NH_Effects")
	if fx and fx:IsA("SoundGroup") then
		snd.SoundGroup = fx
	end
	snd.Parent = SoundService
	snd:Play()
	local life = (def.Length or 2) / (speed or 1)
	task.delay(life, function()
		if snd.Parent then
			tween(snd, TweenInfo.new(0.15), { Volume = 0 })
			task.delay(0.16, function() snd:Destroy() end)
		end
	end)
	return snd
end

-- Settings > Reduce Motion (player attribute NHReducedMotion): stamps and pops become plain fades.
function Components.ReducedMotion(): boolean
	local lp = game:GetService("Players").LocalPlayer
	return lp ~= nil and lp:GetAttribute("NHReducedMotion") == true
end

-- Settings > Reduce Flashing (player attribute NHReducedFlash): full-screen flashes stay at or below 0.25 alpha.
function Components.ReducedFlash(): boolean
	local lp = game:GetService("Players").LocalPlayer
	return lp ~= nil and lp:GetAttribute("NHReducedFlash") == true
end

-- Fade a subtree in from invisible to how it was built (the opposite of FadeOut).
function Components.FadeIn(root: GuiObject, duration: number?)
	local info = TweenInfo.new(duration or 0.22, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	local function go(d)
		if d:GetAttribute("NHBaseT") then -- faded out before: return to how it was built
			if d:IsA("TextLabel") or d:IsA("TextButton") then
				tween(d, info, { TextTransparency = d:GetAttribute("NHBaseText"), TextStrokeTransparency = d:GetAttribute("NHBaseStroke") })
			elseif d:IsA("ImageLabel") then
				tween(d, info, { ImageTransparency = d:GetAttribute("NHBaseImage") })
			elseif d:IsA("UIStroke") then
				tween(d, info, { Transparency = d:GetAttribute("NHBaseUIStroke") })
			end
			if d:IsA("GuiObject") then
				tween(d, info, { BackgroundTransparency = d:GetAttribute("NHBaseBg") })
			end
			return
		end
		if d:IsA("TextLabel") or d:IsA("TextButton") then
			local t, st = d.TextTransparency, d.TextStrokeTransparency
			d.TextTransparency, d.TextStrokeTransparency = 1, 1
			tween(d, info, { TextTransparency = t, TextStrokeTransparency = st })
		elseif d:IsA("ImageLabel") then
			local t = d.ImageTransparency
			d.ImageTransparency = 1
			tween(d, info, { ImageTransparency = t })
		elseif d:IsA("UIStroke") then
			local t = d.Transparency
			d.Transparency = 1
			tween(d, info, { Transparency = t })
		end
		if d:IsA("GuiObject") and d.BackgroundTransparency < 1 then
			local t = d.BackgroundTransparency
			d.BackgroundTransparency = 1
			tween(d, info, { BackgroundTransparency = t })
		end
	end
	go(root)
	for _, d in ipairs(root:GetDescendants()) do
		go(d)
	end
end
function Components.Toast(opts)
	opts = opts or {}
	local accent = opts.color or Components.ToastColors[opts.kind or "Info"] or Components.ToastColors.Info
	local root = new("Frame", {
		Name = "Toast",
		BackgroundColor3 = Colors.Well,
		BackgroundTransparency = 0.05,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, opts.text and 54 or 36),
	})
	rowDepth(root)
	slice("FrameThin", accent:Lerp(Colors.RowFrame, 0.45), { SliceScale = 0.32, Parent = root })
	local milestone = opts.kind == "Milestone" or opts.milestone == true
	local iconKey = opts.icon or Components.ToastIcons[milestone and "Milestone" or (opts.kind or "Info")] or Components.ToastIcons.Info
	local seal = image(iconKey, {
		Name = "Seal", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0, 21, 0.5, 0),
		Size = UDim2.fromOffset(milestone and 28 or 22, milestone and 28 or 22),
		ImageColor3 = if Theme.Baked and Theme.Baked[iconKey] then Color3.new(1, 1, 1) else accent, Parent = root,
	})
	if milestone then
		root.BackgroundColor3 = Colors.Well:Lerp(accent, 0.08)
	end
	emboss(text({
		Name = "Title",
		Text = opts.title or "",
		Font = Fonts.Title,
		TextSize = Sizes.TextBody - 1,
		Position = UDim2.fromOffset(42, opts.text and 6 or 0),
		Size = UDim2.new(1, -52, 0, opts.text and 22 or 36),
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = root,
	}), Color3.fromRGB(160, 150, 140), 1.2)
	if opts.text then
		-- The body wraps (story beats, endings and insights are long) and the toast grows with it, up to
		-- opts.maxLines (default 4) lines, then truncates. A one-line body keeps the classic 54 px toast.
		local body = text({
			Name = "Body",
			Text = opts.text,
			TextSize = Sizes.TextSmall,
			TextColor3 = accent:Lerp(Colors.Text, 0.35),
			Position = UDim2.fromOffset(42, 28),
			Size = UDim2.new(1, -52, 0, 0),
			AutomaticSize = Enum.AutomaticSize.Y, -- (TextTruncate would stop it growing, so it's off until the cap)
			TextWrapped = true,
			TextYAlignment = Enum.TextYAlignment.Top,
			Parent = root,
		})
		local capH = math.ceil(Sizes.TextSmall * 1.25) * (opts.maxLines or 4)
		local capped = false
		local function fit()
			-- AbsoluteSize is screen px (after the screen's NHAutoScale); the toast's Size is design px
			local scale = 1
			local sg = root:FindFirstAncestorWhichIsA("LayerCollector")
			local us = sg and sg:FindFirstChild("NHAutoScale")
			if us and us:IsA("UIScale") and us.Scale > 0 then
				scale = us.Scale
			end
			local h = body.AbsoluteSize.Y / scale
			if h <= 0 then
				return
			end
			if not capped and h > capH then
				-- too long: fixed height, ending in "..."
				capped = true
				body.AutomaticSize = Enum.AutomaticSize.None
				body.Size = UDim2.new(1, -52, 0, capH)
				body.TextTruncate = Enum.TextTruncate.AtEnd
				h = capH
			end
			root.Size = UDim2.new(root.Size.X.Scale, root.Size.X.Offset, 0, math.max(54, math.ceil(28 + math.min(h, capH) + 8)))
		end
		body:GetPropertyChangedSignal("AbsoluteSize"):Connect(fit)
		task.defer(fit)
	end
	place(root, opts)
	local api = { Root = root, Milestone = milestone }
	-- The entrance, once the toast is on screen: fades in and settles from 94% (Back).
	-- Milestone: the seal stamps in (1.6x -> 1x, with a stamp sound) and one gold shimmer runs across
	-- the title. Reduce Motion: a plain fade.
	function api:Play()
		local calm = Components.ReducedMotion()
		Components.FadeIn(root, 0.22)
		if not calm then
			local sc = Instance.new("UIScale")
			sc.Scale = 0.94
			sc.Parent = root
			tween(sc, TweenInfo.new(0.28, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
		end
		if not milestone then
			return
		end
		Components.PlaySound("Stamp")
		if calm then
			return
		end
		local ss = Instance.new("UIScale")
		ss.Scale = 1.6
		ss.Parent = seal
		tween(ss, TweenInfo.new(0.18, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Scale = 1 })
		local title = root:FindFirstChild("Title")
		if title then
			local g = Instance.new("UIGradient")
			g.Color = ColorSequence.new({
				ColorSequenceKeypoint.new(0, Color3.new(1, 1, 1)),
				ColorSequenceKeypoint.new(0.42, Color3.new(1, 1, 1)),
				ColorSequenceKeypoint.new(0.5, Color3.fromRGB(255, 226, 150)),
				ColorSequenceKeypoint.new(0.58, Color3.new(1, 1, 1)),
				ColorSequenceKeypoint.new(1, Color3.new(1, 1, 1)),
			})
			g.Rotation = 12
			g.Offset = Vector2.new(-1, 0)
			g.Parent = title
			task.delay(0.15, function()
				local tw = tween(g, TweenInfo.new(0.7, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Offset = Vector2.new(1, 0) })
				tw.Completed:Connect(function() g:Destroy() end)
			end)
		end
	end
	return root, api
end

-- Fade every visual in a subtree (toasts, popups). Returns the tween of the root.
local function rememberBase(d)
	if d:GetAttribute("NHBaseT") ~= nil then
		return
	end
	if d:IsA("TextLabel") or d:IsA("TextButton") then
		d:SetAttribute("NHBaseText", d.TextTransparency)
		d:SetAttribute("NHBaseStroke", d.TextStrokeTransparency)
	elseif d:IsA("ImageLabel") then
		d:SetAttribute("NHBaseImage", d.ImageTransparency)
	elseif d:IsA("UIStroke") then
		d:SetAttribute("NHBaseUIStroke", d.Transparency)
	end
	if d:IsA("GuiObject") then
		d:SetAttribute("NHBaseBg", d.BackgroundTransparency)
	end
	d:SetAttribute("NHBaseT", true)
end
Components._rememberBase = rememberBase

function Components.FadeOut(root: GuiObject, duration: number?)
	local info = TweenInfo.new(duration or 0.3)
	local last
	rememberBase(root)
	for _, d in ipairs(root:GetDescendants()) do
		rememberBase(d)
		if d:IsA("TextLabel") or d:IsA("TextButton") then
			tween(d, info, { TextTransparency = 1, TextStrokeTransparency = 1 })
		elseif d:IsA("ImageLabel") then
			tween(d, info, { ImageTransparency = 1, BackgroundTransparency = 1 })
		elseif d:IsA("Frame") then
			tween(d, info, { BackgroundTransparency = 1 })
		elseif d:IsA("UIStroke") then
			tween(d, info, { Transparency = 1 })
		end
	end
	last = tween(root, info, { BackgroundTransparency = 1 })
	return last
end

--------------------------------------------------------------------------
-- Button
--------------------------------------------------------------------------
--[[ opts: text, onClick(), style? ("default"|"gold"|"crimson"|"ghost"),
	   icon? (Theme.Images key or asset id), textSize?, enabled? ]]
function Components.Button(opts)
	opts = opts or {}
	local style = opts.style or "default"
	local frameColor = (style == "gold" and Colors.Gold) or (style == "crimson" and Colors.Crimson) or Colors.IronDim
	local textColor = (style == "gold" and Colors.Gold) or (style == "crimson" and lighten(Colors.Crimson, 0.25)) or Colors.Text
	local root = new("TextButton", {
		Name = "Button",
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Colors.Well,
		BackgroundTransparency = style == "ghost" and 1 or 0,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(200, Sizes.RowHeight),
		Selectable = true,
	})
	root:SetAttribute("BaseColor", Colors.Well)
	local frame = slice("FrameThin", frameColor, { SliceScale = 0.4, Parent = root })
	frame:SetAttribute("BaseColor", frameColor)
	local lbl = text({
		Name = "Label",
		Text = opts.text or "Button",
		TextXAlignment = CENTER,
		TextSize = opts.textSize or Sizes.TextBody,
		TextColor3 = textColor,
		Font = Fonts.Title,
		Parent = root,
	})
	if opts.icon then
		image(opts.icon, {
			Name = "Icon",
			AnchorPoint = Vector2.new(0, 0.5),
			Position = UDim2.new(0, 12, 0.5, 0),
			Size = UDim2.fromOffset(22, 22),
			ImageColor3 = textColor,
			Parent = root,
		})
		lbl.Position = UDim2.fromOffset(18, 0)
		lbl.Size = UDim2.new(1, -18, 1, 0)
	end
	wireFeedback(root, root, frame, frameColor)
	local api = { Root = root, Label = lbl }
	function api:SetText(t)
		lbl.Text = t
	end
	function api:SetEnabled(on: boolean)
		root:SetAttribute("Disabled", not on)
		root.Active = on
		lbl.TextTransparency = on and 0 or 0.55
		frame.ImageTransparency = on and 0 or 0.5
	end
	root.Activated:Connect(function()
		if root:GetAttribute("Disabled") then
			return
		end
		if opts.onClick then
			opts.onClick(api)
		end
	end)
	if opts.enabled == false then
		api:SetEnabled(false)
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- TabBar
--------------------------------------------------------------------------
-- opts: tabs {string}, selected? number, onChanged(index, name), textSize?
function Components.TabBar(opts)
	opts = opts or {}
	local tabs = opts.tabs or { "Tab" }
	local selected = opts.selected or 1
	local root = new("Frame", {
		Name = "TabBar",
		BackgroundTransparency = 1,
		Size = UDim2.new(1, 0, 0, Sizes.RowHeight),
	})
	new("Frame", {
		Name = "Rule",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		Size = UDim2.new(1, 0, 0, 1),
		BackgroundColor3 = Colors.IronDim,
		BackgroundTransparency = 0.4,
		BorderSizePixel = 0,
		Parent = root,
	})
	local list = new("Frame", { Name = "Tabs", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Parent = root })
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, SortOrder = Enum.SortOrder.LayoutOrder, Parent = list })
	local buttons, marks = {}, {}
	local api = { Root = root }
	local function render(anim)
		for i, b in ipairs(buttons) do
			local on = i == selected
			local goal = { TextColor3 = on and Colors.Gold or Colors.TextDim }
			if anim then
				tween(b, Theme.Tween.Fast, goal)
				tween(marks[i], Theme.Tween.Fast, { ImageTransparency = on and 0 or 1 })
			else
				b.TextColor3 = goal.TextColor3
				marks[i].ImageTransparency = on and 0 or 1
			end
		end
		root:SetAttribute("Value", tabs[selected])
		root:SetAttribute("Index", selected)
	end
	for i, name in ipairs(tabs) do
		local b = new("TextButton", {
			Name = name,
			AutoButtonColor = false,
			BackgroundTransparency = 1,
			Text = name,
			Font = Fonts.Body,
			TextSize = opts.textSize or Sizes.TextBody,
			TextColor3 = Colors.TextDim,
			TextStrokeTransparency = 0.7,
			Size = UDim2.new(1 / #tabs, 0, 1, 0),
			LayoutOrder = i,
			ZIndex = 3,
			Parent = list,
		})
		marks[i] = image("Divider", {
			Name = "Mark",
			ScaleType = Enum.ScaleType.Stretch,
			ImageColor3 = Colors.Gold,
			AnchorPoint = Vector2.new(0.5, 1),
			Position = UDim2.new(0.5, 0, 1, 6),
			Size = UDim2.new(1, 6, 0, 14),
			Parent = b,
		})
		b.MouseEnter:Connect(function()
			if i ~= selected then
				tween(b, Theme.Tween.Fast, { TextColor3 = Colors.Text })
			end
		end)
		b.MouseLeave:Connect(function()
			if i ~= selected then
				tween(b, Theme.Tween.Fast, { TextColor3 = Colors.TextDim })
			end
		end)
		b.Activated:Connect(function()
			api:Select(i)
		end)
		buttons[i] = b
	end
	function api:Select(i: number, silent: boolean?)
		if i < 1 or i > #tabs then
			return
		end
		local changed = i ~= selected
		selected = i
		render(true)
		if changed and not silent and opts.onChanged then
			opts.onChanged(i, tabs[i])
		end
	end
	function api:Get()
		return selected, tabs[selected]
	end
	api.Buttons = buttons
	render(false)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- row shell shared by Toggle / Slider / KeybindRow
--------------------------------------------------------------------------
local function rowShell(className, opts, labelWidth)
	local root = new(className, {
		Name = opts.Name or "Row",
		BackgroundColor3 = Colors.Well,
		BackgroundTransparency = 0.1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, Sizes.RowHeight),
	})
	if root:IsA("GuiButton") then
		root.AutoButtonColor = false
		;(root :: any).Text = ""
	end
	root:SetAttribute("BaseColor", Colors.Well)
	rowDepth(root)
	local frame = slice("FrameThin", Colors.RowFrame, { SliceScale = 0.32, Parent = root })
	frame:SetAttribute("BaseColor", Colors.RowFrame)
	local lbl = text({
		Name = "Label",
		Text = opts.label or "Setting",
		TextSize = opts.textSize or Sizes.TextBody - 1,
		Position = UDim2.fromOffset(12, 0),
		Size = labelWidth,
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = root,
	})
	return root, frame, lbl
end

--------------------------------------------------------------------------
-- Toggle
--------------------------------------------------------------------------
-- opts: label, value?, onChanged(bool), onText?, offText?
function Components.Toggle(opts)
	opts = opts or {}
	local value = opts.value == true
	local root, frame, lbl = rowShell("TextButton", opts, UDim2.new(1, -112, 1, 0))
	root.Name = opts.Name or "Toggle"
	local sw = new("Frame", {
		Name = "Switch",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -8, 0.5, 0),
		Size = UDim2.fromOffset(86, 28),
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = root,
	})
	local swFrame = slice("FrameThin", Colors.IronDim, { SliceScale = 0.28, ZIndex = 5, Parent = sw })
	local glow = new("Frame", {
		Name = "Glow",
		BackgroundColor3 = Colors.GoldDeep,
		BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 3,
		Parent = sw,
	})
	new("UIGradient", {
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(1, 0.35) }),
		Parent = glow,
	})
	local knob = image("Knob", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromOffset(20, 20), ZIndex = 6, Parent = sw })
	local state = text({ Name = "State", Font = Fonts.Title, TextSize = Sizes.TextSmall, TextXAlignment = CENTER, Size = UDim2.new(0, 56, 1, 0), ZIndex = 6, Parent = sw })
	local api = { Root = root }
	local function render(anim)
		local kp = value and UDim2.new(1, -14, 0.5, 0) or UDim2.new(0, 14, 0.5, 0)
		local kc = value and Colors.On or Colors.Off
		if anim then
			tween(knob, Theme.Tween.Fast, { Position = kp, ImageColor3 = kc })
			tween(glow, Theme.Tween.Fast, { BackgroundTransparency = value and 0 or 1 })
		else
			knob.Position, knob.ImageColor3 = kp, kc
			glow.BackgroundTransparency = value and 0 or 1
		end
		state.Text = value and (opts.onText or "On") or (opts.offText or "Off")
		state.Position = value and UDim2.fromOffset(4, 0) or UDim2.new(1, -60, 0, 0)
		state.TextColor3 = value and Colors.On or Colors.TextDim
		swFrame.ImageColor3 = value and Colors.GoldDeep or Colors.IronDim
		root:SetAttribute("Value", value)
	end
	function api:Set(v: boolean, silent: boolean?)
		v = v == true
		local changed = v ~= value
		value = v
		render(true)
		if changed and not silent and opts.onChanged then
			opts.onChanged(value)
		end
	end
	function api:Get()
		return value
	end
	root.Activated:Connect(function()
		api:Set(not value)
	end)
	wireFeedback(root, root, frame, Colors.RowFrame)
	render(false)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- Slider
--------------------------------------------------------------------------
-- opts: label, min?=0, max?=100, step?=1, value?, suffix?="%", format?(v)->string,
--       onChanged(v), onReleased(v), color?, labelWidth? (0..1, default 0.4)
function Components.Slider(opts)
	opts = opts or {}
	local min, max, step = opts.min or 0, opts.max or 100, opts.step or 1
	local value = math.clamp(opts.value or min, min, max)
	local lw = opts.labelWidth or 0.4
	local root, _, lbl = rowShell("Frame", opts, UDim2.new(lw, -12, 1, 0))
	root.Name = opts.Name or "Slider"
	local accent = opts.color or Colors.Gold
	local hit = new("TextButton", {
		Name = "Hit",
		Text = "",
		AutoButtonColor = false,
		BackgroundTransparency = 1,
		Position = UDim2.new(lw, 0, 0, 0),
		Size = UDim2.new(1 - lw, -58, 1, 0),
		ZIndex = 4,
		Parent = root,
	})
	local track = new("Frame", {
		Name = "Track",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 10, 0.5, 0),
		Size = UDim2.new(1, -20, 0, 4),
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = hit,
	})
	new("UIStroke", { Color = Colors.IronDim, Thickness = 1, Transparency = 0.25, Parent = track })
	for i = 0, 4 do
		new("Frame", {
			Name = "Tick",
			AnchorPoint = Vector2.new(0.5, 0),
			Position = UDim2.new(i / 4, 0, 1, 4),
			Size = UDim2.fromOffset(1, i % 2 == 0 and 5 or 3),
			BackgroundColor3 = Colors.IronDim,
			BackgroundTransparency = 0.3,
			BorderSizePixel = 0,
			ZIndex = 3,
			Parent = track,
		})
	end
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0, ZIndex = 4, Parent = track })
	new("UIGradient", { Color = ColorSequence.new(accent:Lerp(Colors.Ink, 0.6), accent), Parent = fill })
	local knob = image("Knob", { Name = "Knob", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromOffset(22, 22), ImageColor3 = Colors.Text, ZIndex = 6, Parent = track })
	local valueLbl = text({
		Name = "Value",
		Font = Fonts.Title,
		TextSize = Sizes.TextSmall,
		TextXAlignment = RIGHT,
		TextColor3 = Colors.Text,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -12, 0, 0),
		Size = UDim2.new(0, 48, 1, 0),
		Parent = root,
	})
	local api = { Root = root }
	local function fmt(v)
		if opts.format then
			return opts.format(v)
		end
		local num = (step < 1) and string.format("%.1f", v) or tostring(math.floor(v + 0.5))
		return num .. (opts.suffix or "%")
	end
	local function render()
		local a = (max > min) and (value - min) / (max - min) or 0
		fill.Size = UDim2.fromScale(a, 1)
		knob.Position = UDim2.fromScale(a, 0.5)
		valueLbl.Text = fmt(value)
		root:SetAttribute("Value", value)
	end
	function api:Set(v: number, silent: boolean?)
		v = math.clamp(min + math.floor((v - min) / step + 0.5) * step, min, max)
		if v == value then
			return
		end
		value = v
		render()
		if not silent and opts.onChanged then
			opts.onChanged(value)
		end
	end
	function api:Get()
		return value
	end
	local moveConn, endConn
	local function stopDrag()
		local wasDragging = moveConn ~= nil or endConn ~= nil -- (audit) InputBegan calls this first; it isn't a release then
		if moveConn then
			moveConn:Disconnect()
			moveConn = nil
		end
		if endConn then
			endConn:Disconnect()
			endConn = nil
		end
		tween(knob, Theme.Tween.Fast, { Size = UDim2.fromOffset(22, 22), ImageColor3 = Colors.Text })
		if opts.onReleased and wasDragging then
			opts.onReleased(value)
		end
	end
	local function setFromX(x)
		local a = math.clamp((x - track.AbsolutePosition.X) / math.max(track.AbsoluteSize.X, 1), 0, 1)
		api:Set(min + a * (max - min))
	end
	-- gamepad: while the slider is selected, left / right (D-pad or left stick) step it, repeating while held; the
	-- selection stays on it sideways (up / down still move on). onReleased runs when you let go.
	hit.NextSelectionLeft = hit
	hit.NextSelectionRight = hit
	local padStep = step
	if (max - min) / step > 20 then
		padStep = math.max(step, math.floor((max - min) / 20 / step + 0.5) * step)
	end
	local padConns = {}
	local holdDir, holdToken = 0, 0
	local dpadDir, stickDir = 0, 0 -- (kept apart: a resting stick's small movements mustn't cancel a held D-pad)
	local function padHold(dir: number)
		if dir == holdDir then
			return
		end
		holdDir = dir
		holdToken += 1
		if dir == 0 then
			tween(knob, Theme.Tween.Fast, { Size = UDim2.fromOffset(22, 22), ImageColor3 = Colors.Text })
			if opts.onReleased then
				opts.onReleased(value)
			end
			return
		end
		local my = holdToken
		tween(knob, Theme.Tween.Fast, { Size = UDim2.fromOffset(26, 26), ImageColor3 = accent })
		api:Set(value + dir * padStep)
		task.spawn(function()
			task.wait(0.4)
			while holdToken == my and root.Parent do
				api:Set(value + dir * padStep)
				task.wait(0.09)
			end
		end)
	end
	local function padUpdate()
		padHold(if dpadDir ~= 0 then dpadDir else stickDir)
	end
	local function padOff()
		for _, c in padConns do
			c:Disconnect()
		end
		table.clear(padConns)
		dpadDir, stickDir = 0, 0
		padHold(0)
	end
	hit.SelectionGained:Connect(function()
		padOff()
		table.insert(padConns, UserInputService.InputBegan:Connect(function(i)
			if i.KeyCode == Enum.KeyCode.DPadLeft then
				dpadDir = -1
				padUpdate()
			elseif i.KeyCode == Enum.KeyCode.DPadRight then
				dpadDir = 1
				padUpdate()
			end
		end))
		table.insert(padConns, UserInputService.InputEnded:Connect(function(i)
			if (i.KeyCode == Enum.KeyCode.DPadLeft and dpadDir < 0) or (i.KeyCode == Enum.KeyCode.DPadRight and dpadDir > 0) then
				dpadDir = 0
				padUpdate()
			end
		end))
		table.insert(padConns, UserInputService.InputChanged:Connect(function(i)
			if i.KeyCode == Enum.KeyCode.Thumbstick1 then
				local x = i.Position.X
				stickDir = if x > 0.6 then 1 elseif x < -0.6 then -1 else 0
				padUpdate()
			end
		end))
	end)
	hit.SelectionLost:Connect(padOff)
	root.Destroying:Connect(padOff)
	hit.InputBegan:Connect(function(input)
		if not isPress(input) then
			return
		end
		stopDrag()
		setFromX(input.Position.X)
		tween(knob, Theme.Tween.Fast, { Size = UDim2.fromOffset(26, 26), ImageColor3 = accent })
		moveConn = UserInputService.InputChanged:Connect(function(i)
			if i.UserInputType == Enum.UserInputType.MouseMovement or i.UserInputType == Enum.UserInputType.Touch then
				setFromX(i.Position.X)
			end
		end)
		endConn = UserInputService.InputEnded:Connect(function(i)
			if isPress(i) then
				stopDrag()
			end
		end)
	end)
	root.Destroying:Connect(function()
		if moveConn then
			moveConn:Disconnect()
		end
		if endConn then
			endConn:Disconnect()
		end
	end)
	render()
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- KeybindRow
--------------------------------------------------------------------------
-- opts: label, key (Enum.KeyCode | Enum.UserInputType | string), onChanged(newKey)
function Components.KeybindRow(opts)
	opts = opts or {}
	local key = opts.key
	local root, frame, lbl = rowShell("Frame", opts, UDim2.new(1, -96, 1, 0))
	root.Name = opts.Name or "Keybind"
	local btn = new("TextButton", {
		Name = "Key",
		AutoButtonColor = false,
		Text = "",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -6, 0.5, 0),
		Size = UDim2.new(0, 78, 1, -8),
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = root,
	})
	btn:SetAttribute("BaseColor", Colors.Ink)
	local bFrame = slice("FrameThin", Colors.Iron, { SliceScale = 0.28, Parent = btn })
	bFrame:SetAttribute("BaseColor", Colors.Iron)
	local keyLbl = text({ Name = "KeyLabel", Font = Fonts.Title, TextSize = Sizes.TextSmall, TextXAlignment = CENTER, ZIndex = 7, Parent = btn })
	local api = { Root = root }
	local listening, conn = false, nil
	local function render()
		keyLbl.Text = keyName(key)
		keyLbl.TextColor3 = Colors.Text
		root:SetAttribute("Value", keyName(key))
	end
	local function stopListening()
		listening = false
		if conn then
			conn:Disconnect()
			conn = nil
		end
		bFrame.ImageColor3 = Colors.Iron
	end
	function api:Set(k, silent: boolean?)
		key = k
		render()
		if not silent and opts.onChanged then
			opts.onChanged(key)
		end
	end
	function api:Get()
		return key
	end
	btn.Activated:Connect(function()
		if listening then
			return
		end
		listening = true
		keyLbl.Text = "..."
		keyLbl.TextColor3 = Colors.Gold
		bFrame.ImageColor3 = Colors.Gold
		conn = UserInputService.InputBegan:Connect(function(input)
			local k
			-- controller buttons by key code name (Studio's simulated pad sends them as keyboard input): they cancel
			local code = input.KeyCode.Name
			local padButton = string.sub(code, 1, 6) == "Button" or string.sub(code, 1, 4) == "DPad"
			if padButton and not opts.allowGamepad then
				stopListening()
				render()
				return
			end
			if input.UserInputType == Enum.UserInputType.Keyboard or padButton then
				k = input.KeyCode
			elseif input.UserInputType == Enum.UserInputType.MouseButton2 or input.UserInputType == Enum.UserInputType.MouseButton3 then
				k = input.UserInputType
			end
			if not k then
				return
			end
			stopListening()
			if k == Enum.KeyCode.Escape then
				render()
			else
				api:Set(k)
			end
		end)
	end)
	root.Destroying:Connect(stopListening)
	wireFeedback(btn, btn, bFrame, Colors.Iron, Colors.Gold)
	render()
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- ItemSlot
--------------------------------------------------------------------------
-- opts: item? {name, count?, rarity?, icon?, id?}, size?, key? (hotkey text),
--       onClick(item, api), selected?
function Components.ItemSlot(opts)
	opts = opts or {}
	local size = opts.size or Sizes.Slot
	local root = new("TextButton", {
		Name = "ItemSlot",
		AutoButtonColor = false,
		Text = "",
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		Size = UDim2.fromOffset(size, size),
	})
	root:SetAttribute("BaseColor", Colors.Ink)
	local glowImg = image("Glow", {
		Name = "SelectGlow",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1.7, 1.7),
		ImageColor3 = Colors.Gold,
		ImageTransparency = 0.55,
		Visible = false,
		ZIndex = 0,
		Parent = root,
	})
	local inner = new("ImageLabel", {
		Name = "Inner",
		Image = Images.SlotBg,
		ImageColor3 = Color3.fromRGB(74, 66, 84),
		ScaleType = Enum.ScaleType.Stretch,
		BackgroundTransparency = 1,
		Position = UDim2.fromOffset(3, 3),
		Size = UDim2.new(1, -6, 1, -6),
		ZIndex = 1,
		Parent = root,
	})
	local tintGrad = new("Frame", {
		Name = "RarityGlow",
		BackgroundColor3 = Theme.Rarity.Common,
		BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1),
		ZIndex = 2,
		Parent = inner,
	})
	new("UIGradient", {
		Rotation = 90,
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.55, 0.97), NumberSequenceKeypoint.new(1, 0.72) }),
		Parent = tintGrad,
	})
	local frame = slice("FrameSlot", Colors.IronDim, { SliceScale = 0.4 * size / 78, Parent = root })
	frame:SetAttribute("BaseColor", Colors.IronDim)
	local icon = image("Icon", { Name = "Icon", Image = "", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.48), Size = UDim2.fromScale(0.56, 0.56), Parent = root })
	local nameLbl = text({
		Name = "ItemName",
		Font = Fonts.Title,
		TextSize = math.max(11, math.floor(size * 0.15)),
		TextXAlignment = CENTER,
		TextWrapped = true,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.new(1, -12, 0.6, 0),
		ZIndex = 4,
		Parent = root,
	})
	local badge = new("Frame", {
		Name = "Count",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0, 3),
		Size = UDim2.fromOffset(30, 19),
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		ZIndex = 8,
		Parent = root,
	}, { round(10) })
	new("UIStroke", { Color = Colors.IronDim, Thickness = 1, Parent = badge })
	local countLbl = text({ Name = "Label", Font = Fonts.Title, TextSize = 15, TextXAlignment = CENTER, ZIndex = 9, Parent = badge })
	local seal = image("Seal", {
		Name = "Rarity",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 1, -3),
		Size = UDim2.fromOffset(20, 20),
		ZIndex = 8,
		Parent = root,
	})
	local keyLbl
	if opts.key then
		keyLbl = text({
			Name = "Hotkey",
			Text = tostring(opts.key),
			Font = Fonts.Title,
			TextSize = 15,
			TextColor3 = Colors.TextDim,
			Position = UDim2.fromOffset(8, 5),
			Size = UDim2.fromOffset(16, 16),
			ZIndex = 8,
			Parent = root,
		})
	end

	local api = { Root = root, item = nil, selected = false }
	local function render()
		local it = api.item
		local has = it ~= nil
		local rc = has and (Theme.Rarity[it.rarity or "Common"] or Theme.Rarity.Common) or Colors.IronDim
		seal.Visible = has
		seal.ImageColor3 = rc
		tintGrad.BackgroundColor3 = rc
		tintGrad.Visible = has
		badge.Visible = has and it.count ~= nil
		countLbl.Text = has and it.count and string.format("%02d", it.count) or ""
		local ic = has and it.icon
		if ic and Images[ic] then
			ic = Images[ic]
		end
		icon.Image = ic or ""
		icon.Visible = ic ~= nil and ic ~= false
		nameLbl.Visible = has and not icon.Visible
		nameLbl.Text = has and string.upper(it.name or "") or ""
		glowImg.Visible = api.selected
		local fc = api.selected and Colors.Gold or (has and Colors.Iron or Colors.IronDim)
		frame.ImageColor3 = fc
		frame:SetAttribute("BaseColor", fc)
		if keyLbl then
			keyLbl.TextColor3 = api.selected and Colors.Gold or Colors.TextDim
		end
		root:SetAttribute("Value", has and (it.id or it.name) or "")
	end
	function api:SetItem(item)
		api.item = item
		render()
	end
	function api:SetCount(n: number?)
		if api.item then
			api.item.count = n
			render()
		end
	end
	function api:SetSelected(on: boolean)
		api.selected = on
		render()
	end
	function api:Clear()
		api:SetItem(nil)
	end
	root.Activated:Connect(function()
		if opts.onClick then
			opts.onClick(api.item, api)
		end
	end)
	wireFeedback(root, nil, frame, Colors.Iron, Colors.Gold)
	api.item = opts.item
	api.selected = opts.selected == true
	render()
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- ItemGrid
--------------------------------------------------------------------------
-- opts: items {item}, slotSize?, gap?, capacity?, used?, showEmpty? (number of
--       empty slots to pad to), onSelect(item, index), counterOffset? (px),
--       showCounter? (default true)
function Components.ItemGrid(opts)
	opts = opts or {}
	local slotSize = opts.slotSize or Sizes.Slot
	local gap = opts.gap or Sizes.SlotGap
	local root = new("Frame", { Name = "ItemGrid", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) })
	local scroller = new("ScrollingFrame", {
		Name = "Scroller",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 1, -(opts.showCounter == false and 0 or 18)),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollingDirection = Enum.ScrollingDirection.Y,
		ScrollBarThickness = 5,
		ScrollBarImageColor3 = Colors.IronDim,
		ZIndex = 3,
		Parent = root,
	})
	pad(4, 4, 14, 8).Parent = scroller
	new("UIGridLayout", {
		CellSize = UDim2.fromOffset(slotSize, slotSize),
		CellPadding = UDim2.fromOffset(gap, gap + 10),
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = scroller,
	})
	local counter, counterLbl
	if opts.showCounter ~= false then
		counter = plate({
			Name = "Capacity",
			AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.new(0.5, 0, 1, opts.counterOffset or 0),
			Size = UDim2.fromOffset(92, 26),
			Parent = root,
		})
		counterLbl = text({ Name = "Label", Font = Fonts.Title, TextSize = Sizes.TextSmall, TextXAlignment = CENTER, ZIndex = 11, Parent = counter })
	end
	local slots, apis = {}, {}
	local api = { Root = root, Scroller = scroller, Slots = apis }
	local used, capacity = opts.used, opts.capacity
	local selectedIndex = nil
	local function renderCounter()
		if counterLbl then
			local u = used or #(api.items or {})
			counterLbl.Text = capacity and (tostring(u) .. "/" .. tostring(capacity)) or tostring(u)
			counterLbl.TextColor3 = (capacity and u >= capacity) and Colors.Danger or Colors.Text
		end
	end
	function api:SetItems(items)
		api.items = items or {}
		for _, s in ipairs(slots) do
			s:Destroy()
		end
		table.clear(slots)
		table.clear(apis)
		local n = math.max(#api.items, opts.showEmpty or 0)
		for i = 1, n do
			local s, sa = Components.ItemSlot({
				item = api.items[i],
				size = slotSize,
				LayoutOrder = i,
				Name = "Slot" .. i,
				onClick = function(item)
					if item then
						api:Select(i)
					end
				end,
				Parent = scroller,
			})
			slots[i], apis[i] = s, sa
		end
		selectedIndex = nil
		renderCounter()
	end
	function api:Select(i: number?)
		if selectedIndex and apis[selectedIndex] then
			apis[selectedIndex]:SetSelected(false)
		end
		selectedIndex = i
		if i and apis[i] then
			apis[i]:SetSelected(true)
			if opts.onSelect then
				opts.onSelect(apis[i].item, i)
			end
		end
	end
	function api:Filter(query: string?)
		local q = string.lower(query or "")
		for i, sa in ipairs(apis) do
			local it = sa.item
			local show = q == "" or (it ~= nil and string.find(string.lower(it.name or ""), q, 1, true) ~= nil)
			slots[i].Visible = show
		end
	end
	function api:SetCapacity(u: number?, cap: number?)
		used, capacity = u, cap
		renderCounter()
	end
	api:SetItems(opts.items or {})
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- SearchBar
--------------------------------------------------------------------------
-- opts: placeholder?, text?, onChanged(text), onSubmit(text), grid? (ItemGrid api to filter)
function Components.SearchBar(opts)
	opts = opts or {}
	local root = plate({ Name = "SearchBar", Size = UDim2.fromOffset(300, 40), ZIndex = 9 })
	image("IconNib", {
		Name = "Icon",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 12, 0.5, 0),
		Size = UDim2.fromOffset(18, 18),
		ImageColor3 = Colors.TextDim,
		ZIndex = 11,
		Parent = root,
	})
	local box = new("TextBox", {
		Name = "Input",
		BackgroundTransparency = 1,
		ClearTextOnFocus = false,
		Font = Fonts.Body,
		TextSize = Sizes.TextBody - 1,
		TextColor3 = Colors.Text,
		PlaceholderText = opts.placeholder or "Search...",
		PlaceholderColor3 = Colors.TextFaint,
		Text = opts.text or "",
		TextXAlignment = LEFT,
		Position = UDim2.fromOffset(38, 0),
		Size = UDim2.new(1, -50, 1, 0),
		ZIndex = 11,
		Parent = root,
	})
	local api = { Root = root, TextBox = box }
	box:GetPropertyChangedSignal("Text"):Connect(function()
		root:SetAttribute("Value", box.Text)
		if opts.grid then
			opts.grid:Filter(box.Text)
		end
		if opts.onChanged then
			opts.onChanged(box.Text)
		end
	end)
	box.FocusLost:Connect(function(enter)
		if enter and opts.onSubmit then
			opts.onSubmit(box.Text)
		end
	end)
	function api:Get()
		return box.Text
	end
	function api:Set(t: string)
		box.Text = t
	end
	function api:Focus()
		box:CaptureFocus()
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- StatSheet
--------------------------------------------------------------------------
--[[ opts: title?, accent?, sections = { { header = "Student", rows = {
		{ "Label", "Value" [, color] },
		{ label = "EXP", value = "2,450 / 3,000", bar = 0.82, color = ... },
		{ label = "Demerits", pips = { filled = 2, total = 5, color = ... } },
	} }, ... }, rowHeight? ]]
function Components.StatSheet(opts)
	opts = opts or {}
	local root, panel = Components.Panel({
		Name = "StatSheet",
		title = opts.title or "Student Record",
		accent = opts.accent,
		Size = UDim2.fromOffset(320, 520),
		titleFlourishWidth = 250,
	})
	local scroller = new("ScrollingFrame", {
		Name = "Rows",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 1, -14), -- stop short of the bottom corner flourishes
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = Colors.IronDim,
		ZIndex = 3,
		Parent = panel.Content,
	})
	pad(6, 8, 2, 4).Parent = scroller
	new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 1), Parent = scroller })
	local rh = opts.rowHeight or 23
	local values = {}
	local order = 0
	local function nextOrder()
		order += 1
		return order
	end
	local api = { Root = root, Panel = panel, Values = values }
	for si, sec in ipairs(opts.sections or {}) do
		if sec.header then
			Components.SectionHeader({
				text = sec.header,
				height = si == 1 and 28 or 36,
				color = sec.color,
				LayoutOrder = nextOrder(),
				Parent = scroller,
			})
		end
		for _, r in ipairs(sec.rows or {}) do
			local labelText = r.label or r[1]
			local valueText = r.value or r[2] or ""
			local color = r.color or r[3] or Colors.Text
			local row = new("Frame", { Name = labelText, BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, rh), LayoutOrder = nextOrder(), Parent = scroller })
			text({ Name = "Label", Text = labelText, TextSize = Sizes.TextSmall, TextColor3 = Colors.TextDim, Size = UDim2.new(0.42, 0, 1, 0), Parent = row })
			local v = text({
				Name = "Value",
				Text = valueText,
				TextSize = Sizes.TextSmall + 1,
				TextColor3 = color,
				Position = UDim2.fromScale(0.42, 0),
				Size = UDim2.new(0.58, 0, 1, 0),
				TextTruncate = Enum.TextTruncate.AtEnd,
				ZIndex = 5,
				Parent = row,
			})
			if r.bar then
				local track = new("Frame", {
					Name = "Bar",
					AnchorPoint = Vector2.new(0, 1),
					Position = UDim2.new(0.42, 0, 1, -1),
					Size = UDim2.new(0.58, -4, 0, 3),
					BackgroundColor3 = Colors.Ink,
					BorderSizePixel = 0,
					ZIndex = 3,
					Parent = row,
				})
				new("Frame", { Name = "Fill", Size = UDim2.fromScale(math.clamp(r.bar, 0, 1), 1), BackgroundColor3 = r.barColor or Colors.Gold, BorderSizePixel = 0, ZIndex = 4, Parent = track })
			end
			if r.pips then
				v.Text = ""
				local holder = new("Frame", { Name = "Pips", BackgroundTransparency = 1, Position = UDim2.fromScale(0.42, 0), Size = UDim2.new(0.58, 0, 1, 0), ZIndex = 4, Parent = row })
				new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, Padding = UDim.new(0, 3), SortOrder = Enum.SortOrder.LayoutOrder, Parent = holder })
				for p = 1, r.pips.total or 5 do
					image("Pip", {
						Name = "Pip" .. p,
						Size = UDim2.fromOffset(14, 14),
						LayoutOrder = p,
						ImageColor3 = p <= (r.pips.filled or 0) and (r.pips.color or Colors.Crimson) or Colors.IronDim,
						ImageTransparency = p <= (r.pips.filled or 0) and 0 or 0.4,
						Parent = holder,
					})
				end
				if r.pips.caption then
					text({ Name = "Caption", Text = r.pips.caption, TextSize = Sizes.TextTiny, TextColor3 = Colors.TextDim, AutomaticSize = Enum.AutomaticSize.X, Size = UDim2.fromOffset(0, rh), LayoutOrder = 99, Parent = holder })
				end
			end
			values[labelText] = v
		end
	end
	function api:SetValue(label: string, value: string, color: Color3?)
		local v = values[label]
		if v then
			v.Text = value
			if color then
				v.TextColor3 = color
			end
		end
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- DangerAlert
--------------------------------------------------------------------------
-- opts: title?, subtitle?, seconds?, color?, icon? (Images key), onExpired()
function Components.DangerAlert(opts)
	opts = opts or {}
	local color = opts.color or Colors.Danger
	local root = new("Frame", { Name = "DangerAlert", BackgroundTransparency = 1, Size = UDim2.fromOffset(460, 178) })
	local glow = image("Glow", {
		Name = "Glow",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0, 50),
		Size = UDim2.fromOffset(230, 190),
		ImageColor3 = color,
		ImageTransparency = 0.45,
		ZIndex = 1,
		Parent = root,
	})
	local icon = image(opts.icon or "Bell", {
		Name = "Icon",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 0, 40),
		Size = UDim2.fromOffset(80, 80),
		ImageColor3 = Colors.Text,
		ZIndex = 3,
		Parent = root,
	})
	new("UIGradient", {
		Rotation = 90,
		Color = ColorSequence.new(Colors.Text, lighten(color, 0.1)),
		Parent = icon,
	})
	local title = emboss(text({
		Name = "Title",
		Text = opts.title or "CURFEW",
		Font = Fonts.Title,
		TextSize = Sizes.TextHuge,
		TextColor3 = lighten(color, 0.15),
		TextXAlignment = CENTER,
		Position = UDim2.fromOffset(0, 80),
		Size = UDim2.new(1, 0, 0, 40),
		ZIndex = 4,
		Parent = root,
	}), Color3.fromRGB(110, 40, 40), 2)
	local sub = text({
		Name = "Subtitle",
		Text = opts.subtitle or "",
		TextSize = Sizes.TextBody + 3,
		TextStrokeTransparency = 0.3,
		TextXAlignment = CENTER,
		Position = UDim2.fromOffset(0, 120),
		Size = UDim2.new(1, 0, 0, 22),
		ZIndex = 4,
		Parent = root,
	})
	local count = text({
		Name = "Countdown",
		Font = Fonts.Title,
		TextSize = Sizes.TextHeader + 6,
		TextColor3 = color,
		TextStrokeTransparency = 0.3,
		TextXAlignment = CENTER,
		Position = UDim2.fromOffset(0, 144),
		Size = UDim2.new(1, 0, 0, 26),
		ZIndex = 4,
		Parent = root,
	})
	local api = { Root = root }
	local token = 0
	local pulse
	local function setSeconds(s)
		count.Text = s and (tostring(math.max(0, math.ceil(s))) .. "s") or ""
		root:SetAttribute("Value", s or 0)
	end
	function api:SetText(t: string?, s: string?)
		if t then
			title.Text = t
		end
		if s then
			sub.Text = s
		end
	end
	function api:Start(seconds: number, onExpired)
		token += 1
		local my = token
		root.Visible = true
		setSeconds(seconds)
		if pulse then
			pulse:Cancel()
		end
		glow.ImageTransparency = 0.7
		pulse = TweenService:Create(glow, TweenInfo.new(0.8, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { ImageTransparency = 0.3 })
		pulse:Play()
		task.spawn(function()
			local t0 = os.clock()
			while token == my do
				local left = seconds - (os.clock() - t0)
				setSeconds(left)
				if left <= 0 then
					if pulse then
						pulse:Cancel()
					end
					local cb = onExpired or opts.onExpired
					if cb then
						cb()
					end
					break
				end
				task.wait(0.1)
			end
		end)
	end
	function api:Stop(hide: boolean?)
		token += 1
		if pulse then
			pulse:Cancel()
		end
		if hide then
			root.Visible = false
		end
	end
	setSeconds(opts.seconds)
	root.Destroying:Connect(function()
		token += 1
	end)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- PlayerListRow / PlayerList
--------------------------------------------------------------------------
-- opts: number?, name, faction? ("Vigil"|"Court"), race?, isLocal?, onClick(api)
function Components.PlayerListRow(opts)
	opts = opts or {}
	local interactive = opts.onClick ~= nil
	local root = new(interactive and "TextButton" or "Frame", {
		Name = "PlayerRow",
		BackgroundColor3 = Colors.Well,
		BackgroundTransparency = 0.15,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, interactive and Sizes.TapMin or 30),
	})
	if interactive then
		(root :: any).AutoButtonColor = false
		;(root :: any).Text = ""
	end
	local faction = Theme.Faction(opts.faction)
	local fc = opts.isLocal and Colors.Gold or (opts.faction and faction.Frame:Lerp(Colors.RowFrame, 0.5) or Colors.RowFrame)
	rowDepth(root)
	local frame = slice("FrameThin", fc, { SliceScale = 0.28, Parent = root })
	local num = text({
		Name = "Number",
		TextSize = Sizes.TextTiny,
		TextColor3 = Colors.TextFaint,
		Position = UDim2.fromOffset(10, 0),
		Size = UDim2.new(0, 70, 1, 0),
		Parent = root,
	})
	local icon = image(faction.Icon, {
		Name = "Faction",
		AnchorPoint = Vector2.new(0, 0.5),
		Position = UDim2.new(0, 72, 0.5, 0),
		Size = UDim2.fromOffset(16, 16),
		Parent = root,
	})
	local nameLbl = text({
		Name = "PlayerName",
		TextSize = Sizes.TextSmall,
		TextXAlignment = RIGHT,
		Font = Fonts.Body,
		AnchorPoint = Vector2.new(1, 0),
		Position = UDim2.new(1, -12, 0, 0),
		Size = UDim2.new(1, -110, 1, 0),
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = root,
	})
	local api = { Root = root }
	function api:Set(o)
		for k, v in pairs(o) do
			opts[k] = v
		end
		local f = Theme.Faction(opts.faction)
		num.Text = opts.number and string.format("No. %04d", opts.number) or ""
		nameLbl.Text = opts.name or "Student"
		nameLbl.TextColor3 = opts.isLocal and Colors.Gold or Colors.Text
		icon.Image = Images[f.Icon]
		icon.ImageColor3 = opts.faction and f.Accent or Colors.TextFaint
		root:SetAttribute("Value", opts.name)
	end
	if interactive then
		(root :: any).Activated:Connect(function()
			opts.onClick(api)
		end)
		wireFeedback(root, root, frame, fc)
	end
	api:Set({})
	place(root, opts)
	return root, api
end

-- opts: players { PlayerListRow opts }, title?, rowGap?
function Components.PlayerList(opts)
	opts = opts or {}
	local root = new("Frame", { Name = "PlayerList", BackgroundTransparency = 1, Size = UDim2.fromOffset(280, 0), AutomaticSize = Enum.AutomaticSize.Y })
	new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, opts.rowGap or 4), Parent = root })
	if opts.title then
		Components.SectionHeader({ text = opts.title, height = 30, LayoutOrder = 0, Parent = root })
	end
	local rows = {}
	local api = { Root = root, Rows = rows }
	function api:SetPlayers(list)
		for _, r in ipairs(rows) do
			r.Root:Destroy()
		end
		table.clear(rows)
		for i, p in ipairs(list or {}) do
			local o = merge(p, { LayoutOrder = i, Parent = root })
			local _, ra = Components.PlayerListRow(o)
			rows[i] = ra
		end
	end
	api:SetPlayers(opts.players)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- DialogueBox
--------------------------------------------------------------------------
--[[ opts: speaker, text, accent? ("Vigil"|"Court"), replies? { {text, onSelect} },
	   bodyHeight?, hint? (e.g. "[E] Continue"), typewriter? (chars/sec) ]]
function Components.DialogueBox(opts)
	opts = opts or {}
	local root = new("Frame", { Name = "DialogueBox", BackgroundTransparency = 1, Size = UDim2.fromOffset(620, 0), AutomaticSize = Enum.AutomaticSize.Y })
	new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 6), Parent = root })
	local body, panel = Components.Panel({
		Name = "Body",
		ornament = "ornate",
		ornamentScale = 0.8,
		inset = 30,
		accent = opts.accent,
		Size = UDim2.new(1, 0, 0, opts.bodyHeight or 150),
		LayoutOrder = 1,
		Parent = root,
	})
	local faction = Theme.Faction(opts.accent)
	local speaker = emboss(text({
		Name = "Speaker",
		Font = Fonts.Title,
		TextSize = Sizes.TextHeader,
		TextColor3 = opts.accent and faction.Accent or Colors.Gold,
		Position = UDim2.fromOffset(4, -6),
		Size = UDim2.new(1, -8, 0, 26),
		Parent = panel.Content,
	}), Color3.fromRGB(150, 110, 60), 1.4)
	local rule = new("Frame", {
		Name = "Rule",
		Position = UDim2.fromOffset(4, 24),
		Size = UDim2.new(0.45, 0, 0, 1),
		BackgroundColor3 = Colors.IronDim,
		BorderSizePixel = 0,
		Parent = panel.Content,
	})
	new("UIGradient", { Transparency = NumberSequence.new(0, 1), Parent = rule })
	local bodyText = text({
		Name = "Text",
		TextSize = Sizes.TextBody - 1,
		TextWrapped = true,
		TextYAlignment = Enum.TextYAlignment.Top,
		LineHeight = 1.05,
		Position = UDim2.fromOffset(4, 30),
		Size = UDim2.new(1, -8, 1, -34),
		Parent = panel.Content,
	})
	local hint = text({
		Name = "Hint",
		Text = opts.hint or "",
		Font = Fonts.Title,
		TextSize = Sizes.TextTiny,
		TextColor3 = Colors.TextDim,
		TextXAlignment = RIGHT,
		AnchorPoint = Vector2.new(1, 1),
		Position = UDim2.new(1, -2, 1, 2),
		Size = UDim2.fromOffset(160, 16),
		Parent = panel.Content,
	})
	local replyHolder = new("Frame", { Name = "Replies", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 2, Parent = root })
	new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 5), Parent = replyHolder })
	local api = { Root = root, Body = body, Replies = {} }
	local typeToken = 0
	function api:SetSpeaker(name: string)
		speaker.Text = name
	end
	function api:SetText(t: string, cps: number?)
		typeToken += 1
		local my = typeToken
		bodyText.Text = t
		cps = cps or opts.typewriter
		if cps and cps > 0 then
			bodyText.MaxVisibleGraphemes = 0
			task.spawn(function()
				local total = utf8.len(bodyText.ContentText) or #t
				local shown = 0
				while shown < total and typeToken == my do
					shown += math.max(1, math.floor(cps * task.wait()))
					bodyText.MaxVisibleGraphemes = shown
				end
				if typeToken == my then
					bodyText.MaxVisibleGraphemes = -1
				end
			end)
		else
			bodyText.MaxVisibleGraphemes = -1
		end
	end
	function api:SkipTypewriter()
		typeToken += 1
		bodyText.MaxVisibleGraphemes = -1
	end
	function api:SetHint(t: string)
		hint.Text = t or ""
	end
	function api:SetReplies(list)
		for _, r in ipairs(api.Replies) do
			r.Root:Destroy()
		end
		table.clear(api.Replies)
		for i, rep in ipairs(list or {}) do
			local b = Components.ChoiceRow({
				Name = "Reply" .. i,
				index = i,
				text = rep.text or rep[1] or "...",
				color = rep.color,
				LayoutOrder = i,
				onClick = function()
					local cb = rep.onSelect or rep[2] or opts.onReply
					if cb then
						cb(i, rep)
					end
				end,
				Parent = replyHolder,
			})
			b.Name = "Reply" .. i
			api.Replies[i] = { Root = b }
		end
	end
	api:SetSpeaker(opts.speaker or "")
	api:SetText(opts.text or "", nil)
	api:SetReplies(opts.replies)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- HealthBar
--------------------------------------------------------------------------
-- opts: value? (0..1), color?, orb? (default true), orbColor?, frameColor?, label?
-- Height drives everything (design 64px): arcade rails top/bottom, PBR end caps,
-- veined fill with a delayed "ghost" for recent damage, clock-face % orb.
function Components.HealthBar(opts)
	opts = opts or {}
	local value = math.clamp(opts.value or 1, 0, 1)
	local color = opts.color or Colors.Blood
	local frameColor = opts.frameColor or Colors.Iron
	local root = new("Frame", { Name = "HealthBar", BackgroundTransparency = 1, Size = UDim2.fromOffset(800, 64) })
	local track = new("Frame", {
		Name = "Track",
		BackgroundColor3 = Color3.fromRGB(10, 6, 9),
		BorderSizePixel = 0,
		ClipsDescendants = true,
		ZIndex = 2,
		Parent = root,
	})
	local ghost = new("Frame", { Name = "Ghost", BackgroundColor3 = lighten(color, 0.45), BackgroundTransparency = 0.25, BorderSizePixel = 0, ZIndex = 2, Parent = track })
	local fill = new("Frame", { Name = "Fill", BackgroundTransparency = 1, ClipsDescendants = true, ZIndex = 3, Parent = track })
	local tex = new("ImageLabel", {
		Name = "Texture",
		Image = Images.BarFill,
		ImageColor3 = color,
		BackgroundColor3 = color:Lerp(Colors.Ink, 0.55),
		BorderSizePixel = 0,
		ScaleType = Enum.ScaleType.Tile,
		ZIndex = 3,
		Parent = fill,
	})
	-- leading edge highlight on the fill
	local lip = new("Frame", { Name = "Lip", AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), Size = UDim2.new(0, 3, 1, 0), BackgroundColor3 = lighten(color, 0.55), BorderSizePixel = 0, ZIndex = 4, Parent = fill })
	new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 0.8) }), Parent = lip })
	local tile = Enum.ScaleType.Tile
	local railTop = new("ImageLabel", { Name = "RailTop", Image = Images.EdgeT, ImageColor3 = frameColor, BackgroundTransparency = 1, ScaleType = tile, ZIndex = 6, Parent = root })
	local railBot = new("ImageLabel", { Name = "RailBottom", Image = Images.EdgeB, ImageColor3 = frameColor, BackgroundTransparency = 1, ScaleType = tile, AnchorPoint = Vector2.new(0, 1), ZIndex = 6, Parent = root })
	local capL = image("BarCapL", { Name = "CapLeft", ScaleType = Enum.ScaleType.Stretch, ImageColor3 = frameColor, ZIndex = 7, Parent = root })
	local capR = image("BarCapR", { Name = "CapRight", ScaleType = Enum.ScaleType.Stretch, ImageColor3 = frameColor, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromScale(1, 0), ZIndex = 7, Parent = root })
	local orb, pct
	if opts.orb ~= false then
		orb = new("Frame", { Name = "Orb", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), ZIndex = 8, Parent = root })
		image("Glow", { Name = "Halo", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1.5, 1.5), ImageColor3 = Colors.Shadow, ImageTransparency = 0.2, ZIndex = 8, Parent = orb })
		image("OrbFill", { Name = "Glass", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(0.74, 0.74), ImageColor3 = opts.orbColor or Color3.fromRGB(96, 26, 40), ZIndex = 8, Parent = orb })
		image("OrbRing", { Name = "Ring", Size = UDim2.fromScale(1, 1), ImageColor3 = frameColor, ZIndex = 9, Parent = orb })
		pct = emboss(text({ Name = "Percent", Font = Fonts.Title, TextColor3 = Colors.Text, TextXAlignment = CENTER, ZIndex = 10, Parent = orb }), Color3.fromRGB(170, 150, 140), 1.6)
	end
	local lbl
	if opts.label then
		lbl = text({ Name = "Label", Text = opts.label, Font = Fonts.Title, TextSize = Sizes.TextTiny, TextColor3 = Colors.Text, TextStrokeTransparency = 0.3, ZIndex = 9, Parent = root })
	end
	local function layout()
		local H = root.Size.Y.Offset
		if H <= 0 then
			H = 64
		end
		local k = H / 64
		local e, t = 20 * k, 16 * k
		railTop.Position = UDim2.fromOffset(44 * k, 0)
		railTop.Size = UDim2.new(1, -88 * k, 0, e)
		railTop.TileSize = UDim2.fromOffset(t, e)
		railBot.Position = UDim2.new(0, 44 * k, 1, 0)
		railBot.Size = UDim2.new(1, -88 * k, 0, e)
		railBot.TileSize = UDim2.fromOffset(t, e)
		capL.Size = UDim2.fromOffset(64 * k, H)
		capR.Size = UDim2.fromOffset(64 * k, H)
		track.Position = UDim2.fromOffset(46 * k, 14 * k)
		track.Size = UDim2.new(1, -92 * k, 0, 36 * k)
		tex.TileSize = UDim2.fromOffset(192 * k, 36 * k)
		if orb then
			orb.Size = UDim2.fromOffset(H * 1.45, H * 1.45)
			pct.TextSize = math.floor(H * 0.33)
		end
		if lbl then
			lbl.Position = UDim2.fromOffset(56 * k, 14 * k)
			lbl.Size = UDim2.new(0.5, -56 * k - H, 0, 36 * k)
		end
	end
	local api = { Root = root }
	local function render(anim)
		fill.Size = UDim2.fromScale(value, 1)
		tex.Size = UDim2.new(1 / math.max(value, 0.001), 0, 1, 0)
		lip.Visible = value > 0.005 and value < 0.995
		if anim then
			tween(ghost, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out, 0, false, 0.25), { Size = UDim2.fromScale(value, 1) })
		else
			ghost.Size = UDim2.fromScale(value, 1)
		end
		if pct then
			pct.Text = tostring(math.floor(value * 100 + 0.5)) .. "%"
		end
		root:SetAttribute("Value", value)
	end
	function api:Set(v: number, instant: boolean?)
		value = math.clamp(v, 0, 1)
		render(not instant)
	end
	function api:Get()
		return value
	end
	function api:SetColor(c: Color3)
		tex.ImageColor3 = c
		tex.BackgroundColor3 = c:Lerp(Colors.Ink, 0.55)
		ghost.BackgroundColor3 = lighten(c, 0.45)
		lip.BackgroundColor3 = lighten(c, 0.55)
	end
	place(root, opts)
	layout()
	root:GetPropertyChangedSignal("Size"):Connect(layout)
	render(false)
	return root, api
end

--------------------------------------------------------------------------
-- Hotbar
--------------------------------------------------------------------------
-- opts: slots? (6), items? {item}, selected?, slotSize?, onSelect(index, item), bindKeys? (1-9 keys)
function Components.Hotbar(opts)
	opts = opts or {}
	local n = opts.slots or 6
	local size = opts.slotSize or 72
	local gap = opts.gap or 10
	local root = new("Frame", { Name = "Hotbar", BackgroundTransparency = 1, Size = UDim2.fromOffset(n * size + (n - 1) * gap, size + 12) })
	new("UIListLayout", {
		FillDirection = Enum.FillDirection.Horizontal,
		HorizontalAlignment = Enum.HorizontalAlignment.Center,
		VerticalAlignment = Enum.VerticalAlignment.Bottom,
		Padding = UDim.new(0, gap),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = root,
	})
	local apis = {}
	local selected = nil
	local api = { Root = root, Slots = apis }
	function api:Select(i: number?, silent: boolean?)
		if selected and apis[selected] then
			apis[selected]:SetSelected(false)
		end
		selected = i
		if i and apis[i] then
			apis[i]:SetSelected(true)
		end
		root:SetAttribute("Value", i or 0)
		if not silent and opts.onSelect then
			opts.onSelect(i, i and apis[i] and apis[i].item)
		end
	end
	function api:SetItem(i: number, item)
		if apis[i] then
			apis[i]:SetItem(item)
		end
	end
	function api:GetSelected()
		return selected, selected and apis[selected] and apis[selected].item
	end
	for i = 1, n do
		local _, sa = Components.ItemSlot({
			Name = "Slot" .. i,
			item = opts.items and opts.items[i],
			size = size,
			key = i <= 9 and i or nil,
			LayoutOrder = i,
			onClick = function()
				api:Select(selected == i and nil or i)
			end,
			Parent = root,
		})
		apis[i] = sa
	end
	if opts.selected then
		api:Select(opts.selected, true)
	end
	if opts.bindKeys then
		local digits = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Five, Enum.KeyCode.Six, Enum.KeyCode.Seven, Enum.KeyCode.Eight, Enum.KeyCode.Nine }
		local conn = UserInputService.InputBegan:Connect(function(input, gp)
			if gp then
				return
			end
			for i = 1, math.min(n, 9) do
				if input.KeyCode == digits[i] then
					api:Select(selected == i and nil or i)
				end
			end
		end)
		root.Destroying:Connect(function()
			conn:Disconnect()
		end)
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- VerticalMeter
--------------------------------------------------------------------------
-- opts: value? (0..1), color?, segments?, label? (short text under the meter)
function Components.VerticalMeter(opts)
	opts = opts or {}
	local value = math.clamp(opts.value or 1, 0, 1)
	local color = opts.color or Colors.Stamina
	local root = new("Frame", { Name = "VerticalMeter", BackgroundTransparency = 1, Size = UDim2.fromOffset(18, 260) })
	local body = new("Frame", {
		Name = "Body",
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 10),
		Size = UDim2.new(1, 0, 1, opts.label and -36 or -20),
		ZIndex = 2,
		Parent = root,
	})
	local fillHolder = new("Frame", { Name = "Inner", BackgroundTransparency = 1, Position = UDim2.fromOffset(4, 4), Size = UDim2.new(1, -8, 1, -8), ClipsDescendants = true, ZIndex = 3, Parent = body })
	local fill = new("Frame", {
		Name = "Fill",
		AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.fromScale(0, 1),
		BackgroundColor3 = Color3.new(1, 1, 1),
		BorderSizePixel = 0,
		ZIndex = 3,
		Parent = fillHolder,
	})
	local grad = new("UIGradient", { Rotation = 90, Color = ColorSequence.new(lighten(color, 0.25), color:Lerp(Colors.Ink, 0.45)), Parent = fill })
	local segs = opts.segments or 10
	for i = 1, segs - 1 do
		new("Frame", {
			Name = "Seg",
			Position = UDim2.new(0, 0, i / segs, 0),
			Size = UDim2.new(1, 0, 0, 2),
			BackgroundColor3 = Colors.Ink,
			BackgroundTransparency = 0.15,
			BorderSizePixel = 0,
			ZIndex = 4,
			Parent = fillHolder,
		})
	end
	slice("FrameThin", Colors.IronDim, { SliceScale = 0.22, ZIndex = 5, Parent = body })
	local capTop = image("Knob", { Name = "CapTop", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 0, 10), Size = UDim2.fromOffset(16, 16), ImageColor3 = color, ZIndex = 6, Parent = root })
	local capBot = image("Knob", {
		Name = "CapBottom",
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, 0, 1, opts.label and -26 or -10),
		Size = UDim2.fromOffset(16, 16),
		ImageColor3 = color,
		ZIndex = 6,
		Parent = root,
	})
	if opts.label then
		text({
			Name = "Label",
			Text = opts.label,
			Font = Fonts.Title,
			TextSize = Sizes.TextSmall + 1,
			TextColor3 = color,
			TextXAlignment = CENTER,
			AnchorPoint = Vector2.new(0.5, 1),
			Position = UDim2.fromScale(0.5, 1),
			Size = UDim2.fromOffset(110, 20),
			Parent = root,
		})
	end
	local api = { Root = root }
	function api:Set(v: number, instant: boolean?)
		value = math.clamp(v, 0, 1)
		if instant then
			fill.Size = UDim2.fromScale(1, value)
		else
			tween(fill, Theme.Tween.Med, { Size = UDim2.fromScale(1, value) })
		end
		root:SetAttribute("Value", value)
	end
	function api:Get()
		return value
	end
	function api:SetColor(c: Color3)
		grad.Color = ColorSequence.new(lighten(c, 0.25), c:Lerp(Colors.Ink, 0.45))
		capTop.ImageColor3, capBot.ImageColor3 = c, c
	end
	api:Set(value, true)
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- ServerRow
--------------------------------------------------------------------------
--[[ opts: name, players, maxPlayers, region?, period? (in-game time, e.g. "Period 3, 9:10 AM"),
	   ping? (ms), faction? ("Vigil"|"Court" controlling the campus), isCurrent? (you are here),
	   jobId?, onJoin(server, api) ]]
function Components.ServerRow(opts)
	opts = opts or {}
	local root = new("Frame", {
		Name = "ServerRow",
		BackgroundColor3 = Colors.Well,
		BorderSizePixel = 0,
		Size = UDim2.new(1, 0, 0, 74),
	})
	rowDepth(root)
	local frame = slice("FrameSlot", Colors.RowFrame, { SliceScale = 0.36, Parent = root })
	local nameLbl = emboss(text({
		Name = "ServerName",
		Font = Fonts.Title,
		TextSize = Sizes.TextHeader + 1,
		Position = UDim2.fromOffset(22, 9),
		Size = UDim2.new(0.42, -22, 0, 28),
		TextTruncate = Enum.TextTruncate.AtEnd,
		Parent = root,
	}), Color3.fromRGB(150, 140, 130), 1.4)
	local crest = image("IconNib", { Name = "Crest", AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 20, 0, 23), Size = UDim2.fromOffset(18, 18), Visible = false, Parent = root })
	local pop = text({ Name = "Players", TextSize = Sizes.TextSmall, TextColor3 = Colors.TextDim, Position = UDim2.fromOffset(22, 38), Size = UDim2.fromOffset(170, 18), Parent = root })
	local gauge = new("Frame", { Name = "Gauge", Position = UDim2.fromOffset(22, 58), Size = UDim2.fromOffset(150, 3), BackgroundColor3 = Colors.Ink, BorderSizePixel = 0, ZIndex = 3, Parent = root })
	local gfill = new("Frame", { Name = "Fill", BackgroundColor3 = Colors.Gold, BorderSizePixel = 0, ZIndex = 4, Parent = gauge })
	local period = text({ Name = "Period", TextSize = Sizes.TextSmall, TextColor3 = Colors.TextDim, TextXAlignment = RIGHT, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -420, 0, 0), Size = UDim2.new(0, 220, 1, 0), Parent = root })
	local region = text({ Name = "Region", TextSize = Sizes.TextSmall, TextXAlignment = RIGHT, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -230, 0, 0), Size = UDim2.new(0, 180, 1, 0), Parent = root })
	local ping = text({ Name = "Ping", Font = Fonts.Title, TextSize = Sizes.TextTiny, TextXAlignment = RIGHT, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -164, 0, 0), Size = UDim2.new(0, 56, 1, 0), Parent = root })
	local api = { Root = root, data = opts }
	local joining = false
	local _, joinApi = Components.Button({
		Name = "Join",
		text = "Join",
		textSize = Sizes.TextHeader,
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -18, 0.5, 0),
		Size = UDim2.fromOffset(128, Sizes.RowHeight),
		onClick = function()
			if opts.onJoin and not joining then
				opts.onJoin(opts, api)
			end
		end,
		Parent = root,
	})
	api.JoinButton = joinApi
	local function renderButton()
		local p, mx = opts.players or 0, opts.maxPlayers or 30
		if joining then
			joinApi:SetText("Joining...")
			joinApi:SetEnabled(false)
		elseif opts.isCurrent then
			joinApi:SetText("Here")
			joinApi:SetEnabled(false)
		elseif p >= mx then
			joinApi:SetText("Full")
			joinApi:SetEnabled(false)
		else
			joinApi:SetText("Join")
			joinApi:SetEnabled(true)
		end
	end
	function api:Set(o)
		for k, v in pairs(o or {}) do
			opts[k] = v
		end
		local p, mx = opts.players or 0, opts.maxPlayers or 30
		nameLbl.Text = opts.name or "Campus"
		pop.Text = string.format("Students %d / %d", p, mx) .. (opts.isCurrent and "  (you)" or "")
		gfill.Size = UDim2.fromScale(math.clamp(p / math.max(mx, 1), 0, 1), 1)
		gfill.BackgroundColor3 = p >= mx and Colors.Crimson or (p / math.max(mx, 1) > 0.75 and Colors.Gold or Colors.Stamina)
		period.Text = opts.period or ""
		region.Text = opts.region and ("Region: " .. opts.region) or ""
		if opts.ping then
			ping.Text = tostring(opts.ping) .. " ms"
			ping.TextColor3 = opts.ping < 90 and Colors.Stamina or (opts.ping < 180 and Colors.Gold or Colors.Crimson)
		else
			ping.Text = ""
		end
		if opts.faction and Theme.Factions[opts.faction] then
			local f = Theme.Faction(opts.faction)
			crest.Image = Images[f.Icon]
			crest.ImageColor3 = f.Accent
			crest.Visible = true
			nameLbl.Position = UDim2.fromOffset(44, 9)
		else
			crest.Visible = false
			nameLbl.Position = UDim2.fromOffset(22, 9)
		end
		frame.ImageColor3 = opts.isCurrent and Colors.Gold or Colors.RowFrame
		renderButton()
		root:SetAttribute("Value", opts.jobId or opts.name)
	end
	function api:SetJoining(on: boolean)
		joining = on
		renderButton()
	end
	api:Set({})
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- ServerBrowser
--------------------------------------------------------------------------
--[[ opts: title? ("Servers"), servers { ServerRow opts }, onJoin(server, rowApi), onQuickJoin(api),
	   onRefresh(api), searchPlaceholder?, status?
	 Live data: api:UpdateServers(list) diffs rows in place by jobId (or name), so counts,
	 periods and joinability update without the list jumping. ReplicatedStorage.UI.ServerDirectory
	 .Bind(api) polls the real server directory and calls it for you. api.OnJoin / OnQuickJoin /
	 OnRefresh override the opts callbacks at runtime. ]]
function Components.ServerBrowser(opts)
	opts = opts or {}
	local root, panel = Components.Panel({ Name = "ServerBrowser", Size = UDim2.fromOffset(1075, 845) })
	local c = panel.Content
	local header = new("Frame", { Name = "Header", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 56), Parent = c })
	emboss(text({
		Name = "Title",
		Text = string.upper(opts.title or "Servers"),
		Font = Fonts.Title,
		TextSize = 32,
		Position = UDim2.fromOffset(26, -4),
		Size = UDim2.new(0, 260, 0, 40),
		Parent = header,
	}), Color3.fromRGB(150, 140, 130), 1.8)
	local liveDot = image("Glow", { Name = "LiveDot", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0, 32, 0, 45), Size = UDim2.fromOffset(14, 14), ImageColor3 = Colors.TextFaint, Parent = header })
	local status = text({ Name = "Status", Text = "", TextSize = Sizes.TextTiny, TextColor3 = Colors.TextDim, Position = UDim2.fromOffset(44, 36), Size = UDim2.fromOffset(260, 18), Parent = header })
	local api = { Root = root, Panel = panel, Rows = {} }
	local _, search = Components.SearchBar({
		placeholder = opts.searchPlaceholder or "Search campuses...",
		onChanged = function(t)
			api:Filter(t)
		end,
		AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(340, 40),
		Parent = header,
	})
	api.Search = search
	local _, refresh = Components.Button({
		Name = "Refresh",
		text = "Refresh",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -16, 0.5, 0),
		Size = UDim2.fromOffset(124, Sizes.RowHeight),
		onClick = function()
			local cb = api.OnRefresh or opts.onRefresh
			if cb then
				cb(api)
			end
		end,
		Parent = header,
	})
	local _, quick = Components.Button({
		Name = "QuickJoin",
		text = "Quick Join",
		style = "gold",
		AnchorPoint = Vector2.new(1, 0.5),
		Position = UDim2.new(1, -150, 0.5, 0),
		Size = UDim2.fromOffset(140, Sizes.RowHeight),
		onClick = function()
			local cb = api.OnQuickJoin or opts.onQuickJoin
			if cb then
				cb(api)
			end
		end,
		Parent = header,
	})
	api.RefreshButton, api.QuickJoinButton = refresh, quick
	Components.Divider({ color = Colors.IronDim, Position = UDim2.fromOffset(0, 58), Size = UDim2.new(1, 0, 0, 14), Parent = c })
	local list = new("ScrollingFrame", {
		Name = "List",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 78),
		Size = UDim2.new(1, 0, 1, -92),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 5,
		ScrollBarImageColor3 = Colors.IronDim,
		ZIndex = 3,
		Parent = c,
	})
	pad(8, 14, 2, 8).Parent = list
	new("UIListLayout", { SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 12), Parent = list })
	api.List = list
	local empty = text({ Name = "Empty", Text = "No campuses answer the bell.", TextColor3 = Colors.TextDim, TextXAlignment = CENTER, Position = UDim2.fromOffset(0, 120), Size = UDim2.new(1, 0, 0, 30), Visible = false, Parent = c })
	local byKey = {}
	local function keyOf(s)
		return s.jobId or s.id or s.name
	end
	local function makeRow(s, order)
		local o = merge(s, {
			LayoutOrder = order,
			onJoin = s.onJoin or function(server, rowApi)
				local cb = api.OnJoin or opts.onJoin
				if cb then
					cb(server, rowApi)
				end
			end,
			Parent = list,
		})
		local _, ra = Components.ServerRow(o)
		return ra
	end
	function api:SetServers(servers)
		for _, r in ipairs(api.Rows) do
			r.Root:Destroy()
		end
		api.Rows = {}
		table.clear(byKey)
		for i, s in ipairs(servers or {}) do
			local ra = makeRow(s, i)
			api.Rows[i] = ra
			byKey[keyOf(s)] = ra
		end
		api:Filter(search:Get())
	end
	function api:UpdateServers(servers)
		local seen, rows = {}, {}
		for i, s in ipairs(servers or {}) do
			local k = keyOf(s)
			seen[k] = true
			local ra = byKey[k]
			if ra then
				-- (audit) Set merges, so a field that went away (no controlling faction, no period) kept its old value
				for _, f in ipairs({ "region", "period", "faction" }) do
					if s[f] == nil then
						ra.data[f] = nil
					end
				end
				ra:Set(s)
				ra.Root.LayoutOrder = i
			else
				ra = makeRow(s, i)
				byKey[k] = ra
			end
			rows[i] = ra
		end
		for k, ra in pairs(byKey) do
			if not seen[k] then
				ra.Root:Destroy()
				byKey[k] = nil
			end
		end
		api.Rows = rows
		api:Filter(search:Get())
	end
	function api:GetRow(key)
		return byKey[key]
	end
	function api:SetStatus(t: string, live: boolean?)
		status.Text = t or ""
		liveDot.ImageColor3 = (live == true and Colors.Stamina) or (live == false and Colors.Crimson) or Colors.TextFaint
	end
	function api:Filter(q: string?)
		q = string.lower(q or "")
		local shown = 0
		for _, r in ipairs(api.Rows) do
			local d = r.data or {}
			local hay = string.lower((d.name or "") .. " " .. (d.region or "") .. " " .. (d.period or ""))
			local ok = q == "" or string.find(hay, q, 1, true) ~= nil
			r.Root.Visible = ok
			if ok then
				shown += 1
			end
		end
		empty.Visible = shown == 0
		root:SetAttribute("Value", shown)
	end
	api:SetServers(opts.servers)
	if opts.status then
		api:SetStatus(opts.status, opts.statusLive)
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- CharacterPreview
--------------------------------------------------------------------------
--[[ opts: backText? ("Return to Main Menu"), onBack(), footer?, spin?, fov?, zoom?, yaw?,
	   model? (static Model, cloned), player? (Player: live mirror of their character),
	   fallback? (Model shown while the player has no character, e.g. StarterCharacter),
	   mirrorPose? (default true: copies the source rig's joint poses every frame)
	 Live: api:BindPlayer(player) follows player.Character across respawns. api:Watch(model)
	 mirrors any model: appearance changes (parts, accessories, clothing, colours, meshes,
	 textures, body colours) re-clone it (debounced 0.15s), and Motor6D poses are copied
	 every frame so the preview animates with the real character. ]]
local APPEARANCE_PROPS = {
	Color = true, BrickColor = true, Material = true, MaterialVariant = true, Transparency = true, Size = true,
	TextureID = true, MeshId = true, TextureId = true, Image = true, ImageColor3 = true, Scale = true, Offset = true, VertexColor = true,
	ShirtTemplate = true, PantsTemplate = true, Graphic = true, Texture = true, Color3 = true,
	HeadColor3 = true, TorsoColor3 = true, LeftArmColor3 = true, RightArmColor3 = true, LeftLegColor3 = true, RightLegColor3 = true,
	ColorMap = true, NormalMap = true, RoughnessMap = true, MetalnessMap = true,
}
function Components.CharacterPreview(opts)
	opts = opts or {}
	local RunService = game:GetService("RunService")
	local root, panel = Components.Panel({ Name = "CharacterPreview", Size = UDim2.fromOffset(430, 560) })
	local c = panel.Content
	local _, back = Components.Button({
		Name = "Back",
		text = string.upper(opts.backText or "Return to Main Menu"),
		textSize = Sizes.TextBody,
		Size = UDim2.new(1, 0, 0, Sizes.RowHeight),
		onClick = function()
			if opts.onBack then
				opts.onBack()
			end
		end,
		Parent = c,
	})
	local well = new("ImageLabel", {
		Name = "Stage",
		Image = Images.SlotBg,
		ImageColor3 = Color3.fromRGB(62, 56, 70),
		ScaleType = Enum.ScaleType.Stretch,
		BackgroundColor3 = Colors.Ink,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, Sizes.RowHeight + 10),
		Size = UDim2.new(1, 0, 1, -(Sizes.RowHeight + 34)),
		ZIndex = 2,
		Parent = c,
	})
	slice("FrameThin", Colors.IronDim, { SliceScale = 0.4, ZIndex = 6, Parent = well })
	local vpf = new("ViewportFrame", {
		Name = "Viewport",
		BackgroundTransparency = 1,
		Size = UDim2.fromScale(1, 1),
		Ambient = Color3.fromRGB(128, 120, 136),
		LightColor = Color3.fromRGB(255, 236, 205),
		LightDirection = Vector3.new(-0.6, -1, -0.5),
		ZIndex = 3,
		Parent = well,
	})
	local world = new("WorldModel", { Name = "World", Parent = vpf })
	local cam = new("Camera", { FieldOfView = opts.fov or 32, Parent = vpf })
	vpf.CurrentCamera = cam
	local footer = plate({ Name = "Footer", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.new(0.5, 0, 1, -10), Size = UDim2.new(1, 0, 0, 26), Parent = c })
	local footerLbl = text({ Name = "Label", Text = opts.footer or "", TextSize = Sizes.TextSmall, TextXAlignment = CENTER, ZIndex = 11, Parent = footer })
	local api = { Root = root, Viewport = vpf, World = world, Camera = cam, BackButton = back }

	local model, spinConn, poseConn, basePivot
	local yaw = 0
	local framed = false
	local watched, watchConns, playerConns = nil, {}, {}
	local motorPairs = {}

	-- What the shot has to hold: the character's visible parts, hair, accessories, ears and tails,
	-- but not held tools or sheathed weapons (a katana on the back would shrink the whole shot).
	local function framed_part(p, mdl)
		if p.Transparency >= 0.95 or p.Name == "HumanoidRootPart" then
			return false
		end
		local a = p.Parent
		while a and a ~= mdl do
			if a:IsA("Tool") or a.Name == "Weapons" then
				return false
			end
			a = a.Parent
		end
		return true
	end
	-- Height range and spin radius around the model's own up axis: these don't change as it turns around.
	local function shotBounds(mdl)
		local pivot = mdl:GetPivot()
		local loY, hiY, rad = math.huge, -math.huge, 0
		for _, p in ipairs(mdl:GetDescendants()) do
			if p:IsA("BasePart") and framed_part(p, mdl) then
				local h = p.Size / 2
				for _, sx in ipairs({ -1, 1 }) do
					for _, sy in ipairs({ -1, 1 }) do
						for _, sz in ipairs({ -1, 1 }) do
							local v = pivot:PointToObjectSpace(p.CFrame * Vector3.new(h.X * sx, h.Y * sy, h.Z * sz))
							loY = math.min(loY, v.Y)
							hiY = math.max(hiY, v.Y)
							rad = math.max(rad, math.sqrt(v.X * v.X + v.Z * v.Z))
						end
					end
				end
			end
		end
		if loY > hiY then
			local _, size = mdl:GetBoundingBox()
			return pivot.Position, size.Y, math.max(size.X, size.Z) / 2
		end
		return pivot.Position + Vector3.new(0, (loY + hiY) / 2, 0), hiY - loY, rad
	end
	-- Fit head to feet and the full turn-around width inside this viewport, with a margin. Recomputed on
	-- every re-clone and resize, so a frame taken mid-load (or mid-crouch) never sticks.
	local function frameCamera()
		if not model then
			return false
		end
		local vp = vpf.AbsoluteSize
		if vp.X < 4 or vp.Y < 4 then
			return false
		end
		local target, height, rad = shotBounds(model)
		local margin = opts.margin or 1.1
		local tanV = math.tan(math.rad(cam.FieldOfView) / 2)
		local aspect = vp.X / vp.Y
		local dist = math.max(height / 2 * margin / tanV, rad * margin / (tanV * aspect)) + rad * 0.5
		local dir = CFrame.Angles(0, math.rad(opts.yaw or -20), 0) * Vector3.new(0, 0.08, -1)
		cam.CFrame = CFrame.lookAt(target + dir.Unit * dist, target)
		return true
	end
	-- the panel can resize (FitToScreen, AutoScale, stage mode): reframe so nothing gets cut off
	vpf:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		task.defer(frameCamera)
	end)
	-- ViewportFrames don't draw SurfaceGuis: turn painted face plates (UI.Appearance) back into Decals
	local function facePlatesToDecals(mdl)
		local plates = {}
		for _, d in ipairs(mdl:GetDescendants()) do
			if d.Name == "NHFacePlate" then
				table.insert(plates, d)
			end
		end
		for _, plate in ipairs(plates) do
			local head = plate.Parent
			local sg = plate:FindFirstChildWhichIsA("SurfaceGui", true)
			if head and head:IsA("BasePart") and sg then
				for _, im in ipairs(sg:GetChildren()) do
					if im:IsA("ImageLabel") then
						local dc = Instance.new("Decal")
						dc.Name = im.Name
						dc.Face = Enum.NormalId.Front
						dc.Texture = im.Image
						dc.Color3 = im.ImageColor3
						dc.ZIndex = im.ZIndex
						dc.Parent = head
					end
				end
			end
			plate:Destroy()
		end
	end
	local function stripForDisplay(mdl)
		facePlatesToDecals(mdl)
		for _, d in ipairs(mdl:GetDescendants()) do
			if d:IsA("LuaSourceContainer") or d:IsA("Sound") or d:IsA("ForceField") then
				d:Destroy()
			elseif d:IsA("BasePart") then
				d.CanCollide = false
			end
		end
		local hum = mdl:FindFirstChildOfClass("Humanoid")
		if hum then
			hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		end
		local rp = mdl:FindFirstChild("HumanoidRootPart") or mdl.PrimaryPart
		if rp and rp:IsA("BasePart") then
			rp.Anchored = true
			rp.Transparency = 1
		end
	end
	local function pathOf(inst, top)
		local parts = {}
		while inst and inst ~= top do
			table.insert(parts, 1, inst.Name)
			inst = inst.Parent
		end
		return table.concat(parts, "/")
	end
	local function buildMotorPairs(srcModel, dst)
		table.clear(motorPairs)
		if not srcModel then
			return
		end
		local srcMotors = {}
		for _, d in ipairs(srcModel:GetDescendants()) do
			if d:IsA("Motor6D") then
				srcMotors[pathOf(d, srcModel)] = d
			end
		end
		for _, d in ipairs(dst:GetDescendants()) do
			if d:IsA("Motor6D") then
				local s = srcMotors[pathOf(d, dst)]
				if s then
					table.insert(motorPairs, { s, d })
				end
			end
		end
	end
	local function updatePoseLoop()
		if poseConn then
			poseConn:Disconnect()
			poseConn = nil
		end
		if opts.mirrorPose ~= false and #motorPairs > 0 then
			poseConn = RunService.RenderStepped:Connect(function()
				for _, p in ipairs(motorPairs) do
					if p[1].Parent and p[2].Parent then
						p[2].Transform = p[1].Transform
					end
				end
			end)
		end
	end
	local function show(mdl, srcModel, keepCamera)
		if model then
			model:Destroy()
		end
		model = nil
		table.clear(motorPairs)
		if mdl then
			local was = mdl.Archivable
			mdl.Archivable = true
			local ok, clone = pcall(mdl.Clone, mdl)
			mdl.Archivable = was
			if ok and clone then
				model = clone
				stripForDisplay(model)
				model:PivotTo(CFrame.new())
				basePivot = model:GetPivot()
				if yaw ~= 0 then
					model:PivotTo(basePivot * CFrame.Angles(0, yaw, 0))
				end
				model.Parent = world
				buildMotorPairs(srcModel, model)
				-- the shot is measured from the unturned pose at the origin, so reframing never jumps mid-spin
				if yaw ~= 0 then
					model:PivotTo(basePivot)
				end
				framed = frameCamera() or framed
				if yaw ~= 0 then
					model:PivotTo(basePivot * CFrame.Angles(0, yaw, 0))
				end
			end
		end
		updatePoseLoop()
		root:SetAttribute("Value", model and model.Name or "")
	end
	function api:Unwatch()
		for _, cn in ipairs(watchConns) do
			cn:Disconnect()
		end
		table.clear(watchConns)
		watched = nil
	end
	function api:SetModel(mdl)
		api:Unwatch()
		show(mdl, nil, false)
	end
	function api:GetModel()
		return model
	end
	function api:Watch(source)
		api:Unwatch()
		if not source then
			show(opts.fallback, nil, false)
			return
		end
		watched = source
		local pending = false
		local function schedule()
			if pending then
				return
			end
			pending = true
			task.delay(0.15, function()
				pending = false
				if watched == source and source.Parent then
					show(source, source, true)
				end
			end)
		end
		local function hook(d)
			if d:IsA("BasePart") or d:IsA("DataModelMesh") or d:IsA("Clothing") or d:IsA("ShirtGraphic") or d:IsA("Decal")
				or d:IsA("BodyColors") or d:IsA("SurfaceAppearance") then
				table.insert(watchConns, d.Changed:Connect(function(prop)
					if APPEARANCE_PROPS[prop] then
						schedule()
					end
				end))
			end
		end
		for _, d in ipairs(source:GetDescendants()) do
			hook(d)
		end
		local function relevant(d)
			return not (d:IsA("JointInstance") or d:IsA("Sound") or d:IsA("LuaSourceContainer") or d:IsA("Animator")
				or d:IsA("AnimationTrack") or d:IsA("Animation") or d:IsA("Constraint") or d:IsA("Attachment") or d:IsA("BodyMover"))
		end
		table.insert(watchConns, source.DescendantAdded:Connect(function(d)
			hook(d)
			if relevant(d) then
				schedule()
			end
		end))
		table.insert(watchConns, source.DescendantRemoving:Connect(function(d)
			if relevant(d) then
				schedule()
			end
		end))
		show(source, source, framed)
	end
	function api:BindPlayer(player)
		for _, cn in ipairs(playerConns) do
			cn:Disconnect()
		end
		table.clear(playerConns)
		if not player then
			api:Watch(nil)
			return
		end
		local function onChar(ch)
			task.spawn(function()
				ch:WaitForChild("HumanoidRootPart", 5)
				if player.Character == ch then
					api:Watch(ch)
				end
			end)
		end
		table.insert(playerConns, player.CharacterAdded:Connect(onChar))
		table.insert(playerConns, player.CharacterRemoving:Connect(function()
			api:Watch(nil)
		end))
		if player.Character then
			onChar(player.Character)
		else
			api:Watch(nil)
		end
	end
	function api:SetFooter(t: string)
		footerLbl.Text = t
	end
	function api:SetSpin(on: boolean)
		if spinConn then
			spinConn:Disconnect()
			spinConn = nil
		end
		if on then
			spinConn = RunService.Heartbeat:Connect(function(dt)
				if model and basePivot and root.Visible then
					yaw += dt * 0.6
					model:PivotTo(basePivot * CFrame.Angles(0, yaw, 0))
				end
			end)
		end
	end
	root.Destroying:Connect(function()
		api:SetSpin(false)
		api:Unwatch()
		for _, cn in ipairs(playerConns) do
			cn:Disconnect()
		end
		if poseConn then
			poseConn:Disconnect()
		end
	end)
	if opts.player then
		api:BindPlayer(opts.player)
	elseif opts.model then
		api:SetModel(opts.model)
	elseif opts.fallback then
		show(opts.fallback, nil, false)
	end
	if opts.spin then
		api:SetSpin(true)
	end
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- CreditsPanel
--------------------------------------------------------------------------
-- opts: title? ("Credits"), entries { {role, name} }, columns? (2)
function Components.CreditsPanel(opts)
	opts = opts or {}
	local root, panel = Components.Panel({ Name = "Credits", title = opts.title or "Credits", Size = UDim2.fromOffset(430, 280), titleFlourishWidth = 220 })
	local sc = new("ScrollingFrame", {
		Name = "Entries",
		BackgroundTransparency = 1,
		BorderSizePixel = 0,
		Position = UDim2.fromOffset(0, 8),
		Size = UDim2.new(1, 0, 1, -18),
		CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4,
		ScrollBarImageColor3 = Colors.IronDim,
		ZIndex = 3,
		Parent = panel.Content,
	})
	pad(10, 10, 0, 0).Parent = sc
	local cols = opts.columns or 2
	new("UIGridLayout", {
		CellSize = UDim2.new(1 / cols, -8, 0, 38),
		CellPadding = UDim2.fromOffset(8, 2),
		SortOrder = Enum.SortOrder.LayoutOrder,
		Parent = sc,
	})
	for i, e in ipairs(opts.entries or {}) do
		local cell = new("Frame", { Name = "Entry" .. i, BackgroundTransparency = 1, LayoutOrder = i, Parent = sc })
		local role = text({ Name = "Role", Text = e.role or e[1], TextSize = Sizes.TextSmall, Size = UDim2.new(1, 0, 0, 18), Parent = cell })
		role.FontFace = Theme.FontFaces.BodyBold
		text({ Name = "Who", Text = e.name or e[2] or "Name", TextSize = Sizes.TextSmall - 1, TextColor3 = Colors.TextDim, Position = UDim2.fromOffset(0, 17), Size = UDim2.new(1, 0, 0, 17), Parent = cell })
	end
	place(root, opts)
	return root, { Root = root, Panel = panel }
end

--------------------------------------------------------------------------
-- ColorPicker: hue/saturation wheel + brightness bar + HEX box + presets
--------------------------------------------------------------------------
-- opts: value? Color3, onChanged(c) (live while dragging), onReleased(c) (commit), presets? {Color3}
function Components.ColorPicker(opts)
	opts = opts or {}
	local h, s, v = (opts.value or Color3.new(1, 1, 1)):ToHSV()
	local root = new("Frame", { Name = "ColorPicker", BackgroundTransparency = 1, Size = UDim2.fromOffset(520, 196) })
	local wheel = new("ImageButton", {
		Name = "Wheel", AutoButtonColor = false, BackgroundTransparency = 1, Image = Images.ColorWheel,
		Position = UDim2.fromOffset(0, 6), Size = UDim2.fromOffset(184, 184), ZIndex = 4, Parent = root,
	})
	local dim = new("ImageLabel", {
		Name = "Dim", BackgroundTransparency = 1, Image = Images.ColorWheel, ImageColor3 = Color3.new(0, 0, 0),
		Size = UDim2.fromScale(1, 1), ZIndex = 5, Parent = wheel,
	})
	new("UIStroke", { Color = Colors.IronDim, Thickness = 1.5, Transparency = 0.2, Parent = new("Frame", {
		Name = "Ring", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 6, Parent = wheel,
	}) })
	new("UICorner", { CornerRadius = UDim.new(1, 0), Parent = wheel.Ring })
	local cursor = image("Knob", {
		Name = "Cursor", AnchorPoint = Vector2.new(0.5, 0.5), Size = UDim2.fromOffset(20, 20), ImageColor3 = Colors.Chalk, ZIndex = 8, Parent = wheel,
	})

	local bar = new("TextButton", {
		Name = "Brightness", AutoButtonColor = false, Text = "", BackgroundColor3 = Color3.new(1, 1, 1), BorderSizePixel = 0,
		Position = UDim2.fromOffset(200, 6), Size = UDim2.fromOffset(26, 184), ZIndex = 4, Parent = root,
	})
	local grad = new("UIGradient", { Rotation = 90, Parent = bar })
	slice("FrameSlot", Colors.IronDim, { SliceScale = 0.25, ZIndex = 6, Parent = bar })
	local barMark = new("Frame", {
		Name = "Mark", AnchorPoint = Vector2.new(0.5, 0.5), BackgroundColor3 = Colors.Chalk, BorderSizePixel = 0,
		Size = UDim2.new(1, 10, 0, 4), ZIndex = 8, Parent = bar,
	})
	new("UIStroke", { Color = Colors.Ink, Thickness = 1, Parent = barMark })

	local right = new("Frame", { Name = "Right", BackgroundTransparency = 1, Position = UDim2.fromOffset(244, 6), Size = UDim2.new(1, -244, 0, 184), Parent = root })
	local swatch = new("Frame", { Name = "Swatch", BorderSizePixel = 0, Size = UDim2.fromOffset(64, 64), ZIndex = 4, Parent = right })
	slice("FrameSlot", Colors.Iron, { SliceScale = 0.3, ZIndex = 6, Parent = swatch })
	text({ Name = "HexLabel", Text = "HEX", TextSize = Sizes.TextSmall, TextColor3 = Colors.TextDim, Position = UDim2.fromOffset(78, 0), Size = UDim2.fromOffset(80, 20), Parent = right })
	local hexPlate = plate({ Name = "Hex", Position = UDim2.fromOffset(78, 22), Size = UDim2.fromOffset(150, 40) })
	hexPlate.Parent = right
	local hexBox = new("TextBox", {
		Name = "Input", BackgroundTransparency = 1, ClearTextOnFocus = false, Font = Fonts.Body, TextSize = Sizes.TextBody,
		TextColor3 = Colors.Text, PlaceholderText = "#RRGGBB", PlaceholderColor3 = Colors.TextFaint, Text = "",
		TextXAlignment = CENTER, Size = UDim2.fromScale(1, 1), ZIndex = 11, Parent = hexPlate,
	})
	local presetRow = new("Frame", { Name = "Presets", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 78), Size = UDim2.new(1, 0, 0, 100), Parent = right })
	new("UIGridLayout", { CellSize = UDim2.fromOffset(30, 30), CellPadding = UDim2.fromOffset(6, 6), SortOrder = Enum.SortOrder.LayoutOrder, Parent = presetRow })

	local api = { Root = root }
	local function color()
		return Color3.fromHSV(h, s, v)
	end
	local function render()
		local c = color()
		local ang = h * 2 * math.pi
		cursor.Position = UDim2.fromScale(0.5 + math.cos(ang) * s * 0.5, 0.5 - math.sin(ang) * s * 0.5)
		dim.ImageTransparency = 0.4 + 0.6 * v -- the hues stay visible on dark colours (the swatch shows the true colour)
		grad.Color = ColorSequence.new(Color3.fromHSV(h, s, 1), Color3.new(0, 0, 0))
		barMark.Position = UDim2.fromScale(0.5, 1 - v)
		swatch.BackgroundColor3 = c
		if not hexBox:IsFocused() then
			hexBox.Text = "#" .. string.upper(c:ToHex())
		end
		root:SetAttribute("Value", c)
	end
	local function fire(final)
		if opts.onChanged then
			opts.onChanged(color())
		end
		if final and opts.onReleased then
			opts.onReleased(color())
		end
	end
	local dragging = nil
	local function update(pos)
		if dragging == "wheel" then
			local a, sz = wheel.AbsolutePosition, wheel.AbsoluteSize
			local dx = (pos.X - a.X) / sz.X * 2 - 1
			local dy = (pos.Y - a.Y) / sz.Y * 2 - 1
			s = math.min(1, math.sqrt(dx * dx + dy * dy))
			h = (math.atan2(-dy, dx) / (2 * math.pi)) % 1
			if v < 0.3 then
				-- (2.1.3) a hue picked from a dark colour came out still almost black (the black hair preset is 9% bright,
				-- under the old 5% lift), so the wheel looked dead: lift it to where the hue shows. The bar still darkens it.
				v = 0.85
			end
		elseif dragging == "bar" then
			local a, sz = bar.AbsolutePosition, bar.AbsoluteSize
			v = 1 - math.clamp((pos.Y - a.Y) / sz.Y, 0, 1)
		end
		render()
		fire(false)
	end
	local function begin(kind)
		return function(input)
			if isPress(input) then
				dragging = kind
				update(input.Position)
			end
		end
	end
	wheel.InputBegan:Connect(begin("wheel"))
	bar.InputBegan:Connect(begin("bar"))
	local moveConn = UserInputService.InputChanged:Connect(function(input)
		if dragging and (input.UserInputType == Enum.UserInputType.MouseMovement or input.UserInputType == Enum.UserInputType.Touch) then
			update(input.Position)
		end
	end)
	local endConn = UserInputService.InputEnded:Connect(function(input)
		if dragging and isPress(input) then
			dragging = nil
			fire(true)
		end
	end)
	root.Destroying:Connect(function()
		moveConn:Disconnect()
		endConn:Disconnect()
	end)
	hexBox.FocusLost:Connect(function()
		local hex = string.match(hexBox.Text, "^%s*#?(%x%x%x%x%x%x)%s*$")
		if hex then
			h, s, v = Color3.fromHex(hex):ToHSV()
			render()
			fire(true)
		else
			render() -- put the current value back
		end
	end)
	for i, c in ipairs(opts.presets or {}) do
		local b = new("TextButton", { Name = "Preset" .. i, Text = "", AutoButtonColor = false, BackgroundColor3 = c, BorderSizePixel = 0, LayoutOrder = i, ZIndex = 4, Parent = presetRow })
		slice("FrameSlot", Colors.RowFrame, { SliceScale = 0.2, ZIndex = 6, Parent = b })
		b.Activated:Connect(function()
			h, s, v = c:ToHSV()
			render()
			fire(true)
		end)
	end
	function api:Set(c: Color3, silent: boolean?)
		h, s, v = c:ToHSV()
		render()
		if not silent then
			fire(true)
		end
	end
	function api:Get()
		return color()
	end
	render()
	place(root, opts)
	return root, api
end

--------------------------------------------------------------------------
-- SpinReel: a slot-machine window that rolls through entries and lands on one
--------------------------------------------------------------------------
-- opts: height? (64), textSize?  api:Show(entry)  api:Spin(entries, final, duration?, onDone?)
-- entry = { text = string, color? = Color3, sub? = string }
-- Rarity reveal on any framed element (spin results, item cards): one tier per rarity.
--   Common     a glint sweeps across
--   Uncommon   + a soft flash
--   Rare       + one ring burst in the rarity colour
--   Epic       + a second ring, a chime
--   Legendary / Cursed  "Surge": a double glow pulse, three rings, the stamp sound
-- Reduce Motion: no rings or sweep, just the glow fading. Reduce Flashing: softer flashes.
Components.RarityTiers = { Common = 1, Uncommon = 2, Rare = 3, Epic = 4, Legendary = 5, Cursed = 5 }
function Components.RarityReveal(target: GuiObject, rarity: string?, color: Color3?)
	if not (target and target.Parent) then
		return
	end
	local tier = Components.RarityTiers[rarity or ""] or 1
	local tint = color or Colors.Gold
	local calm = Components.ReducedMotion()
	local soft = Components.ReducedFlash()
	local z = (target.ZIndex or 1) + 8
	local made = {}
	local function img(name, props)
		local i = image(name, props)
		i.ZIndex = z
		i.Parent = target
		table.insert(made, i)
		return i
	end
	-- glint (every tier)
	if not calm then
		local glint = Instance.new("Frame")
		glint.Name = "Glint"
		glint.BackgroundColor3 = Color3.new(1, 1, 1)
		glint.BackgroundTransparency = 0.55
		glint.BorderSizePixel = 0
		glint.Size = UDim2.new(0.12, 0, 1, 0)
		glint.Position = UDim2.fromScale(-0.15, 0)
		glint.Rotation = 14
		glint.ZIndex = z
		local g = Instance.new("UIGradient")
		g.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0), NumberSequenceKeypoint.new(1, 1) })
		g.Parent = glint
		glint.Parent = target
		table.insert(made, glint)
		tween(glint, TweenInfo.new(0.45, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut), { Position = UDim2.fromScale(1.05, 0) })
	end
	-- flash / glow pulse (Uncommon+)
	if tier >= 2 then
		local glow = img("Glow", {
			Name = "RevealGlow", ScaleType = Enum.ScaleType.Stretch, ImageColor3 = tint,
			ImageTransparency = if soft then 0.7 else (tier >= 5 and 0.05 or 0.35),
			AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, 60, 1, 60),
		})
		glow.ZIndex = math.max(1, z - 9) -- behind the text
		tween(glow, TweenInfo.new(0.7, Enum.EasingStyle.Sine), { ImageTransparency = 1 })
		if tier >= 5 then -- the Surge pulses twice
			task.delay(0.45, function()
				if glow.Parent then
					glow.ImageTransparency = if soft then 0.75 else 0.2
					tween(glow, TweenInfo.new(0.9, Enum.EasingStyle.Sine), { ImageTransparency = 1 })
				end
			end)
		end
	end
	-- rings (Rare+)
	if tier >= 3 and not calm then
		local count = if tier >= 5 then 3 elseif tier >= 4 then 2 else 1
		for i = 1, count do
			task.delay((i - 1) * 0.14, function()
				if not target.Parent then return end
				local ring = img("OrbRing", {
					Name = "RevealRing", ImageColor3 = tint, ImageTransparency = 0.15,
					AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(40, 40),
				})
				ring.ZIndex = target.ZIndex or 1 -- behind the content (the result text), bursting out past the edges
				local s = math.max(target.AbsoluteSize.X, 120) * (0.9 + i * 0.25)
				tween(ring, TweenInfo.new(0.6, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = UDim2.fromOffset(s, s * 0.45), ImageTransparency = 1 })
			end)
		end
	end
	if tier >= 5 then
		Components.PlaySound("Stamp", 1, 0.85)
	elseif tier >= 4 then
		Components.PlaySound("Confirm", 0.7, 1.2)
	end
	task.delay(1.6, function()
		for _, m in ipairs(made) do
			if m.Parent then m:Destroy() end
		end
	end)
end

function Components.SpinReel(opts)
	opts = opts or {}
	local H = opts.height or 64
	local root = plate({ Name = "SpinReel", Size = UDim2.fromOffset(420, H + 8) }, Colors.GoldDeep)
	local window = new("CanvasGroup", {
		Name = "Window", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, -16, 0, H), ZIndex = 11, Parent = root,
	})
	new("UIGradient", {
		Rotation = 90,
		Transparency = NumberSequence.new({
			NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.22, 0),
			NumberSequenceKeypoint.new(0.78, 0), NumberSequenceKeypoint.new(1, 1),
		}),
		Parent = window,
	})
	local strip = new("Frame", { Name = "Strip", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, H), ZIndex = 11, Parent = window })
	local flash = image("Glow", {
		Name = "Flash", ScaleType = Enum.ScaleType.Stretch, ImageColor3 = Colors.Gold, ImageTransparency = 1,
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, 40, 1, 40), ZIndex = 9, Parent = root,
	})
	local api = { Root = root }
	local function cell(i, e)
		local f = new("Frame", { Name = "Cell" .. i, BackgroundTransparency = 1, Position = UDim2.fromOffset(0, (i - 1) * H), Size = UDim2.new(1, 0, 0, H), ZIndex = 11, Parent = strip })
		local t = text({
			Name = "Text", Text = e.text or "?", TextXAlignment = CENTER, Font = Fonts.Title,
			TextSize = opts.textSize or Sizes.TextHeader + 6, TextColor3 = e.color or Colors.Text,
			Size = UDim2.new(1, 0, e.sub and 0.66 or 1, 0), ZIndex = 12, Parent = f,
		})
		emboss(t)
		if e.sub then
			text({
				Name = "Sub", Text = e.sub, TextXAlignment = CENTER, TextSize = Sizes.TextSmall, TextColor3 = Colors.TextDim,
				Position = UDim2.fromScale(0, 0.6), Size = UDim2.new(1, 0, 0.36, 0), ZIndex = 12, Parent = f,
			})
		end
		return f
	end
	local function clear()
		for _, c in ipairs(strip:GetChildren()) do
			c:Destroy()
		end
	end
	local token = 0
	function api:Show(e)
		token += 1
		clear()
		strip.Position = UDim2.new()
		cell(1, e or { text = "-" })
		root:SetAttribute("Value", e and e.text or "")
	end
	function api:Spin(entries, final, duration, onDone)
		token += 1
		local my = token
		clear()
		local n = 26
		local rng = Random.new()
		for i = 1, n - 1 do
			cell(i, entries[rng:NextInteger(1, #entries)])
		end
		cell(n, final)
		strip.Size = UDim2.new(1, 0, 0, n * H)
		strip.Position = UDim2.new()
		-- Near-miss (Legendary / Cursed): it slows as if it will stop one short, hangs a beat, then clicks
		-- over onto the result with a small overshoot. Reduce Motion: the plain spin.
		local rare = final and (final.nearMiss == true or final.rarity == "Legendary" or final.rarity == "Cursed")
		local nearMiss = rare and not Components.ReducedMotion()
		local total = duration or 2.4
		local tw
		if nearMiss then
			local short = tween(strip, TweenInfo.new(total * 0.82, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Position = UDim2.fromOffset(0, -(n - 1.62) * H) })
			local done = Instance.new("BindableEvent")
			tw = { Completed = done.Event }
			short.Completed:Connect(function()
				if my ~= token then
					done:Destroy()
					return
				end
				task.delay(0.32, function()
					if my ~= token then
						done:Destroy()
						return
					end
					local click = tween(strip, TweenInfo.new(0.5, Enum.EasingStyle.Back, Enum.EasingDirection.Out), { Position = UDim2.fromOffset(0, -(n - 1) * H) })
					click.Completed:Connect(function()
						done:Fire()
						done:Destroy()
					end)
				end)
			end)
		else
			tw = tween(strip, TweenInfo.new(total, Enum.EasingStyle.Quint, Enum.EasingDirection.Out), { Position = UDim2.fromOffset(0, -(n - 1) * H) })
		end
		tw.Completed:Connect(function()
			if my ~= token then
				return
			end
			api:Show(final)
			if final.rarity and Components.RarityTiers[final.rarity] then
				Components.RarityReveal(root, final.rarity, final.color)
			else
				flash.ImageColor3 = final.color or Colors.Gold
				flash.ImageTransparency = if Components.ReducedFlash() then 0.7 else 0.2
				tween(flash, TweenInfo.new(0.8), { ImageTransparency = 1 })
			end
			if onDone then
				onDone(final)
			end
		end)
	end
	api:Show(opts.entry)
	place(root, opts)
	return root, api
end

return Components
