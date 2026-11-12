--[[
	GamepadControls (client): console controls. Controllers.Gui.GamepadControls

	Combat buttons are in Bind.Keybinds.Config, next to each action's keyboard key (so they run the same action modules):
	  RT strike (hold)   RB heavy   LT block (hold)   LB feint   B dodge   X interact / draw   Y carry / drop
	  D-pad Up grip (or your skateboard)   A jump (Roblox's)
	This module adds what isn't a plain key:
	  LS (L3)       run, a toggle (Shift on a keyboard)
	  RS (R3)       tap: crouch / slide, a toggle (Ctrl), on release. Hold RS and press RT: an uppercut (Ctrl + click),
	                and then no crouch toggle (Player attribute NHPadUppercut while RS is down, read by Combat.M1)
	  D-pad Down    your race's action on a downed body (N)
	  D-pad L / R   the hotbar slot before / after (1-9)
	  View          the quick menu: the phone, journal, factions, report card, students, study group, locker, wardrobe,
	                emotes, transform and night sight (night races), cinematic view, settings, and the controls
	  As a wolf     RT bites (held, it keeps biting), RB leaps
	  Riding        A ollie, X kickflip, LT push, the left stick steers, D-pad Up gets off (Controllers.World.Skateboard)
	Menus: when one opens on a gamepad its first button is selected, the D-pad / left stick moves between buttons, A presses
	and B closes it (Shared.Menus says how for each). The selection outline is the kit's FrameThin in gold. B or View also
	leaves the cinematic view. While a menu is open the player attribute NHPadMenu is set, and Bind.Keybinds ignores the
	pad (no strikes or feints from a menu). Buttons with the attribute NHPadFirst are selected first; NHPadSkip ones never
	are (they can still be reached), like "Leave lesson".
	Lessons (Controllers.Gui.Activities) count as a menu: B is the lesson's own back (Activities.PadBack).
	Button names follow the pad: Xbox or PlayStation (Kit.PadStyle, Kit.KeyName; Settings > Controls picks or reads it).
	Studio: ReplicatedStorage NHGamepadTest treats the session as a gamepad (Components.InputKind).
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local GuiService = game:GetService(`GuiService`)
local ContextActionService = game:GetService(`ContextActionService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Theme = Kit.Theme
local UnPackets = require(ReplicatedStorage.Remotes.UnPackets)

local Player = Players.LocalPlayer
local Shared = {}
local Local = {}

local NIGHT = { Vampire = true; Werewolf = true; Ghoul = true; Wraith = true }

---| controllers (siblings the loader starts; required when first used) |---

local Cache = {}
function Local.Ctl(Path: { string })
	local Key = table.concat(Path, `.`)
	if Cache[Key] ~= nil then return Cache[Key] or nil end
	local M = Player:WaitForChild(`PlayerScripts`):WaitForChild(`Controllers`)
	for _, N in Path do M = M and M:FindFirstChild(N) end
	local Ok, R = pcall(require, M)
	Cache[Key] = if Ok and typeof(R) == `table` then R else false
	return Cache[Key] or nil
end
local function Input() return Local.Ctl({ `Character`, `InputController` }) end

function Local.Pad(): boolean return Kit.InputKind and Kit.InputKind() == `Gamepad` end

-- Menus B can close: gui name -> how. Anything else with a button named Close gets that button selected instead.
Shared.Menus = {
	QuestJournal = { `Gui`, `QuestJournal` };
	NHPhone = { `Gui`, `Phone` };
	SettingsMenu = { `Gui`, `SettingsMenu` };
	FactionsPanel = { `Gui`, `FactionsPanel` };
	Wardrobe = { `Gui`, `Wardrobe` };
	NHLocker = { `Gui`, `Locker` };
	NHConcessionMenu = { `Gui`, `Locker`; Fn = `CloseStand` }; -- (inventory audit 1.90) B closes the stand, not the Locker
	NHStudents = { `Gui`, `Students` };
	NHStudyGroup = { `Gui`, `StudyGroup` };
	NHTimetable = { `Gui`, `Timetable` };
	NHReportCard = { `Gui`, `StatsPanel` };
	NHProgress = { `Gui`, `Progress` };
	Identity = { `Gui`, `Identity` };
	NHAdminPanel = { `Gui`, `AdminPanel` };
	NHClassLocker = { `Gui`, `ClassLocker`; Close = `Close` };
	NHEnrollment = { `Gui`, `Enrollment`; Close = `Close` };
	NHEmotes = { `Character`, `Emotes`; Fn = `ToggleMenu` };
	NHGamepadMenu = { Self = true };
	Lesson = { `Gui`, `Activities`; Fn = `PadBack` };
}

---| what's open |---

-- the open menu: a visible direct child panel of an enabled gui, at least 400 design px tall or most of the screen
-- (the HUD, toasts and the study group dock are smaller), or the emote menu / quick menu
local SKIP = { NHTouchControls = true; NHTouchCinematic = true; KitHud = true; Notifications = true; NHTopBar = true;
	NHCompass = true; ClockHud = true; QuestTracker = true; NHExpStrip = true; Freecam = true; Cmdr = true; NHCinematic = true;
	MainMenu = true }
function Local.OpenMenu(): (ScreenGui?, GuiObject?)
	local PG = Player:FindFirstChild(`PlayerGui`)
	if not PG then return nil end
	local Best, BestPanel = nil, nil
	for _, G in PG:GetChildren() do
		if G:IsA(`ScreenGui`) and G.Enabled and not SKIP[G.Name] and not G:GetAttribute(`NHPhonePreviewHost`) then
			for _, P in G:GetChildren() do
				if P:IsA(`GuiObject`) and P.Visible and not P:GetAttribute(`NHNotPanel`) then
					local D = P:GetAttribute(`NHPhoneDesign`)
					local H = if typeof(D) == `Vector2` then D.Y else P.Size.Y.Offset
					local Small = G.Name == `NHEmotes` or G.Name == `NHGamepadMenu` or (G.Name == `NHStudyGroup` and P.Name == `Drawer`)
					if Small or H >= 400 or P.Size.Y.Scale >= 0.6 then
						if not Best or G.DisplayOrder >= Best.DisplayOrder then Best, BestPanel = G, P end
					end
				end
			end
		end
	end
	return Best, BestPanel
end

-- the first button to select in a panel: the top-left visible, active button (ones marked NHPadFirst before the rest;
-- never Close or one marked NHPadSkip)
function Local.FirstButton(Root: Instance): GuiObject?
	local Best, BestKey, BestFirst = nil, math.huge, false
	for _, D in Root:GetDescendants() do
		if D:IsA(`GuiButton`) and D.Visible and D.Active and D.Selectable and D.AbsoluteSize.X > 4 and not D:GetAttribute(`NHPadSkip`) then
			local Shown = true
			local A = D.Parent
			while A and A ~= Root do
				if A:IsA(`GuiObject`) and not A.Visible then Shown = false break end
				A = A.Parent
			end
			if Shown and D.Name ~= `Close` then
				local First = D:GetAttribute(`NHPadFirst`) == true
				local Key = D.AbsolutePosition.Y * 4 + D.AbsolutePosition.X
				if (First and not BestFirst) or (First == BestFirst and Key < BestKey) then Best, BestKey, BestFirst = D, Key, First end
			end
		end
	end
	return Best
end

local Current = { Gui = nil :: ScreenGui?, Panel = nil :: GuiObject? }
local BackBound = false
function Local.Back(_, State)
	if State ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
	local Cine = Local.Ctl({ `Gui`, `Cinematic` })
	if Cine and Cine.IsOn and Cine.IsOn() then Cine.Toggle(false) return Enum.ContextActionResult.Sink end
	if Current.Panel then Local.CloseMenu() return Enum.ContextActionResult.Sink end
	return Enum.ContextActionResult.Pass
end
function Local.MenuTick()
	local G, P = Local.OpenMenu()
	local Cine = Local.Ctl({ `Gui`, `Cinematic` })
	local Want = P ~= nil or (Cine ~= nil and Cine.IsOn ~= nil and Cine.IsOn() == true)
	-- combat ignores the pad while a menu is open (Bind.Keybinds)
	local InMenu = P ~= nil
	if Player:GetAttribute(`NHPadMenu`) ~= (InMenu or nil) then Player:SetAttribute(`NHPadMenu`, InMenu or nil) end
	if Want ~= BackBound then
		BackBound = Want
		if Want then ContextActionService:BindActionAtPriority(`NHMenuBack`, Local.Back, false, 3000, Enum.KeyCode.ButtonB)
		else ContextActionService:UnbindAction(`NHMenuBack`) end
	end
	if G ~= Current.Gui or P ~= Current.Panel then
		pcall(function() GuiService:RemoveSelectionGroup(`NHMenu`) end)
		Current.Gui, Current.Panel = G, P
		if P and Local.Pad() then
			pcall(function() GuiService:AddSelectionParent(`NHMenu`, P) end)
			GuiService.SelectedObject = Local.FirstButton(P)
		elseif not P and GuiService.SelectedObject and not (G and G.Name == `MainMenu`) then
			GuiService.SelectedObject = nil
		end
	elseif P and Local.Pad() then
		-- the selection fell off (the list was rebuilt, a tab changed) or there was nothing to pick yet: pick again
		local S = GuiService.SelectedObject
		if not S or not S:IsDescendantOf(P) or not S.Visible or not S.Selectable then GuiService.SelectedObject = Local.FirstButton(P) end
	end
	-- dialogue replies
	local PG = Player:FindFirstChild(`PlayerGui`)
	local Dlg = PG and PG:FindFirstChild(`Dialogue`)
	if Dlg and Dlg.Enabled and not P and Local.Pad() then
		local S = GuiService.SelectedObject
		if not S or not S:IsDescendantOf(Dlg) then GuiService.SelectedObject = Local.FirstButton(Dlg) end
	end
end

function Local.CloseMenu(): boolean
	local G, P = Current.Gui, Current.Panel
	if not (G and P and G.Parent) then return false end
	local How = Shared.Menus[G.Name]
	if How and How.Self then Shared.ToggleMenu(false) return true end
	if How then
		local M = Local.Ctl({ How[1], How[2] })
		local Fn = M and M[How.Fn or How.Close or `Toggle`]
		if Fn then
			pcall(Fn, false)
			-- the phone held from the hotbar opens itself again: put it away too
			local Char = Player.Character
			if G.Name == `NHPhone` and Char and Char:FindFirstChild(`Phone`) then
				local Hud = Local.Ctl({ `Gui`, `KitHud` })
				local Ui = Hud and Hud.GetUi and Hud.GetUi()
				if Ui and Ui.Hotbar then pcall(function() Ui.Hotbar:Select(nil) end) end
			end
			return true
		end
	end
	-- no known way: select its Close button, so A closes it
	local Close = P:FindFirstChild(`Close`, true)
	if Close and Close:IsA(`GuiButton`) then GuiService.SelectedObject = Close return true end
	return false
end

---| the quick menu (View) |---

local Menu = nil :: ScreenGui?
local MenuGrid = nil :: Frame?
local MenuItems = {}

function Local.Items()
	local Race = Player:GetAttribute(`Race`) or `Human`
	local Items = {
		{ `Phone`, function() local M = Local.Ctl({ `Gui`, `Phone` }) if M and M.Toggle then M.Toggle(true) end end };
		{ `Journal`, function() local M = Local.Ctl({ `Gui`, `QuestJournal` }) if M and M.Toggle then M.Toggle() end end };
		{ `Factions`, function() local M = Local.Ctl({ `Gui`, `FactionsPanel` }) if M and M.Toggle then M.Toggle() end end };
		{ `Report Card`, function() local M = Local.Ctl({ `Gui`, `Progress` }) if M and M.Toggle then M.Toggle(true) end end };
		{ `Students`, function() local M = Local.Ctl({ `Gui`, `Students` }) if M and M.Toggle then M.Toggle() end end };
		{ `Study Group`, function() local M = Local.Ctl({ `Gui`, `StudyGroup` }) if M and M.Toggle then M.Toggle() end end };
		{ `Locker`, function() local M = Local.Ctl({ `Gui`, `Locker` }) if M and M.Toggle then M.Toggle() end end };
		{ `Wardrobe`, function() local M = Local.Ctl({ `Gui`, `Wardrobe` }) if M and M.Toggle then M.Toggle() end end };
		{ `Emotes`, function() local M = Local.Ctl({ `Character`, `Emotes` }) if M and M.ToggleMenu then M.ToggleMenu() end end };
	}
	if NIGHT[Race] then
		table.insert(Items, { `Transform`, function() UnPackets.Action:Fire(`Transform`) end })
		table.insert(Items, { `Night Sight`, function() local M = Local.Ctl({ `Character`, `NightSight` }) if M and M.Toggle then M.Toggle() end end })
	end
	table.insert(Items, { `Cinematic`, function() local M = Local.Ctl({ `Gui`, `Cinematic` }) if M and M.Toggle then M.Toggle(true) end end })
	table.insert(Items, { `Settings`, function() local M = Local.Ctl({ `Gui`, `SettingsMenu` }) if M and M.Toggle then M.Toggle() end end })
	return Items
end

-- the controls list (Kit.PadControls), with this pad's button names
function Local.ControlLines(): { { string } }
	local Out = {}
	for _, C in Kit.PadControls do
		if C[1] == `DPadLeft` then
			table.insert(Out, { `D-pad L / R`, `Hotbar` })
		elseif C[1] == `ButtonSelect` then
			table.insert(Out, { Kit.KeyName(C[1]), `This menu` })
		else
			table.insert(Out, { Kit.KeyName(C[1]), C[2] })
		end
	end
	return Out
end

function Local.BuildMenu()
	local G = Instance.new(`ScreenGui`)
	G.Name = `NHGamepadMenu`
	G.ResetOnSpawn = false
	G.IgnoreGuiInset = true
	G.DisplayOrder = 40
	G.Enabled = false
	Kit.AutoScale(G)
	local Root, Api = Kit.Panel({
		title = `Menu`; Name = `Panel`;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(860, 470);
		Parent = G;
	})
	local Content = Api and Api.Content or Root
	local Grid = Instance.new(`Frame`)
	Grid.Name = `Grid`
	Grid.BackgroundTransparency = 1
	Grid.Size = UDim2.new(0.56, 0, 1, 0)
	Grid.Parent = Content
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(220, 48)
	L.CellPadding = UDim2.fromOffset(10, 10)
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = Grid
	-- the controls, right of the buttons
	local Side = Instance.new(`Frame`)
	Side.Name = `Controls`
	Side.BackgroundTransparency = 1
	Side.Position = UDim2.new(0.6, 0, 0, 0)
	Side.Size = UDim2.new(0.4, 0, 1, 0)
	Side.Parent = Content
	local SL = Instance.new(`UIListLayout`)
	SL.Padding = UDim.new(0, 2)
	SL.SortOrder = Enum.SortOrder.LayoutOrder
	SL.Parent = Side
	for I, C in Local.ControlLines() do
		local T = Instance.new(`TextLabel`)
		T.Name = `Line`
		T.BackgroundTransparency = 1
		T.LayoutOrder = I
		T.Size = UDim2.new(1, 0, 0, 24)
		T.Font = Theme.Fonts.Body
		T.TextSize = Theme.Sizes.TextSmall
		T.TextXAlignment = Enum.TextXAlignment.Left
		T.TextColor3 = Theme.Colors.Text
		T.RichText = true
		T.Text = `<font color="#EBCD78">{C[1]}</font>   {C[2]}`
		T.Parent = Side
	end
	G.Parent = Player:WaitForChild(`PlayerGui`)
	return G, Grid
end

function Local.FillMenu()
	for _, B in MenuItems do B:Destroy() end
	table.clear(MenuItems)
	for I, Item in Local.Items() do
		local B = Kit.Button({
			text = Item[1]; Name = Item[1]; LayoutOrder = I; Size = UDim2.fromOffset(220, 48);
			onClick = function()
				Shared.ToggleMenu(false)
				task.defer(Item[2])
			end;
		})
		B.Parent = MenuGrid
		table.insert(MenuItems, B)
	end
end

function Shared.ToggleMenu(On: boolean?)
	if not Menu then Menu, MenuGrid = Local.BuildMenu() end
	if On == nil then On = not Menu.Enabled end
	if On then
		Local.FillMenu()
		-- the controls list again: the pad (and its button names) may have changed
		local Side = Menu:FindFirstChild(`Controls`, true)
		if Side then
			for I, C in Local.ControlLines() do
				local Lines = {}
				for _, L in Side:GetChildren() do if L:IsA(`TextLabel`) then Lines[L.LayoutOrder] = L end end
				if Lines[I] then Lines[I].Text = `<font color="#EBCD78">{C[1]}</font>   {C[2]}` end
			end
		end
	end
	Menu.Enabled = On
	if not On and Current.Gui == Menu then GuiService.SelectedObject = nil end
end

---| buttons |---

local WolfBite = 0
function Local.OnButton(Io: InputObject, Processed: boolean, Down: boolean)
	local K = Io.KeyCode
	-- (B in menus and the cinematic view: Local.Back; View: the quick menu binding)
	if Processed then return end
	local Char = Player.Character
	local Hum = Char and Char:FindFirstChildWhichIsA(`Humanoid`)
	if not (Char and Hum) then return end
	local IC = Input()
	-- the wolf
	if Char:GetAttribute(`WolfForm`) and (K == Enum.KeyCode.ButtonR2 or K == Enum.KeyCode.ButtonR1) then
		if K == Enum.KeyCode.ButtonR1 then
			if Down then UnPackets.Action:Fire(`WolfLeap`) end
			return
		end
		WolfBite += 1
		if not Down then return end
		local My = WolfBite
		task.spawn(function()
			-- (audit) also stop once R2 is up, the wolf form ends or you respawn: the release that bumps WolfBite can be
			-- swallowed (processed input, form ended mid-hold), and the loop then bit every 0.35 s for the whole session
			local UIS = game:GetService(`UserInputService`)
			while My == WolfBite and Player.Character == Char and Char:GetAttribute(`WolfForm`)
				and UIS:IsGamepadButtonDown(Io.UserInputType, Enum.KeyCode.ButtonR2) do
				UnPackets.Action:Fire(`WolfBite`)
				task.wait(0.35)
			end
		end)
		return
	end
	if not Down then return end
	if Char:GetAttribute(`SkateboardRiding`) then return end -- the board owns the pad while you ride
	if K == Enum.KeyCode.ButtonL3 and IC then
		-- run: the first press holds Shift down, the next lets go (the server can also stop a sprint)
		if IC.IsPressed(`Sprint`) and Hum:GetAttribute(`Sprint`) then
			IC.Press(`Sprint`, false)
		else
			if IC.IsPressed(`Sprint`) then IC.Press(`Sprint`, false) end
			IC.Press(`Sprint`, true)
		end
	elseif K == Enum.KeyCode.DPadDown then
		UnPackets.Action:Fire(`RaceAction`)
	elseif K == Enum.KeyCode.DPadLeft or K == Enum.KeyCode.DPadRight then
		local Hud = Local.Ctl({ `Gui`, `KitHud` })
		local Ui = Hud and Hud.GetUi and Hud.GetUi()
		if Ui and Ui.Hotbar and (Ui.Slots or 0) > 0 then
			local Cur = Ui.Hotbar:GetSelected()
			local Step = if K == Enum.KeyCode.DPadRight then 1 else -1
			local Nxt = if Cur then ((Cur - 1 + Step) % Ui.Slots) + 1 else (if Step > 0 then 1 else Ui.Slots)
			Ui.Hotbar:Select(Nxt)
		end
	end
end

---| the selection outline (kit art) |---

function Local.SelectionImage()
	local PG = Player:WaitForChild(`PlayerGui`)
	local Img = Instance.new(`ImageLabel`)
	Img.Name = `NHSelection`
	Img.BackgroundTransparency = 1
	Img.Image = Theme.Images.FrameThin
	Img.ImageColor3 = Theme.Colors.Gold
	Img.ScaleType = Enum.ScaleType.Slice
	local S = Theme.Slices.FrameThin
	Img.SliceCenter = S.Center
	Img.SliceScale = S.Scale * 0.8
	Img.Size = UDim2.new(1, 8, 1, 8)
	Img.Position = UDim2.fromOffset(-4, -4)
	PG.SelectionImageObject = Img
end

function Shared.OnStart()
	Local.SelectionImage()
	-- View is ours (the quick menu): without this Roblox takes it first and starts selecting the top bar's buttons
	-- (everything on the top bar is in the quick menu). Menus select their own first button (Local.MenuTick).
	pcall(function() GuiService.AutoSelectGuiEnabled = false end)
	-- gamepad buttons (by key code, so Studio's simulated presses count too)
	local function pad(I: InputObject): boolean
		local N = I.KeyCode.Name
		return string.sub(N, 1, 6) == `Button` or string.sub(N, 1, 4) == `DPad`
	end
	UserInputService.InputBegan:Connect(function(I, P) if pad(I) then Local.OnButton(I, P, true) end end)
	UserInputService.InputEnded:Connect(function(I, P) if pad(I) then Local.OnButton(I, P, false) end end)
	-- View opens the quick menu (instead of Roblox's selection toggle)
	ContextActionService:BindActionAtPriority(`NHGamepadMenu`, function(_, State)
		if State ~= Enum.UserInputState.Begin then return Enum.ContextActionResult.Sink end
		local Cine = Local.Ctl({ `Gui`, `Cinematic` })
		if Cine and Cine.IsOn and Cine.IsOn() then Cine.Toggle(false) return Enum.ContextActionResult.Sink end
		if Player:GetAttribute(`InMainMenu`) == true then return Enum.ContextActionResult.Pass end
		if Current.Panel and Current.Gui ~= Menu then Local.CloseMenu() return Enum.ContextActionResult.Sink end
		Shared.ToggleMenu()
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonSelect)
	-- RS: hold it and press RT for an uppercut; a tap on its own toggles crouch / slide (on release, so the uppercut
	-- doesn't crouch you first). Roblox's gamepad camera uses RS to zoom: this takes it over (and passes it on in menus).
	local RsCombo = false
	ContextActionService:BindActionAtPriority(`NHGamepadCrouch`, function(_, State)
		if Current.Panel or Player:GetAttribute(`InMainMenu`) == true then
			Player:SetAttribute(`NHPadUppercut`, nil)
			return Enum.ContextActionResult.Pass
		end
		if State == Enum.UserInputState.Begin then
			RsCombo = false
			Player:SetAttribute(`NHPadUppercut`, true)
			return Enum.ContextActionResult.Sink
		end
		if State ~= Enum.UserInputState.End and State ~= Enum.UserInputState.Cancel then return Enum.ContextActionResult.Sink end
		Player:SetAttribute(`NHPadUppercut`, nil)
		if RsCombo or State == Enum.UserInputState.Cancel then return Enum.ContextActionResult.Sink end
		local Char = Player.Character
		if not Char or Char:GetAttribute(`SkateboardRiding`) then return Enum.ContextActionResult.Sink end
		local IC = Input()
		if IC and IC.Press then IC.Press(`Slide`, not IC.IsPressed(`Slide`)) end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.ButtonR3)
	-- RT while RS is held: that was an uppercut, so letting go of RS doesn't toggle crouch
	UserInputService.InputBegan:Connect(function(I)
		if I.KeyCode == Enum.KeyCode.ButtonR2 and Player:GetAttribute(`NHPadUppercut`) == true then RsCombo = true end
	end)
	task.spawn(function()
		while true do
			task.wait(0.2)
			pcall(Local.MenuTick)
		end
	end)
	Player.CharacterAdded:Connect(function()
		local IC = Input()
		if IC and IC.IsPressed then
			for _, N in { `Sprint`, `Slide` } do if IC.IsPressed(N) then IC.Press(N, false) end end
		end
	end)
end

return Shared
