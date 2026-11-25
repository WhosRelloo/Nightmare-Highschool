--[[
	Factions panel (client). Toggle with P or the "Factions" button (left edge, for touch).
	Read-only view of PlayerData.Social: reputation, each faction's rank, standing, initiation,
	perks, mission and leader relationship, plus earned titles (Equip sends SocialAction).
	Everything shown is computed by the server; this file only draws it.
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

---| Modules |---

local Packets = require(ReplicatedStorage.Remotes.Packets)
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local SchoolTime = require(ReplicatedStorage.Functions.SchoolTime)
local StateController = require(script.Parent.Parent.StateController)
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`)) -- NH UI kit
local KitTheme = Kit.Theme

local Player = Players.LocalPlayer
local TOGGLE_KEY = Enum.KeyCode.L -- (2026-11-02 key map: P is Options now)

local TEXT = KitTheme.Colors.Text
local DIM = KitTheme.Colors.TextDim
local CARD_BG = Color3.fromRGB(70, 62, 80) -- tint over the slate texture
local ORDER = { `Vigil`, `CrimsonCourt` }
local REP_ORDER = { `Popularity`, `Intimidation`, `Trust`, `Academics` }

local Local = {}
local Shared = {}

local Ui = nil

---| Helpers |---

function Local.Label(Parent: Instance, Props): TextLabel
	local L = Instance.new(`TextLabel`)
	L.BackgroundTransparency = 1
	L.Font = Props.Font or KitTheme.Fonts.Body
	L.TextSize = math.max(Props.TextSize or 14, 18) + (if L.Font == KitTheme.Fonts.Body then 3 else 0) -- UI audit: >= 18 design px; Garamond runs small
	L.TextStrokeTransparency = 0.75
	L.TextColor3 = Props.Color or TEXT
	L.TextXAlignment = Props.Align or Enum.TextXAlignment.Left
	L.TextWrapped = true
	L.RichText = true
	L.Size = Props.Size or UDim2.new(1, 0, 0, 0)
	L.AutomaticSize = if Props.Size then Enum.AutomaticSize.None else Enum.AutomaticSize.Y
	L.LayoutOrder = Props.Order or 0
	L.Name = Props.Name or `Label`
	L.Text = Props.Text or ``
	L.Parent = Parent
	return L
end

function Local.List(Parent: Instance, Padding: number)
	local Layout = Instance.new(`UIListLayout`)
	Layout.SortOrder = Enum.SortOrder.LayoutOrder
	Layout.Padding = UDim.new(0, Padding)
	Layout.Parent = Parent
end

function Local.Corner(Parent: Instance, Radius: number)
	local C = Instance.new(`UICorner`)
	C.CornerRadius = UDim.new(0, Radius)
	C.Parent = Parent
end

function Local.Pad(Parent: Instance, N: number)
	local P = Instance.new(`UIPadding`)
	P.PaddingTop, P.PaddingBottom = UDim.new(0, N), UDim.new(0, N)
	P.PaddingLeft, P.PaddingRight = UDim.new(0, N), UDim.new(0, N)
	P.Parent = Parent
end

function Local.Bar(Parent: Instance, Order: number, Fraction: number, Color: Color3, Caption: string)
	local Holder = Kit.Bar({ Name = `Bar`; fraction = Fraction; color = Color; caption = Caption; height = 22; LayoutOrder = Order; Parent = Parent })
	return Holder
end

function Local.Hex(C: Color3): string
	return `#{C:ToHex()}`
end

function Local.RelationState(Record): string
	if typeof(Record) ~= `table` or not Record.Met then return `Not met` end
	for _, State in RepConfig.RelationshipStates do
		if (Record.Value or 0) <= State.Max then return State.Name end
	end
	return `Trusted`
end

function Local.RankIndex(Name: string): number
	for Index, Rank in FactionConfig.Ranks do
		if Rank.Name == Name then return Index end
	end
	return 1
end

-- Mission count in the current window (mirrors Factions.MissionStatus on the server).
function Local.MissionCount(Id: string, M): number
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if typeof(M) ~= `table` or not Epoch then return 0 end
	local State = SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
	local Current = if Id == `Vigil`
		then `Day{State.Day}`
		elseif State.Segment.Kind == `Class` then `D{State.Day}-S{State.SegmentIndex}` else nil
	return if Current and M.Key == Current and typeof(M.Items) == `table` then #M.Items else 0
end

---| Build |---

function Local.Build()
	local Gui = Instance.new(`ScreenGui`)
	Gui.Name = `FactionsPanel`
	Gui.ResetOnSpawn = false
	Gui.DisplayOrder = 6
	Gui.IgnoreGuiInset = false
	Kit.AutoScale(Gui) -- same design-px scale as every other kit screen

	local Toggle = Kit.Button({
		Name = `Toggle`; text = if UserInputService.KeyboardEnabled then `Factions [L]` else `Factions`; textSize = 16;
		AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 8, 0.5, 0); Size = UDim2.new(0, 132, 0, 44); Parent = Gui;
	})
	-- phones: up a little, so the left column (compass, quest tracker, these two) clears the KitHud bar
	local function PhonePlace()
		local Toggle = Gui:FindFirstChild(`Toggle`)
		if Toggle then Toggle.Position = UDim2.new(0, 8, 0.5, if Kit.Phone and Kit.Phone() then -55 else 0) end
	end
	PhonePlace()
	if Kit.PreviewChanged then Kit.PreviewChanged:Connect(PhonePlace) end
	if workspace.CurrentCamera then workspace.CurrentCamera:GetPropertyChangedSignal(`ViewportSize`):Connect(PhonePlace) end

	-- Ornate kit panel with an engraved title plaque on its top edge.
	local Panel = Instance.new(`Frame`)
	Panel.Name = `Panel`
	Panel.Visible = false
	Panel.AnchorPoint = Vector2.new(0.5, 0.5)
	Panel.Position = UDim2.fromScale(0.5, 0.5)
	Panel.Size = UDim2.new(0.9, 0, 0.82, 0)
	Panel.Parent = Gui
	local Max = Instance.new(`UISizeConstraint`)
	Max.MaxSize = Vector2.new(840, 640)
	Max.Parent = Panel
	Kit.Decorate(Panel, { title = `Who's Who After Dark`; titleSize = 20; titleFlourishWidth = 380 })

	local Close = Kit.Button({
		Name = `Close`; text = `X`; textSize = 18;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -26, 0, 26); Size = UDim2.new(0, 44, 0, 44); Parent = Panel;
	})
	Close.ZIndex = 3

	local Scroll = Instance.new(`ScrollingFrame`)
	Scroll.Name = `Body`
	Scroll.Position = UDim2.new(0, 30, 0, 76)
	Scroll.Size = UDim2.new(1, -60, 1, -104)
	Scroll.BackgroundTransparency = 1
	Scroll.BorderSizePixel = 0
	Scroll.ZIndex = 2
	Scroll.ScrollBarThickness = 5
	Scroll.ScrollBarImageColor3 = KitTheme.Colors.IronDim
	Scroll.CanvasSize = UDim2.new()
	Scroll.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Scroll.Parent = Panel
	Local.List(Scroll, 10)

	Gui.Parent = Player:WaitForChild(`PlayerGui`)
	Toggle.Activated:Connect(function() Shared.Toggle() end)
	Close.Activated:Connect(function() Shared.Toggle(false) end)
	return { Gui = Gui; Panel = Panel; Body = Scroll }
end

-- Kit card: an outer frame carries the art (bracket-corner border, slate fill); the returned
-- inner frame holds the padded, listed content (so layouts don't move the art).
function Local.Card(Parent: Instance, Order: number, Accent: Color3?): Frame
	local Outer = Instance.new(`Frame`)
	Outer.Name = `Card`
	Outer.LayoutOrder = Order
	Outer.Size = UDim2.new(1, -8, 0, 0)
	Outer.AutomaticSize = Enum.AutomaticSize.Y
	Outer.Parent = Parent
	Kit.Decorate(Outer, {
		ornament = `slot`; shadow = false; bgColor = CARD_BG;
		frameColor = if Accent then Accent:Lerp(KitTheme.Colors.RowFrame, 0.35) else KitTheme.Colors.RowFrame;
	})
	local Card = Instance.new(`Frame`)
	Card.BackgroundTransparency = 1
	Card.Size = UDim2.new(1, 0, 0, 0)
	Card.AutomaticSize = Enum.AutomaticSize.Y
	Card.ZIndex = 2
	Card.Parent = Outer
	Local.Pad(Card, 16)
	Local.List(Card, 6)
	return Card
end

function Local.FactionCard(Parent: Instance, Order: number, Id: string, Social)
	local Def = FactionConfig.Factions[Id]
	local F = Social.Factions and Social.Factions[Id] or {}
	local Standing = F.Standing or 0
	local Rank = F.Rank or `Outsider`
	local Member = F.Member == true
	local Card = Local.Card(Parent, Order, Def.Color)
	Card.Name = Id

	Kit.Emboss(Local.Label(Card, { Order = 1; Text = Def.Name; Font = Enum.Font.Fantasy; TextSize = 23; Color = Def.Color }), Def.Color:Lerp(Color3.new(0, 0, 0), 0.45), 1.4)
	Local.Label(Card, { Order = 2; Text = `<i>{Def.Tagline}</i>`; TextSize = 13; Color = DIM })

	-- Rank + bar to the next rank
	local Index = Local.RankIndex(Rank)
	local Next = FactionConfig.Ranks[Index + 1]
	local Min = FactionConfig.Ranks[Index].Min
	local Status = if Member then `Member` else `Not a member`
	Local.Label(Card, { Order = 3; Name = `Rank`; Text = `<b>{Rank}</b>  ·  {Status}  ·  {math.floor(Standing)} standing`; TextSize = 15 })
	if Next then
		local Fraction = (Standing - Min) / math.max(1, Next.Min - Min)
		local Caption = `{math.floor(Standing)} / {Next.Min} to {Next.Name}`
		if Next.RequiresMember and not Member then Caption = `Join to reach {Next.Name}` end
		Local.Bar(Card, 4, Fraction, Def.Color, Caption)
	else
		Local.Bar(Card, 4, 1, Def.Color, `Highest rank`)
	end

	-- Joining
	if not Member then
		local Flags = F.Flags or {}
		local Noticed = Standing >= FactionConfig.Ranks[2].Min
		local Done = Def.Initiation and Flags[Def.Initiation.Flag]
		local Tick = function(Ok) return if Ok then `<font color="#7fd28c">✓</font>` else `<font color="#8a8596">○</font>` end
		Local.Label(Card, { Order = 5; TextSize = 13; Text =
			`<b>To join</b>   {Tick(Noticed)} Reach Prospect ({FactionConfig.Ranks[2].Min} standing)   {Tick(Done)} {Def.Initiation.Text}   then talk to {RepConfig.Npcs[Def.Leader].Name}` })
	end

	-- Leader + hangout
	local Record = Social.Relationships and Social.Relationships[Def.Leader]
	local Npc = RepConfig.Npcs[Def.Leader]
	Local.Label(Card, { Order = 6; TextSize = 13; Color = DIM; Text =
		`Leader: <b>{Npc.Name}</b> ({Local.RelationState(Record)})  ·  Hangout: {Def.Hangout}` })
	Local.Label(Card, { Order = 7; TextSize = 13; Text = `<b>Activity:</b> {Def.Activity.Name}. {Def.Activity.Text}` })

	-- Mission
	if Def.Mission then
		local M = F.Missions and F.Missions[Def.Mission.Id]
		local Done = typeof(M) == `table` and M.Done
		local Progress = if Done then `<font color="#7fd28c">Complete</font>`
			elseif Member then `{Local.MissionCount(Id, M)}/3`
			else `<font color="#8a8596">members only</font>`
		Local.Label(Card, { Order = 8; TextSize = 13; Text =
			`<b>Mission: {Def.Mission.Name}</b> ({Progress}). {Def.Mission.Text} Reward: title "{Def.Mission.Reward.Title}".` })
	end

	-- Perks
	local PerkOrder = 9
	for _, RankDef in FactionConfig.Ranks do
		local Perk = Def.Perks and Def.Perks[RankDef.Name]
		if Perk then
			local Has = Member and Index >= Local.RankIndex(RankDef.Name)
			local Need = if RankDef.Name == `Inner Circle` and Def.InnerCircleRequires
				then ` (also needs {Def.InnerCircleRequires.Min} {Def.InnerCircleRequires.Reputation})` else ``
			local Star = if Has then `<font color="` .. Local.Hex(Def.Color) .. `">★</font>` else `☆`
			Local.Label(Card, { Order = PerkOrder; TextSize = 13; Color = if Has then TEXT else DIM; Text =
				`{Star} <b>{Perk.Name}</b> · {RankDef.Name}{Need}: {Perk.Text}` })
			PerkOrder += 1
		end
	end
end

function Local.Render()
	if not Ui or not Ui.Panel.Visible then return end
	local Profile = StateController.GetProfile(false)
	local Social = Profile and Profile.Social
	for _, Child in Ui.Body:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	if typeof(Social) ~= `table` then
		Local.Label(Ui.Body, { Text = `Loading...`; Color = DIM })
		return
	end

	-- Reputation
	local Rep = Local.Card(Ui.Body, 1)
	Rep.Name = `Reputation`
	local TitleText = if Social.Title and Social.Title ~= `` then `  ·  Title: <b>{Social.Title}</b>` else ``
	Local.Label(Rep, { Order = 0; Text = `<b>Reputation</b>{TitleText}`; TextSize = 16 })
	for I, Category in REP_ORDER do
		local Rule = RepConfig.Categories[Category]
		local Value = Social.Reputation and Social.Reputation[Category] or 0
		Local.Bar(Rep, I * 2 - 1, Value / Rule.Max, Color3.fromRGB(120, 110, 160), `{Category}  {math.floor(Value)} / {Rule.Max}`)
		Local.Label(Rep, { Order = I * 2; Text = Rule.Text; TextSize = 12; Color = DIM })
	end

	-- Factions
	for I, Id in ORDER do
		Local.FactionCard(Ui.Body, 1 + I, Id, Social)
	end

	-- Titles
	local Titles = Local.Card(Ui.Body, 10)
	Titles.Name = `Titles`
	Local.Label(Titles, { Order = 0; Text = `<b>Titles</b>`; TextSize = 16 })
	local Owned = if typeof(Social.Titles) == `table` then Social.Titles else {}
	if #Owned == 0 then
		Local.Label(Titles, { Order = 1; Text = `None yet. Faction missions award titles.`; TextSize = 13; Color = DIM })
	end
	for I, Title in Owned do
		local Equipped = Social.Title == Title
		local Button = Kit.Button({
			Name = `Title{I}`; LayoutOrder = I; Size = UDim2.new(0, 260, 0, 44); textSize = 18;
			style = if Equipped then `gold` else `default`;
			text = if Equipped then `{Title}  (equipped)` else `Equip "{Title}"`;
			Parent = Titles;
		})
		Button.Activated:Connect(function()
			Packets.SocialAction:Fire({ Action = `EquipTitle`; Title = if Equipped then `` else Title })
		end)
	end

	-- Rumours
	local Rumours = Local.Card(Ui.Body, 11)
	Rumours.Name = `Rumours`
	Local.Label(Rumours, { Order = 0; Text = `<b>Rumours</b>`; TextSize = 16 })
	for I, Planned in FactionConfig.Planned or {} do
		Local.Label(Rumours, { Order = I; TextSize = 13; Color = DIM; Text = `<b>{Planned.Name}</b>: {Planned.Text}` })
	end
end

---| API |---

function Shared.Toggle(Open: boolean?)
	Ui = Ui or Local.Build()
	if Open == nil then Open = not Ui.Panel.Visible end
	Ui.Panel.Visible = Open
	if Open then Local.Render() end
end

function Shared.OnStart()
	Ui = Local.Build()
	UserInputService.InputBegan:Connect(function(Input, Processed)
		if Processed or Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() then return end
		Shared.Toggle()
	end)
	StateController.ProfileUpdated:Connect(function(_, Action)
		if Action and Action.type == `SetSocial` then Local.Render() end
	end)
end

return Shared
