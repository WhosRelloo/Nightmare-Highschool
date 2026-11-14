--[[
	Identity panel (client): "Name & Clan" + "Spin Shop". Server: Services.Player.Identity, Services.Player.Purchases.
	Config: ReplicatedStorage.Config.Clans, ReplicatedStorage.Config.Shop.

	Name & Clan: sign the register with your first name (the server checks and filters it), and spin
	  your clan (family name). The server rolls; this panel only plays the reel to the result.
	  Height (1.62): your rolled height (Config.Heights) on its own reel, with its spins and pity. A student whose height
	  hasn't been revealed yet (new, or a save from before heights) sees it roll the first time the register opens.
	Spin Shop: Robux developer products for clan / race / variant / trait spins and name changes.
	  Spins go to the student you are playing.

	The main menu docks it on the right while you edit your student (SetStageMode). In school it can
	be opened from anywhere with Identity.OpenTab("Name" | "Shop").
	API: Toggle(on?), OpenTab(name), GetTab(), SetStageMode(on), Reveal(), Prompt(text), HasName(), IsBusy(), FullName(),
	     Get() -> identity, TabChanged (signal: "Name"|"Shop"), Rolled (signal: clanId, rarity), Changed (signal: identity),
     HeightRolled (signal: bandId, rarity), RevealHeight()
]]

---| Services |---

local MarketplaceService = game:GetService(`MarketplaceService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local TweenService = game:GetService(`TweenService`)

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Clans = require(ReplicatedStorage.Config.Clans)
local Heights = require(ReplicatedStorage.Config:WaitForChild(`Heights`))
local Shop = require(ReplicatedStorage.Config.Shop)

local Player = Players.LocalPlayer
local C = Kit.Theme.Colors
local NOTE = C.TextDim:Lerp(C.Text, 0.45) -- TextDim alone is 2.9:1 on the panel; notes need 4.5:1
local Fonts = Kit.Theme.Fonts
local TABS = { `Bloodline`, `Name & Clan`, `Spin Shop` }
local TAB_KEYS = { `Bloodline`, `Name`, `Shop` }
local ROMAN = { `I`, `II`, `III`, `IV`, `V` }

local Local = {}
local Shared = {}

local Ui = nil
local Tab = 2 -- Name & Clan opens first (a new student signs the register)
local StageMode = false
local Ident = nil       -- last identity from the server
local LineSpins = nil   -- Lineage spins { Race, Variant, Trait }
local Busy = false
local StatusToken = 0
local Prices = {}       -- product key -> real Robux price

local TabChangedEvent = Instance.new(`BindableEvent`)
local RolledEvent = Instance.new(`BindableEvent`)
local ChangedEvent = Instance.new(`BindableEvent`)
local HeightRolledEvent = Instance.new(`BindableEvent`)
Shared.TabChanged = TabChangedEvent.Event
Shared.Rolled = RolledEvent.Event
Shared.HeightRolled = HeightRolledEvent.Event -- (bandId, rarity) once the height reel lands
Shared.Changed = ChangedEvent.Event -- fires when your identity (name, clan, spins) changes

-- names are private (never on public attributes), so the menu reads yours from here
local function SetIdent(I)
	Ident = I
	ChangedEvent:Fire(I)
end

---| Helpers |---

function Local.Remote(Name: string): Instance?
	local F = ReplicatedStorage:WaitForChild(`NHIdentity`, 10)
	return F and F:FindFirstChild(Name)
end

function Local.Free(): boolean
	return Clans.FreeInStudio and RunService:IsStudio()
end

function Local.Hex(Color: Color3): string
	return `#{Color:ToHex()}`
end

function Local.Entry(Id: string?)
	local Def = Id and Clans.ById[Id]
	if not Def then return { text = `Unrolled`; sub = `Spin to find out`; color = C.TextDim } end
	return { text = Def.Name; sub = `{Def.Rarity}  ·  {Def.Perk.Name}`; color = Clans.Rarity[Def.Rarity].Color }
end

-- a height on the reel: 6'2" over "Very Tall · Rare", in the rarity's colour (your race's range)
function Local.HeightEntry(P: number?)
	if typeof(P) ~= `number` then return { text = `Unmeasured`; sub = `Spin to find out`; color = C.TextDim } end
	local B = Heights.Band(P)
	local S = Heights.Scale(Player:GetAttribute(`Race`), P)
	return { text = Heights.Text(S); sub = `{B.Name}  ·  {B.Rarity}`; color = Clans.Rarity[B.Rarity].Color }
end

function Local.FreeHeight(): boolean
	return Heights.FreeInStudio and RunService:IsStudio()
end

function Local.FullName(I): string
	local Def = I and I.Clan and Clans.ById[I.Clan]
	local First = if I and I.First ~= `` then I.First else `???`
	local Clan = if Def then Def.Name else `???`
	local Col = if Def then Clans.Rarity[Def.Rarity].Color else C.TextDim
	return `<font color="{Local.Hex(C.Text)}">{First}</font> <font color="{Local.Hex(Col)}">{Clan}</font>`
end

function Local.Status(Text: string, Color: Color3?)
	if not Ui then return end
	StatusToken += 1
	local My = StatusToken
	Ui.Status.Text = Text
	Ui.Status.TextColor3 = Color or C.TextDim
	task.delay(6, function()
		if My == StatusToken and Ui then Ui.Status.Text = `` end
	end)
end

function Local.Fetch()
	local Remote = Local.Remote(`Get`)
	if not Remote then return end
	local Ok, I, Spins = pcall(function() return Remote:InvokeServer() end)
	if Ok and typeof(I) == `table` then LineSpins = Spins SetIdent(I) end
end

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `Identity`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 9
	Gui.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	Gui.Enabled = false
	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(Gui)

	local Panel, PanelApi = Kit.Panel({
		title = `The Register`; Name = `Panel`;
		AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(760, 760); Visible = false; Parent = Gui;
	})
	local Content = PanelApi.Content

	local CloseButton = Kit.Button({
		text = `X`; style = `ghost`; onClick = function() Shared.Toggle(false) end;
		Name = `Close`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 2);
		Size = UDim2.fromOffset(48, 44); Parent = Content;
	})

	local TabsRoot, Tabs = Kit.TabBar({
		tabs = TABS; selected = Tab; textSize = 18;
		onChanged = function(Index)
			Tab = Index
			Local.Render()
			TabChangedEvent:Fire(TAB_KEYS[Index])
		end;
		Name = `Tabs`; Position = UDim2.fromOffset(0, 0); Size = UDim2.new(1, -60, 0, 44); Parent = Content;
	})

	local Options = Instance.new(`ScrollingFrame`)
	Options.Name = `Options`
	Options.BackgroundTransparency = 1
	Options.BorderSizePixel = 0
	Options.Position = UDim2.fromOffset(0, 56)
	Options.Size = UDim2.new(1, 0, 1, -56 - 44)
	Options.CanvasSize = UDim2.new()
	Options.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Options.ScrollBarThickness = 5
	Options.ScrollBarImageColor3 = C.IronDim
	Options.Parent = Content
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, 10)
	Layout.Parent = Options
	local Pad = Instance.new(`UIPadding`)
	Pad.PaddingRight = UDim.new(0, 14)
	Pad.Parent = Options

	local Status = Kit.Text({
		Name = `Status`; Text = ``; TextSize = 18; TextColor3 = NOTE; TextWrapped = true;
		AnchorPoint = Vector2.new(0, 1); Position = UDim2.new(0, 0, 1, 0); Size = UDim2.new(1, 0, 0, 40); Parent = Content;
	})

	local function Refit() task.defer(Local.FitStage) end
	workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(Refit)
	local Scaler = Gui:FindFirstChild(`NHAutoScale`)
	if Scaler then Scaler:GetPropertyChangedSignal(`Scale`):Connect(Refit) end
	Ui = { Gui = Gui; Panel = Panel; Content = Content; Tabs = Tabs; TabsRoot = TabsRoot; Options = Options; Status = Status; Close = CloseButton; Order = 0 }
	Local.ApplyStage()
end

-- In the creator the main menu's letterbox bars cover the top and bottom of the screen:
-- size and centre the docked panel in the space between them (its contents scroll).
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
	Ui.Panel.Size = UDim2.fromOffset(720, Height / S)
	Ui.Panel.Position = UDim2.new(1, -48, 0, ((Top + Bottom) / 2 - InsetY) / S)
end

function Local.ApplyStage()
	if not Ui then return end
	if StageMode then
		Ui.Panel.AnchorPoint = Vector2.new(1, 0.5)
		Ui.Panel.Position = UDim2.new(1, -48, 0.5, 0)
		Ui.Panel.Size = UDim2.fromOffset(720, 740)
		Ui.Close.Visible = false
		-- in the creator the menu's left-hand buttons pick the tab, so the panel's own strip would be a duplicate
		Ui.TabsRoot.Visible = false
		Ui.Options.Position = UDim2.fromOffset(0, 0)
		Ui.Options.Size = UDim2.new(1, 0, 1, -44)
		Local.FitStage()
	else
		Ui.Panel.AnchorPoint = Vector2.new(0.5, 0.5)
		Ui.Panel.Position = UDim2.fromScale(0.5, 0.5)
		Ui.Panel.Size = UDim2.fromOffset(760, 760)
		Ui.Close.Visible = true
		Ui.TabsRoot.Visible = true
		Ui.Options.Position = UDim2.fromOffset(0, 56)
		Ui.Options.Size = UDim2.new(1, 0, 1, -56 - 44)
	end
end

function Local.Next(): number
	Ui.Order += 1
	return Ui.Order
end

function Local.Section(Text: string)
	local Holder = Instance.new(`Frame`)
	Holder.Name = `Section`
	Holder.BackgroundTransparency = 1
	Holder.Size = UDim2.new(1, 0, 0, 40)
	Holder.LayoutOrder = Local.Next()
	Holder.Parent = Ui.Options
	local T = Kit.Text({ Text = string.upper(Text); Font = Fonts.Title; TextSize = 22; TextColor3 = C.Gold; Size = UDim2.new(1, 0, 0, 30); Parent = Holder })
	pcall(Kit.Emboss, T)
	local Rule = Instance.new(`Frame`)
	Rule.BorderSizePixel = 0
	Rule.BackgroundColor3 = C.GoldDeep
	Rule.Position = UDim2.fromOffset(0, 34)
	Rule.Size = UDim2.new(1, 0, 0, 1)
	Rule.Parent = Holder
	local G = Instance.new(`UIGradient`)
	G.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.7, 0.6), NumberSequenceKeypoint.new(1, 1) })
	G.Parent = Rule
	return Holder
end

function Local.Note(Text: string, Color: Color3?, Height: number?)
	return Kit.Text({
		Name = `Note`; Text = Text; RichText = true; TextWrapped = true; TextSize = 18; TextColor3 = if Color == nil or Color == C.TextDim or Color == C.TextFaint then NOTE else Color;
		TextYAlignment = Enum.TextYAlignment.Top; AutomaticSize = Enum.AutomaticSize.Y;
		Size = UDim2.new(1, 0, 0, Height or 22); LayoutOrder = Local.Next(); Parent = Ui.Options;
	})
end

function Local.Row(Height: number)
	local Row = Instance.new(`Frame`)
	Row.Name = `Row`
	Row.BackgroundTransparency = 1
	Row.Size = UDim2.new(1, 0, 0, Height)
	Row.LayoutOrder = Local.Next()
	Row.Parent = Ui.Options
	return Row
end

function Local.Well(Parent: Instance, Props)
	local F = Instance.new(`Frame`)
	F.BackgroundColor3 = C.Ink
	F.BackgroundTransparency = 0.15
	F.BorderSizePixel = 0
	for K, V in Props do F[K] = V end
	local Stroke = Instance.new(`UIStroke`)
	Stroke.Color = C.GoldDeep
	Stroke.Thickness = 1
	Stroke.Transparency = 0.25
	Stroke.Parent = F
	local Corner = Instance.new(`UICorner`)
	Corner.CornerRadius = UDim.new(0, 3)
	Corner.Parent = F
	F.Parent = Parent
	return F, Stroke
end

---| Name & Clan |---

function Local.NameTab()
	local I = Ident
	Local.Section(`Sign the register`)

	-- the big name plate: First Clan
	local Plate = Local.Row(96)
	local Big = Kit.Text({
		Name = `FullName`; Text = Local.FullName(I); RichText = true; Font = Fonts.Title; TextSize = 50;
		TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 62); Parent = Plate;
	})
	pcall(Kit.Emboss, Big)
	local Def = I and I.Clan and Clans.ById[I.Clan]
	Kit.Text({
		Name = `Tag`; Text = if Def then `{string.upper(Def.Rarity)} CLAN  ·  1 in {math.max(1, math.floor(100 / Clans.Chance(Def.Id) + 0.5))}` else ``;
		Font = Fonts.Title; TextSize = 19; TextColor3 = if Def then Clans.Rarity[Def.Rarity].Color else NOTE;
		TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 64); Size = UDim2.new(1, 0, 0, 24); Parent = Plate;
	})
	Ui.Big = Big

	-- first name input
	local Row = Local.Row(60)
	local Field, Stroke = Local.Well(Row, { Name = `Field`; Size = UDim2.new(1, -190, 1, 0) })
	local Box = Instance.new(`TextBox`)
	Box.Name = `FirstName`
	Box.BackgroundTransparency = 1
	Box.ClearTextOnFocus = false
	Box.Font = Fonts.Title
	Box.TextSize = 30
	Box.TextColor3 = C.Text
	Box.PlaceholderText = `First name`
	Box.PlaceholderColor3 = C.TextFaint
	Box.Text = if I and I.First ~= `` then I.First else ``
	Box.TextXAlignment = Enum.TextXAlignment.Left
	Box.Position = UDim2.fromOffset(16, 0)
	Box.Size = UDim2.new(1, -32, 1, 0)
	Box.Parent = Field
	Ui.Box = Box
	local Locked = I and I.Locked
	local CanEdit = not Locked or (I and I.NameChanges > 0)
	Box.TextEditable = CanEdit
	Box.Focused:Connect(function() Stroke.Color = C.Gold end)
	Box:GetPropertyChangedSignal(`Text`):Connect(function()
		if #Box.Text > Clans.Name.Max + 4 then Box.Text = Box.Text:sub(1, Clans.Name.Max + 4) end
		if Ui and Ui.Big then
			local Preview = table.clone(Ident or {})
			Preview.First = if Box.Text:match(`%S`) then Box.Text else ``
			Ui.Big.Text = Local.FullName(Preview)
		end
	end)
	Box.FocusLost:Connect(function(Enter)
		Stroke.Color = C.GoldDeep
		if Enter then Local.SubmitName() end
	end)
	local _, SignApi = Kit.Button({
		text = if Locked then `Rename` else `Sign`; style = `gold`; textSize = 24;
		onClick = function() Local.SubmitName() end; enabled = CanEdit;
		Name = `Sign`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 0); Size = UDim2.fromOffset(176, 60); Parent = Row;
	})
	Ui.Sign = SignApi

	Local.Note(if Locked
		then `Enrolled. Renames left: <b>{I.NameChanges}</b>. A Name Change from the Spin Shop adds one.`
		else `{Clans.Name.Min}-{Clans.Name.Max} letters. A space, ' or - may go between letters. You can change it freely until you enter school.`,
		C.TextFaint)

	-- clan
	Local.Section(`Your clan`)
	local ReelRow = Local.Row(96)
	local _, Reel = Kit.SpinReel({ entry = Local.Entry(I and I.Clan); height = 84; textSize = 40; Size = UDim2.new(1, 0, 0, 92); Parent = ReelRow })
	Ui.Reel = Reel
	local Burst = Kit.Text({
		Name = `Burst`; Text = ``; Font = Fonts.Title; TextSize = 64; TextTransparency = 1;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(1, 0, 1, 0); ZIndex = 20; Parent = ReelRow;
	})
	Ui.Burst = Burst

	local Buttons = Local.Row(52)
	local SpinCount = if Local.Free() then `free` else tostring(I and I.Spins or 0)
	local _, SpinApi = Kit.Button({
		text = `Spin clan ({SpinCount})`; style = `crimson`; textSize = 22;
		onClick = function() Local.Spin() end;
		Name = `Spin`; Size = UDim2.new(0.5, -6, 1, 0); Parent = Buttons;
	})
	Ui.SpinButton = SpinApi
	Kit.Button({
		text = `Get more spins`; textSize = 20;
		onClick = function() Shared.OpenTab(`Shop`) end;
		Name = `More`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.fromScale(1, 0); Size = UDim2.new(0.5, -6, 1, 0); Parent = Buttons;
	})

	if Def then
		Local.Note(`<i>{Def.Text}</i>`, C.Text)
		Local.Note(`<b>{Def.Perk.Name}.</b> {Def.Perk.Text}`, C.TextDim)
	end

	-- pity meter
	local PityRow = Local.Row(34)
	-- (audit) the guarantee is the spin after Pity.Spins misses (server Identity.Roll): count that spin too
	local Left = math.max(1, Clans.Pity.Spins + 1 - (I and I.Pity or 0))
	Kit.Text({ Text = `{Clans.Pity.MinRarity} or better guaranteed within <b>{Left}</b> spin{if Left == 1 then `` else `s`}`; RichText = true; TextSize = 18; TextColor3 = NOTE; Size = UDim2.new(1, 0, 0, 22); Parent = PityRow })
	local Track = Local.Well(PityRow, { Name = `Track`; Position = UDim2.fromOffset(0, 24); Size = UDim2.new(1, 0, 0, 8) })
	local Fill = Instance.new(`Frame`)
	Fill.BorderSizePixel = 0
	Fill.BackgroundColor3 = Clans.Rarity[Clans.Pity.MinRarity].Color
	Fill.Size = UDim2.fromScale(math.clamp((I and I.Pity or 0) / Clans.Pity.Spins, 0, 1), 1)
	Fill.Parent = Track

	-- height
	Local.HeightSection(I)

	-- odds
	Local.Section(`Odds`)
	for N = #Clans.RarityOrder, 1, -1 do
		local Rarity = Clans.RarityOrder[N]
		local List = Clans.ByRarity[Rarity]
		if List then
			local Names = {}
			for _, Clan in List do table.insert(Names, Clan.Name) end
			local Col = Clans.Rarity[Rarity].Color
			Local.Note(`<font color="{Local.Hex(Col)}"><b>{Rarity}  {Clans.RarityWeights[Rarity]}%</b></font>   {table.concat(Names, `, `)}`, C.TextDim)
		end
	end
	if Local.Free() then Local.Note(`Clan spins are free while testing in Studio.`, C.TextFaint) end
	-- height odds: both ends share each rarity
	Local.Section(`Height odds`)
	local Seen = {}
	for N = #Clans.RarityOrder, 1, -1 do
		local Rarity = Clans.RarityOrder[N]
		local Names, Share = {}, 0
		for _, B in Heights.Bands do
			if B.Rarity == Rarity then table.insert(Names, B.Name) Share += Heights.Chance(B.Id) end
		end
		if #Names > 0 and not Seen[Rarity] then
			Seen[Rarity] = true
			local Col = Clans.Rarity[Rarity].Color
			Local.Note(`<font color="{Local.Hex(Col)}"><b>{Rarity}  {math.floor(Share + 0.5)}%</b></font>   {table.concat(Names, ` or `)}`, C.TextDim)
		end
	end
end

-- your height: its reel, a spin button, the pity meter and your race's range
function Local.HeightSection(I)
	local H = I and I.Height
	Local.Section(`Your height`)
	local ReelRow = Local.Row(96)
	Ui.HeightRow = ReelRow
	local _, Reel = Kit.SpinReel({ entry = Local.HeightEntry(H and H.P); height = 84; textSize = 40; Size = UDim2.new(1, 0, 0, 92); Parent = ReelRow })
	Ui.HReel = Reel
	local Burst = Kit.Text({
		Name = `Burst`; Text = ``; Font = Fonts.Title; TextSize = 64; TextTransparency = 1;
		TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5);
		Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.new(1, 0, 1, 0); ZIndex = 20; Parent = ReelRow;
	})
	Ui.HBurst = Burst
	local Band = H and H.P and Heights.Band(H.P)
	if Band then
		Kit.Text({
			Name = `HeightTag`; Text = `{string.upper(Band.Rarity)} HEIGHT  ·  1 in {Heights.OneIn(Band.Id)}`;
			Font = Fonts.Title; TextSize = 19; TextColor3 = Clans.Rarity[Band.Rarity].Color;
			TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 24); LayoutOrder = Local.Next(); Parent = Ui.Options;
		})
	end
	local Buttons = Local.Row(52)
	local Count = if Local.FreeHeight() then `free` else tostring(H and H.Spins or 0)
	Kit.Button({
		text = `Spin height ({Count})`; style = `crimson`; textSize = 22;
		onClick = function() Local.SpinHeight() end;
		Name = `SpinHeight`; Size = UDim2.new(0.5, -6, 1, 0); Parent = Buttons;
	})
	Kit.Button({
		text = `Get more spins`; textSize = 20;
		onClick = function() Shared.OpenTab(`Shop`) end;
		Name = `MoreHeight`; AnchorPoint = Vector2.new(1, 0); Position = UDim2.fromScale(1, 0); Size = UDim2.new(0.5, -6, 1, 0); Parent = Buttons;
	})
	local R = Heights.Range(Player:GetAttribute(`Race`))
	local Race = Player:GetAttribute(`Race`)
	Local.Note(`{if Race then `{Race}s` else `Students`} stand <b>{Heights.Text(R[1])}</b> to <b>{Heights.Text(R[#R])}</b>. A race spin keeps your place in the range. Height is only for looks.`, C.TextDim)
	local PityRow = Local.Row(34)
	local Left = math.max(1, Heights.Pity.Spins + 1 - (H and H.Pity or 0))
	Kit.Text({ Text = `{Heights.Pity.MinRarity} or better guaranteed within <b>{Left}</b> spin{if Left == 1 then `` else `s`}`; RichText = true; TextSize = 18; TextColor3 = NOTE; Size = UDim2.new(1, 0, 0, 22); Parent = PityRow })
	local Track = Local.Well(PityRow, { Name = `Track`; Position = UDim2.fromOffset(0, 24); Size = UDim2.new(1, 0, 0, 8) })
	local Fill = Instance.new(`Frame`)
	Fill.BorderSizePixel = 0
	Fill.BackgroundColor3 = Clans.Rarity[Heights.Pity.MinRarity].Color
	Fill.Size = UDim2.fromScale(math.clamp((H and H.Pity or 0) / Heights.Pity.Spins, 0, 1), 1)
	Fill.Parent = Track
	if Local.FreeHeight() then Local.Note(`Height spins are free while testing in Studio.`, C.TextFaint) end
end

function Local.SpinHeight()
	if Busy or not Ui or not Ui.HReel then return end
	Busy = true
	Local.Status(`Measuring...`)
	local Remote = Local.Remote(`SpinHeight`)
	local Ok, A, B = pcall(function() return Remote:InvokeServer() end)
	if not (Ok and A) then
		Busy = false
		Local.Status(if Ok then tostring(B) else `Spin failed.`, C.Danger)
		return
	end
	SetIdent(B)
	Local.PlayHeightReel(B.Height.P, function()
		Busy = false
		Local.Render()
	end)
end

-- rolls the height reel through sample heights and lands on P; rarer bands take longer and burst on landing
function Local.PlayHeightReel(P: number, OnDone: (() -> ())?)
	if not (Ui and Ui.HReel and typeof(P) == `number`) then if OnDone then OnDone() end return end
	local Band = Heights.Band(P)
	local Pool = {}
	for _, B in Heights.Bands do
		local Copies = math.max(1, 7 - Clans.Rarity[B.Rarity].Order)
		for K = 1, Copies do table.insert(Pool, Local.HeightEntry(B.From + (B.To - B.From) * (K / (Copies + 1)))) end
	end
	local Order = Clans.Rarity[Band.Rarity].Order
	local Duration = 2.2 + math.max(0, Order - 3) * 0.6
	local Final = Local.HeightEntry(P)
	Final.rarity = Band.Rarity
	local Fired = false
	local function Finish()
		if Fired then return end
		Fired = true
		if OnDone then OnDone() end
	end
	Ui.HReel:Spin(Pool, Final, Duration, function()
		local Col = Clans.Rarity[Band.Rarity].Color
		Local.Status(`You stand {Final.text}. {Band.Name} ({Band.Rarity}).`, Col)
		if Order >= 4 and Ui and Ui.HBurst then
			local Burst = Ui.HBurst
			Burst.Text = string.upper(Band.Name)
			Burst.TextColor3 = Col
			Burst.TextTransparency = 0
			Burst.TextSize = 40
			TweenService:Create(Burst, TweenInfo.new(1.4, Enum.EasingStyle.Quint), { TextSize = 96; TextTransparency = 1 }):Play()
		end
		HeightRolledEvent:Fire(Band.Id, Band.Rarity)
		task.delay(if Order >= 4 then 1.2 else 0.3, Finish)
	end)
	task.delay(Duration + 3, Finish)
end

-- bring the height reel into view (the register scrolls)
function Local.ShowHeight()
	if not (Ui and Ui.HeightRow) then return end
	local O = Ui.Options
	local Y = Ui.HeightRow.AbsolutePosition.Y - O.AbsolutePosition.Y + O.CanvasPosition.Y
	O.CanvasPosition = Vector2.new(0, math.max(0, Y - 60))
end

function Local.SubmitName()
	if Busy or not Ui or not Ui.Box then return end
	local Text = Ui.Box.Text
	if not Text:match(`%S`) then Local.Status(`Write your first name in the register.`, C.Danger) return end
	Busy = true
	Local.Status(`Signing...`)
	local Remote = Local.Remote(`SetName`)
	local Ok, A, B = pcall(function() return Remote:InvokeServer(Text) end)
	Busy = false
	if Ok and A then
		SetIdent(B)
		Local.Render()
		Local.Status(`Signed: {B.First}.`, C.Gold)
	else
		Local.Status(if Ok then tostring(B) else `The register is closed right now, try again.`, C.Danger)
	end
end

function Local.Spin()
	if Busy or not Ui or not Ui.Reel then return end
	Busy = true
	Local.Status(`Spinning...`)
	local Remote = Local.Remote(`SpinClan`)
	local Ok, A, B = pcall(function() return Remote:InvokeServer() end)
	if not (Ok and A) then
		Busy = false
		Local.Status(if Ok then tostring(B) else `Spin failed.`, C.Danger)
		return
	end
	SetIdent(B)
	Local.PlayReel(B.Clan, function()
		Busy = false
		Local.Render()
	end)
end

-- Rolls the reel through every clan and lands on Id; rarer clans take longer and burst on landing.
function Local.PlayReel(Id: string, OnDone: (() -> ())?)
	local Def = Clans.ById[Id]
	if not (Ui and Ui.Reel and Def) then if OnDone then OnDone() end return end
	local Pool = {}
	for _, Clan in Clans.List do
		-- weight the blur toward common names so near-misses on rare ones feel rare
		local Copies = math.max(1, 7 - Clans.Rarity[Clan.Rarity].Order)
		for _ = 1, Copies do table.insert(Pool, Local.Entry(Clan.Id)) end
	end
	local Order = Clans.Rarity[Def.Rarity].Order
	local Duration = 2.4 + math.max(0, Order - 3) * 0.6
	-- rarity on the landing entry: the kit plays the tiered reveal (and the near-miss for Legendary/Cursed)
	local Final = Local.Entry(Id)
	Final.rarity = Def.Rarity
	local Fired = false
	local function Finish()
		if Fired then return end
		Fired = true
		if OnDone then OnDone() end
	end
	Ui.Reel:Spin(Pool, Final, Duration, function()
		local Col = Clans.Rarity[Def.Rarity].Color
		Local.Status(`The {Def.Name} family claims you. ({Def.Rarity})`, Col)
		if Order >= 4 and Ui and Ui.Burst then
			local Burst = Ui.Burst
			Burst.Text = string.upper(Def.Rarity)
			Burst.TextColor3 = Col
			Burst.TextTransparency = 0
			Burst.TextSize = 40
			TweenService:Create(Burst, TweenInfo.new(1.4, Enum.EasingStyle.Quint), { TextSize = 96; TextTransparency = 1 }):Play()
		end
		RolledEvent:Fire(Def.Id, Def.Rarity)
		task.delay(if Order >= 4 then 1.2 else 0.3, Finish)
	end)
	-- (audit) a Render mid-spin (tab switch, Updated) destroys the reel and its tween may never complete, which left
	-- Busy stuck (no more spins or signing): run OnDone anyway once the spin must be over
	task.delay(Duration + 3, Finish)
end

---| Spin Shop |---

function Local.Owned(Group: string): string
	if Group == `Clan` then return if Local.Free() then `free in Studio` else tostring(Ident and Ident.Spins or 0) end
	if Group == `Height` then return if Local.FreeHeight() then `free in Studio` else tostring(Ident and Ident.Height and Ident.Height.Spins or 0) end
	if Group == `NameChange` then return tostring(Ident and Ident.NameChanges or 0) end
	if Group == `Capes` then return `{#((Ident and Ident.Capes) or {})} of 3` end
	local N = LineSpins and LineSpins[Group]
	return if RunService:IsStudio() then `free in Studio` else tostring(N or 0)
end

function Local.ShopTab()
	local Slot = Player:GetAttribute(`Slot`)
	Local.Note(`Spins go to <b>this student</b>{if Slot then ` (Slot {ROMAN[Slot] or Slot})` else ``}. Purchases are in Robux.`, C.TextDim)
	for _, G in Shop.Groups do
		Local.Section(G.Name)
		local Head = Local.Row(44)
		Kit.Text({ Text = G.Text; TextSize = 18; TextColor3 = NOTE; TextWrapped = true; TextYAlignment = Enum.TextYAlignment.Top; Size = UDim2.new(1, -170, 1, 0); Parent = Head })
		Kit.Text({ Text = `You have: <b>{Local.Owned(G.Id)}</b>`; RichText = true; TextSize = 18; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right; AnchorPoint = Vector2.new(1, 0); Position = UDim2.fromScale(1, 0); Size = UDim2.fromOffset(170, 24); Parent = Head })
		local Row = Local.Row(78)
		local List = Instance.new(`UIListLayout`)
		List.FillDirection = Enum.FillDirection.Horizontal
		List.Padding = UDim.new(0, 10)
		List.SortOrder = Enum.SortOrder.LayoutOrder
		List.Parent = Row
		local Count = 0
		for _, P in Shop.Products do if P.Group == G.Id then Count += 1 end end
		local N = 0
		for _, P in Shop.Products do
			if P.Group ~= G.Id then continue end
			N += 1
			Local.ProductCard(Row, P, N, Count)
		end
	end
end

function Local.ProductCard(Row: Instance, P, N: number, Count: number)
	local OnSale = P.ProductId and P.ProductId ~= 0
	local Width = math.min(220, (640 - 10 * (Count - 1)) / Count)
	local Holder = Instance.new(`Frame`)
	Holder.BackgroundTransparency = 1
	Holder.Size = UDim2.fromOffset(Width, 78)
	Holder.LayoutOrder = N
	Holder.Parent = Row
	local Label = if P.Kind == `NameChange` then `1 rename` elseif P.Kind == `Cape` then (P.Cape or `Cape`) else `x{P.Amount}`
	local Price = Prices[P.Key] or P.Price
	local _, Api = Kit.Button({
		text = if OnSale then `{Label}   R$ {Price}` else `{Label}   (not on sale yet)`;
		style = if P.Badge then `gold` else `default`; textSize = if OnSale then 22 else 19;
		enabled = OnSale;
		onClick = function() Local.Buy(P) end;
		Name = P.Key; Position = UDim2.fromOffset(0, 18); Size = UDim2.new(1, 0, 0, 60); Parent = Holder;
	})
	if P.Badge then
		Kit.Text({ Text = string.upper(P.Badge); Font = Fonts.Title; TextSize = 16; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center; Size = UDim2.new(1, 0, 0, 18); Parent = Holder })
	end
	if OnSale and not Prices[P.Key] then
		task.spawn(function()
			local Ok, Info = pcall(function() return MarketplaceService:GetProductInfo(P.ProductId, Enum.InfoType.Product) end)
			if Ok and Info and Info.PriceInRobux then
				Prices[P.Key] = Info.PriceInRobux
				if Api and Api.Root.Parent then Api:SetText(`{Label}   R$ {Info.PriceInRobux}`) end
			end
		end)
	end
end

function Local.Buy(P)
	if not P.ProductId or P.ProductId == 0 then return end
	if not Player:GetAttribute(`Slot`) then Local.Status(`Pick a student first.`, C.Danger) return end
	Local.Status(`Opening the Robux prompt...`)
	local Ok = pcall(function() MarketplaceService:PromptProductPurchase(Player, P.ProductId) end)
	if not Ok then Local.Status(`The shop is closed right now.`, C.Danger) end
end

---| Render |---

function Local.Render()
	if not Ui then return end
	for _, Child in Ui.Options:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	Ui.Order = 0
	Ui.Big, Ui.Box, Ui.Reel, Ui.Burst = nil, nil, nil, nil
	Ui.HReel, Ui.HBurst, Ui.HeightRow = nil, nil, nil
	local Key = TAB_KEYS[Tab]
	if Key == `Bloodline` then
		-- race, variant, passive and traits (Controllers.Gui.Bloodline builds the content)
		local Ok, Bloodline = pcall(require, script.Parent:WaitForChild(`Bloodline`, 5))
		if Ok and Bloodline then
			Bloodline.Build({ Section = Local.Section; Note = Local.Note; Row = Local.Row; Next = Local.Next; Options = Ui.Options;
				Status = Local.Status; Render = Local.Render; OpenTab = Shared.OpenTab })
		end
	elseif Key == `Name` then Local.NameTab() else Local.ShopTab() end
end

-- only a visible register may take the keyboard (a hidden one would swallow every key in school)
function Local.Focus()
	if Ui and Ui.Box and Ui.Gui.Enabled and Ui.Panel.Visible and Ui.Box:IsDescendantOf(Ui.Panel) then
		Ui.Box:CaptureFocus()
	end
end

---| API |---

function Shared.Get() return Ident end
-- "First Clan" in plain text ("" until both exist)
function Shared.FullName(): string
	local Def = Ident and Ident.Clan and Clans.ById[Ident.Clan]
	if not (Ident and Ident.First ~= `` and Def) then return `` end
	return `{Ident.First} {Def.Name}`
end
function Shared.IsBusy(): boolean return Busy end
function Shared.HasName(): boolean return Ident ~= nil and Ident.First ~= `` end
function Shared.GetTab(): string return TAB_KEYS[Tab] end

function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Panel.Visible end
	if On then
		Ui.Gui.Enabled = true
		if not Ident then Local.Fetch() end
		Local.Render()
	end
	Ui.Panel.Visible = On
	if On then task.delay(0.6, Local.FitStage) Local.FitStage() end
	-- a height not revealed yet (a new student, or a save from before heights) rolls the first time the register opens,
	-- unless the clan reveal is playing (it chains into this when it lands)
	if On then
		task.delay(1.2, function()
			if Ui and Ui.Panel.Visible and not Busy and Tab == 2 then Local.MaybeRevealHeight() end
		end)
	end
	-- a hidden name box must never keep the keyboard (it would swallow every key in school)
	if not On and Ui.Box and Ui.Box:IsFocused() then Ui.Box:ReleaseFocus() end
end

function Shared.OpenTab(Name: string)
	local Index = table.find(TAB_KEYS, Name) or table.find(TABS, Name) or 2
	if not Ui then Local.Build() end
	local Changed = Index ~= Tab
	Tab = Index
	pcall(function() Ui.Tabs:Select(Index, true) end)
	Shared.Toggle(true)
	if Changed then TabChangedEvent:Fire(TAB_KEYS[Index]) end
end

function Shared.SetStageMode(On: boolean)
	StageMode = On
	if not Ui then Local.Build() end
	Local.ApplyStage()
end

-- Plays the reel up to your current clan (the free first roll of a new student).
function Shared.Reveal()
	if not Ui then Local.Build() end
	if not Ident then Local.Fetch() end
	if not (Ident and Ident.Clan) then return end
	Shared.OpenTab(`Name`)
	Busy = true
	Local.Status(`Fate is writing your family name...`, C.TextDim)
	task.wait(0.6)
	Local.PlayReel(Ident.Clan, function()
		Busy = false
		Local.Render()
		if not Local.MaybeRevealHeight() then Local.Focus() end
	end)
end

-- plays the height reel up to your height if you haven't seen it yet; true when it started
function Local.MaybeRevealHeight(): boolean
	local H = Ident and Ident.Height
	if Busy or not (H and typeof(H.P) == `number` and not H.Seen) then return false end
	task.spawn(Shared.RevealHeight)
	return true
end

function Shared.RevealHeight()
	if not Ui then Local.Build() end
	if not Ident then Local.Fetch() end
	local H = Ident and Ident.Height
	if not (H and typeof(H.P) == `number`) or Busy then return end
	if Tab ~= 2 or not Ui.Panel.Visible then Shared.OpenTab(`Name`) end
	Busy = true
	Local.ShowHeight()
	Local.Status(`Fate is taking your measure...`, C.TextDim)
	task.wait(0.6)
	Local.PlayHeightReel(H.P, function()
		H.Seen = true
		local Seen = Local.Remote(`SeenHeight`)
		if Seen then Seen:FireServer() end
		Busy = false
		Local.Render()
		Local.ShowHeight()
		Local.Focus()
	end)
end

function Shared.Prompt(Text: string)
	Shared.OpenTab(`Name`)
	Local.Status(Text, C.Danger)
	if not (Ui and Ui.Box) then return end
	Ui.Options.CanvasPosition = Vector2.zero
	-- make it obvious: the name field pulses crimson and the placeholder says what to do
	local Stroke = Ui.Box.Parent:FindFirstChildOfClass(`UIStroke`)
	Ui.Box.PlaceholderText = `Write your first name here`
	if Stroke then
		Stroke.Color = C.Crimson
		Stroke.Thickness = 2
		Stroke.Transparency = 0
		task.spawn(function()
			for _ = 1, 3 do
				TweenService:Create(Stroke, TweenInfo.new(0.35), { Transparency = 0.6 }):Play()
				task.wait(0.35)
				TweenService:Create(Stroke, TweenInfo.new(0.35), { Transparency = 0 }):Play()
				task.wait(0.35)
			end
		end)
	end
	Local.Focus()
end

function Shared.OnStart()
	task.spawn(function()
		local Folder = ReplicatedStorage:WaitForChild(`NHIdentity`, 30)
		if not Folder then return end
		Folder:WaitForChild(`Updated`).OnClientEvent:Connect(function(I, Spins)
			if typeof(I) == `table` then SetIdent(I) end
			if typeof(Spins) == `table` then LineSpins = Spins end
			if Ui and Ui.Panel.Visible and not Busy then Local.Render() end
		end)
	end)
	MarketplaceService.PromptProductPurchaseFinished:Connect(function(UserId, _, Purchased)
		if UserId ~= Player.UserId then return end
		Local.Status(if Purchased then `Thank you! Adding it to your student...` else `Purchase cancelled.`, if Purchased then C.Gold else C.TextDim)
	end)
	-- a new save slot means a new student
	Player:GetAttributeChangedSignal(`Slot`):Connect(function()
		Ident, LineSpins = nil, nil
		if Player:GetAttribute(`Slot`) then task.spawn(Local.Fetch) end
	end)
end

return Shared
