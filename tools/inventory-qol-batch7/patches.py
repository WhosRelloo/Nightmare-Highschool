# Inventory QOL batch 7: drag to reorder the pouch (2) and hotbar loadouts (6).
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"
HUD = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitHud"

EDITS = [
# ---- Config.Items: the loadout names, and their saved form
(ITEMS, r"""Items.MaxPinned = 4""",
        r"""Items.MaxPinned = 4
Items.Loadouts = { `Day`, `Fight`, `Night` } -- (inventory QOL batch 7) three saved pouch sets"""),
(ITEMS, r"""	-- (inventory QOL batch 6) what you've looked at in the Locker""",
        r"""	-- (inventory QOL batch 7) loadouts: { Active = name, Sets = { [name] = { id } } }; the active set lives in Pinned
	if typeof(Raw.Loadouts) == `table` then
		local L = { Active = Items.Loadouts[1]; Sets = {} }
		if table.find(Items.Loadouts, Raw.Loadouts.Active) then L.Active = Raw.Loadouts.Active end
		if typeof(Raw.Loadouts.Sets) == `table` then
			for _, Name in Items.Loadouts do
				local S = Raw.Loadouts.Sets[Name]
				if Name ~= L.Active and typeof(S) == `table` then
					local List = {}
					for _, Id in S do
						if typeof(Id) == `string` and Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` and not table.find(List, Id) and #List < Items.MaxPinned then table.insert(List, Id) end
					end
					L.Sets[Name] = List
				end
			end
		end
		Out.Loadouts = L
	end
	-- (inventory QOL batch 6) what you've looked at in the Locker"""),
# ---- Inventory: the active loadout in the state
(INV, r"""		Seen = Local.SeenFor(P, Inv); -- (inventory QOL batch 6) the "new" dots""",
      r"""		Seen = Local.SeenFor(P, Inv); -- (inventory QOL batch 6) the "new" dots
		Loadout = Inv.Loadouts and Inv.Loadouts.Active or Items.Loadouts[1]; -- (inventory QOL batch 7)"""),
# ---- Inventory: each snack tool knows its pouch slot, so the hotbar can put them in that order
(INV, r"""					Have[Id] = T
					T:SetAttribute(`Count`, Inv.Items[Id] or 0)""",
      r"""					Have[Id] = T
					T:SetAttribute(`Count`, Inv.Items[Id] or 0)
					T:SetAttribute(`NHPinIndex`, table.find(Inv.Pinned, Id)) -- (inventory QOL batch 7) KitHud's order"""),
(INV, r"""			local T = Local.MakeTool(P, Items.ById[Id])
			T:SetAttribute(`Count`, Inv.Items[Id] or 0)""",
      r"""			local T = Local.MakeTool(P, Items.ById[Id])
			T:SetAttribute(`Count`, Inv.Items[Id] or 0)
			T:SetAttribute(`NHPinIndex`, table.find(Inv.Pinned, Id)) -- (inventory QOL batch 7)"""),
# ---- Inventory: move a pin, switch loadouts
(INV, r"""function Shared.Drop(P: Player, Id: any, N: any): (boolean, string?)""",
      r"""-- (inventory QOL batch 7) move a pinned snack to another pouch slot (the hotbar follows, keys 1-4 too)
function Shared.MovePin(P: Player, Id: any, To: any): (boolean, string?)
	local Inv = Shared.Get(P)
	if not (Inv and typeof(Id) == `string`) then return false, `Unknown item.` end
	local At = table.find(Inv.Pinned, Id)
	if not At then return false, `That isn't in your pouch.` end
	if typeof(To) ~= `number` or To ~= To then return false, `Couldn't move it.` end
	To = math.clamp(math.floor(To), 1, #Inv.Pinned)
	if To == At then return true end
	table.remove(Inv.Pinned, At)
	table.insert(Inv.Pinned, To, Id)
	Local.Save(P, Inv)
	return true
end

-- (inventory QOL batch 7) loadouts: three saved pouch sets (Items.Loadouts). The active one lives in Pinned; switching
-- keeps it and brings the other back, empty pins included (so "Restock my pins" refills them). A set you've never used
-- starts as a copy of your pouch.
function Shared.Loadout(P: Player, Name: any): (boolean, string?)
	local Inv = Shared.Get(P)
	if not Inv then return false, `Your record isn't loaded yet.` end
	if not table.find(Items.Loadouts, Name) then return false, `Unknown loadout.` end
	local L = Inv.Loadouts or { Active = Items.Loadouts[1]; Sets = {} }
	if L.Active == Name then return true, `{Name} is already on your hotbar.` end
	L.Sets[L.Active] = table.clone(Inv.Pinned)
	local Fresh = L.Sets[Name] == nil
	local Next = L.Sets[Name] or table.clone(Inv.Pinned)
	L.Sets[Name] = nil
	L.Active = Name
	Inv.Pinned = {}
	for _, Id in Next do
		if Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` and not table.find(Inv.Pinned, Id) and #Inv.Pinned < Items.MaxPinned then table.insert(Inv.Pinned, Id) end
	end
	Inv.Loadouts = L
	Local.Save(P, Inv)
	return true, if Fresh then `{Name} starts as a copy of your pouch. Change its pins as you like.` else `{Name} loadout on your hotbar.`
end

function Shared.Drop(P: Player, Id: any, N: any): (boolean, string?)"""),
(INV, r"""	local Feed = rf(`Feed`) -- (inventory QOL batch 5)""",
      r"""	local Feed = rf(`Feed`) -- (inventory QOL batch 5)
	local MovePin, Loadout = rf(`MovePin`), rf(`Loadout`) -- (inventory QOL batch 7)"""),
(INV, r"""	Feed.OnServerInvoke = function(P, Model, Id) if limited(P) then return false, `One moment...` end return Shared.Feed(P, Model, Id) end""",
      r"""	Feed.OnServerInvoke = function(P, Model, Id) if limited(P) then return false, `One moment...` end return Shared.Feed(P, Model, Id) end
	MovePin.OnServerInvoke = function(P, Id, To) if limited(P) then return false, `One moment...` end return Shared.MovePin(P, Id, To) end
	Loadout.OnServerInvoke = function(P, Name) if limited(P) then return false, `One moment...` end return Shared.Loadout(P, Name) end"""),
# ---- KitHud: snack tools sit in pouch order, in the slots snacks already hold (weapons don't move)
(HUD, r"""if A == `Count` or A == `NHEmpty` or A == `NHReadyAt` then Local.Schedule() end""",
      r"""if A == `Count` or A == `NHEmpty` or A == `NHReadyAt` or A == `NHPinIndex` then Local.Schedule() end"""),
(HUD, r"""	Order = NewOrder
end""",
      r"""	Order = NewOrder
	-- (inventory QOL batch 7) snacks follow your pouch order (the tool's NHPinIndex), inside the slots they already hold
	local At, Snacks = {}, {}
	for I, Tool in Order do
		if typeof(Tool:GetAttribute(`NHPinIndex`)) == `number` then table.insert(At, I) table.insert(Snacks, Tool) end
	end
	table.sort(Snacks, function(A, B) return A:GetAttribute(`NHPinIndex`) < B:GetAttribute(`NHPinIndex`) end)
	for K, I in At do Order[I] = Snacks[K] end
end"""),
# ---- Locker: loadout chips and the move buttons beside the pouch
(LOCK, r"""function Local.Build()""",
       r"""local POUCH_HINT = `Drag a slot to move it, or pick a snack and press \u{2039} \u{203A}.` -- (inventory QOL batch 7)

function Local.Build()"""),
(LOCK, r"""		Pouch[I] = { Root = Slot; Api = SlotApi }
	end""",
       r"""		Pouch[I] = { Root = Slot; Api = SlotApi }
	end
	-- (inventory QOL batch 7) the loadouts on the pouch's left, moving a slot on its right
	local Loadouts = Instance.new(`Frame`)
	Loadouts.Name = `Loadouts`
	Loadouts.BackgroundTransparency = 1
	Loadouts.Position = UDim2.fromOffset(6, 6)
	Loadouts.Size = UDim2.fromOffset(92, 96)
	Loadouts.Parent = PouchApi.Content
	local Side = Instance.new(`Frame`)
	Side.Name = `Move`
	Side.BackgroundTransparency = 1
	Side.AnchorPoint = Vector2.new(1, 0)
	Side.Position = UDim2.new(1, -6, 0, 6)
	Side.Size = UDim2.fromOffset(94, 96)
	Side.Parent = PouchApi.Content
	for K, Dir in { -1, 1 } do
		local B = Kit.Button({ text = if Dir < 0 then `\u{2039}` else `\u{203A}`; Size = UDim2.fromOffset(44, 28); Position = UDim2.fromOffset((K - 1) * 50, 0); Parent = Side;
			onClick = function() Local.MoveSelected(Dir) end })
		if typeof(B) == `Instance` then B.Name = if Dir < 0 then `MoveLeft` else `MoveRight` end
	end
	local Hint = Local.Label(Side, POUCH_HINT, 12, { Name = `Hint`; TextColor3 = C.TextDim; Position = UDim2.fromOffset(0, 34); Size = UDim2.new(1, 0, 1, -34) })"""),
(LOCK, r"""Actions = Actions; Pouch = Pouch; Tip = Tip;""",
       r"""Actions = Actions; Pouch = Pouch; Tip = Tip; Loadouts = Loadouts; PouchHint = Hint;"""),
(LOCK, r"""	Local.BuildToolbar()
end""",
       r"""	Local.BuildToolbar()
	Local.HookDrag() -- (inventory QOL batch 7)
end"""),
(LOCK, r"""function Local.RefreshPouch()
	local Pinned = State and State.Pinned or {}""",
       r"""-- (inventory QOL batch 7) moving pouch slots: drag one onto another, or pick a pinned snack and press < >. And loadouts.
local Drag = nil
local NoClickUntil = 0
local HintToken = 0

function Local.PouchSay(Msg: string)
	local Hint = Ui and Ui.PouchHint
	if not Hint then return end
	HintToken += 1
	local My = HintToken
	Hint.Text = Msg
	Hint.TextColor3 = C.Gold
	task.delay(4, function()
		if My == HintToken and Hint.Parent then Hint.Text = POUCH_HINT Hint.TextColor3 = C.TextDim end
	end)
end

function Local.MovePin(Id: string, To: number)
	local Ok, Msg = Local.Call(`MovePin`, Id, To)
	if not Ok then Local.PouchSay(Msg or `Couldn't move it. Try again.`) end
end

function Local.MoveSelected(Dir: number)
	local Pinned = State and State.Pinned or {}
	local At = Selected and Selected.kind == `Snack` and table.find(Pinned, Selected.id)
	if not At then Local.PouchSay(`Pick a snack in your pouch first.`) return end
	local To = At + Dir
	if To < 1 or To > #Pinned then return end
	Local.MovePin(Selected.id, To)
end

function Local.PouchAt(Pos: Vector3): number?
	for I, P in (Ui and Ui.Pouch) or {} do
		local A, S = P.Root.AbsolutePosition, P.Root.AbsoluteSize
		if Pos.X >= A.X and Pos.X <= A.X + S.X and Pos.Y >= A.Y and Pos.Y <= A.Y + S.Y then return I end
	end
	return nil
end

-- the slot being dragged dims; the one under the pointer gets a gold edge
function Local.DragMarks(From: number?, Over: number?)
	for I, P in (Ui and Ui.Pouch) or {} do
		local Mark = P.Root:FindFirstChild(`NHDrag`)
		local Want = if I == From then `From` elseif I == Over then `Over` else nil
		if not Want then
			if Mark then Mark:Destroy() end
		else
			if not Mark then
				Mark = Instance.new(`Frame`)
				Mark.Name = `NHDrag`
				Mark.BorderSizePixel = 0
				Mark.BackgroundColor3 = Color3.new(0, 0, 0)
				Mark.AnchorPoint = Vector2.new(0.5, 0.5)
				Mark.Position = UDim2.fromScale(0.5, 0.5)
				Mark.Size = UDim2.new(1, -4, 1, -4)
				Mark.ZIndex = 9
				local St = Instance.new(`UIStroke`) St.Thickness = 2 St.Parent = Mark
				Mark.Parent = P.Root
			end
			Mark.BackgroundTransparency = if Want == `From` then 0.55 else 1
			local St = Mark:FindFirstChildOfClass(`UIStroke`)
			if St then St.Color = if Want == `From` then C.TextDim else C.Gold end
		end
	end
end

function Local.HookDrag()
	local function isPress(Input) return Input.UserInputType == Enum.UserInputType.MouseButton1 or Input.UserInputType == Enum.UserInputType.Touch end
	for I, P in Ui.Pouch do
		P.Root.InputBegan:Connect(function(Input)
			if not isPress(Input) then return end
			local Pid = State and State.Pinned and State.Pinned[I]
			if Pid then Drag = { From = I; Id = Pid; Start = Input.Position; On = false } end
		end)
	end
	UserInputService.InputChanged:Connect(function(Input)
		if not Drag then return end
		if Input.UserInputType ~= Enum.UserInputType.MouseMovement and Input.UserInputType ~= Enum.UserInputType.Touch then return end
		if not Drag.On then
			if (Input.Position - Drag.Start).Magnitude < 8 then return end
			Drag.On = true
			NoClickUntil = math.huge -- a drag isn't a click
		end
		Local.DragMarks(Drag.From, Local.PouchAt(Input.Position))
	end)
	UserInputService.InputEnded:Connect(function(Input)
		if not (Drag and isPress(Input)) then return end
		local D = Drag
		Drag = nil
		Local.DragMarks(nil, nil)
		if not D.On then return end
		NoClickUntil = os.clock() + 0.25
		local To = Local.PouchAt(Input.Position)
		if To and To ~= D.From and Ui.Gui.Enabled then Local.MovePin(D.Id, math.min(To, #(State and State.Pinned or {}))) end
	end)
end

-- the three loadout chips; the active one is gold
function Local.RefreshLoadouts()
	local Root = Ui and Ui.Loadouts
	if not Root then return end
	local Active = State and State.Loadout or Items.Loadouts[1]
	if Root:GetAttribute(`Active`) == Active then return end
	Root:SetAttribute(`Active`, Active)
	local Sel = GuiService.SelectedObject
	local Refocus = Sel and Sel:IsDescendantOf(Root) and Sel.Name or nil
	for _, Ch in Root:GetChildren() do if Ch:IsA(`GuiObject`) then Ch:Destroy() end end
	for K, Name in Items.Loadouts do
		local On = Name == Active
		local B = Kit.Button({ text = Name; style = if On then `gold` else `default`; Size = UDim2.fromOffset(92, 28); Position = UDim2.fromOffset(0, (K - 1) * 32); Parent = Root;
			onClick = function()
				if On then Local.PouchSay(`{Name} is on your hotbar now.`) return end
				local Ok, Msg = Local.Call(`Loadout`, Name)
				Local.PouchSay(Msg or (if Ok then `{Name} loadout.` else `Couldn't switch. Try again.`))
			end })
		if typeof(B) == `Instance` then B.Name = `Loadout{Name}` end
	end
	local B = Refocus and Root:FindFirstChild(Refocus)
	if B and B:IsA(`GuiButton`) then GuiService.SelectedObject = B end
end

function Local.RefreshPouch()
	Local.RefreshLoadouts() -- (inventory QOL batch 7)
	local Pinned = State and State.Pinned or {}"""),
(LOCK, r"""			P.Root.Activated:Connect(function()
				local Pid = State and State.Pinned and State.Pinned[I]""",
       r"""			P.Root.Activated:Connect(function()
				if os.clock() < NoClickUntil then return end -- (inventory QOL batch 7) the end of a drag
				local Pid = State and State.Pinned and State.Pinned[I]"""),
(LOCK, r"""(if Pinned then `in your pouch (hotbar)` else `not in your pouch`)""",
       r"""(if Pinned then `pouch slot {table.find(State.Pinned, Id)} (move it with \u{2039} \u{203A})` else `not in your pouch`)"""),
]

# ---- then, applied on top: the fixes from the first play-test (q7b)
# Batch 7 fixes from the first play-test: pouch snacks lead the hotbar (keys 1-4 = pouch 1-4, even after a loadout
# switch re-makes the tools), and ASCII arrows (the UI fonts have no single guillemets).
HUD = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitHud"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

EDITS_FIX = [
(HUD, r"""	-- (inventory QOL batch 7) snacks follow your pouch order (the tool's NHPinIndex), inside the slots they already hold
	local At, Snacks = {}, {}
	for I, Tool in Order do
		if typeof(Tool:GetAttribute(`NHPinIndex`)) == `number` then table.insert(At, I) table.insert(Snacks, Tool) end
	end
	table.sort(Snacks, function(A, B) return A:GetAttribute(`NHPinIndex`) < B:GetAttribute(`NHPinIndex`) end)
	for K, I in At do Order[I] = Snacks[K] end""",
      r"""	-- (inventory QOL batch 7) your pouch snacks come first, in pouch order (the tool's NHPinIndex), so keys 1-4 are your
	-- pouch even after a loadout switch re-makes the tools; everything else keeps its order after them
	local Snacks, Rest = {}, {}
	for _, Tool in Order do
		if typeof(Tool:GetAttribute(`NHPinIndex`)) == `number` then table.insert(Snacks, Tool) else table.insert(Rest, Tool) end
	end
	table.sort(Snacks, function(A, B) return A:GetAttribute(`NHPinIndex`) < B:GetAttribute(`NHPinIndex`) end)
	Order = Snacks
	for _, Tool in Rest do table.insert(Order, Tool) end"""),
(LOCK, r"""local POUCH_HINT = `Drag a slot to move it, or pick a snack and press \u{2039} \u{203A}.` -- (inventory QOL batch 7)""",
       r"""local POUCH_HINT = `Drag a slot to move it, or pick a snack and press &lt; &gt;.` -- (inventory QOL batch 7)"""),
(LOCK, r"""text = if Dir < 0 then `\u{2039}` else `\u{203A}`;""",
       r"""text = if Dir < 0 then `<` else `>`;"""),
(LOCK, r"""(if Pinned then `pouch slot {table.find(State.Pinned, Id)} (move it with \u{2039} \u{203A})` else `not in your pouch`)""",
       r"""(if Pinned then `pouch slot {table.find(State.Pinned, Id)}` else `not in your pouch`)"""),
]
