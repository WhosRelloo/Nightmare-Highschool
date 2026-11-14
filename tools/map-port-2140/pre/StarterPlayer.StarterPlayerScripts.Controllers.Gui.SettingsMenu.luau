--[[
	Settings menu (client, NH UI kit). Toggle with M or the "Settings" button (left edge, for touch).
	(Not O: Roblox's camera uses I/O for zoom and swallows them.)
	Tabs: Controls (rebind combat keys; the controller's buttons and which names they show), Audio, Camera, Interface,
	Graphics. On a controller LB / RB (L1 / R1) change tab and sliders step with left / right.
	Everything applies instantly and is saved to your profile a second after you stop changing
	things. The logic lives in ReplicatedStorage.UI.Settings; this file only draws it.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key
local GuiService = game:GetService(`GuiService`)
local ContextActionService = game:GetService(`ContextActionService`)

---| Modules |---

local UI = ReplicatedStorage:WaitForChild(`UI`)
local Kit = require(UI:WaitForChild(`Components`))
local Settings = require(UI:WaitForChild(`Settings`))

local Player = Players.LocalPlayer
local C = Kit.Theme.Colors
local TOGGLE_KEY = Enum.KeyCode.P -- Options (2026-11-02 key map: P options, M report card, L factions, ` locker)
local TABS = { `Controls`, `Audio`, `Camera`, `Interface`, `Graphics` }

local Local = {}
local Shared = {}

local Ui = nil
local Tab = 1

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `SettingsMenu`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 9
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(Gui)

	local Toggle = Kit.Button({
		text = if UserInputService.KeyboardEnabled then `Options [P]` else `Settings`;
		style = `ghost`; onClick = function() Shared.Toggle() end;
		Name = `Toggle`; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 8, 0.5, 130);
		Size = UDim2.fromOffset(150, 44); Parent = Gui;
	})

	local Panel, PanelApi = Kit.Panel({
		title = `Settings`; Name = `Panel`;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(720, 680); Visible = false; Parent = Gui;
	})
	Kit.FitToScreen(Panel)
	-- the top bar's Menu button opens this panel too: on keyboard devices drop the duplicate left-edge toggle
	if game:GetService(`UserInputService`).KeyboardEnabled and script.Parent:FindFirstChild(`TopBar`) then
		Toggle.Visible = false
	end
	local Content = PanelApi.Content

	local _, Tabs = Kit.TabBar({
		tabs = TABS; selected = 1; textSize = 19;
		onChanged = function(Index) Tab = Index Local.Render() end;
		Name = `Tabs`; Size = UDim2.new(1, -60, 0, 48); Parent = Content;
	})
	Kit.Button({
		text = `X`; style = `ghost`; onClick = function() Shared.Toggle(false) end;
		Name = `Close`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 2);
		Size = UDim2.fromOffset(48, 44); Parent = Content;
	})

	local Body = Instance.new(`ScrollingFrame`)
	Body.Name = `Body`
	Body.BackgroundTransparency = 1
	Body.BorderSizePixel = 0
	Body.Position = UDim2.fromOffset(0, 58)
	Body.Size = UDim2.new(1, 0, 1, -116)
	Body.CanvasSize = UDim2.new()
	Body.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Body.ScrollBarThickness = 5
	Body.ScrollBarImageColor3 = C.IronDim
	Body.Parent = Content
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = Body
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingRight = UDim.new(0, 10)
	Pad.Parent = Body

	local Status = Kit.Text({
		Name = `Status`; Text = ``; TextSize = 18; TextColor3 = C.TextDim;
		AnchorPoint = Vector2.new(0, 1); Position = UDim2.fromScale(0, 1); Size = UDim2.new(0.6, 0, 0, 44); Parent = Content;
	})
	Kit.Button({
		text = `Reset to defaults`; style = `crimson`; textSize = 18;
		onClick = function()
			Settings.Reset()
			Local.Render()
			Local.Status(`Defaults restored`, true)
		end;
		Name = `Reset`; AnchorPoint = Vector2.new(1, 1); Position = UDim2.fromScale(1, 1);
		Size = UDim2.fromOffset(210, 44); Parent = Content;
	})

	return { Gui = Gui; Toggle = Toggle; Panel = Panel; Body = Body; Tabs = Tabs; Status = Status }
end

---| Rows |---

function Local.Status(Text: string, Ok: boolean?)
	if not Ui then return end
	Ui.Status.Text = Text
	Ui.Status.TextColor3 = if Ok == false then C.Danger elseif Ok then C.Gold else C.TextDim
end

function Local.Section(Text: string, Order: number)
	Kit.SectionHeader({ text = Text; LayoutOrder = Order; Size = UDim2.new(1, -8, 0, 34); Parent = Ui.Body })
end

function Local.Note(Text: string, Order: number)
	Kit.Text({
		Text = Text; TextSize = 18; TextColor3 = C.TextDim; TextWrapped = true;
		Size = UDim2.new(1, -8, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Order; Parent = Ui.Body;
	})
end

function Local.Slider(Label: string, Key: string, Order: number, Suffix: string?, OnRelease: boolean?)
	local Range = Settings.Ranges[Key]
	Kit.Slider({
		label = Label; min = Range[1]; max = Range[2]; step = Range[3]; value = Settings.Get(Key);
		suffix = Suffix or `%`; labelWidth = 0.34;
		onChanged = if OnRelease then nil else function(V) Settings.Set(Key, V) end;
		onReleased = if OnRelease then function(V) Settings.Set(Key, V) end else nil;
		Name = Key; LayoutOrder = Order; Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Body;
	})
end

function Local.Toggle(Label: string, Key: string, Order: number)
	Kit.Toggle({
		label = Label; value = Settings.Get(Key) == true;
		onChanged = function(V) Settings.Set(Key, V) end;
		Name = Key; LayoutOrder = Order; Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Body;
	})
end

-- A toggle for a two-value string setting (on = OnValue).
function Local.ChoiceToggle(Label: string, Key: string, OnValue: string, OffValue: string, Order: number)
	Kit.Toggle({
		label = Label; value = Settings.Get(Key) == OnValue;
		onChanged = function(V) Settings.Set(Key, if V then OnValue else OffValue) end;
		Name = Key; LayoutOrder = Order; Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Body;
	})
end

-- A setting with a few string values: the button shows the value and steps to the next one.
function Local.Cycle(Label: string, Key: string, Order: number, Shown: (string) -> string, OnChanged: (() -> ())?)
	local Values = Settings.Choices[Key]
	local Row = Instance.new(`Frame`)
	Row.Name = Key
	Row.BackgroundTransparency = 1
	Row.Size = UDim2.new(1, -8, 0, 44)
	Row.LayoutOrder = Order
	Row.Parent = Ui.Body
	Kit.Text({
		Name = `Label`; Text = Label; TextSize = 19; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Left;
		Position = UDim2.fromOffset(14, 0); Size = UDim2.new(0.5, -14, 1, 0); Parent = Row;
	})
	local _, Api
	_, Api = Kit.Button({
		text = Shown(Settings.Get(Key)); textSize = 18; Name = `Value`;
		AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -6, 0.5, 0); Size = UDim2.fromOffset(260, 40); Parent = Row;
		onClick = function()
			local I = table.find(Values, Settings.Get(Key)) or 1
			Settings.Set(Key, Values[I % #Values + 1])
			Api:SetText(Shown(Settings.Get(Key)))
			if OnChanged then OnChanged() end
		end;
	})
end

-- The controller: which button names to show, and what every button does (fixed, Kit.PadControls)
function Local.PadSection(Base: number)
	Local.Section(`Controller`, Base)
	local Rows = {}
	Local.Cycle(`Button names`, `ControllerButtons`, Base + 1, function(V)
		return if V == `Auto` then `Auto ({Kit.PadStyle()})` else V
	end, function()
		for _, R in Rows do R[1]:Set(R[2], true) end
	end)
	local Grid = Local.Grid(Base + 2)
	for Index, Pair in Kit.PadControls do
		local Row, Api = Kit.KeybindRow({ label = Pair[2]; key = Pair[1]; LayoutOrder = Index; Parent = Grid })
		Row.Key.Interactable = false
		Row.Key.Selectable = false
		Row.Key.KeyLabel.TextColor3 = C.TextDim
		Row.Label.TextColor3 = C.TextDim
		table.insert(Rows, { Api, Pair[1] })
	end
	Local.Note(Kit.PadText("Controller buttons can't be changed. In menus: {A} picks, {B} closes, {L1} / {R1} change tab here, and left / right move a slider. Auto reads the controller you plugged in."), Base + 3)
end

function Local.Grid(Order: number): Frame
	local Grid = Instance.new(`Frame`)
	Grid.BackgroundTransparency = 1
	Grid.Size = UDim2.new(1, -8, 0, 0)
	Grid.AutomaticSize = Enum.AutomaticSize.Y
	Grid.LayoutOrder = Order
	Grid.Parent = Ui.Body
	local Layout = Instance.new(`UIGridLayout`)
	Layout.CellSize = UDim2.new(0.5, -4, 0, 44)
	Layout.CellPadding = UDim2.fromOffset(8, 8)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Parent = Grid
	return Grid
end

---| Render |---

function Local.Render()
	if not Ui or not Ui.Panel.Visible then return end
	for _, Child in Ui.Body:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end

	if Tab == 1 then
		-- on a controller its section comes first; with a keyboard it's after the keys (when a pad is plugged in)
		local PadFirst = Kit.InputKind and Kit.InputKind() == `Gamepad`
		if PadFirst then Local.PadSection(-10) end
		if UserInputService.GamepadEnabled and not PadFirst then Local.PadSection(10) end
		Local.Section(`Combat keys`, 1)
		Local.Note(`Click a key, then press the new one (Esc cancels). Keys used elsewhere can't be taken.`, 2)
		local Grid = Local.Grid(3)
		for Index, Action in Settings.KeyActions do
			Kit.KeybindRow({
				label = Action.Label; key = Settings.Get(`Keys`)[Action.Id]; LayoutOrder = Index; Name = Action.Id; Parent = Grid;
				onChanged = function(Key)
					local Name = if typeof(Key) == `EnumItem` then Key.Name else tostring(Key)
					local Ok, Message = Settings.SetKey(Action.Id, Name)
					Local.Status(Message, Ok)
					if not Ok then task.defer(Local.Render) end
				end;
			})
		end
		Local.Section(`Fixed keys`, 4)
		local Fixed = Local.Grid(5)
		for Index, Pair in Settings.FixedKeys do
			local Row = Kit.KeybindRow({ label = Pair[1]; key = Pair[2]; LayoutOrder = Index; Parent = Fixed })
			Row.Key.Interactable = false
			Row.Key.KeyLabel.TextColor3 = C.TextDim
			Row.Label.TextColor3 = C.TextDim
		end
	elseif Tab == 2 then
		Local.Section(`Volume`, 1)
		Local.Slider(`Master`, `MasterVolume`, 2)
		Local.Slider(`Combat Effects`, `EffectsVolume`, 3)
		Local.Slider(`Music & Ambience`, `MusicVolume`, 4)
		Local.Note(`Music & Ambience covers looping sounds; everything else is an effect.`, 5)
	elseif Tab == 3 then
		Local.Section(`Camera`, 1)
		Local.Slider(`Field of View`, `FieldOfView`, 2, `\u{00B0}`)
		Local.Slider(`Camera Shake`, `CameraShake`, 3)
		Local.Note(`Camera Shake scales hits, slams and other impacts. 0% turns it off.`, 4)
		Local.Section(`Comfort`, 5)
		Local.Toggle(`Reduce Motion`, `ReducedMotion`, 6)
		Local.Toggle(`Reduce Flashing`, `ReducedFlashing`, 7)
		Local.Note(`Reduce Motion softens camera kicks, zooms and sweeping effects. Reduce Flashing dims bright flashes and strobes. Reduce Motion starts from your device's setting.`, 8)
	elseif Tab == 4 then
		Local.Section(`Interface`, 1)
		Local.Slider(`UI Scale`, `UIScale`, 2, `%`, true)
		Local.Toggle(`Show HUD (health, hotbar, Yen)`, `ShowHud`, 3)
		Local.Toggle(`Show Clock`, `ShowClock`, 4)
		Local.Slider(`Cursor Size`, `CursorSize`, 5, `px`)
		Local.Toggle(`Animated Cursor`, `AnimatedCursor`, 6)
		Local.Note(`UI Scale applies when you let go of the slider. Reduce Motion also keeps the cursor still.`, 7)
		-- (1.98.0) owner: "an option to show your weapon or hide it"
		Local.Section(`Character`, 8)
		Local.Toggle(`Show Weapon When Put Away`, `ShowWeapon`, 9)
		Local.Note(`Off hides the weapon on your back while it's put away, for everyone. It always shows in your hand while it's out.`, 10)
	else
		Local.Section(`Graphics`, 1)
		Local.Toggle(`Shadows`, `Shadows`, 2)
		Local.Toggle(`Screen Vignette`, `Vignette`, 3)
		Local.ChoiceToggle(`High-quality Effects`, `EffectsQuality`, `High`, `Low`, 4)
		Local.Note(`Turning shadows or high-quality effects off helps on slower devices. Effects quality starts from your Roblox graphics level.`, 5)
	end
end

---| API |---

-- the first button in the body, for the controller's selection after a tab change
function Local.SelectBody()
	if not (Ui and GuiService.SelectedObject) then return end
	task.defer(function()
		local Best, BestY = nil, math.huge
		for _, D in Ui.Body:GetDescendants() do
			if D:IsA(`GuiButton`) and D.Visible and D.Active and D.Selectable and D.AbsolutePosition.Y < BestY then
				Best, BestY = D, D.AbsolutePosition.Y
			end
		end
		if Best then GuiService.SelectedObject = Best end
	end)
end

local TabsBound = false
function Local.PadTabs(On: boolean)
	if On == TabsBound then return end
	TabsBound = On
	if not On then ContextActionService:UnbindAction(`NHSettingsTabs`) return end
	ContextActionService:BindActionAtPriority(`NHSettingsTabs`, function(_, State, Io)
		if State ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
		local Step = if Io.KeyCode == Enum.KeyCode.ButtonR1 then 1 else -1
		Shared.SelectTab((Tab - 1 + Step) % #TABS + 1)
		Local.SelectBody()
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonL1, Enum.KeyCode.ButtonR1)
end

function Shared.Toggle(Open: boolean?)
	if not Ui then return end
	if Open == nil then Open = not Ui.Panel.Visible end
	Ui.Panel.Visible = Open
	Local.PadTabs(Open)
	if Open then
		Local.Status(``)
		Local.Render()
	end
end

function Shared.SelectTab(Index: number)
	Tab = Index
	if Ui then Ui.Tabs:Select(Index, true) end
	Local.Render()
end

function Shared.OnStart()
	Ui = Local.Build()
	task.spawn(Settings.Load) -- apply saved settings on join, even if the menu is never opened
	Settings.Changed.Event:Connect(function(Key)
		if Key == `_saved` and Ui.Panel.Visible and not string.find(Ui.Status.Text, ` is `) then
			Local.Status(`Saved to your profile`, true)
		elseif Key == `_pending` and Ui.Panel.Visible then -- (2.1.3) main menu, no slot loaded yet
			Local.Status(`Kept: saves when you pick a slot`, true)
		end
	end)
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() then return end
		Shared.Toggle()
	end)
end

return Shared
