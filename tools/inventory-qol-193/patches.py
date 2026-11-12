# Inventory QOL batch 3 (1.93.0): Locker sort and filter, favourites, drop how many with Undo.
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

TROPHY_CARD_OLD = """		local DropB = Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
			onClick = function()
				if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
				ConfirmDrop = nil
				Local.ShowCard()
				local Ok, Msg = Local.Call(`Drop`, Id, 1)
				if not Ok then Local.Say(Msg or `Couldn't drop it. Try again.`) end
			end })
		if typeof(DropB) == `Instance` then DropB.Name = `Drop` end
		return
	end"""
TROPHY_CARD_NEW = """		if ConfirmDrop == Id then Local.DropChoices(A, Id, Have) return end
		local DropB = Kit.Button({ text = `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
			onClick = function() Local.DropAsk(Id, Have) end })
		if typeof(DropB) == `Instance` then DropB.Name = `Drop` end
		Local.FavButton(A, Id, UDim2.new(1, -112, 0.5, 0))
		return
	end"""

SNACK_CARD_OLD = """	local Pinned = table.find(State.Pinned or {}, Id) ~= nil
	Info.Text = `You carry {Have}  \\u{00B7}  ` .. (if Pinned then `in your pouch (hotbar)` else `not in your pouch`)"""
SNACK_CARD_NEW = """	local Pinned = table.find(State.Pinned or {}, Id) ~= nil
	Info.Text = `You carry {Have}  \\u{00B7}  ` .. (if Pinned then `in your pouch (hotbar)` else `not in your pouch`)
	if ConfirmDrop == Id then Local.DropChoices(A, Id, Have) return end -- (inventory QOL 1.93) how many to drop
	Info.Size = UDim2.new(1, -400, 0, 40) -- room for the star
	Local.FavButton(A, Id, UDim2.new(1, -344, 0.5, 0))"""

SNACK_DROP_OLD = """	local DropB = Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
		onClick = function()
			if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
			ConfirmDrop = nil
			Local.ShowCard()
			local Ok, Msg = Local.Call(`Drop`, Id, 1)
			if not Ok then Local.Say(Msg or `Couldn't drop it. Try again.`) end
		end })"""
SNACK_DROP_NEW = """	local DropB = Kit.Button({ text = `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
		onClick = function() Local.DropAsk(Id, Have) end })"""

HELPERS = """-- (inventory QOL 1.93) dropping: one goes at once; more than one asks how many (1, 5, All). Either way an Undo bar
-- stays for 5 s (the server keeps the last drop that long).
function Local.DropAsk(Id: string, Have: number)
	if Have <= 1 then Local.DoDrop(Id, 1) return end
	ConfirmDrop = Id
	Local.ShowCard()
end

function Local.DoDrop(Id: string, N: number)
	ConfirmDrop = nil
	local Ok, Msg = Local.Call(`Drop`, Id, N)
	if not Ok then Local.ShowCard() Local.Say(Msg or `Couldn't drop it. Try again.`) return end
	local It = Items.ById[Id]
	Local.ShowUndo(`Dropped {N} {It and It.Name or Id}.`)
end

function Local.DropChoices(A: Frame, Id: string, Have: number)
	local Info = A:FindFirstChild(`Info`, true)
	if Info and Info:IsA(`TextLabel`) then Info.Text = `Drop how many? You carry {Have}.` end
	local Choices = { { `1`, 1 } }
	if Have > 5 then table.insert(Choices, { `5`, 5 }) end
	table.insert(Choices, { `All ({Have})`, Have })
	local X = 0
	local B = Kit.Button({ text = `Cancel`; style = `ghost`; Size = UDim2.fromOffset(96, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, X, 0.5, 0); Parent = A;
		onClick = function() ConfirmDrop = nil Local.ShowCard() end })
	if typeof(B) == `Instance` then B.Name = `DropCancel` end
	X -= 104
	for I = #Choices, 1, -1 do
		local C = Choices[I]
		local W = if #C[1] > 2 then 96 else 56
		local Btn = Kit.Button({ text = C[1]; style = `crimson`; Size = UDim2.fromOffset(W, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, X, 0.5, 0); Parent = A;
			onClick = function() Local.DoDrop(Id, C[2]) end })
		if typeof(Btn) == `Instance` then Btn.Name = `Drop{C[2]}` end
		X -= W + 8
	end
end

local UndoToken = 0
function Local.ShowUndo(Text: string)
	local Bar = Ui and Ui.UndoBar
	if not Bar then return end
	UndoToken += 1
	local My = UndoToken
	Bar.Text.Text = Text
	Bar.Root.Visible = true
	task.spawn(function()
		for Left = 5, 1, -1 do
			if My ~= UndoToken then return end
			Bar.Undo:SetText(`Undo ({Left})`)
			task.wait(1)
		end
		if My == UndoToken then Bar.Root.Visible = false end
	end)
end

function Local.Undo()
	UndoToken += 1
	if Ui then Ui.UndoBar.Root.Visible = false end
	local Ok, Msg = Local.Call(`Undo`)
	if not Ok then Local.Say(Msg or `Too late to undo.`) end
end

-- (inventory QOL 1.93) favourites: a star on the card; starred items come first in the Locker and at the stand
function Local.IsFav(Id: string): boolean
	return State ~= nil and table.find(State.Fav or {}, Id) ~= nil
end

function Local.FavButton(A: Frame, Id: string, Pos: UDim2)
	local On = Local.IsFav(Id)
	local B = Kit.Button({ text = if On then `\\u{2605}` else `\\u{2606}`; style = if On then `gold` else `default`; Size = UDim2.fromOffset(44, 40);
		AnchorPoint = Vector2.new(1, 0.5); Position = Pos; Parent = A;
		onClick = function()
			local Ok, Msg = Local.Call(`Fav`, Id, not On)
			if not Ok then Local.Say(Msg or `Couldn't change your favourites.`) end
		end })
	if typeof(B) == `Instance` then B.Name = `Fav` end
end

-- (inventory QOL 1.93) the sort and filter bar over the grid (kept while the game runs)
local SORTS = { `Kind`, `Rarity`, `Most owned`, `A-Z` }
local FILTERS = { `Heals`, `Buffs`, `Lunch`, `Specials`, `Trophies`, `\\u{2605}` }
local SortMode, Filter = 1, nil
local RARITY_RANK = { Common = 1; Uncommon = 2; Rare = 3; Epic = 4; Legendary = 5; Mythic = 6; Cursed = 7 }

function Local.BuildToolbar()
	local Bar = Ui and Ui.Toolbar
	if not Bar then return end
	for _, Ch in Bar:GetChildren() do if Ch:IsA(`GuiObject`) then Ch:Destroy() end end
	local S = Kit.Button({ text = `Sort: {SORTS[SortMode]}`; style = `ghost`; Size = UDim2.fromOffset(140, 30); Position = UDim2.fromOffset(0, 0); Parent = Bar;
		onClick = function() SortMode = SortMode % #SORTS + 1 Local.BuildToolbar() Local.Refresh() end })
	if typeof(S) == `Instance` then S.Name = `Sort` end
	local X = 148
	for _, F in FILTERS do
		local On = Filter == F
		local W = if #F <= 3 then 40 else 72
		local B = Kit.Button({ text = F; style = if On then `gold` else `default`; Size = UDim2.fromOffset(W, 30); Position = UDim2.fromOffset(X, 0); Parent = Bar;
			onClick = function() Filter = if Filter == F then nil else F Local.BuildToolbar() Local.Refresh() end })
		if typeof(B) == `Instance` then B.Name = if F == `\\u{2605}` then `FilterFav` else `Filter{F}` end
		X += W + 6
	end
end

-- does an entry pass the filter chip?
function Local.Passes(E): boolean
	if not Filter then return true end
	if Filter == `\\u{2605}` then return Local.IsFav(E.id) end
	local It = (E.kind == `Snack` or E.kind == `Trophy`) and Items.ById[E.id]
	if not It then return false end
	if Filter == `Heals` then return It.Kind == `Heal` end
	if Filter == `Buffs` then return It.Kind == `Buff` end
	if Filter == `Lunch` then return It.Lunch == true end
	if Filter == `Specials` then return It.Special ~= nil end
	if Filter == `Trophies` then return It.Kind == `Trophy` end
	return true
end

function Local.Entries()"""

EDITS = [
# ---- Config.Items: favourites ride in the save ----
(ITEMS, """	if typeof(Raw.Daily) == `table` and typeof(Raw.Daily.Day) == `number` then""",
        """	-- (inventory QOL 1.93) favourites: up to 12 item ids (Inventory.Fav checks they're real)
	if typeof(Raw.Fav) == `table` then
		Out.Fav = {}
		for _, Id in Raw.Fav do
			if typeof(Id) == `string` and #Id <= 48 and not table.find(Out.Fav, Id) and #Out.Fav < 12 then table.insert(Out.Fav, Id) end
		end
	end
	if typeof(Raw.Daily) == `table` and typeof(Raw.Daily.Day) == `number` then"""),
# ---- Inventory (server) ----
(INV, """		Items = Inv.Items; Pinned = Inv.Pinned; Boards = Inv.Boards;""",
      """		Items = Inv.Items; Pinned = Inv.Pinned; Boards = Inv.Boards; Fav = Inv.Fav or {}; -- (inventory QOL 1.93)"""),
(INV, """	Inv.Items[Id] = math.max(0, Inv.Items[Id] - Count)
	if Inv.Items[Id] == 0 then Inv.Items[Id] = nil end
	Local.Save(P, Inv)
	return true
end
""", """	Count = math.min(Count, Inv.Items[Id])
	Inv.Items[Id] = math.max(0, Inv.Items[Id] - Count)
	if Inv.Items[Id] == 0 then Inv.Items[Id] = nil end
	Local.Save(P, Inv)
	LastDrop[P] = { Id = Id; N = Count; Until = os.clock() + 5 } -- (inventory QOL 1.93) Undo for 5 s
	return true
end

-- (inventory QOL 1.93) put back the last drop, within 5 s
function Shared.Undo(P: Player): (boolean, string?)
	local D = LastDrop[P]
	LastDrop[P] = nil
	if not D or os.clock() > D.Until then return false, `Too late to undo.` end
	local Inv = Shared.Get(P)
	if not Inv then return false, `Your record isn't loaded yet.` end
	Inv.Items[D.Id] = math.min(Items.MaxStack, (Inv.Items[D.Id] or 0) + D.N)
	Local.Save(P, Inv)
	return true
end

-- (inventory QOL 1.93) star an item (a snack, a trophy or a piece of gear); up to 12
function Shared.Fav(P: Player, Id: any, On: any): (boolean, string?)
	local Inv = Shared.Get(P)
	if not (Inv and typeof(Id) == `string`) then return false, `Unknown item.` end
	local Known = Items.ById[Id] ~= nil
	if not Known then
		local Ok, Gear = pcall(require, ReplicatedStorage.Config.Gear)
		Known = Ok and Gear.ById and Gear.ById[Id] ~= nil
	end
	if not Known then return false, `Unknown item.` end
	Inv.Fav = Inv.Fav or {}
	local At = table.find(Inv.Fav, Id)
	if On and not At then
		if #Inv.Fav >= 12 then return false, `You can star 12 things. Unstar one first.` end
		table.insert(Inv.Fav, Id)
	elseif not On and At then
		table.remove(Inv.Fav, At)
	end
	Local.Save(P, Inv)
	return true
end
"""),
(INV, """local LastCall = {} :: { [Player]: number }""", """local LastCall = {} :: { [Player]: number }
local LastDrop = {} :: { [Player]: { Id: string, N: number, Until: number } } -- (inventory QOL 1.93) Undo"""),
(INV, """	local Restock = rf(`Restock`) -- (inventory QOL 1.92)""", """	local Restock = rf(`Restock`) -- (inventory QOL 1.92)
	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)
	Undo.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.Undo(P) end
	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end"""),
(INV, """	Players.PlayerRemoving:Connect(function(P) Buffs[P] = nil Cooldowns[P] = nil Busy[P] = nil LastCall[P] = nil end)""",
      """	Players.PlayerRemoving:Connect(function(P) Buffs[P] = nil Cooldowns[P] = nil Busy[P] = nil LastCall[P] = nil LastDrop[P] = nil end)"""),
# ---- Locker: toolbar, undo bar, grid moved down ----
(LOCK, """	local Grid, GridApi = Kit.ItemGrid({ Name = `Grid`; slotSize = 82; gap = 12; showEmpty = 25; showCounter = false;
		Position = UDim2.fromOffset(0, 44); Size = UDim2.new(1, 0, 1, -124); Parent = Bag;""",
       """	-- (inventory QOL 1.93) the sort and filter bar, under the tabs
	local Toolbar = Instance.new(`Frame`)
	Toolbar.Name = `Toolbar`
	Toolbar.BackgroundTransparency = 1
	Toolbar.Position = UDim2.fromOffset(4, 42)
	Toolbar.Size = UDim2.new(1, -8, 0, 30)
	Toolbar.Parent = Bag
	local Grid, GridApi = Kit.ItemGrid({ Name = `Grid`; slotSize = 82; gap = 12; showEmpty = 25; showCounter = false;
		Position = UDim2.fromOffset(0, 78); Size = UDim2.new(1, 0, 1, -158); Parent = Bag;"""),
(LOCK, """	Ui = { Gui = G; Preview = PrevApi; Equip = Equip; Scale = ScaleApi.Content; Yen = YenApi; Tabs = TabApi; Grid = GridApi; GridRoot = Grid;
		Actions = Actions; Pouch = Pouch; Tip = Tip; TipBody = TipApi.Content }
end""", """	-- (inventory QOL 1.93) "Dropped 3 Onigiri. [Undo (5)]", over the bottom of the grid
	local UndoRoot = Instance.new(`Frame`)
	UndoRoot.Name = `UndoBar`
	UndoRoot.BackgroundColor3 = Color3.fromRGB(20, 16, 18)
	UndoRoot.BackgroundTransparency = 0.1
	UndoRoot.BorderSizePixel = 0
	UndoRoot.Position = UDim2.new(0, 4, 1, -118)
	UndoRoot.Size = UDim2.new(1, -8, 0, 38)
	UndoRoot.ZIndex = 30
	UndoRoot.Visible = false
	UndoRoot.Parent = Bag
	local UndoText = Local.Label(UndoRoot, ``, 15, { Name = `Text`; TextColor3 = C.Gold; Position = UDim2.fromOffset(10, 0); Size = UDim2.new(1, -150, 1, 0);
		TextYAlignment = Enum.TextYAlignment.Center; ZIndex = 31 })
	local UndoB, UndoApi = Kit.Button({ text = `Undo (5)`; style = `gold`; Size = UDim2.fromOffset(120, 30); AnchorPoint = Vector2.new(1, 0.5);
		Position = UDim2.new(1, -6, 0.5, 0); Parent = UndoRoot; onClick = function() Local.Undo() end })
	if typeof(UndoB) == `Instance` then UndoB.Name = `Undo` UndoB.ZIndex = 31 end
	Ui = { Gui = G; Preview = PrevApi; Equip = Equip; Scale = ScaleApi.Content; Yen = YenApi; Tabs = TabApi; Grid = GridApi; GridRoot = Grid;
		Actions = Actions; Pouch = Pouch; Tip = Tip; TipBody = TipApi.Content; Toolbar = Toolbar;
		UndoBar = { Root = UndoRoot; Text = UndoText; Undo = UndoApi } }
	Local.BuildToolbar()
end"""),
(LOCK, """function Local.Entries()""", HELPERS),
(LOCK, """	local KindRank = { Snack = 1; Kit = 1.5; Trophy = 2; Gear = 3; Board = 4 } -- (beasts) a strict order across the item kinds
	table.sort(Out, function(A, B)
		if A.kind ~= B.kind then return (KindRank[A.kind] or 9) < (KindRank[B.kind] or 9) end
		if A.order ~= B.order then return A.order < B.order end
		return A.name < B.name
	end)
	return Out""", """	-- (inventory QOL 1.93) the filter chip, then favourites first and the chosen sort
	local Kept = {}
	for _, E in Out do if Local.Passes(E) then table.insert(Kept, E) end end
	Out = Kept
	local KindRank = { Snack = 1; Kit = 1.5; Trophy = 2; Gear = 3; Board = 4 } -- (beasts) a strict order across the item kinds
	local Mode = SORTS[SortMode]
	table.sort(Out, function(A, B)
		local FA, FB = Local.IsFav(A.id), Local.IsFav(B.id)
		if FA ~= FB then return FA end
		if Mode == `Rarity` then
			local RA, RB = RARITY_RANK[A.rarity] or 0, RARITY_RANK[B.rarity] or 0
			if RA ~= RB then return RA > RB end
		elseif Mode == `Most owned` then
			local CA, CB = A.count or 1, B.count or 1
			if CA ~= CB then return CA > CB end
		elseif Mode == `A-Z` then
			if A.name ~= B.name then return A.name < B.name end
		end
		if A.kind ~= B.kind then return (KindRank[A.kind] or 9) < (KindRank[B.kind] or 9) end
		if A.order ~= B.order then return (A.order or 0) < (B.order or 0) end
		return A.name < B.name
	end)
	return Out"""),
(LOCK, """			Local.HoverTip(Slot, E.kind, E.id)
""", """			Local.HoverTip(Slot, E.kind, E.id)
			if Local.IsFav(E.id) then -- (inventory QOL 1.93) a starred item
				Kit.Text({ Name = `Fav`; Text = `\\u{2605}`; Font = Fonts.Title; TextSize = 16; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Left;
					Position = UDim2.fromOffset(6, 2); Size = UDim2.fromOffset(18, 18); ZIndex = 9; Parent = Slot })
			end
"""),
(LOCK, TROPHY_CARD_OLD, TROPHY_CARD_NEW),
(LOCK, SNACK_CARD_OLD, SNACK_CARD_NEW),
(LOCK, SNACK_DROP_OLD, SNACK_DROP_NEW),
# ---- the stand: favourites first ----
(LOCK, """		if (A.Special ~= nil) ~= (B.Special ~= nil) then return A.Special ~= nil end -- today's special first
		return (A.Order or 0) < (B.Order or 0)""", """		if (A.Special ~= nil) ~= (B.Special ~= nil) then return A.Special ~= nil end -- today's special first
		local FA, FB = Local.IsFav(A.Id), Local.IsFav(B.Id) -- (inventory QOL 1.93) then your favourites
		if FA ~= FB then return FA end
		return (A.Order or 0) < (B.Order or 0)"""),
]
# batch 3 fix: the Undo / Fav handlers go after `limited` is defined
INV = "ServerScriptService.Services.Features.Inventory"
EDITS = [
(INV, """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)
	Undo.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.Undo(P) end
	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end""",
      """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)"""),
(INV, """	Restock.OnServerInvoke = function(P, To) if limited(P) then return false, `One moment...` end return Shared.Restock(P, To) end""",
      """	Restock.OnServerInvoke = function(P, To) if limited(P) then return false, `One moment...` end return Shared.Restock(P, To) end
	Undo.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.Undo(P) end
	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end"""),
]
# batch 3 polish: "Sort: Most owned" fits its button
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"
EDITS = [
(LOCK, """Size = UDim2.fromOffset(140, 30); Position = UDim2.fromOffset(0, 0); Parent = Bar;""",
       """Size = UDim2.fromOffset(170, 30); Position = UDim2.fromOffset(0, 0); Parent = Bar;"""),
(LOCK, """	local X = 148
""", """	local X = 176
"""),
(LOCK, """local W = if #F <= 3 then 40 else 72""", """local W = if #F <= 3 then 36 else 68"""),
]
