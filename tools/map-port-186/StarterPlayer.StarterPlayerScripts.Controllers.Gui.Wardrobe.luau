--[[
	Wardrobe (client, NH UI kit): make your student. Toggle with K or the "Wardrobe" button.
	Opens by itself the first time a player joins a live game (never in Studio).
	Tabs: Look (style, skin) | Face (eye shape, eye set, eye colour) | Hair (style, catalog hair id, colour)
	      | Outfit (Roblox outfit or the NH uniform).  Race lives in the Bloodline tab (Controllers.Gui.Bloodline).
	Main menu hooks: Shared.TabChanged (signal, tab name), Shared.SetStageMode(on) (no built-in preview,
	panel on the right, for a real 3D character on screen), Shared.OpenTab(name). It never opens by itself
	while Player:GetAttribute("InMainMenu") is true.
	The preview on the left is your live character; the server applies each change
	(ReplicatedStorage.UI.Appearance) and saves it to your profile. Cosmetic tabs never touch race:
	race is only ever rolled by the server (ReplicatedStorage.Lineage).
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

---| Modules |---

local UI = ReplicatedStorage:WaitForChild(`UI`)
local Kit = require(UI:WaitForChild(`Components`))
local Appearance = require(UI:WaitForChild(`Appearance`))
local CliqueConfig = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Config`):WaitForChild(`Cliques`)) -- Clique Looks (1.28)

local Player = Players.LocalPlayer
local C = Kit.Theme.Colors
local TOGGLE_KEY = Enum.KeyCode.K -- unused: the wardrobe opens from locker-room stations
local AtStation: Instance? = nil
local Mode = `Full` -- `Full` (creator / first look), `Outfit` (locker-room wardrobe), `Barber` (hair only)
local FirstLook = false
local TABS = { `Look`, `Face`, `Hair`, `Outfit`, `Accessories`, `Admin`, `Bloodline` } -- (Map, 1.65) Bloodline: the full game's tab (Controllers.Gui.Bloodline) -- Admin: staff only (Appearance.IsStaff; the server checks too) -- race, variant and traits live in the Bloodline tab (Controllers.Gui.Bloodline)

local Local = {}
local Shared = {}

local Ui = nil
local Data = table.clone(Appearance.Defaults)
local Loaded = false -- true once Data holds the CURRENT profile's saved look (never save Defaults over it)
local Profiles = nil -- StateController (for spotting a save-slot swap)
local SeenProfile = nil
local Reloading = false
local Tab = 1
local Spinning = false
local StatusToken = 0
local StageMode = false
local TabChangedEvent = Instance.new(`BindableEvent`)
Shared.TabChanged = TabChangedEvent.Event -- fires (tabName) whenever the tab changes

---| Build |---

-- Your student's name (Identity, private to you); "a new student" until you sign it
function Local.StudentName(): string
	local Module = script.Parent:FindFirstChild(`Identity`)
	if Module then
		local Ok, Identity = pcall(require, Module)
		if Ok and Identity and Identity.FullName then
			local Ok2, Name = pcall(Identity.FullName)
			if Ok2 and type(Name) == `string` and Name ~= `` then return Name end
		end
	end
	return `a new student`
end

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `Wardrobe`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 9
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(Gui)

	local Toggle = Kit.Button({
		text = if UserInputService.KeyboardEnabled then `Wardrobe [K]` else `Wardrobe`;
		style = `ghost`; onClick = function() Shared.Toggle() end;
		Name = `Toggle`; AnchorPoint = Vector2.new(0, 0.5);
		-- move up into Settings' slot when the top bar's Menu button replaces that toggle (keyboard)
		Position = if UserInputService.KeyboardEnabled and script.Parent:FindFirstChild(`TopBar`) then UDim2.new(0, 8, 0.5, 130) else UDim2.new(0, 8, 0.5, 182);
		Size = UDim2.fromOffset(150, 44); Parent = Gui;
	})
	Toggle.Visible = false -- the wardrobe lives in the locker rooms now (NHWardrobe stations), no HUD button

	local Panel, PanelApi = Kit.Panel({
		title = `Wardrobe`; Name = `Panel`;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1120, 740); Visible = false; Parent = Gui;
	})
	local Content = PanelApi.Content

	local _, Preview = Kit.CharacterPreview({
		Name = `Preview`;
		backText = `Turn around`;
		onBack = function()
			Spinning = not Spinning
			if Ui then Ui.Preview:SetSpin(Spinning) end
		end;
		footer = `Enrolled as {Local.StudentName()}`;
		player = Player;
		fallback = game:GetService(`StarterPlayer`):FindFirstChild(`StarterCharacter`);
		Position = UDim2.fromOffset(0, 0); Size = UDim2.new(0, 400, 1, 0); Parent = Content;
	})

	Kit.Button({
		text = `X`; style = `ghost`; onClick = function() Shared.Toggle(false) end;
		Name = `Close`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 2);
		Size = UDim2.fromOffset(48, 44); Parent = Content;
	})

	local _, Tabs = Kit.TabBar({
		tabs = TABS; selected = Tab; textSize = 19;
		onChanged = function(Index) Tab = Index; Local.Render(); TabChangedEvent:Fire(TABS[Index]) end;
		Name = `Tabs`; Position = UDim2.fromOffset(424, 0); Size = UDim2.new(1, -482, 0, 44); Parent = Content;
	})

	local Options = Instance.new(`ScrollingFrame`)
	Options.Name = `Options`
	Options.BackgroundTransparency = 1
	Options.BorderSizePixel = 0
	Options.Position = UDim2.fromOffset(424, 56)
	Options.Size = UDim2.new(1, -424, 1, -56 - 56)
	Options.CanvasSize = UDim2.new()
	Options.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Options.ScrollBarThickness = 5
	Options.ScrollBarImageColor3 = C.IronDim
	Options.Parent = Content
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = Options
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingRight = UDim.new(0, 12)
	Pad.Parent = Options

	local Status = Kit.Text({
		Name = `Status`; Text = ``; TextSize = 18; TextColor3 = C.TextDim;
		AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 424, 1, 0); Size = UDim2.new(1, -424 - 176, 0, 44); Parent = Content;
	})
	Kit.Button({
		text = `Done`; style = `gold`; onClick = function() Shared.Toggle(false) end;
		Name = `Done`; AnchorPoint = Vector2.new(1, 1); Position = UDim2.fromScale(1, 1);
		Size = UDim2.fromOffset(160, 44); Parent = Content;
	})

	Kit.FitToScreen(Panel)
	return { Gui = Gui; Toggle = Toggle; Panel = Panel; PanelApi = PanelApi; Options = Options; Status = Status; Preview = Preview; Tabs = Tabs;
		TabsRoot = Content:FindFirstChild(`Tabs`); PreviewRoot = Content:FindFirstChild(`Preview`) }
end

-- Normal: centred, preview on the left. Stage mode (main menu): no preview, narrower panel on the right.
function Local.ApplyLayout()
	if not Ui then return end
	-- docked on the right: the main-menu creator, and wardrobe stations / the barber (where the world camera
	-- frames you beside the panel, Local.StationCamera); otherwise the centred panel with its own preview
	local Docked = StageMode or AtStation ~= nil
	local Left = if Docked then 0 else 424
	Ui.Panel:SetAttribute(`DesignSize`, Vector2.new(if Docked then 720 else 1120, 740))
	Ui.Panel.AnchorPoint = if Docked then Vector2.new(1, 0.5) else Vector2.new(0.5, 0.5)
	Ui.Panel.Position = if Docked then UDim2.new(1, -48, 0.5, 0) else UDim2.fromScale(0.5, 0.5)
	if Ui.PreviewRoot then Ui.PreviewRoot.Visible = not Docked end
	if Ui.TabsRoot then
		Ui.TabsRoot.Position = UDim2.fromOffset(Left, 0)
		Ui.TabsRoot.Size = UDim2.new(1, -Left - 58, 0, 44)
	end
	Ui.Options.Position = UDim2.fromOffset(Left, 56)
	Ui.Options.Size = UDim2.new(1, -Left, 1, -56 - 56)
	Ui.Status.Position = UDim2.new(0, Left, 1, 0)
	Ui.Status.Size = UDim2.new(1, -Left - 176, 0, 44)
	Ui.Toggle.Visible = false -- no HUD button: the wardrobe opens at locker-room stations
end

---| Helpers |---

function Local.Status(Text: string, Ok: boolean?)
	if not Ui then return end
	Ui.Status.Text = Text
	Ui.Status.TextColor3 = if Ok then C.Gold else C.TextDim
end

-- Items are laid out in the order Render creates them.
Local.Seq = 0
function Local.Next(): number
	Local.Seq += 1
	return Local.Seq
end

function Local.Section(Text: string)
	Kit.SectionHeader({ text = Text; LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 34); Parent = Ui.Options })
end

function Local.Note(Text: string, Color: Color3?)
	return Kit.Text({
		Text = Text; TextSize = 18; TextColor3 = Color or C.TextDim; TextWrapped = true; RichText = true;
		Size = UDim2.new(1, -8, 0, 0); AutomaticSize = Enum.AutomaticSize.Y; LayoutOrder = Local.Next(); Parent = Ui.Options;
	})
end

function Local.Row(Height: number?): Frame
	local Row = Instance.new(`Frame`)
	Row.BackgroundTransparency = 1
	Row.Size = UDim2.new(1, -8, 0, Height or 44)
	Row.LayoutOrder = Local.Next()
	Row.Parent = Ui.Options
	local Layout = Instance.new(`UIListLayout`)
	Layout.FillDirection = Enum.FillDirection.Horizontal
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.VerticalAlignment = Enum.VerticalAlignment.Center
	Layout.Padding = UDim.new(0, 8)
	Layout.Parent = Row
	return Row
end

function Local.Swatch(Parent: Instance, Order: number, Color: Color3, Selected: boolean, OnClick: () -> ())
	local B = Instance.new(`TextButton`)
	B.Name = `Swatch{Order}`
	B.Text = ``
	B.AutoButtonColor = false
	B.LayoutOrder = Order
	B.Size = UDim2.fromOffset(56, 44)
	B.BackgroundColor3 = Color
	B.BorderSizePixel = 0
	B.Parent = Parent
	Kit.Slice(`FrameSlot`, if Selected then C.Gold else C.RowFrame, { SliceScale = 0.32, Parent = B })
	if Selected then
		Kit.Image(`Knob`, {
			AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromOffset(16, 16);
			ImageColor3 = C.Gold; ZIndex = 7; Parent = B;
		})
	end
	B.Activated:Connect(OnClick)
	return B
end

function Local.Choice(Parent: Instance, Order: number, Text: string, Selected: boolean, OnClick: () -> (), Width: number?, Icon: string?)
	return Kit.Button({
		text = Text; style = if Selected then `gold` else `default`; textSize = 18; icon = Icon;
		onClick = OnClick; LayoutOrder = Order; Size = UDim2.fromOffset(Width or 150, 44); Parent = Parent;
	})
end

function Local.Saving()
	Local.Status(`Saving...`)
	StatusToken += 1
	local My = StatusToken
	task.delay(1.2, function()
		if My == StatusToken then Local.Status(`Saved to your profile`, true) end
	end)
end

-- Re-read the saved look (first open, or the main menu swapped in another save slot's profile).
function Local.Reload()
	if Reloading then return end
	Reloading = true
	Loaded = false
	Appearance.CancelSend() -- anything still queued belongs to the old profile
	Local.Status(`Loading your look...`)
	task.spawn(function()
		local Saved = Appearance.Fetch()
		SeenProfile = Profiles and Profiles.GetProfile(false) or SeenProfile
		Data = table.clone(Saved)
		Loaded = true
		Reloading = false
		Local.Status(``)
		Local.Render()
	end)
end

-- May edits be saved right now? Not before the saved look is in, nor while another slot's loads.
function Local.Ready(): boolean
	if Profiles then
		local Now = Profiles.GetProfile(false)
		if Now and Now ~= SeenProfile then
			Local.Reload()
			return false
		end
	end
	if not Loaded then
		Local.Status(`Loading your look...`)
		return false
	end
	return true
end

-- Change one or more fields, save, and redraw the tab.
function Local.Set(Key: string | { [string]: any }, Value: any?)
	if not Local.Ready() then return end
	if type(Key) == `table` then
		for K, V in Key do Data[K] = V end
	else
		Data[Key] = Value
	end
	local HairOff = Local.DropForHair()
	Appearance.Send(Data)
	Local.Render()
	Local.Saving()
	if HairOff then Local.Notice(HairOff) end
end

-- A message that stays up (the "Saved" that follows a change would otherwise replace it).
function Local.Notice(Text: string, _Ok: boolean?)
	StatusToken += 1
	Local.Status(Text, true)
end

-- (1.79) the accessories the current hair passes through come off (a hair change at the barber or in the creator);
-- returns what to tell the student, or nil. The server does the same (UI.Appearance).
function Local.DropForHair(): string?
	if type(Data.Acc) ~= `string` or Data.Acc == `` then return nil end
	local AccCfg = require(ReplicatedStorage.Config.Accessories)
	local AccWear = require(UI:WaitForChild(`AccessoryWear`))
	local Worn, Off = AccCfg.Parse(Data.Acc), {}
	for Slot, Id in AccCfg.Parse(Data.Acc) do
		local It = AccCfg.ById[Id]
		if It and not AccWear.FitsHair(It, Data.HairId) then
			Worn[Slot] = nil
			table.insert(Off, It.Name)
		end
	end
	if #Off == 0 then return nil end
	Data.Acc = AccCfg.Join(Worn)
	return `Took off {table.concat(Off, ", ")}: this hair would pass through it.`
end

-- Change a field without redrawing (colour wheel drags).
function Local.SetQuiet(Key: string, Value: any)
	if not Local.Ready() then return end
	Data[Key] = Value
	Appearance.Send(Data)
	Local.Saving()
end

-- Preset swatches + a colour wheel / HEX picker for one colour.
function Local.ColorBlock(Presets: { Color3 }, IndexKey: string, HexKey: string, Current: Color3)
	local Row = Local.Row()
	for Index, Color in Presets do
		Local.Swatch(Row, Index, Color, Data[HexKey] == `` and Data[IndexKey] == Index, function()
			Local.Set({ [IndexKey] = Index, [HexKey] = `` })
		end)
	end
	Kit.ColorPicker({
		value = Current;
		onChanged = function(Color) Local.SetQuiet(HexKey, string.upper(Color:ToHex())) end;
		onReleased = function() task.defer(Local.Render) end;
		LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 196); Parent = Ui.Options;
	})
	if Data[HexKey] ~= `` then
		Local.Note(`Custom colour <font color="#{Data[HexKey]}">#{Data[HexKey]}</font>. Pick a swatch to go back to a preset.`)
	end
end

---| Tabs |---

function Local.LookTab()
	Local.Section(`Look`)
	local Looks = Local.Row()
	local LookText = ``
	for Index, Look in Appearance.Looks do
		if Look.Id == Data.LookStyle then LookText = Look.Text end
		Local.Choice(Looks, Index, Look.Label, Look.Id == Data.LookStyle, function() Local.Set(`LookStyle`, Look.Id) end, 176, Look.Icon)
	end
	Local.Note(`{LookText}  Just a look: your race comes from your Bloodline spin, never the mirror.`)

	Local.Section(`Body`)
	-- body types (2026-11-10): the build (Skinny / Conditioned / Heavy) comes only from training or the admin desk,
	-- so here you only pick male or female; your build carries over (the server enforces both)
	local Build, Step = Appearance.BodyBuild(Data.Body or 1)
	local Genders = Local.Row()
	for I, G in { `Male`, `Female` } do
		local Base = Appearance.BodyFor(G, `Average`, 0)
		local Label = if Appearance.Bodies[Base] then Appearance.Bodies[Base].Name else G
		Local.Choice(Genders, I, Label, Appearance.BodyGender(Data.Body or 1) == G, function()
			-- (1.71) clothes follow the gender: each piece becomes its counterpart, or that gender's default
			local L = table.clone(Data)
			L.Body = Appearance.BodyFor(G, Build, Step) or Base
			if Appearance.BodyGender(Data.Body or 1) ~= G then Appearance.DressForGender(L, Appearance.IsStaff(Player)) end
			Local.Set({ Body = L.Body; Uniform = L.Uniform; Bottoms = L.Bottoms })
		end, 176)
	end
	if Build ~= `Average` then
		local B = Appearance.Bodies[Data.Body or 1]
		Local.Note(`Build: {if B then B.Name else Build}. Your build comes from training.`)
	end

	Local.Section(`Skin`)
	local Race = Player:GetAttribute(`Race`)
	local Palette = Appearance.RacePalette(Race)
	if Palette then
		-- bloodline races (Vampire, Ghoul): only their own tones, no free colour wheel
		local Current = Appearance.NearestColor(Palette, Appearance.SkinColor(Data))
		local Rows = {}
		for Index, Color in Palette do
			local R = math.ceil(Index / 5)
			Rows[R] = Rows[R] or Local.Row()
			Local.Swatch(Rows[R], Index, Color, Color == Current, function()
				Local.Set(`SkinHex`, string.upper(Color:ToHex()))
			end)
		end
		Local.Note(`Your {Race} blood keeps your skin to these tones. In your Roblox outfit, your avatar's own skin shifts to the nearest one.`)
	else
		Local.ColorBlock(Appearance.Skins, `Skin`, `SkinHex`, Appearance.SkinColor(Data))
	end
	if Data.UseAvatar and not Palette then
		Local.Note(`Skin shows with the school uniform (Outfit tab). With your Roblox outfit on, your avatar's skin is kept.`)
	end
end

function Local.FaceTab()
	Local.Section(`Eyes`)
	local Rows = {}
	local EyeN = 0
	for Index, E in Appearance.Eyes do
		if E.Shape == nil then continue end -- no Roblox face (owner, 2026-11-01)
		EyeN += 1
		local R = math.ceil(EyeN / 3)
		Rows[R] = Rows[R] or Local.Row()
		Local.Choice(Rows[R], Index, E.Name, Index == Data.Eyes, function() Local.Set(`Eyes`, Index) end, 184)
	end
	local Painted = Appearance.Eyes[Data.Eyes] and Appearance.Eyes[Data.Eyes].Shape ~= nil
	if Painted then
		Local.Section(`Eye set`)
		local Sets = Local.Row()
		for Index, Name in Appearance.EyeSets do
			Local.Choice(Sets, Index, Name, Index == Data.EyeSet, function() Local.Set(`EyeSet`, Index) end, 184)
		end
		Local.Note(`Female eyes have fuller lashes, a longer wing and a finer brow.`)
		Local.Section(`Eye colour`)
		if Data.LookStyle == `Nightborn` then
			Local.Note(`Nightborn eyes are always crimson.`)
		else
			local Presets = {}
			for _, E in Appearance.EyeColors do table.insert(Presets, E.Color) end
			Local.ColorBlock(Presets, `EyeColor`, `EyeHex`, Appearance.EyeColor(Data))
		end

		Local.Section(`Brows`)
		local BrowRows = {}
		for Index, B in Appearance.Brows do
			local R = math.ceil(Index / 3)
			BrowRows[R] = BrowRows[R] or Local.Row()
			Local.Choice(BrowRows[R], Index, B.Name, Index == Data.Brows, function() Local.Set(`Brows`, Index) end, 184)
		end
		if Appearance.Brows[Data.Brows] and Appearance.Brows[Data.Brows].Style then
			Local.Note(if Data.BrowHex == `` then `Brow colour matches your hair. Pick one below to change it.` else `Custom brow colour.`)
			local BrowPresets = {}
			for _, H in Appearance.HairColors do table.insert(BrowPresets, H.Color) end
			local Row = Local.Row()
			Kit.Button({ text = `Match hair`; style = if Data.BrowHex == `` then `gold` else `default`; textSize = 17;
				onClick = function() Local.Set(`BrowHex`, ``) end; LayoutOrder = 0; Size = UDim2.fromOffset(130, 44); Parent = Row })
			for Index, Color in BrowPresets do
				Local.Swatch(Row, Index, Color, Data.BrowHex == string.upper(Color:ToHex()), function() Local.Set(`BrowHex`, string.upper(Color:ToHex())) end)
			end
			Kit.ColorPicker({
				value = Appearance.BrowColor(Data);
				onChanged = function(Color) Local.SetQuiet(`BrowHex`, string.upper(Color:ToHex())) end;
				onReleased = function() task.defer(Local.Render) end;
				LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 196); Parent = Ui.Options;
			})
		end

		Local.Section(`Mouth`)
		local MouthRows = {}
		local Race = Player:GetAttribute(`Race`)
		local MouthN = 0
		for Index, M in Appearance.Mouths do
			if M.Race and M.Race ~= Race then continue end -- race mouths: your own race only
			MouthN += 1
			local R = math.ceil(MouthN / 3)
			MouthRows[R] = MouthRows[R] or Local.Row()
			Local.Choice(MouthRows[R], Index, M.Name, Index == Data.Mouth, function() Local.Set(`Mouth`, Index) end, 184)
		end
		Kit.Toggle({
			label = `Fuller lips`; value = Data.Lips;
			onChanged = function(V) Local.Set(`Lips`, V) end;
			Name = `Lips`; LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Options;
		})
		-- face marks and bloodline eyes (2026-11-04)
		Local.Section(`Face marks`)
		local MarkRows, MarkN = {}, 0
		for Index, Mk in Appearance.Marks or {} do
			if Mk.Race and Mk.Race ~= Race then continue end
			MarkN += 1
			local R = math.ceil(MarkN / 3)
			MarkRows[R] = MarkRows[R] or Local.Row()
			Local.Choice(MarkRows[R], Index, Mk.Name, Index == (Data.Marks or 1), function() Local.Set(`Marks`, Index) end, 184)
		end
		if Race and Race ~= `Human` then
			Kit.Toggle({
				label = `{Race} eyes`; value = Data.RaceEyes == true;
				onChanged = function(V) Local.Set(`RaceEyes`, V) end;
				Name = `RaceEyes`; LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Options;
			})
			Local.Note(`Your {Race} blood unlocks its own marks, mouths and eyes. They only show while you are a {Race}.`, C.TextFaint)
		end
	else
		Local.Note(`Keeping your Roblox face. Pick a shape above for Nightmare High eyes, brows and mouth.`)
	end
	Local.Note(`When you transform, your eyes and mouth change on their own (vampire, wolf, ghoul, wraith).`, C.TextFaint)
end

function Local.HairTab()
	Local.Section(`Hairstyle`)
	local Styles = Local.Row()
	for Index, Name in Appearance.HairStyles do
		Local.Choice(Styles, Index, Name, Data.HairId == 0 and Index == Data.Hair, function() Local.Set({ Hair = Index, HairId = 0 }) end, 104)
	end
	Local.Note(`Built hairstyles show with the school uniform.`)

	-- the barber's book: the school's own cuts (ReplicatedStorage.NHHairCatalog)
	-- the barber's book, in two sections: Male and Female cuts (from each hair's Group), yours first
	local Book = game:GetService(`ReplicatedStorage`):FindFirstChild(`NHHairCatalog`)
	local Groups = { Male = {}, Female = {} }
	for _, H in (Book and Book:GetChildren()) or {} do
		local G = if H:GetAttribute(`Group`) == `Female` then `Female` else `Male`
		table.insert(Groups[G], H)
	end
	local Order = if Appearance.IsFemale(Data) then { `Female`, `Male` } else { `Male`, `Female` }
	for _, G in Order do
		local Cuts = Groups[G]
		if #Cuts == 0 then continue end
		table.sort(Cuts, function(X, Y) return (X:GetAttribute(`DisplayName`) or X.Name) < (Y:GetAttribute(`DisplayName`) or Y.Name) end)
		Local.Section(`Barber's book · {G}`)
		local BRow
		for N, H in Cuts do
			if (N - 1) % 4 == 0 then BRow = Local.Row() end
			local Id = H:GetAttribute(`AssetId`)
			Local.Choice(BRow, N, H:GetAttribute(`DisplayName`) or H.Name, Data.HairId == Id, function() Local.Set(`HairId`, Id) end, 138)
		end
	end
	Local.Note(`Cuts from the school barber. Hair colour below tints them when "Recolour" is on.`)
	Local.Section(`Catalog hair`)
	local Row = Local.Row()
	local _, Box = Kit.SearchBar({
		placeholder = `Hair accessory ID`; text = if Data.HairId > 0 then tostring(Data.HairId) else ``;
		Name = `HairId`; LayoutOrder = 1; Size = UDim2.fromOffset(250, 44); Parent = Row;
	})
	local Info = nil
	local function Try()
		local Text = string.gsub(Box:Get(), `%D`, ``)
		local Id = tonumber(Text)
		if not Id then
			Info.Text = `Paste the number from a hair's Roblox shop link.`
			return
		end
		Info.Text = `Checking...`
		task.spawn(function()
			local Ok, Name = Appearance.CheckHair(Id)
			if Ok then
				Local.Set(`HairId`, Id)
				Local.Status(`Wearing "{Name}"`, true)
			elseif Info and Info.Parent then
				Info.Text = Name or `That hair couldn't be loaded.`
				Info.TextColor3 = C.Crimson
			end
		end)
	end
	Box.TextBox.FocusLost:Connect(function(Enter) if Enter then Try() end end)
	Kit.Button({ text = `Wear`; style = `gold`; onClick = Try; LayoutOrder = 2; Size = UDim2.fromOffset(110, 44); Parent = Row })
	Kit.Button({ text = `Remove`; enabled = Data.HairId > 0; onClick = function() Local.Set(`HairId`, 0) end; LayoutOrder = 3; Size = UDim2.fromOffset(120, 44); Parent = Row })
	Info = Local.Note(if Data.HairId > 0 then `Wearing catalog hair {Data.HairId}. It replaces your built and avatar hair.` else `Any Roblox hair accessory: paste its ID (the number in the shop link).`)
	Kit.Toggle({
		label = `Recolour catalog hair`; value = Data.TintHair;
		onChanged = function(V) Local.Set(`TintHair`, V) end;
		Name = `TintHair`; LayoutOrder = Local.Next(); Size = UDim2.new(1, -8, 0, 44); Parent = Ui.Options;
	})

	Local.Section(`Hair colour`)
	local Presets = {}
	for _, H in Appearance.HairColors do table.insert(Presets, H.Color) end
	Local.ColorBlock(Presets, `HairColor`, `HairHex`, Appearance.HairColor(Data))
end

function Local.OutfitTab()
	Local.Section(`Outfit`)
	Local.Note(`Change what you wear here. Hair is done at the barber in the hallway.`)
	Local.Section(`Top`)
	-- only clothes you own: civilian ones, school tops from the Enrollment desk / School Store (Services.School.Enrollment)
	local OwnedTops, Enrolled = {}, true
	pcall(function()
		local P = Profiles and Profiles.GetProfile(false)
		local Ident = P and P.Identity
		for _, Id in (Ident and Ident.Uniforms) or {} do OwnedTops[Id] = true end
		OwnedTops.List = (Ident and Ident.Uniforms) or {}
		Enrolled = not (Ident and Ident.Enrolled == false)
	end)
	local Rows = {}
	local Shown = 0
	-- (1.71) only your gender's clothes (and Unisex ones); the admin kit only for staff. What you wear stays listed.
	local Staff = Appearance.IsStaff(Player)
	for Index, U in Appearance.Uniforms do
		if Index ~= Data.Uniform and not Appearance.ClothingAllows(U, Data, Staff) then continue end
		if Appearance.IsSchoolTop(Index) and not Appearance.OwnsTop(OwnedTops.List, U.Id) and Index ~= Data.Uniform then continue end
		Shown += 1
		local R = math.ceil(Shown / 3)
		Rows[R] = Rows[R] or Local.Row()
		Local.Choice(Rows[R], Index, U.Name, Index == Data.Uniform, function() Local.Set(`Uniform`, Index) end, 184)
	end
	Local.Note(if Enrolled then `School uniforms you own, plus your own clothes. More at the School Store.` else `Your own clothes. You'll get a school uniform when you enrol at the Enrollment desk.`)
	Local.Section(`Bottoms`)
	local BRows = {}
	local BShown = 0
	for Index, B in Appearance.BottomsList do
		if Index ~= Data.Bottoms and not Appearance.ClothingAllows(B, Data, Staff) then continue end
		if Appearance.IsSchoolBottom(Index) and not Enrolled and Index ~= Data.Bottoms then continue end
		BShown += 1
		local R = math.ceil(BShown / 3)
		BRows[R] = BRows[R] or Local.Row()
		Local.Choice(BRows[R], Index, B.Name, Index == Data.Bottoms, function() Local.Set(`Bottoms`, Index) end, 184)
	end
	Local.Note(`Shorts, the skirt, rolled sleeves and the PE shirt show your skin colour (Look tab).`)

	-- (1.28, Cliques Phase 3) one click wears a clique's signature look; each is earned by its respect
	-- (Respected standing and its leader's second job: player attribute CliqueReward_<Id>, Social.Cliques)
	Local.Section(`Clique Looks`)
	local LRows = {}
	local LShown = 0
	for _, Id in CliqueConfig.Order do
		local D = CliqueConfig.Defs[Id]
		local L = D and D.SignatureLook
		if L and L.FemaleTop and Appearance.IsFemale(Data) then L = { Top = L.FemaleTop; Bottoms = L.FemaleBottoms or L.Bottoms } end
		local Ti = L and L.Top and Appearance.IndexOf(Appearance.Uniforms, L.Top)
		local Bi = L and L.Bottoms and Appearance.IndexOf(Appearance.BottomsList, L.Bottoms)
		if Ti and Bi then
			LShown += 1
			local R = math.ceil(LShown / 3)
			LRows[R] = LRows[R] or Local.Row()
			local Have = Player:GetAttribute(`CliqueReward_{Id}`) == true
			Local.Choice(LRows[R], LShown, if Have then D.Name else `{D.Name}  (Respected)`, Have and Data.Uniform == Ti and Data.Bottoms == Bi, function()
				if Have then
					Local.Set({ Uniform = Ti; Bottoms = Bi })
				else
					Local.Status(`Earn the respect of {D.Name} first: reach Respected and finish {D.Leader}'s second job.`, false)
				end
			end, 184)
		end
	end
	Local.Note(`Each clique's look unlocks when they respect you. One click wears its top and bottoms together.`)

	Local.Section(`Cape`)
	local Owned = {}
	pcall(function()
		local P = Profiles and Profiles.GetProfile(false)
		for _, K in (P and P.Identity and P.Identity.Capes) or {} do Owned[K] = true end
	end)
	local CRows, CShown = {}, 0
	local CapeStaff = Appearance.IsStaff(Player)
	for Index, Cape in Appearance.Capes or {} do
		-- the admin kit's 3D capes: staff only (the server and WearCape refuse them too), never in the shop
		if Cape.Admin and not CapeStaff then continue end
		local Have = Index == 1 or (Cape.Admin and CapeStaff) or (not Cape.Admin and (Owned[Cape.Id] == true or RunService:IsStudio()))
		CShown += 1
		local R = math.ceil(CShown / 3)
		CRows[R] = CRows[R] or Local.Row()
		Local.Choice(CRows[R], Index, if Have then (Cape.Short or Cape.Name) else `{Cape.Name}  (shop)`, Index == (Data.Cape or 1), function()
			if Have then
				local AccCfg = require(ReplicatedStorage.Config.Accessories)
				local Worn, Off = AccCfg.Parse(Data.Acc), {}
				for S, Id in AccCfg.Parse(Data.Acc) do
					if AccCfg.CapeClash(Cape.Id, AccCfg.ById[Id]) then Worn[S] = nil table.insert(Off, AccCfg.ById[Id].Name) end
				end
				Local.Set({ Cape = Index; Acc = AccCfg.Join(Worn) })
				if #Off > 0 then Local.Notice(`Took off {table.concat(Off, ", ")}: it can't be worn with a cape.`, true) end
			else
				Local.Status(`Buy the {Cape.Name} in the Spin Shop first.`, false)
			end
		end, 184)
	end
	Local.Note(if CapeStaff then `Capes come from the Spin Shop and belong to the student you buy them on; the admin capes are staff-only. They sway as you move.` else `Capes come from the Spin Shop and belong to the student you buy them on. They sway as you move.`)
	-- 3D gear (Config.Gear / Services.Features.Gear): one item per slot, from what you own
	Local.Section(`Gear`)
	local GearCfg = require(game:GetService(`ReplicatedStorage`).Config.Gear)
	local OwnedGear, GearOn = {}, {}
	pcall(function()
		local P = Profiles and Profiles.GetProfile(false)
		local Ident = P and P.Identity
		for _, Id in (Ident and Ident.Gear) or {} do OwnedGear[Id] = true end
		for Slot, Id in (Ident and Ident.GearOn) or {} do GearOn[Slot] = Id end
	end)
	local function equip(Slot, Id)
		task.spawn(function()
			local F = game:GetService(`ReplicatedStorage`):FindFirstChild(`NHGearRemotes`)
			local R = F and F:GetAttribute(`Ready`) and F:FindFirstChild(`Equip`)
			if not R then return end
			local Ok, A, B = pcall(R.InvokeServer, R, Slot, Id)
			if Ok and A then
				GearOn[Slot] = Id
				Local.Status(if Id then `Wearing {GearCfg.ById[Id].Name}` else `Took it off`, true)
				task.delay(0.4, Local.Render)
			elseif Ok then
				Local.Status(B or `Couldn't change that`)
			end
		end)
	end
	local Any = false
	for _, Slot in { `Head`, `Face`, `Neck` } do
		local Row = Local.Row()
		Local.Choice(Row, 0, `No {Slot:lower()} item`, GearOn[Slot] == nil, function() equip(Slot, nil) end, 184)
		local N = 1
		for _, It in GearCfg.Items do
			if It.Slot == Slot and OwnedGear[It.Id] then
				Any = true
				if N % 3 == 0 then Row = Local.Row() end
				Local.Choice(Row, N, It.Name, GearOn[Slot] == It.Id, function() equip(Slot, It.Id) end, 184)
				N += 1
			end
		end
	end
	local Worn = {}
	for _, Id in GearOn do local It = GearCfg.ById[Id] if It then table.insert(Worn, `{It.Name} ({GearCfg.Describe(It)})`) end end
	Local.Note(if #Worn > 0 then table.concat(Worn, `  ·  `) elseif Any then `Pick an accessory for each slot.` else `Find accessories in chests around campus, or buy them at the School Store.`)
end

-- 3D accessories (Config.Accessories, UI.AccessoryWear): a row per slot, from what you own (all of it in Studio).
-- Picking one takes off whatever it can't be worn with (they'd pass through each other) and says so; pieces must
-- fit over your hair. Admin = true items live in the Admin tab (staff only). The server checks all of it again.
function Local.AccessoryRows(AdminKit: boolean)
	local AccCfg = require(ReplicatedStorage.Config.Accessories)
	local AccWear = require(UI:WaitForChild(`AccessoryWear`))
	local Owned = {}
	pcall(function()
		local P = Profiles and Profiles.GetProfile(false)
		for _, Id in (P and P.Identity and P.Identity.Accessories) or {} do Owned[Id] = true end
	end)
	local Worn = AccCfg.Parse(Data.Acc)
	local CapeDef = Appearance.Capes[Data.Cape or 1]
	local Gender = Appearance.BodyGender(Data.Body)
	local Any = false
	local function pick(It)
		if not AccWear.FitsHair(It, Data.HairId) then
			Local.Status(`{It.Name} doesn't fit over this hair. Try another hairstyle at the barber.`, false)
			return
		end
		local New = AccCfg.Resolve(Worn, It.Id)
		local Off = {}
		for S, Id in Worn do
			if New[S] ~= Id and S ~= It.Slot then table.insert(Off, AccCfg.ById[Id].Name) end
		end
		local Change = { Acc = AccCfg.Join(New) }
		if CapeDef and AccCfg.CapeClash(CapeDef.Id, It) then
			Change.Cape = 1
			table.insert(Off, CapeDef.Short or CapeDef.Name)
		end
		Local.Set(Change)
		if #Off > 0 then Local.Notice(`Took off {table.concat(Off, ", ")}: they can't be worn together.`, true) end
	end
	for _, Slot in AccCfg.Slots do
		local List = {}
		for _, It in AccCfg.BySlot[Slot] do
			if (It.Admin == true) ~= AdminKit or not AccCfg.Ready(It) then continue end
			if It.Gender ~= `Unisex` and It.Gender ~= Gender and Worn[Slot] ~= It.Id then continue end
			if not AdminKit and not (Owned[It.Id] or RunService:IsStudio() or Worn[Slot] == It.Id) then continue end
			table.insert(List, It)
		end
		if #List == 0 then continue end
		Any = true
		Local.Section(AccCfg.SlotNames[Slot] or Slot)
		local Row = Local.Row()
		Local.Choice(Row, 0, `None`, Worn[Slot] == nil, function()
			local New = table.clone(Worn)
			New[Slot] = nil
			Local.Set(`Acc`, AccCfg.Join(New))
		end, 184)
		for N, It in List do
			if N % 3 == 0 then Row = Local.Row() end
			local Fits = AccWear.FitsHair(It, Data.HairId)
			Local.Choice(Row, N, if Fits then It.Name else `{It.Name}  (not with this hair)`, Worn[Slot] == It.Id, function() pick(It) end, 184)
		end
	end
	return Any
end

function Local.AccessoriesTab()
	Local.Section(`Accessories`)
	Local.Note(`3D pieces, one per slot. They're bought at the School Store and belong to this student. A few can't be worn together (they'd pass through each other): picking one takes the other off.`)
	if not Local.AccessoryRows(false) then
		Local.Note(`You don't own any accessories yet. Find them at the School Store.`)
	end
end

function Local.AdminTab()
	if not Appearance.IsStaff(Player) then
		Local.Note(`Staff only.`)
		return
	end
	Local.Section(`The Headmaster's Circle`)
	Local.Note(`Admin regalia: staff only, never sold. The server checks it on every change.`)
	if not Local.AccessoryRows(true) then
		Local.Note(`No regalia in the game yet.`)
	end
end

-- (Map, 1.65) the Bloodline tab: race, variant, tier, the race and variant spins, the passive, traits and race looks.
-- The Map has no creator or Student Record, so the full game's Controllers.Gui.Bloodline is shown here instead. Race is
-- still rolled by the server (ReplicatedStorage.Lineage, started by ServerScriptService.NHLineage); nothing is saved.
function Local.BloodlineTab()
	local Ok, Bloodline = pcall(require, script.Parent:WaitForChild(`Bloodline`, 5))
	if not (Ok and Bloodline) then Local.Note(`The bloodline isn't available here.`) return end
	Bloodline.Build({
		Section = Local.Section; Note = Local.Note; Next = Local.Next; Options = Ui.Options;
		-- a plain row (the Bloodline tab places its own children), unlike the wardrobe's horizontal rows
		Row = function(Height: number)
			local Row = Instance.new(`Frame`)
			Row.Name = `Row`
			Row.BackgroundTransparency = 1
			Row.Size = UDim2.new(1, -8, 0, Height)
			Row.LayoutOrder = Local.Next()
			Row.Parent = Ui.Options
			return Row
		end;
		Status = function(Text: string, Color: Color3?)
			if not Ui then return end
			Ui.Status.Text = Text
			Ui.Status.TextColor3 = Color or C.TextDim
		end;
		Render = Local.Render; OpenTab = Shared.OpenTab;
	})
end

---| Render |---

function Local.Render()
	if not Ui or not Ui.Panel.Visible then return end
	for _, Child in Ui.Options:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	Local.Seq = 0
	-- the tabs each mode shows: the creator all of them; a wardrobe station the outfit, accessories and (staff) the Admin
	-- tab; the barber hair only
	local IsStaff = Appearance.IsStaff(Player)
	local Show = if Mode == `Barber` then { Hair = true }
		elseif Mode == `Outfit` then { Outfit = true; Accessories = true; Admin = IsStaff }
		else { Look = true; Face = true; Hair = true; Outfit = true; Accessories = true; Admin = IsStaff; Bloodline = true }
	if not Show[TABS[Tab]] then Tab = if Mode == `Barber` then 3 else 4 end
	local TabBar = Ui.Panel:FindFirstChild(`Tabs`, true)
	if TabBar then
		TabBar.Visible = Mode ~= `Barber`
		local Shown = 0
		for _, N in TABS do if Show[N] then Shown += 1 end end
		local List = TabBar:FindFirstChild(`Tabs`)
		for _, N in TABS do
			local B = List and List:FindFirstChild(N)
			if B and B:IsA(`GuiObject`) then
				B.Visible = Show[N] == true
				B.Size = UDim2.new(1 / math.max(1, Shown), 0, 1, 0)
			end
		end
		if Ui.Tabs and Ui.Tabs.Select then Ui.Tabs:Select(Tab, true) end
	end
	if Ui.PanelApi and Ui.PanelApi.SetTitle then Ui.PanelApi:SetTitle(if Mode == `Barber` then `Barber` else `Wardrobe`) end
	local Build = ({ Local.LookTab, Local.FaceTab, Local.HairTab, Local.OutfitTab, Local.AccessoriesTab, Local.AdminTab, Local.BloodlineTab })[Tab]
	Build()
end

---| API |---

-- At a wardrobe station or the barber, the camera frames you (your hair at the barber, your whole outfit at a
-- wardrobe) in the part of the screen the panel leaves free, and gives your own camera back when you close.
local StationCam = nil :: { Type: Enum.CameraType, Fov: number }?
local StationFaded = nil :: { [BasePart]: number }?
local StationLight = nil :: Attachment?
function Local.StationCamera(On: boolean)
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	if On then
		local Char = Player.Character
		local Root = Char and Char:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Head = Char and Char:FindFirstChild(`Head`) :: BasePart?
		local Ok, Frame = pcall(require, game:GetService(`ReplicatedStorage`):WaitForChild(`Functions`):WaitForChild(`FrameCamera`))
		if not (Root and Ok and Ui) then return end
		local HairShot = Mode == `Barber`
		local Front = Root.CFrame.LookVector * Vector3.new(1, 0, 1)
		Front = if Front.Magnitude > 0.01 then Front.Unit else Vector3.new(0, 0, -1)
		local Target = if HairShot and Head then Head.Position + Vector3.new(0, 0.45, 0) else Root.Position + Vector3.new(0, 0.05, 0)
		local H, Wd = if HairShot then 3.1 else 6.4, if HairShot then 3.4 else 4.6
		local Fov = 40
		local Rect = Frame.FreeRect({ Ui.Panel })
		-- look back at your front from a little to the side and above; pick the first angle nothing blocks
		-- (the barber or a wall standing between the camera and you)
		local Params = RaycastParams.new()
		Params.FilterType = Enum.RaycastFilterType.Exclude
		Params.FilterDescendantsInstances = { Char :: Instance }
		-- NPC bodies don't take raycasts (CanQuery is off), so check other characters against the sight line too
		local function blocker(From: Vector3, To: Vector3): Model?
			local Seg = To - From
			local Len = Seg.Magnitude
			for _, Folder in { workspace:FindFirstChild(`Live`), workspace:FindFirstChild(`NHAmbient`) } do
				for _, M in (Folder and Folder:GetChildren()) or {} do
					local R = M ~= Char and M:IsA(`Model`) and M:FindFirstChild(`HumanoidRootPart`) :: BasePart?
					if R then
						for _, Y in { 1.6, 0, -1.4 } do -- head, chest, hips
							local P = R.Position + Vector3.new(0, Y, 0)
							local T = math.clamp((P - From):Dot(Seg) / (Len * Len), 0, 1)
							if T > 0.05 and (From + Seg * T - P).Magnitude < 2.2 then return M end
						end
					end
				end
			end
			return nil
		end
		local CF, Blocked
		-- the barber stands right in front of you, so a front shot runs into him (camera audit 2026-11-02: the old
		-- first choice ended up inside the barber and faded him into a dark blob). At the barber: a three-quarter
		-- profile from whichever side is more open (the angle that shows a haircut). At a wardrobe: from the front.
		local Angles = { 20, -20, 45, -45, 70, -70, 110, -110, 160 }
		if HairShot then
			local function open(Deg: number): number
				local Dir = CFrame.Angles(0, math.rad(Deg), 0) * Front
				local Hit = workspace:Raycast(Target, Dir * 8, Params)
				return if Hit then (Hit.Position - Target).Magnitude else 8
			end
			local Side = if open(80) >= open(-80) then 1 else -1
			Angles = { 70 * Side, 90 * Side, 55 * Side, 110 * Side, -70 * Side, -90 * Side, 130 * Side, -130 * Side, 160 }
		end
		for _, Deg in Angles do
			local Look = (CFrame.Angles(0, math.rad(Deg), 0) * -Front) + Vector3.new(0, if HairShot then -0.22 else -0.1, 0)
			local Try = Frame.Frame(Target, Look, H, Wd, Rect, Fov)
			local Hit = workspace:Raycast(Target, Try.Position - Target, Params) or blocker(Target, Try.Position)
			if not Hit then CF = Try Blocked = nil break end
			if not CF then CF, Blocked = Try, Hit end
		end
		-- nothing clear: fade whatever is still in the way, just for you, until you close the panel
		StationFaded = {}
		if Blocked then
			local Npc = blocker(Target, CF.Position)
			if Npc then
				for _, P in Npc:GetDescendants() do
					if P:IsA(`BasePart`) and P.LocalTransparencyModifier < 0.75 then
						StationFaded[P] = P.LocalTransparencyModifier
						P.LocalTransparencyModifier = 0.75
					end
				end
			end
			local Ray = workspace:Raycast(Target, CF.Position - Target, Params)
			local Seen = 0
			while Ray and Seen < 6 do
				Seen += 1
				local M = Ray.Instance:FindFirstAncestorOfClass(`Model`)
				local Group = if M and M ~= workspace then M else Ray.Instance
				for _, P in (if Group:IsA(`BasePart`) then { Group } else Group:GetDescendants()) do
					if P:IsA(`BasePart`) and P.LocalTransparencyModifier < 0.75 then
						StationFaded[P] = P.LocalTransparencyModifier
						P.LocalTransparencyModifier = 0.75
					end
				end
				local Skip = Params.FilterDescendantsInstances
				table.insert(Skip, Group)
				Params.FilterDescendantsInstances = Skip
				Ray = workspace:Raycast(Target, CF.Position - Target, Params)
			end
		end
		-- at the barber, the barber himself stands right beside the shot: fade him (just for you) while his book is open
		if HairShot then
			for _, Tagged in game:GetService(`CollectionService`):GetTagged(`NHBarber`) do
				local Npc = Tagged:FindFirstAncestorOfClass(`Model`) or Tagged
				if Root and Npc:IsA(`Model`) and (Npc:GetPivot().Position - Root.Position).Magnitude < 14 then
					for _, P in Npc:GetDescendants() do
						if P:IsA(`BasePart`) and P.LocalTransparencyModifier < 0.85 then
							StationFaded[P] = StationFaded[P] or P.LocalTransparencyModifier
							P.LocalTransparencyModifier = 0.85
						end
					end
				end
			end
		end
		-- a soft warm key light on you (only you see it), so hair and clothes read at night too
		if not StationLight then
			local At = Instance.new(`Attachment`)
			At.Name = `NHStationKey`
			At.Position = Vector3.new(0, 1.2, -1.5)
			local L = Instance.new(`PointLight`)
			L.Color = Color3.fromRGB(255, 226, 190)
			L.Brightness = 1.3
			L.Range = 9
			L.Shadows = false
			L.Parent = At
			At.Parent = Head or Root
			StationLight = At
		end
		local Lease = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Functions`):WaitForChild(`CameraLease`))
		local function shot() game:GetService(`TweenService`):Create(Cam, TweenInfo.new(0.5, Enum.EasingStyle.Quad), { CFrame = CF; FieldOfView = Fov }):Play() end
		if not Lease.Take(`Station`, function() return Ui ~= nil and Ui.Panel.Visible and AtStation ~= nil end, shot) then return end
		StationCam = { Type = Enum.CameraType.Custom; Fov = Fov }
		shot()
	elseif StationCam then
		local Back = StationCam
		StationCam = nil
		for P, Was in StationFaded or {} do if P.Parent then P.LocalTransparencyModifier = Was end end
		StationFaded = nil
		if StationLight then StationLight:Destroy() StationLight = nil end
		require(game:GetService(`ReplicatedStorage`):WaitForChild(`Functions`):WaitForChild(`CameraLease`)).Release(`Station`)
	end
end

function Shared.Toggle(Open: boolean?)
	if not Ui then return end
	if Open == nil then Open = not Ui.Panel.Visible end
	-- outside the main menu it only opens at a wardrobe station (or for a student's very first look)
	if Open and not StageMode and not AtStation and Player:GetAttribute(`InMainMenu`) ~= true and not FirstLook
		and not workspace:GetAttribute(`NHAnywhereWardrobe`) then return end -- (Map preview) opens anywhere
	if not StageMode then Local.ApplyLayout() end
	Ui.Panel.Visible = Open
	if not StageMode then task.defer(Local.StationCamera, Open == true and AtStation ~= nil) end
	if Open and StageMode then
		Local.FitStage()
		task.delay(0.6, Local.FitStage)
	end
	if Open then
		if Ui.Preview and Ui.Preview.SetFooter then Ui.Preview:SetFooter(`Enrolled as {Local.StudentName()}`) end
		Local.Status(``)
		Local.Render()
	end
end

function Shared.OpenTab(Name: string)
	local Index = table.find(TABS, Name)
	if not Index or not Ui then return end
	local Changed = Index ~= Tab
	Tab = Index
	Ui.Tabs:Select(Index, true)
	Shared.Toggle(true)
	if Changed then TabChangedEvent:Fire(Name) end
end

-- Stage mode (main menu creator): fit between the menu's letterbox bars so Done never hides under them.
function Local.FitStage()
	if not (Ui and StageMode) then return end
	local Cam = workspace.CurrentCamera
	if not Cam then return end
	local Scaler = Ui.Gui:FindFirstChild(`NHAutoScale`)
	local S = Scaler and Scaler.Scale or 1
	local Bar = 0
	local Menu = Player.PlayerGui:FindFirstChild(`MainMenu`)
	for _, B in if Menu then Menu:GetChildren() else {} do
		if B.Name == `Letterbox` and B:IsA(`GuiObject`) and B.Visible then Bar = math.max(Bar, B.AbsoluteSize.Y) end
	end
	local InsetY = if Ui.Gui.IgnoreGuiInset then 0 else game:GetService(`GuiService`):GetGuiInset().Y
	local Top = math.max(InsetY, Bar) + 10
	local Bottom = Cam.ViewportSize.Y - Bar - 10
	local Height = math.max(240 * S, math.min(740 * S, Bottom - Top))
	Ui.Panel:SetAttribute(`DesignSize`, Vector2.new(720, Height / S))
	Ui.Panel.Position = UDim2.new(1, -48, 0, ((Top + Bottom) / 2 - InsetY) / S)
end

function Shared.SetStageMode(On: boolean)
	if On then Mode = `Full` end
	StageMode = On == true
	Local.ApplyLayout()
	if StageMode then
		Local.FitStage()
		task.delay(0.6, Local.FitStage) -- the letterbox bars slide in
	end
end

function Shared.GetTab(): string
	return TABS[Tab]
end

-- First person: Roblox hides your own head; hide your painted face strips with it (SurfaceGuis ignore
-- part transparency, so they would otherwise float in front of the camera).
function Local.WatchOwnFace(Character: Model)
	local Head = Character:WaitForChild(`Head`, 10)
	if not Head then return end
	local function Update()
		local Plate = Head:FindFirstChild(`NHFacePlate`)
		if not Plate then return end
		local Hide = Head.LocalTransparencyModifier > 0.5
		for _, Gui in Plate:GetDescendants() do
			if Gui:IsA(`SurfaceGui`) then Gui.Enabled = not Hide end
		end
	end
	Head:GetPropertyChangedSignal(`LocalTransparencyModifier`):Connect(Update)
	Head.ChildAdded:Connect(function(Child)
		if Child.Name == `NHFacePlate` then task.defer(Update) end
	end)
	Update()
end

function Shared.OnStart()
	local function Refit() task.defer(Local.FitStage) end
	workspace:GetPropertyChangedSignal(`CurrentCamera`):Connect(function()
		if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(Refit) end
	end)
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(Refit) end
	Player:GetAttributeChangedSignal(`Race`):Connect(function() Local.Render() end) -- skin palette follows the race
	Player.AttributeChanged:Connect(function(Name) if Name:match(`^CliqueReward_`) then Local.Render() end end) -- Clique Looks unlock
	Player.CharacterAdded:Connect(Local.WatchOwnFace)
	if Player.Character then task.spawn(Local.WatchOwnFace, Player.Character) end
	Ui = Local.Build()
	local Scaler = Ui.Gui:FindFirstChild(`NHAutoScale`)
	if Scaler then Scaler:GetPropertyChangedSignal(`Scale`):Connect(function() task.defer(Local.FitStage) end) end
	task.spawn(function()
		local Ok, StateController = pcall(require, Player.PlayerScripts:WaitForChild(`Controllers`):WaitForChild(`StateController`))
		if Ok then
			Profiles = StateController
			SeenProfile = StateController.GetProfile(false)
		end
		local Saved, New = Appearance.Fetch()
		if Profiles then SeenProfile = Profiles.GetProfile(false) or SeenProfile end
		Data = table.clone(Saved)
		Loaded = true
		Local.Render()
		-- save slots: re-read the look when the main menu swaps in another slot's profile
		-- (Local.Ready also checks on every edit, so a click inside this 1 s gap can't save to the wrong slot)
		task.spawn(function()
			while Profiles do
				task.wait(1)
				local Now = Profiles.GetProfile(false)
				if Now and Now ~= SeenProfile then Local.Reload() end
			end
		end)
		if New and not RunService:IsStudio() and not Player:GetAttribute(`InMainMenu`) then
			FirstLook = true
			Mode = `Full`
			Shared.Toggle(true) -- first visit: make your student
		end
	end)
	-- Wardrobe stations: a locker-room wardrobe's prompt (Services.Features.WardrobeStations) opens it; walking
	-- away closes it. No hotkey any more.
	-- (Map preview) no stations in the Map: K opens the full wardrobe anywhere
	game:GetService(`UserInputService`).InputBegan:Connect(function(Input, Processed)
		if Processed or Input.KeyCode ~= TOGGLE_KEY or not workspace:GetAttribute(`NHAnywhereWardrobe`) then return end
		if game:GetService(`UserInputService`):GetFocusedTextBox() then return end
		AtStation = nil
		Mode = `Full`
		Shared.Toggle()
		if Ui and Ui.Panel.Visible then Local.Render() end
	end)
	game:GetService(`ProximityPromptService`).PromptTriggered:Connect(function(Prompt)
		local IsWardrobe, IsBarber = Prompt:GetAttribute(`NHWardrobe`), Prompt:GetAttribute(`NHBarber`)
		if not (IsWardrobe or IsBarber) then return end
		AtStation = Prompt.Parent
		Mode = if IsBarber then `Barber` else `Outfit`
		Shared.Toggle(true)
		Local.Render()
	end)
	RunService.Heartbeat:Connect(function()
		if not (Ui and Ui.Panel.Visible) or StageMode or not AtStation then return end
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
		-- (audit) the server's own reach test (Appearance.AtTag: WardrobeReach studs from a tagged station), so the
		-- wardrobe never stays open where the server would drop the change
		local Tag = if AtStation:FindFirstChild(`NHBarberPrompt`) then `NHBarber` else `NHWardrobe`
		if not Root or not AtStation.Parent or not Appearance.AtTag(Player, Tag) then
			AtStation = nil
			Mode = `Full`
			Shared.Toggle(false)
		end
	end)
end

return Shared
