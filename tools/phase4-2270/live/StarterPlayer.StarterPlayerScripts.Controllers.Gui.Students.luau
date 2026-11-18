--[[
	Students (client): the game's player list, grouped by faction. Replaces Roblox's default list.

	Replaces Roblox's player list (kept switched off). Closed by default so it's never in the way. Open it with Tab or the top bar's Students button.
	It drops down under the top bar in the top-left corner: a narrow ink plate with a gold rim,
	at most 40% of the screen tall (it scrolls past that), and it closes again with Tab or the button.
	Groups: The Vigil, The Crimson Court, then Unaffiliated (empty groups are hidden). Each row is the
	UI kit's PlayerListRow: student file number, faction seal, full name ("First Clan"), you in gold,
	with the faction rank, title and clan rarity on a second, smaller line.
	Stranger system: students whose name you haven't learned show as "Stranger" (no file number, no
	details). Names come only from Controllers.Gui.Strangers (the server sends each player the names
	they know); faction membership (Faction_<Id> attributes) is public, so groups still show.
	(2.27) Classmates: the rostered students (Config.Students) you've met, from your saved relationships
	(Social.Relationships, sent with SetSocial): their name, clique, how they feel about you, and their bio.
	API: Toggle(on?), IsOpen()
]]

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local StarterGui = game:GetService(`StarterGui`)
local TweenService = game:GetService(`TweenService`)
local UserInputService = game:GetService(`UserInputService`)
local Typing = require(game:GetService(`ReplicatedStorage`):WaitForChild(`Packages`):WaitForChild(`Bind`):WaitForChild(`Typing`)) -- (2.1.0) one "is the player typing?" for every key

---| Modules |---

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local FactionConfig = require(ReplicatedStorage.Config.Factions)
local SportsConfig = require(ReplicatedStorage.Config.Sports)
local StudentsConfig = require(ReplicatedStorage.Config.Students) -- (2.27) the roster
local CliqueConfig = require(ReplicatedStorage.Config.Cliques)
local RepConfig = require(ReplicatedStorage.Config.Reputation)
local StateController = require(script.Parent.Parent.StateController)
local Clans = require(ReplicatedStorage.Config.Clans)
local Strangers = require(script.Parent:WaitForChild(`Strangers`))

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local WIDTH = 300
local TOGGLE_KEY = Enum.KeyCode.Tab

-- Config faction id -> UI kit theme key, in display order
local GROUPS = {
	{ Id = `Vigil`; Theme = `Vigil` };
	{ Id = `CrimsonCourt`; Theme = `Court` };
	{ Id = nil; Theme = nil }; -- unaffiliated
}

local Local = {}
local Shared = {}
local Ui = nil
local Open = false
local Dirty = true

---| Helpers |---

local function new(Class: string, Props, Parent: Instance?)
	local I = Instance.new(Class)
	for K, V in Props do I[K] = V end
	if Parent then I.Parent = Parent end
	return I
end

function Local.FactionOf(P: Player): (string?, string?)
	for _, G in GROUPS do
		if G.Id then
			local Rank = P:GetAttribute(`Faction_{G.Id}`)
			if Rank then return G.Id, Rank end
		end
	end
	return nil, nil
end

function Local.FileNumber(P: Player): number
	return math.abs(P.UserId) % 10000
end

---| Build |---

function Local.Build()
	local Gui = new(`ScreenGui`, {
		Name = `NHStudents`; DisplayOrder = 19; ResetOnSpawn = false; IgnoreGuiInset = true;
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling; Enabled = true;
	}, Player:WaitForChild(`PlayerGui`))
	local Scale = new(`UIScale`, {}, Gui)
	local Plate = new(`CanvasGroup`, {
		Name = `Plate`; BackgroundTransparency = 1; BorderSizePixel = 0;
		Position = UDim2.fromOffset(12, 58); Size = UDim2.fromOffset(WIDTH, 60); Visible = false; GroupTransparency = 1;
	}, Gui)
	-- background on its own layer: a gradient on the CanvasGroup itself would tint the text too
	local Bg = new(`Frame`, { Name = `Bg`; BackgroundColor3 = C.Ink; BackgroundTransparency = 0.15; BorderSizePixel = 0; Size = UDim2.fromScale(1, 1); ZIndex = 0 }, Plate)
	new(`UICorner`, { CornerRadius = UDim.new(0, 6) }, Bg)
	new(`UIStroke`, { Color = C.GoldDeep; Thickness = 1; Transparency = 0.35 }, Bg)
	new(`UIGradient`, { Rotation = 90; Color = ColorSequence.new(Color3.fromRGB(56, 46, 58), Color3.fromRGB(20, 16, 22)) }, Bg)

	local Head = new(`TextLabel`, {
		Name = `Head`; BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextSize = 16; TextColor3 = C.Gold;
		TextXAlignment = Enum.TextXAlignment.Left; Text = `STUDENTS`; Position = UDim2.fromOffset(12, 6); Size = UDim2.new(1, -24, 0, 20);
	}, Plate)
	local Count = new(`TextLabel`, {
		Name = `Count`; BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 15; TextColor3 = C.TextFaint;
		TextXAlignment = Enum.TextXAlignment.Right; Text = ``; Position = UDim2.fromOffset(12, 6); Size = UDim2.new(1, -24, 0, 20);
	}, Plate)
	local Rule = new(`Frame`, { BackgroundColor3 = C.Crimson; BorderSizePixel = 0; Position = UDim2.new(0, 12, 0, 28); Size = UDim2.new(1, -24, 0, 1) }, Plate)
	new(`UIGradient`, { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, Rule)

	local List = new(`ScrollingFrame`, {
		Name = `List`; BackgroundTransparency = 1; BorderSizePixel = 0; Position = UDim2.fromOffset(8, 34);
		Size = UDim2.new(1, -16, 1, -40); CanvasSize = UDim2.new(); AutomaticCanvasSize = Enum.AutomaticSize.Y;
		ScrollBarThickness = 3; ScrollBarImageColor3 = C.IronDim; ScrollingDirection = Enum.ScrollingDirection.Y;
	}, Plate)
	local Layout = new(`UIListLayout`, { SortOrder = Enum.SortOrder.LayoutOrder; Padding = UDim.new(0, 3) }, List)
	new(`UIPadding`, { PaddingRight = UDim.new(0, 4); PaddingBottom = UDim.new(0, 4) }, List)

	Ui = { Gui = Gui; Scale = Scale; Plate = Plate; List = List; Layout = Layout; Count = Count }
	Local.Place()
end

-- under the top bar, scaled like it
function Local.Place()
	if not Ui then return end
	local View = workspace.CurrentCamera and workspace.CurrentCamera.ViewportSize or Vector2.new(1920, 1080)
	local S = math.clamp(View.Y / 1080, 0.8, 1.4)
	Ui.Scale.Scale = S
	local Bar = Player.PlayerGui:FindFirstChild(`NHTopBar`)
	local BarPlate = Bar and Bar:FindFirstChild(`Plate`, true)
	local X = if BarPlate then BarPlate.Position.X.Offset else 12
	Ui.Plate.Position = UDim2.fromOffset(X, 58)
	Ui.MaxHeight = (View.Y * 0.4) / S
end

function Local.Group(Order: number, Def, Members)
	local Theme_ = Theme.Faction(Def.Theme)
	local Name = if Def.Id then (FactionConfig.Factions[Def.Id] and FactionConfig.Factions[Def.Id].Name or Def.Id) else `Unaffiliated`
	local Header = new(`Frame`, { Name = `Group_{Def.Id or `None`}`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 22); LayoutOrder = Order }, Ui.List)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextSize = 15; TextXAlignment = Enum.TextXAlignment.Left;
		TextColor3 = if Def.Id then Theme_.Accent else C.TextDim; Text = string.upper(Name);
		Position = UDim2.fromOffset(4, 4); Size = UDim2.new(1, -40, 1, -4);
	}, Header)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextXAlignment = Enum.TextXAlignment.Right;
		TextColor3 = C.TextFaint; Text = tostring(#Members); Position = UDim2.fromOffset(0, 4); Size = UDim2.new(1, -4, 1, -4);
	}, Header)
	for I, M in Members do
		local Row = new(`Frame`, { Name = `Student`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, if M.Sub ~= `` then 48 else 30); LayoutOrder = Order + I }, Ui.List)
		Kit.PlayerListRow({
			number = if M.Known then Local.FileNumber(M.Player) else nil; name = M.Name; faction = Def.Theme; isLocal = M.Player == Player;
			Size = UDim2.new(1, 0, 0, 30); Parent = Row;
		})
		if M.Sub ~= `` then
			new(`TextLabel`, {
				BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextColor3 = C.TextDim; RichText = true;
				TextXAlignment = Enum.TextXAlignment.Right; Text = M.Sub; TextTruncate = Enum.TextTruncate.AtEnd;
				Position = UDim2.fromOffset(0, 30); Size = UDim2.new(1, -12, 0, 17);
			}, Row)
		end
	end
end

-- (2.27) the rostered students you've met, under the player groups
function Local.Classmates(Order: number): number
	local Profile = StateController.GetProfile(false)
	local Rels = Profile and Profile.Social and Profile.Social.Relationships
	if typeof(Rels) ~= `table` then return 0 end
	local Rows = {}
	for Id, R in Rels do
		local E = StudentsConfig.ById[Id]
		if E and typeof(R) == `table` and R.Met then
			local State = `Trusted`
			for _, St in RepConfig.RelationshipStates do if (R.Value or 0) <= St.Max then State = St.Name break end end
			local Clique = CliqueConfig.Defs[E.Clique]
			table.insert(Rows, { Name = E.Name; Sub = `{Clique and Clique.Name or E.Clique}  ·  {State}  ·  {E.Bio}` })
		end
	end
	if #Rows == 0 then return 0 end
	table.sort(Rows, function(A, B) return A.Name < B.Name end)
	local Header = new(`Frame`, { Name = `Group_Classmates`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 22); LayoutOrder = Order }, Ui.List)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Title; TextSize = 15; TextXAlignment = Enum.TextXAlignment.Left;
		TextColor3 = C.TextDim; Text = `CLASSMATES`; Position = UDim2.fromOffset(4, 4); Size = UDim2.new(1, -40, 1, -4);
	}, Header)
	new(`TextLabel`, {
		BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextXAlignment = Enum.TextXAlignment.Right;
		TextColor3 = C.TextFaint; Text = tostring(#Rows); Position = UDim2.fromOffset(0, 4); Size = UDim2.new(1, -4, 1, -4);
	}, Header)
	for I, M in Rows do
		local Row = new(`Frame`, { Name = `Classmate`; BackgroundTransparency = 1; Size = UDim2.new(1, 0, 0, 48); LayoutOrder = Order + I }, Ui.List)
		Kit.PlayerListRow({ name = M.Name; Size = UDim2.new(1, 0, 0, 30); Parent = Row })
		new(`TextLabel`, {
			BackgroundTransparency = 1; Font = Theme.Fonts.Body; TextSize = 14; TextColor3 = C.TextDim;
			TextXAlignment = Enum.TextXAlignment.Right; Text = M.Sub; TextTruncate = Enum.TextTruncate.AtEnd;
			Position = UDim2.fromOffset(0, 30); Size = UDim2.new(1, -12, 0, 17);
		}, Row)
	end
	return #Rows
end

function Local.Render()
	if not Ui then return end
	Dirty = false
	for _, Child in Ui.List:GetChildren() do
		if Child:IsA(`GuiObject`) then Child:Destroy() end
	end
	local Buckets = {}
	for _, P in Players:GetPlayers() do
		local Id, Rank = Local.FactionOf(P)
		local Key = Id or `None`
		Buckets[Key] = Buckets[Key] or {}
		local Card = Strangers.NameOf(P)
		local Bits = {}
		if Card then
			local Clan = Card.Rarity
			local ClanCol = Clan and Clans.Rarity[Clan] and Clans.Rarity[Clan].Color
			local Level = P:GetAttribute(`Level`)
			if Level then table.insert(Bits, `Lv {Level}`) end
			if Rank then table.insert(Bits, Rank) end
			local Title = P:GetAttribute(`Title`)
			if Title then table.insert(Bits, `“{Title}”`) end
			local ClubId = P:GetAttribute(`Club`)
			local ClubDef = ClubId and SportsConfig.Clubs[ClubId]
			if ClubDef then table.insert(Bits, `<font color="#{ClubDef.Color:ToHex()}">{ClubDef.Short}{if P:GetAttribute(`ClubRank`) == `Captain` then ` Captain` else ``}</font>`) end
			if ClanCol and Clan ~= `Common` then table.insert(Bits, `<font color="#{ClanCol:ToHex()}">{Clan}</font>`) end
		end
		table.insert(Buckets[Key], {
			Player = P;
			Known = Card ~= nil;
			Name = if Card then Card.Name elseif P == Player then P.DisplayName else `Stranger`;
			Sub = table.concat(Bits, `  ·  `);
		})
	end
	local Order, Total = 0, 0
	for _, G in GROUPS do
		local Members = Buckets[G.Id or `None`]
		if Members and #Members > 0 then
			table.sort(Members, function(A, B)
				if (A.Player == Player) ~= (B.Player == Player) then return A.Player == Player end
				if A.Known ~= B.Known then return A.Known end
				return A.Name < B.Name
			end)
			Local.Group(Order, G, Members)
			Order += 100
			Total += #Members
		end
	end
	Local.Classmates(Order + 1000) -- (2.27)
	Ui.Count.Text = `{Total} enrolled`
	-- fit the plate to its rows, up to 40% of the screen
	task.defer(function()
		if not Ui then return end
		local H = Ui.Layout.AbsoluteContentSize.Y / Ui.Scale.Scale + 50 -- 34 header + list padding (not in AbsoluteContentSize)
		Ui.Plate.Size = UDim2.fromOffset(WIDTH, math.min(H, Ui.MaxHeight or 400))
	end)
end

---| API |---

function Shared.IsOpen(): boolean return Open end

function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Open end
	Open = On
	if On then
		Local.Place()
		Local.Render()
		Ui.Plate.Visible = true
		TweenService:Create(Ui.Plate, TweenInfo.new(0.18, Enum.EasingStyle.Quad), { GroupTransparency = 0; Position = Ui.Plate.Position }):Play()
	else
		local Tw = TweenService:Create(Ui.Plate, TweenInfo.new(0.15, Enum.EasingStyle.Quad), { GroupTransparency = 1 })
		Tw:Play()
		Tw.Completed:Connect(function() if not Open and Ui then Ui.Plate.Visible = false end end)
	end
end

function Shared.OnStart()
	-- Roblox's own list is replaced by this one, and stays off (other code may switch it back on)
	local function KillCoreList()
		pcall(function()
			if StarterGui:GetCoreGuiEnabled(Enum.CoreGuiType.PlayerList) then
				StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.PlayerList, false)
			end
		end)
	end
	task.spawn(function()
		while true do
			KillCoreList()
			task.wait(2)
		end
	end)
	Player:GetAttributeChangedSignal(`InMainMenu`):Connect(function() task.defer(KillCoreList) end)
	Local.Build()
	local function Watch(P: Player)
		P.AttributeChanged:Connect(function(Name)
			if Name == `Title` or Name == `Level` or Name == `Club` or Name == `ClubRank` or Name:sub(1, 8) == `Faction_` then Dirty = true end
		end)
	end
	Strangers.Changed:Connect(function() Dirty = true end)
	StateController.ProfileUpdated:Connect(function(_, Action) -- (2.27) a new classmate, or a change in how one feels
		if Action and Action.type == `SetSocial` then Dirty = true end
	end)
	for _, P in Players:GetPlayers() do Watch(P) end
	Players.PlayerAdded:Connect(function(P) Watch(P) Dirty = true end)
	Players.PlayerRemoving:Connect(function() Dirty = true end)
	task.spawn(function()
		while true do
			task.wait(0.5)
			if Open and Dirty then Local.Render() end
		end
	end)
	UserInputService.InputBegan:Connect(function(Input)
		-- Roblox always marks Tab as processed (it used to open its own list), so only typing blocks it
		if Input.KeyCode ~= TOGGLE_KEY then return end
		if Typing.Active() then return end
		if Player:GetAttribute(`InMainMenu`) then return end
		Shared.Toggle()
	end)
	local Cam = workspace.CurrentCamera
	if Cam then Cam:GetPropertyChangedSignal(`ViewportSize`):Connect(Local.Place) end
end

---| Testing |---

function Shared.Debug()
	local Groups = {}
	if Ui then
		for _, Child in Ui.List:GetChildren() do
			if Child:IsA(`Frame`) and Child.Name:sub(1, 6) == `Group_` then table.insert(Groups, Child.Name) end
		end
	end
	return { Open = Open; Groups = Groups }
end

return Shared
