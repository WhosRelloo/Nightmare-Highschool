# Inventory QOL batch 6: the replace-buff check (8), "new" dots (14), the trophy case (29).
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

EDITS = [
# ---- Config.Items: what you've looked at (the "new" dots)
(ITEMS, """	-- (inventory QOL 1.93) favourites: up to 12 item ids (Inventory.Fav checks they're real)""",
        """	-- (inventory QOL batch 6) what you've looked at in the Locker ({ [id] = true }); anything else you carry is "new"
	if typeof(Raw.Seen) == `table` then
		Out.Seen = {}
		for Id, V in Raw.Seen do if V == true and Items.ById[Id] then Out.Seen[Id] = true end end
	end
	-- (inventory QOL 1.93) favourites: up to 12 item ids (Inventory.Fav checks they're real)"""),
# ---- Inventory: the replace-buff check
(INV, """	if Busy[P] then return false, `Still eating.` end -- (inventory QOL 1.91) no silent refusals""",
      """	if Busy[P] then return false, `Still eating.` end -- (inventory QOL 1.91) no silent refusals
	-- (inventory QOL batch 6) don't throw away a different buff with more than a minute left without asking: the first
	-- use says so, a second within 3 s goes ahead
	if It.Kind == `Buff` then
		local B = Buffs[P]
		local Left = B and (B.Until - workspace:GetServerTimeNow()) or 0
		if B and B.Id ~= Id and Left > 60 then
			local Ask = ReplaceAsk[P]
			if not (Ask and Ask.Id == Id and os.clock() < Ask.Until) then
				ReplaceAsk[P] = { Id = Id; Until = os.clock() + 3 }
				local Cur = Items.ById[B.Id]
				return false, `Replace {Cur and Cur.Name or `your buff`} ({math.floor(Left / 60)}:{string.format(`%02d`, math.floor(Left % 60))} left)? Use again to swap.`
			end
		end
		ReplaceAsk[P] = nil
	end"""),
(INV, """local LastDrop = {} :: { [Player]: { Id: string, N: number, Until: number } } -- (inventory QOL 1.93) Undo""",
      """local LastDrop = {} :: { [Player]: { Id: string, N: number, Until: number } } -- (inventory QOL 1.93) Undo
local ReplaceAsk = {} :: { [Player]: { Id: string, Until: number } } -- (inventory QOL batch 6) the replace-buff check"""),
# ---- Inventory: seen ids in the state (seeded with what you carry the first time), and the Seen remote
(INV, """		Items = Inv.Items; Pinned = Inv.Pinned; Boards = Inv.Boards; Fav = Inv.Fav or {}; -- (inventory QOL 1.93)""",
      """		Items = Inv.Items; Pinned = Inv.Pinned; Boards = Inv.Boards; Fav = Inv.Fav or {}; -- (inventory QOL 1.93)
		Seen = Local.SeenFor(P, Inv); -- (inventory QOL batch 6) the "new" dots"""),
(INV, """function Shared.Fav(P: Player, Id: any, On: any): (boolean, string?)""",
      """-- (inventory QOL batch 6) what you've looked at. The first time, everything you already carry counts as seen, so only
-- things you get from now on show a "new" dot.
function Local.SeenFor(P: Player, Inv): { [string]: boolean }
	if Inv.Seen then return Inv.Seen end
	Inv.Seen = {}
	for Id in Inv.Items do Inv.Seen[Id] = true end
	Data.UpdateState(P, { type = `SetInventory`; inventory = Inv })
	return Inv.Seen
end

function Shared.Seen(P: Player, Id: any): boolean
	local Inv = Shared.Get(P)
	if not (Inv and typeof(Id) == `string` and Items.ById[Id]) then return false end
	Inv.Seen = Inv.Seen or {}
	if Inv.Seen[Id] then return true end
	Inv.Seen[Id] = true
	Data.UpdateState(P, { type = `SetInventory`; inventory = Inv }) -- quietly: no Changed, so the Locker isn't rebuilt
	return true
end

function Shared.Fav(P: Player, Id: any, On: any): (boolean, string?)"""),
(INV, """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)""",
      """	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)
	local Seen = rf(`Seen`) -- (inventory QOL batch 6)"""),
(INV, """	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end""",
      """	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end
	Seen.OnServerInvoke = function(P, Id) return Shared.Seen(P, Id) end -- cheap, and never blocks a Use"""),
(INV, """	Players.PlayerRemoving:Connect(function(P) Buffs[P] = nil Cooldowns[P] = nil Busy[P] = nil LastCall[P] = nil LastDrop[P] = nil end)""",
      """	Players.PlayerRemoving:Connect(function(P) Buffs[P] = nil Cooldowns[P] = nil Busy[P] = nil LastCall[P] = nil LastDrop[P] = nil ReplaceAsk[P] = nil end)"""),
# ---- Locker: mark an item seen when you pick it; the dot; the trophy case
(LOCK, """		onSelect = function(Item, I) if Item then LastIndex = I Selected = { kind = Item.kind; id = Item.id } ConfirmDrop = nil Local.ShowCard() end end })""",
       """		onSelect = function(Item, I) if Item then LastIndex = I Selected = { kind = Item.kind; id = Item.id } ConfirmDrop = nil Local.ShowCard() Local.MarkSeen(Item) end end })"""),
(LOCK, """function Local.Entries()""", """-- (inventory QOL batch 6) picking an item you haven't looked at clears its "new" dot (Inventory.Seen, quietly)
function Local.MarkSeen(Item)
	if not (State and (Item.kind == `Snack` or Item.kind == `Trophy`) and not Item.locked) then return end
	State.Seen = State.Seen or {}
	if State.Seen[Item.id] then return end
	State.Seen[Item.id] = true
	task.spawn(function()
		Local.Call(`Seen`, Item.id)
		local Slot = Ui and Ui.GridRoot:FindFirstChild(`Slot{LastIndex or 0}`, true)
		local Dot = Slot and Slot:FindFirstChild(`New`)
		if Dot then Dot:Destroy() end
	end)
end

function Local.Entries()"""),
(LOCK, """	-- (kit 1.79) the everyday kit you own""", """	-- (inventory QOL batch 6) the trophy case: under the Trophies chip, the ones you haven't found show as silhouettes
	if (Tab == 1 or Tab == 3) and Filter == `Trophies` then
		for _, It in Items.Trophies or {} do
			if not (State.Items or {})[It.Id] then
				table.insert(Out, { name = It.Name; rarity = It.Rarity; kind = `Trophy`; id = It.Id; order = It.Order; locked = true })
			end
		end
	end
	-- (kit 1.79) the everyday kit you own"""),
(LOCK, """			if E.kind == `Taste` then -- (inventory QOL batch 5) untasted: a dark silhouette; tasted: a gilt tick""",
       """			-- (inventory QOL batch 6) a "new" dot on things you haven't looked at; a found-nothing trophy is a silhouette
			if (E.kind == `Snack` or E.kind == `Trophy`) and not E.locked and State and State.Seen and not State.Seen[E.id] then
				local Dot = Instance.new(`Frame`)
				Dot.Name = `New`
				Dot.BackgroundColor3 = C.Gold
				Dot.BorderSizePixel = 0
				Dot.AnchorPoint = Vector2.new(1, 0)
				Dot.Position = UDim2.new(1, -7, 0, 7)
				Dot.Size = UDim2.fromOffset(11, 11)
				Dot.ZIndex = 10
				Instance.new(`UICorner`, Dot).CornerRadius = UDim.new(1, 0)
				local St = Instance.new(`UIStroke`) St.Color = Color3.fromRGB(30, 20, 10) St.Thickness = 1.5 St.Parent = Dot
				Dot.Parent = Slot
			end
			if E.locked then
				local V = Slot:FindFirstChild(`NHView`)
				if V and V:IsA(`ViewportFrame`) then V.ImageColor3 = Color3.new(0, 0, 0) V.ImageTransparency = 0.25 end
				Kit.Text({ Name = `Unknown`; Text = `?`; Font = Fonts.Title; TextSize = 26; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
					AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.45); Size = UDim2.fromOffset(30, 30); ZIndex = 9; Parent = Slot })
			end
			if E.kind == `Taste` then -- (inventory QOL batch 5) untasted: a dark silhouette; tasted: a gilt tick"""),
(LOCK, """	-- (beasts) a trophy: kept, not used or pinned; you can still drop it
	if Selected.kind == `Trophy` then""", """	-- (inventory QOL batch 6) a trophy you haven't found yet (the trophy case)
	if Selected.kind == `Trophy` and Have <= 0 then
		Info.Text = `Not found yet  \\u{00B7}  a rare drop from the {It.Beast or `night`}`
		return
	end
	-- (beasts) a trophy: kept, not used or pinned; you can still drop it
	if Selected.kind == `Trophy` then"""),
]
