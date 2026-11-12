--[[
	Locker (client). Controllers.Gui.Locker
	  `             your Locker, laid out like the owner's reference (2026-11-02):
	                  left   your character (kit CharacterPreview) with equipment slots around it: Head, Face, Neck
	                         (worn gear) on the left, your Weapon class and active Snack buff on the right; the Gear
	                         Scale under it adds up what your worn gear gives
	                  right  the Backpack: tabs All / Gear / Snacks, a 5-wide grid (each slot shows the item in 3D),
	                         a tooltip on hover, and the selected item's actions under the grid
	                         (snacks: Use, To pouch / Unpin, Drop with a confirm; gear: worn or "at a wardrobe");
	                         the Pouch under it: your four hotbar snacks (click one to select it)
	  Concession    the stand's menu (prompt attribute NHConcession): every snack with its price, what you carry,
	                Buy 1 / Buy 5. Closes when you walk away.
	Built only from the UI kit (CharacterPreview, Panel, TabBar, ItemGrid / ItemSlot, Button, Plate, Text).
	Server: Services.Features.Inventory (remotes ReplicatedStorage.NHInventory).
]]
local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Items = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Items`))
local GearCfg = require(ReplicatedStorage.Config.Gear)
local BoardsCfg = require(ReplicatedStorage.Config:WaitForChild(`Boards`))
local CliqueCfg = require(ReplicatedStorage.Config:WaitForChild(`Cliques`))
-- (1.28) prices after clique discounts (Config.Cliques.PriceFactor; the server charges the same)
local function Price(Shop: string, Base: number): number
	return math.ceil(Base * CliqueCfg.PriceFactor(Players.LocalPlayer, Shop))
end

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local YEN = `\u{A5}`
local TOGGLE_KEY = Enum.KeyCode.Backquote -- ` (owner, 2026-11-02; G is the introduce-yourself key)
local TABS = { `All`, `Gear`, `Snacks`, `Boards`, `Kit` } -- (kit 1.79) Kit: the everyday kit (Controllers.Gui.KitUi)
local KitUi = require(script.Parent:WaitForChild(`KitUi`))

local Shared = {}
local Local = {}
local Ui = nil
local State = nil
local Tab = 1
local Selected = nil -- { kind = "Snack" | "Gear", id }
local StandAt: Instance? = nil
local ConfirmDrop = nil
local LastIndex = nil -- (inventory audit 1.90) where the selection was, so it stays put when a stack runs out
local OpenToken = 0 -- (inventory audit 1.90) a close during the opening round trip wins
local GuiService = game:GetService(`GuiService`)

---| helpers |---

function Local.Remote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHInventory`)
	return F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
end

function Local.Call(Name: string, ...)
	local R = Local.Remote(Name)
	if not R then return nil end
	local Ok, A, B = pcall(R.InvokeServer, R, ...)
	if not Ok then return nil end
	return A, B
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; TextWrapped = true; RichText = true;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.Screen(Name: string, Order: number, ScaleOpts: {}?): ScreenGui
	local G = Instance.new(`ScreenGui`)
	G.Name = Name
	G.ResetOnSpawn = false
	G.DisplayOrder = Order
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = false
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G, ScaleOpts)
	return G
end

-- a little 3D view of the item inside a slot (gear template, or the snack's hand prop)
function Local.Model(Kind: string, Id: string): Instance?
	if Kind == `Kit` then return KitUi.ModelFor(Id) end -- (kit 1.79)
	if Kind == `Board` then
		local Lib = ReplicatedStorage:FindFirstChild(`NHSkate`)
		local Store = Lib and Lib:FindFirstChild(`Boards`)
		local T = Store and Store:FindFirstChild(Id)
		if not T then return nil end
		local M = T:Clone()
		for _, D in M:GetDescendants() do if D:IsA(`ProximityPrompt`) or D:IsA(`Sound`) then D:Destroy() end end
		M:PivotTo(CFrame.Angles(math.rad(-28), math.rad(35), 0)) -- tipped up so the deck art shows
		return M
	end
	if Kind == `Gear` then
		local Store = ReplicatedStorage:FindFirstChild(`NHGear`)
		local T = Store and Store:FindFirstChild(Id)
		return T and T:Clone()
	end
	local It = Items.ById[Id]
	if not It then return nil end
	-- (batch 54) the item's modelled hand prop when it's in (ReplicatedStorage.NHSnacks.<Id>.Handle)
	local Lib = ReplicatedStorage:FindFirstChild(`NHSnacks`)
	local Tpl = Lib and Lib:FindFirstChild(Id)
	if Tpl and Tpl:FindFirstChild(`Handle`) then
		local M = Tpl:Clone() -- the whole model, so the glass (welded in the hand, not here) moves with it
		M:PivotTo(CFrame.Angles(0, math.rad(-25), 0))
		return M
	end
	local P = Instance.new(`Part`)
	P.Anchored = true
	P.Color = It.Prop.Color
	P.Material = Enum.Material.SmoothPlastic
	local Shape = It.Prop.Shape
	if Shape == `Can` then P.Shape = Enum.PartType.Cylinder P.Size = Vector3.new(0.75, 0.42, 0.42) P.CFrame = CFrame.Angles(0, 0, math.rad(90))
	elseif Shape == `Bottle` then P.Shape = Enum.PartType.Cylinder P.Size = Vector3.new(0.95, 0.36, 0.36) P.CFrame = CFrame.Angles(0, 0, math.rad(90)) P.Material = Enum.Material.Glass P.Transparency = 0.2
	elseif Shape == `Box` then P.Size = Vector3.new(0.75, 0.32, 0.55) P.Material = Enum.Material.Wood P.CFrame = CFrame.Angles(math.rad(20), math.rad(30), 0)
	elseif Shape == `Bone` then P.Shape = Enum.PartType.Cylinder P.Size = Vector3.new(1.0, 0.16, 0.16) P.Material = Enum.Material.Marble P.CFrame = CFrame.Angles(math.rad(10), math.rad(35), math.rad(25)) -- (beasts) a trophy bone
	elseif Shape == `Locket` then P.Shape = Enum.PartType.Cylinder P.Size = Vector3.new(0.12, 0.62, 0.62) P.Material = Enum.Material.Metal P.CFrame = CFrame.Angles(0, math.rad(70), math.rad(10)) -- (beasts) a trophy locket
	elseif Shape == `Fang` then P.Shape = Enum.PartType.Wedge P.Size = Vector3.new(0.22, 0.85, 0.38) P.CFrame = CFrame.Angles(math.rad(-12), math.rad(40), math.rad(14)) -- (beasts) a trophy fang
	else P.Shape = Enum.PartType.Ball P.Size = Vector3.new(0.55, 0.55, 0.55) end
	return P
end

function Local.View(Slot: GuiObject, Kind: string, Id: string)
	local Old = Slot:FindFirstChild(`NHView`)
	if Old then Old:Destroy() end
	local M = Local.Model(Kind, Id)
	if not M then return end
	local V = Instance.new(`ViewportFrame`)
	V.Name = `NHView`
	V.BackgroundTransparency = 1
	V.AnchorPoint = Vector2.new(0.5, 0.5)
	V.Position = UDim2.fromScale(0.5, 0.47)
	V.Size = UDim2.fromScale(0.72, 0.72)
	V.ZIndex = 6
	V.Ambient = Color3.fromRGB(150, 140, 130)
	V.LightColor = Color3.fromRGB(255, 236, 210)
	V.LightDirection = Vector3.new(-1, -1.4, -0.8)
	for _, D in M:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true end end
	if M:IsA(`BasePart`) then M.Anchored = true end
	M.Parent = V
	local CF, Size
	if M:IsA(`Model`) then CF, Size = M:GetBoundingBox() else CF, Size = M.CFrame, M.Size end
	local R = math.max(Size.X, Size.Y, Size.Z)
	local Cam = Instance.new(`Camera`)
	Cam.FieldOfView = 30
	Cam.CFrame = CFrame.lookAt(CF.Position + Vector3.new(0.55, 0.35, -1).Unit * R * 2.3, CF.Position)
	Cam.Parent = V
	V.CurrentCamera = Cam
	V.Parent = Slot
	-- the kit draws the item's name when there's no icon: the 3D view replaces it
	local Name = Slot:FindFirstChild(`ItemName`, true)
	if Name and Name:IsA(`TextLabel`) then Name.TextTransparency = 1 Name.TextStrokeTransparency = 1 end
end

function Local.BuffText(): string?
	local Id = Player:GetAttribute(`NHSnackBuff`)
	local Until = Player:GetAttribute(`NHSnackBuffUntil`)
	local It = Id and Items.ById[Id]
	if not (It and Until) then return nil end
	local Left = math.max(0, Until - workspace:GetServerTimeNow())
	if Left <= 0 then return nil end
	return `{It.Name}: {Items.Describe(It):gsub(` for .*$`, ``)} ({string.format(`%d:%02d`, Left // 60, Left % 60)} left)`
end

---| the Locker |---
-- Layout (owner's reference, 2026-11-02): your character in the middle of the left panel with equipment slots
-- around it (Head / Face / Neck on the left, Weapon / Snack buff on the right) and a Gear Scale under it; the
-- Backpack grid on the right with a hover tooltip, and the Pouch (your four hotbar snacks) under it.

local EQUIP = {
	{ Key = `Head`; Label = `Head`; Side = -1; Row = 0 };
	{ Key = `Face`; Label = `Face`; Side = -1; Row = 1 };
	{ Key = `Neck`; Label = `Neck`; Side = -1; Row = 2 };
	{ Key = `Weapon`; Label = `Weapon`; Side = 1; Row = 0 };
	{ Key = `Snack`; Label = `Snack buff`; Side = 1; Row = 1 };
}

function Local.Build()
	-- (inventory audit 1.90) the whole 1200 x 680 row fits on a phone (its panels are placed by offset, so the panel
	-- clamp can't shrink them one by one)
	local G = Local.Screen(`NHLocker`, 12, { fitWidth = 1200; fitHeight = 680 })
	G:SetAttribute(`NHNoPanelClamp`, true)
	local Row = Instance.new(`Frame`)
	Row.Name = `Row`
	Row.BackgroundTransparency = 1
	Row.AnchorPoint = Vector2.new(0.5, 0.5)
	Row.Position = UDim2.fromScale(0.5, 0.5)
	Row.Size = UDim2.fromOffset(1200, 680)
	Row.Parent = G
	-- left: you, with your equipment around you
	local Prev, PrevApi = Kit.CharacterPreview({ Name = `Character`; footer = `Locker`; Position = UDim2.fromOffset(0, 0); Size = UDim2.fromOffset(560, 470); Parent = Row })
	-- the preview's own "Return to Main Menu" button isn't wanted here
	local Back = Prev:FindFirstChild(`Back`, true)
	if Back and Back:IsA(`GuiObject`) then Back.Visible = false end
	-- camera audit 2026-11-02: with the button hidden, let the stage use the whole panel so you're framed head to toe
	local Stage = Prev:FindFirstChild(`Stage`, true)
	if Stage and Stage:IsA(`GuiObject`) then Stage.Position = UDim2.fromOffset(0, 0) Stage.Size = UDim2.new(1, 0, 1, -28) end
	local Equip = {}
	for _, E in EQUIP do
		local X = if E.Side < 0 then UDim2.new(0, 34, 0, 0) else UDim2.new(1, -34 - 86, 0, 0)
		local Slot, SlotApi = Kit.ItemSlot({ Name = `Equip{E.Key}`; size = 86; Position = X + UDim2.fromOffset(0, 64 + E.Row * 120); Parent = Prev })
		Slot.ZIndex = 12
		Kit.Text({ Text = E.Label; Font = Fonts.Title; TextSize = 14; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 1, 4); Size = UDim2.new(1, 20, 0, 16); ZIndex = 12; Parent = Slot })
		Equip[E.Key] = { Root = Slot; Api = SlotApi }
	end
	local _, ScaleApi = Kit.Panel({ title = `Gear Scale`; Name = `GearScale`; ornament = `thin`; Position = UDim2.fromOffset(0, 482); Size = UDim2.fromOffset(560, 198); Parent = Row })
	-- right: the backpack and the pouch
	local _, BagApi = Kit.Panel({ title = `Backpack`; Name = `Backpack`; Position = UDim2.fromOffset(576, 0); Size = UDim2.fromOffset(624, 500); Parent = Row })
	local Bag = BagApi.Content
	local _, YenApi = Kit.Plate({ text = `{YEN} 0`; Name = `Yen`; Size = UDim2.fromOffset(140, 32); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -6, 0, 0); Parent = Bag })
	local _, TabApi = Kit.TabBar({ tabs = TABS; selected = Tab; textSize = 16; Name = `Tabs`;
		Size = UDim2.new(1, -160, 0, 36); Position = UDim2.fromOffset(4, 0); Parent = Bag;
		onChanged = function(I) Tab = I Local.Refresh() end })
	local Grid, GridApi = Kit.ItemGrid({ Name = `Grid`; slotSize = 82; gap = 12; showEmpty = 25; showCounter = false;
		Position = UDim2.fromOffset(0, 44); Size = UDim2.new(1, 0, 1, -124); Parent = Bag;
		onSelect = function(Item, I) if Item then LastIndex = I Selected = { kind = Item.kind; id = Item.id } ConfirmDrop = nil Local.ShowCard() end end })
	local Actions = Instance.new(`Frame`)
	Actions.Name = `Actions`
	Actions.BackgroundTransparency = 1
	Actions.Position = UDim2.new(0, 4, 1, -76)
	Actions.Size = UDim2.new(1, -8, 0, 76)
	Actions.Parent = Bag
	local _, PouchApi = Kit.Panel({ title = `Pouch`; Name = `Pouch`; ornament = `thin`; Position = UDim2.fromOffset(576, 512); Size = UDim2.fromOffset(624, 168); Parent = Row })
	local Pouch = {}
	for I = 1, Items.MaxPinned do
		local Slot, SlotApi = Kit.ItemSlot({ Name = `Pouch{I}`; size = 82; Position = UDim2.new(0.5, (I - 1 - (Items.MaxPinned - 1) / 2) * 100 - 41, 0, 14); Parent = PouchApi.Content })
		Pouch[I] = { Root = Slot; Api = SlotApi }
	end
	-- hover tooltip
	local Tip, TipApi = Kit.Panel({ Name = `Tip`; ornament = `thin`; Size = UDim2.fromOffset(270, 150); Visible = false; ZIndex = 40; Parent = G })
	Ui = { Gui = G; Preview = PrevApi; Equip = Equip; Scale = ScaleApi.Content; Yen = YenApi; Tabs = TabApi; Grid = GridApi; GridRoot = Grid;
		Actions = Actions; Pouch = Pouch; Tip = Tip; TipBody = TipApi.Content }
end

function Local.Entries()
	local Out = {}
	if not State then return Out end
	if Tab == 1 or Tab == 2 then
		for _, Id in State.Gear or {} do
			local It = GearCfg.ById[Id]
			if It then
				local Worn = false
				for _, On in State.GearOn or {} do if On == Id then Worn = true end end
				table.insert(Out, { name = It.Name; rarity = It.Rarity; kind = `Gear`; id = Id; worn = Worn; order = 100 + table.find(GearCfg.Rarities, It.Rarity) })
			end
		end
	end
	if Tab == 1 or Tab == 3 then
		for Id, N in State.Items or {} do
			local It = Items.ById[Id]
			-- (beasts) trophies show under All, not Snacks
			local Trophy = It and It.Kind == `Trophy`
			if It and not (Trophy and Tab == 3) then
				table.insert(Out, { name = It.Name; rarity = It.Rarity; count = N; kind = if Trophy then `Trophy` else `Snack`; id = Id; order = It.Order })
			end
		end
	end
	-- (kit 1.79) the everyday kit you own
	if Tab == 1 or Tab == 5 then for _, E in KitUi.Entries() do table.insert(Out, E) end end
	-- every board: yours to equip, the rest to buy (Config.Boards; Services.Features.Skateboard)
	if Tab == 4 then
		local Mine = State.Boards or { Owned = {} }
		for _, B in BoardsCfg.List do
			table.insert(Out, { name = B.Name; rarity = B.Rarity; kind = `Board`; id = B.Id; owned = table.find(Mine.Owned or {}, B.Id) ~= nil;
				equipped = Mine.Equipped == B.Id; order = B.Order })
		end
	end
	local KindRank = { Snack = 1; Kit = 1.5; Trophy = 2; Gear = 3; Board = 4 } -- (beasts) a strict order across the item kinds
	table.sort(Out, function(A, B)
		if A.kind ~= B.kind then return (KindRank[A.kind] or 9) < (KindRank[B.kind] or 9) end
		if A.order ~= B.order then return A.order < B.order end
		return A.name < B.name
	end)
	return Out
end

function Local.Def(Kind: string, Id: string)
	return if Kind == `Gear` then GearCfg.ById[Id] elseif Kind == `Board` then BoardsCfg.ById[Id] elseif Kind == `Kit` then KitUi.Def(Id) else Items.ById[Id]
end

-- a board's ownership line (tooltip and card)
function Local.BoardLine(Id: string): string
	local B = BoardsCfg.ById[Id]
	local Mine = State and State.Boards
	if not B then return `` end
	if Mine and Mine.Equipped == Id then return `Your board  \u{00B7}  B to ride, B again to step off` end
	if Mine and table.find(Mine.Owned or {}, Id) then return `Owned  \u{00B7}  equip it to ride` end
	return `{YEN} {Price(`Boards`, B.Price)}`
end

-- the tooltip follows the mouse over a slot
function Local.HoverTip(Slot: GuiObject, Kind: string, Id: string)
	Slot.MouseEnter:Connect(function()
		local It = Local.Def(Kind, Id)
		if not (Ui and It) then return end
		local B = Ui.TipBody
		Local.Clear(B)
		local RC = Theme.Rarity[It.Rarity] or C.Text
		Local.Label(B, It.Name, 20, { Font = Fonts.Title; Position = UDim2.fromOffset(4, 0); Size = UDim2.new(1, -8, 0, 24) })
		Local.Label(B, string.upper(`{It.Rarity}  \u{00B7}  {if Kind == `Gear` then It.Slot elseif Kind == `Board` then `Skateboard` elseif Kind == `Kit` then `Everyday kit` else (if It.Kind == `Heal` then `Food` elseif It.Kind == `Trophy` then `Trophy` elseif It.Kind == `Prank` then `Prank kit` else `Buff`)}`), 12,
			{ Font = Fonts.Title; TextColor3 = RC; Position = UDim2.fromOffset(4, 26); Size = UDim2.new(1, -8, 0, 14) })
		local Effect = if Kind == `Gear` then GearCfg.Describe(It) elseif Kind == `Board` then Local.BoardLine(Id) elseif Kind == `Kit` then It.Use else Items.Describe(It)
		Local.Label(B, Effect, 15, { TextColor3 = Color3.fromRGB(150, 205, 140); Position = UDim2.fromOffset(4, 46); Size = UDim2.new(1, -8, 0, 36) })
		Local.Label(B, `<i>{if Kind == `Gear` then `From a gear chest or the School Store.` else It.Text}</i>`, 14,
			{ TextColor3 = C.TextDim; Position = UDim2.fromOffset(4, 84); Size = UDim2.new(1, -8, 0, 36) })
		Ui.Tip.Visible = true
		Local.MoveTip()
	end)
	Slot.MouseLeave:Connect(function() if Ui then Ui.Tip.Visible = false end end)
end

function Local.MoveTip()
	if not (Ui and Ui.Tip.Visible) then return end
	local M = UserInputService:GetMouseLocation()
	local Scale = Ui.Gui:FindFirstChildOfClass(`UIScale`)
	local K = if Scale then Scale.Scale else 1
	local Inset = game:GetService(`GuiService`):GetGuiInset()
	Ui.Tip.Position = UDim2.fromOffset((M.X + 18) / K, (M.Y - Inset.Y + 12) / K)
end

function Local.Clear(Parent: Instance)
	for _, Ch in Parent:GetChildren() do if not Ch:IsA(`UIBase`) then Ch:Destroy() end end
end

function Local.Refresh()
	if not Ui then return end
	Ui.Tip.Visible = false -- (audit) the slots are rebuilt, so the hovered one never gets its MouseLeave
	local List = Local.Entries()
	local Sel = GuiService.SelectedObject -- (inventory audit 1.90) a gamepad cursor in the grid stays in the grid
	local InGrid = Sel ~= nil and Sel:IsDescendantOf(Ui.GridRoot)
	Ui.Grid:SetItems(List)
	for I, E in List do
		local Slot = Ui.GridRoot:FindFirstChild(`Slot{I}`, true)
		if Slot then
			Local.View(Slot, E.kind, E.id)
			Local.HoverTip(Slot, E.kind, E.id)
			if E.kind == `Board` and (E.equipped or not E.owned) then
				Kit.Text({ Name = `Worn`; Text = if E.equipped then `RIDING` else `{YEN} {Price(`Boards`, BoardsCfg.ById[E.id].Price)}`; Font = Fonts.Title; TextSize = 11;
					TextColor3 = if E.equipped then C.Gold else C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
					AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -2); Size = UDim2.new(1, 0, 0, 14); ZIndex = 9; Parent = Slot })
			end
			if E.worn then
				Kit.Text({ Name = `Worn`; Text = `WORN`; Font = Fonts.Title; TextSize = 11; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center;
					AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -2); Size = UDim2.new(1, 0, 0, 14); ZIndex = 9; Parent = Slot })
			end
		end
	end
	Ui.Yen.Label.Text = `{YEN} {State and State.Yen or 0}`
	Local.RefreshEquip()
	Local.RefreshPouch()
	Local.RefreshScale()
	local Keep = nil
	for I, E in List do if Selected and E.kind == Selected.kind and E.id == Selected.id then Keep = I end end
	if Keep then Ui.Grid:Select(Keep) elseif List[1] then Ui.Grid:Select(math.clamp(LastIndex or 1, 1, #List)) else Selected = nil Local.ShowCard() end
	if InGrid then
		local S = Ui.GridRoot:FindFirstChild(`Slot{Keep or math.clamp(LastIndex or 1, 1, math.max(#List, 1))}`, true)
		if S and S:IsA(`GuiObject`) then GuiService.SelectedObject = S end
	end
	Local.TickBuff()
end

function Local.RefreshEquip()
	local On = State and State.GearOn or {}
	for _, Slot in { `Head`, `Face`, `Neck` } do
		local E = Ui.Equip[Slot]
		local Id = On[Slot]
		local It = Id and GearCfg.ById[Id]
		E.Api:SetItem(if It then { name = It.Name; rarity = It.Rarity } else nil)
		if It then Local.View(E.Root, `Gear`, Id) else local V = E.Root:FindFirstChild(`NHView`) if V then V:Destroy() end end
		if It and not E.Tipped then E.Tipped = true end
	end
	-- weapon class (Katana / Fist / Claws ...) from your profile
	local Weapon = (State and State.Weapon) or Player:GetAttribute(`Weapon`)
	Ui.Equip.Weapon.Api:SetItem(if Weapon then { name = Weapon; rarity = `Rare` } else nil)
	local Buff = Player:GetAttribute(`NHSnackBuff`)
	local It = Buff and Items.ById[Buff]
	Ui.Equip.Snack.Api:SetItem(if It then { name = It.Name; rarity = It.Rarity } else nil)
	if It then Local.View(Ui.Equip.Snack.Root, `Snack`, Buff) else local V = Ui.Equip.Snack.Root:FindFirstChild(`NHView`) if V then V:Destroy() end end
	if Player.Character then pcall(function() Ui.Preview:Watch(Player.Character) end) end
end

-- the snack-buff slot empties itself when the buff runs out
function Local.RefreshEquipBuff()
	local Buff = Player:GetAttribute(`NHSnackBuff`)
	if Buff ~= Ui.LastBuff then Ui.LastBuff = Buff Local.RefreshEquip() end
end

function Local.RefreshPouch()
	local Pinned = State and State.Pinned or {}
	for I, P in Ui.Pouch do
		local Id = Pinned[I]
		local N = Id and State.Items[Id] or 0
		local It = Id and Items.ById[Id] or nil
		P.Api:SetItem(if It then { name = It.Name; rarity = It.Rarity; count = N } else nil)
		if It then Local.View(P.Root, `Snack`, Id) else local V = P.Root:FindFirstChild(`NHView`) if V then V:Destroy() end end
		-- (inventory QOL 1.91) a pinned snack you've run out of shows greyed, waiting for the restock; click it to unpin
		local Shade = P.Root:FindFirstChild(`NHEmpty`)
		if It and N <= 0 then
			if not Shade then
				Shade = Instance.new(`Frame`)
				Shade.Name = `NHEmpty`
				Shade.BackgroundColor3 = Color3.new(0, 0, 0)
				Shade.BackgroundTransparency = 0.45
				Shade.BorderSizePixel = 0
				Shade.AnchorPoint = Vector2.new(0.5, 0.5)
				Shade.Position = UDim2.fromScale(0.5, 0.5)
				Shade.Size = UDim2.new(1, -8, 1, -8)
				Shade.ZIndex = 7
				Shade.Parent = P.Root
				Local.Label(Shade, `Restock\n<font size="11">click to unpin</font>`, 14, { TextXAlignment = Enum.TextXAlignment.Center;
					TextYAlignment = Enum.TextYAlignment.Bottom; Position = UDim2.fromOffset(0, -4); Size = UDim2.fromScale(1, 1); ZIndex = 7 })
			end
			Shade.Visible = true
		elseif Shade then
			Shade.Visible = false
		end
		if not P.Hooked then
			P.Hooked = true
			-- click a pouch slot to select that snack in the backpack
			P.Root.Activated:Connect(function()
				local Pid = State and State.Pinned and State.Pinned[I]
				if not Pid then return end
				-- (inventory audit 1.90) an empty pin (you ran out) is cleared by clicking it
				if (State.Items[Pid] or 0) <= 0 then Local.Call(`Pin`, Pid, false) return end
				Selected = { kind = `Snack`; id = Pid } Tab = 1 Ui.Tabs:Select(1, true) Local.Refresh()
			end)
		end
	end
end

-- what your worn gear adds up to, in three columns
function Local.RefreshScale()
	local B = Ui.Scale
	Local.Clear(B)
	local Sum = {}
	for _, Id in (State and State.GearOn) or {} do
		local It = GearCfg.ById[Id]
		for K, V in (It and It.Effects) or {} do Sum[K] = (Sum[K] or 0) + V end
	end
	local Order = { `DamageDealt`, `DamageTaken`, `MaxHealth`, `PostureGain`, `Stealth`, `NightPower`, `CombatExp`, `AllExp` }
	for I, K in Order do
		local V = Sum[K] or 0
		local Col = (I - 1) // 3
		local RowN = (I - 1) % 3
		local Text
		if K == `MaxHealth` then Text = if V ~= 0 then `+{V}` else `\u{2014}`
		else
			local P = math.floor(math.abs(V) * 1000 + 0.5) / 10
			Text = if V ~= 0 then `+{P}%` else `\u{2014}`
		end
		Local.Label(B, `{GearCfg.StatNames[K] or K}:  <font color="#{(if V ~= 0 then Color3.fromRGB(150, 205, 140) else C.TextDim):ToHex()}">{Text}</font>`, 16,
			{ Position = UDim2.new(Col / 3, 10, 0, 8 + RowN * 30); Size = UDim2.new(1 / 3, -14, 0, 24) })
	end
	Local.Label(B, `<i>Gear changes at a locker-room wardrobe (Outfit tab).</i>`, 13,
		{ TextColor3 = C.TextDim; Position = UDim2.new(0, 10, 1, -22); Size = UDim2.new(1, -20, 0, 18) })
end

function Local.TickBuff()
	if not Ui then return end
	local T = Local.BuffText()
	local Footer = if T then `Snack buff \u{2014} {T}` else "`  Close    \u{00B7}    Hover to inspect    \u{00B7}    Click to select"
	pcall(function() Ui.Preview:SetFooter(Footer) end)
end

-- (inventory audit 1.90) a line under the selected item (a refusal from the server)
function Local.Say(Msg: string)
	local Line = Ui and Ui.Actions:FindFirstChild(`Info`, true)
	if Line and Line:IsA(`TextLabel`) then Line.Text = Msg end
end

-- (inventory audit 1.90) the card is rebuilt on every change: put a gamepad cursor back on the button it was on
function Local.ShowCard()
	if not Ui then return end
	local Sel = GuiService.SelectedObject
	local Refocus = Sel and Sel:IsDescendantOf(Ui.Actions) and Sel.Name or nil
	Local.BuildCard()
	local B = Refocus and Ui.Actions:FindFirstChild(Refocus)
	if B and B:IsA(`GuiButton`) then GuiService.SelectedObject = B end
end

local EMPTY = { -- (inventory audit 1.90) the empty text for each tab
	`Your backpack is empty. The concession stand by the west doors sells snacks; gear comes from chests and the School Store.`;
	`No gear yet. It comes from gear chests and the School Store.`;
	`No snacks. The concession stand by the west doors sells them.`;
	`No boards.`;
	`No everyday kit yet. MORROW & VANE and THE WICK & KETTLE sell it.`;
}

-- the selected item's actions, under the grid
function Local.BuildCard()
	local A = Ui.Actions
	Local.Clear(A)
	if not (Selected and State) then
		Local.Label(A, `<i>{if State then EMPTY[Tab] or EMPTY[1] else `Loading your locker...`}</i>`, 15,
			{ TextColor3 = C.TextDim; Position = UDim2.fromOffset(4, 6); Size = UDim2.new(1, -8, 1, -12) })
		return
	end
	if Selected.kind == `Kit` then -- (kit 1.79)
		local It = KitUi.Def(Selected.id)
		if not It then return end
		Local.Label(A, It.Name, 20, { Font = Fonts.Title; Position = UDim2.fromOffset(4, 4); Size = UDim2.new(1, -360, 0, 24) })
		local Info = Local.Label(A, ``, 14, { Name = `Info`; TextColor3 = Theme.Rarity[It.Rarity] or C.Text; Position = UDim2.fromOffset(4, 32); Size = UDim2.new(1, -360, 0, 40) })
		KitUi.Card(A, Selected.id, Info, function() Local.Refresh() end)
		return
	end
	local Gear = Selected.kind == `Gear`
	local It = Local.Def(Selected.kind, Selected.id)
	if not It then return end
	local RC = Theme.Rarity[It.Rarity] or C.Text
	Local.Label(A, It.Name, 20, { Font = Fonts.Title; Position = UDim2.fromOffset(4, 4); Size = UDim2.new(1, -360, 0, 24) })
	local Info = Local.Label(A, ``, 14, { Name = `Info`; TextColor3 = RC; Position = UDim2.fromOffset(4, 32); Size = UDim2.new(1, -360, 0, 40) })
	if Gear then
		local Worn = false
		for _, On in State.GearOn or {} do if On == Selected.id then Worn = true end end
		Info.Text = (if Worn then `Worn  \u{00B7}  ` else ``) .. GearCfg.Describe(It)
		Kit.Button({ text = if Worn then `Worn` else `Wardrobe only`; enabled = false; Size = UDim2.fromOffset(170, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A })
		return
	end
	if Selected.kind == `Board` then
		local Id = Selected.id
		local Mine = State.Boards or { Owned = {} }
		local Own = table.find(Mine.Owned or {}, Id) ~= nil
		Info.Text = Local.BoardLine(Id) .. `  \u{00B7}  ` .. It.Text
		local function call(Name: string)
			local F = ReplicatedStorage:FindFirstChild(`NHSkateboard`)
			local R = F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
			if not R then Info.Text = `Skateboards aren't ready yet.` return end
			local Ok, _, Msg = pcall(R.InvokeServer, R, Id)
			local S = Local.Call(`Get`)
			if S then State = S Local.Refresh() end
			local Line = Ui and Ui.Actions:FindFirstChild(`Info`, true)
			if Ok and Msg and Line and Line:IsA(`TextLabel`) then Line.Text = Msg end
		end
		if Own then
			Kit.Button({ text = if Mine.Equipped == Id then `Riding` else `Equip`; style = `gold`; enabled = Mine.Equipped ~= Id;
				Size = UDim2.fromOffset(150, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
				onClick = function() call(`Equip`) end })
		else
			Kit.Button({ text = `Buy  {YEN} {Price(`Boards`, It.Price)}`; style = `gold`; Size = UDim2.fromOffset(170, 40); AnchorPoint = Vector2.new(1, 0.5);
				Position = UDim2.new(1, 0, 0.5, 0); Parent = A; onClick = function() call(`Buy`) end })
		end
		return
	end
	local Id = Selected.id
	local Have = State.Items[Id] or 0
	-- (beasts) a trophy: kept, not used or pinned; you can still drop it
	if Selected.kind == `Trophy` then
		Info.Text = `You have {Have}  \u{00B7}  {Items.Describe(It)}`
		local DropB = Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
			onClick = function()
				if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
				ConfirmDrop = nil
				Local.ShowCard()
				local Ok, Msg = Local.Call(`Drop`, Id, 1)
				if not Ok then Local.Say(Msg or `Couldn't drop it. Try again.`) end
			end })
		if typeof(DropB) == `Instance` then DropB.Name = `Drop` end
		return
	end
	local Pinned = table.find(State.Pinned or {}, Id) ~= nil
	Info.Text = `You carry {Have}  \u{00B7}  ` .. (if Pinned then `in your pouch (hotbar)` else `not in your pouch`)
	local UseB = Kit.Button({ text = `Use`; style = `gold`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -232, 0.5, 0); Parent = A;
		onClick = function()
			local Ok, Msg = Local.Call(`Use`, Id)
			if not Ok and Msg then Local.Say(Msg) end
		end })
	local PinB = Kit.Button({ text = if Pinned then `Unpin` else `To pouch`; Size = UDim2.fromOffset(112, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -112, 0.5, 0); Parent = A;
		onClick = function()
			local Ok, Msg = Local.Call(`Pin`, Id, not Pinned)
			if not Ok then Local.Say(Msg or `Couldn't change your pouch. Try again.`) end
		end })
	local DropB = Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
		onClick = function()
			if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
			ConfirmDrop = nil
			Local.ShowCard()
			local Ok, Msg = Local.Call(`Drop`, Id, 1)
			if not Ok then Local.Say(Msg or `Couldn't drop it. Try again.`) end
		end })
	-- (inventory audit 1.90) named, so ShowCard can put a gamepad cursor back on the same button
	if typeof(UseB) == `Instance` then UseB.Name = `Use` end
	if typeof(PinB) == `Instance` then PinB.Name = `Pin` end
	if typeof(DropB) == `Instance` then DropB.Name = `Drop` end
end

function Shared.IsOpen(): boolean return Ui ~= nil and Ui.Gui.Enabled end
function Shared.KitChanged() if Ui and Ui.Gui.Enabled then Local.Refresh() end end -- (kit 1.79) Controllers.Gui.KitUi

-- (inventory audit 1.90) opens at once and fills in after the round trip; a close in between wins. Not while
-- dead or in the main menu. Closing drops the preview's clone and its pose loop.
function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Gui.Enabled end
	if On then
		if Player:GetAttribute(`InMainMenu`) == true then return end
		local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
		if not Hum or Hum.Health <= 0 then return end
	end
	OpenToken += 1
	local My = OpenToken
	Ui.Gui.Enabled = On
	if On then
		Local.Refresh()
		pcall(Kit.PlaySound, `Tick`)
		task.spawn(function()
			local S = Local.Call(`Get`)
			pcall(KitUi.Refresh) -- (kit 1.79)
			if My ~= OpenToken or not Ui.Gui.Enabled then return end
			if S then State = S end
			Local.Refresh()
		end)
	else
		Ui.Tip.Visible = false
		pcall(function() Ui.Preview:SetModel(nil) end)
	end
end

---| the concession stand |---

local Stand = nil

-- (inventory QOL 1.92) the stand: tabs by kind of food, a quantity picker on every item, dimmed when you can't afford it
-- or carry 20, the lunch meals during lunch (with a countdown when it's shut), and "Restock my pins". Cells are built
-- once per tab and updated in place on every inventory change.
local STAND_TABS = Items.StandTabs
local RESTOCK_TO = 5 -- Inventory.RESTOCK_TO
local StandTab = 1

function Local.BuildStand()
	local G = Local.Screen(`NHConcessionMenu`, 12)
	local Panel, Api = Kit.Panel({ title = `Concession Stand`; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(960, 640); Parent = G })
	local Body = Api.Content
	Local.Label(Body, `<i>Mrs. Okada's snacks. Food heals over a few seconds; drinks give one buff at a time.</i>`, 17,
		{ TextColor3 = C.TextDim; Size = UDim2.new(1, -200, 0, 24); Position = UDim2.fromOffset(8, 0) })
	local _, YenApi = Kit.Plate({ text = `{YEN} 0`; Size = UDim2.fromOffset(150, 34); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 0, -4); Parent = Body })
	local _, TabApi = Kit.TabBar({ tabs = STAND_TABS; selected = StandTab; textSize = 16; Name = `Tabs`;
		Size = UDim2.new(1, -300, 0, 36); Position = UDim2.fromOffset(4, 32); Parent = Body;
		onChanged = function(I) StandTab = I Local.FillStand() end })
	local Lunch = Local.Label(Body, ``, 15, { Name = `Lunch`; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Right;
		AnchorPoint = Vector2.new(1, 0); Size = UDim2.fromOffset(290, 36); Position = UDim2.new(1, -8, 0, 32) })
	local Grid = Instance.new(`ScrollingFrame`)
	Grid.Name = `Grid`
	Grid.BackgroundTransparency = 1
	Grid.BorderSizePixel = 0
	Grid.Position = UDim2.fromOffset(0, 76)
	Grid.Size = UDim2.new(1, 0, 1, -136)
	Grid.CanvasSize = UDim2.new()
	Grid.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Grid.ScrollBarThickness = 5
	Grid.ScrollBarImageColor3 = C.IronDim
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(200, 240)
	L.CellPadding = UDim2.fromOffset(12, 10)
	L.HorizontalAlignment = Enum.HorizontalAlignment.Center
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = Grid
	Grid.Parent = Body
	local Empty = Local.Label(Body, ``, 17, { Name = `Empty`; TextColor3 = C.TextDim; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.new(1, -40, 0, 60); Position = UDim2.new(0, 20, 0, 160); Visible = false })
	local Status = Local.Label(Body, ``, 17, { Name = `Status`; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Left;
		Size = UDim2.new(1, -540, 0, 24); Position = UDim2.new(0, 10, 1, -44) })
	local _, RestockApi = Kit.Button({ text = `Restock my pins`; style = `gold`; Size = UDim2.fromOffset(330, 40); AnchorPoint = Vector2.new(1, 0);
		Position = UDim2.new(1, -176, 1, -52); Parent = Body; onClick = function() Local.Restock() end })
	Kit.Button({ text = `Close`; style = `ghost`; Size = UDim2.fromOffset(160, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.CloseStand() end })
	Stand = { Gui = G; Grid = Grid; Yen = YenApi; Status = Status; Tabs = TabApi; Lunch = Lunch; Empty = Empty; Restock = RestockApi; Cells = {} }
end

-- the restock: every pinned item on sale, up to RESTOCK_TO each (the server applies daily limits and your Yen)
function Local.RestockPlan(): (number, number)
	local Total, Count = 0, 0
	for _, Id in (State and State.Pinned) or {} do
		local It = Items.ById[Id]
		if It and It.Price and not It.DailyLimit and Items.OnSale(It) then -- prank kits and specials aren't restocked
			local Need = math.max(0, RESTOCK_TO - ((State.Items and State.Items[Id]) or 0))
			Total += Need * Price(`Concession`, It.Price)
			Count += Need
		end
	end
	return Total, Count
end

function Local.Restock()
	local Total, Count = Local.RestockPlan()
	if Count <= 0 then Stand.Status.Text = `Your pins are already stocked ({RESTOCK_TO} each).` return end
	local Ok, Msg = Local.Call(`Restock`, RESTOCK_TO)
	Stand.Status.Text = Msg or (if Ok then `` else `Couldn't restock. Try again.`)
	if Ok then pcall(Kit.PlaySound, `Confirm`) end
end

function Local.StandList(): { any }
	local Tab = STAND_TABS[StandTab] or `All`
	local Out = {}
	local Pool = {}
	for _, It in Items.List do table.insert(Pool, It) end
	for _, It in Items.Lunch or {} do table.insert(Pool, It) end
	for _, It in Pool do
		if It.Special and not Items.OnSale(It) then continue end -- a daily special only on its day
		local Cat = Items.CategoryOf(It)
		if Tab == `All` then
			if It.Lunch and not Items.LunchOpen() then continue end
		elseif Cat ~= Tab then
			continue
		end
		table.insert(Out, It)
	end
	table.sort(Out, function(A, B)
		if (A.Special ~= nil) ~= (B.Special ~= nil) then return A.Special ~= nil end -- today's special first
		return (A.Order or 0) < (B.Order or 0)
	end)
	return Out
end

function Local.FillStand()
	if not Stand then return end
	for _, Ch in Stand.Grid:GetChildren() do if Ch:IsA(`Frame`) then Ch:Destroy() end end
	Stand.Cells = {}
	local MyRace = Player:GetAttribute(`Race`)
	local List = Local.StandList()
	for I, It in List do
		local Cell = Instance.new(`Frame`)
		Cell.Name = It.Id
		Cell.BackgroundTransparency = 1
		Cell.LayoutOrder = I
		Cell.Parent = Stand.Grid
		local Slot, SlotApi = Kit.ItemSlot({ item = { name = It.Name; rarity = It.Rarity; count = nil }; size = 84;
			AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 2); Parent = Cell })
		Local.View(Slot, `Snack`, It.Id)
		Local.Label(Cell, if It.Special then `Today: {It.Name}` else It.Name, 18, { Font = Fonts.Title; TextColor3 = if It.Special then C.Gold else nil;
			TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 90); Size = UDim2.new(1, 0, 0, 22) })
		local Note = It.Special and Items.RaceNote(It, MyRace)
		Local.Label(Cell, Note or Items.Describe(It), 14, { TextColor3 = if Note then Color3.fromRGB(226, 150, 120) else Color3.fromRGB(150, 205, 140);
			TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(4, 112); Size = UDim2.new(1, -8, 0, 36) })
		local Q = { It = It; N = 1; Slot = SlotApi }
		local function setN(N: number)
			Q.N = math.clamp(N, 1, Items.MaxStack)
			Local.UpdateCell(Q)
		end
		local MinusB = Kit.Button({ text = `-`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(6, 154); Parent = Cell; onClick = function() setN(Q.N - 1) end })
		Q.NLabel = Local.Label(Cell, `1`, 20, { Name = `Qty`; Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; TextYAlignment = Enum.TextYAlignment.Center;
			Position = UDim2.fromOffset(40, 154); Size = UDim2.fromOffset(36, 32) })
		local PlusB = Kit.Button({ text = `+`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(78, 154); Parent = Cell; onClick = function() setN(Q.N + 1) end })
		if typeof(MinusB) == `Instance` then MinusB.Name = `Minus` end
		if typeof(PlusB) == `Instance` then PlusB.Name = `Plus` end
		local MaxB = Kit.Button({ text = `Max`; Size = UDim2.fromOffset(76, 32); Position = UDim2.fromOffset(118, 154); Parent = Cell; onClick = function()
			local Unit = Price(`Concession`, It.Price)
			local Room = Items.MaxStack - ((State and State.Items[It.Id]) or 0)
			setN(math.max(1, math.min(Room, if Unit > 0 then math.floor(((State and State.Yen) or 0) / Unit) else Room)))
		end })
		if typeof(MaxB) == `Instance` then MaxB.Name = `Max` end
		local BuyB, BuyApi = Kit.Button({ text = ``; style = `gold`; Size = UDim2.fromOffset(188, 36); Position = UDim2.fromOffset(6, 194); Parent = Cell;
			onClick = function()
				local Ok, Msg = Local.Call(`Buy`, It.Id, Q.N)
				Stand.Status.Text = Msg or ``
				if Ok then pcall(Kit.PlaySound, `Confirm`) Q.N = 1 Local.UpdateCell(Q) end
			end })
		Q.Buy = BuyApi
		if typeof(BuyB) == `Instance` then BuyB.Name = `Buy` end
		local Dim = Instance.new(`Frame`)
		Dim.Name = `Dim`
		Dim.BackgroundColor3 = Color3.new(0, 0, 0)
		Dim.BackgroundTransparency = 0.55
		Dim.BorderSizePixel = 0
		Dim.Size = UDim2.new(1, 0, 0, 150)
		Dim.ZIndex = 20
		Dim.Active = false
		Dim.Visible = false
		Dim.Parent = Cell
		Q.Dim = Dim
		table.insert(Stand.Cells, Q)
		Local.UpdateCell(Q)
	end
	local Tab = STAND_TABS[StandTab]
	Stand.Empty.Visible = #List == 0
	Stand.Empty.Text = if Tab == `Lunch` and not Items.LunchOpen() then `The lunch meals are served at lunch. {Local.LunchLine()}` else `Nothing here today.`
	Local.UpdateStand()
end

-- what changes without rebuilding: what you own, your Yen, what you can afford, lunch and the restock total
function Local.UpdateCell(Q)
	local It = Q.It
	local Have = (State and State.Items[It.Id]) or 0
	local Yen = (State and State.Yen) or 0
	local Unit = Price(`Concession`, It.Price)
	local Room = Items.MaxStack - Have
	local N = math.min(Q.N, math.max(Room, 1))
	Q.N = N
	Q.NLabel.Text = tostring(N)
	Q.Slot:SetItem({ name = It.Name; rarity = It.Rarity; count = if Have > 0 then Have else nil })
	local Full = Room <= 0
	local Shut = not Items.OnSale(It)
	local Afford = Yen >= Unit * N
	Q.Buy:SetText(if Full then `Full ({Items.MaxStack})` elseif Shut then `Not now` elseif N > 1 then `Buy {N}  {YEN}{Unit * N}` else `Buy  {YEN}{Unit}`)
	Q.Buy:SetEnabled(not Full and not Shut and Afford)
	Q.Dim.Visible = Full or Shut or Yen < Unit
end

function Local.LunchLine(): string
	local Open, Secs = Items.LunchInfo()
	if not Secs then return if Open then `Lunch is on.` else `No lunch today.` end
	local T = if Secs >= 3600 then `{math.floor(Secs / 3600)} h {math.floor(Secs % 3600 / 60)} min`
		else `{math.floor(Secs / 60)}:{string.format(`%02d`, math.floor(Secs % 60))}`
	return if Open then `Lunch is on \u{00B7} {T} left` else `Lunch opens in {T}`
end

function Local.UpdateStand()
	if not Stand then return end
	Stand.Yen.Label.Text = `{YEN} {State and State.Yen or 0}`
	for _, Q in Stand.Cells do Local.UpdateCell(Q) end
	Stand.Lunch.Text = Local.LunchLine()
	local Total, Count = Local.RestockPlan()
	Stand.Restock:SetText(if Count > 0 then `Restock my pins  {YEN}{Total}` else `Pins stocked`)
	Stand.Restock:SetEnabled(Count > 0)
end

function Shared.OpenStand(At: Instance?)
	if not Stand then Local.BuildStand() end
	StandAt = At
	local S = Local.Call(`Get`)
	if S then State = S end
	Stand.Status.Text = ``
	Local.FillStand()
	Stand.Gui.Enabled = true
	pcall(Kit.PlaySound, `Tick`)
end

function Shared.CloseStand()
	StandAt = nil
	if Stand then Stand.Gui.Enabled = false end
end

function Shared.OnStart()
	local F = ReplicatedStorage:WaitForChild(`NHInventory`, 30)
	if F then
		F:WaitForChild(`Changed`).OnClientEvent:Connect(function(S)
			if typeof(S) ~= `table` then return end
			State = S
			if Ui and Ui.Gui.Enabled then Local.Refresh() end
			if Stand and Stand.Gui.Enabled then Local.UpdateStand() end -- (inventory QOL 1.92) in place, no rebuild
		end)
	end
	UserInputService.InputBegan:Connect(function(Input)
		if Input.KeyCode ~= TOGGLE_KEY then return end
		if UserInputService:GetFocusedTextBox() or Player:GetAttribute(`InMainMenu`) == true then return end
		Shared.Toggle()
	end)
	ProximityPromptService.PromptTriggered:Connect(function(Prompt)
		if Prompt:GetAttribute(`NHConcession`) then Shared.OpenStand(Prompt.Parent) end
	end)
	local Acc = 0
	RunService.Heartbeat:Connect(function(Dt)
		Local.MoveTip()
		Acc += Dt
		if Acc < 0.5 then return end
		Acc = 0
		if Ui and Ui.Gui.Enabled then Local.TickBuff() Local.RefreshEquipBuff() end
		if Stand and Stand.Gui.Enabled then
			-- (inventory QOL 1.92) the lunch countdown; lunch opening or closing rebuilds the list
			local WasOpen = Stand.LunchOpen
			Stand.LunchOpen = Items.LunchOpen()
			if WasOpen ~= nil and WasOpen ~= Stand.LunchOpen then Local.FillStand() else Stand.Lunch.Text = Local.LunchLine() end
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
			local Pos = StandAt and StandAt:IsA(`BasePart`) and StandAt.Position
			if not (Root and Pos) or (Root.Position - Pos).Magnitude > 16 then Shared.CloseStand() end
		end
		-- (inventory audit 1.90) dying or the main menu closes the Locker properly (its preview too)
		if Ui and Ui.Gui.Enabled then
			local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
			if not Hum or Hum.Health <= 0 or Player:GetAttribute(`InMainMenu`) == true then Shared.Toggle(false) end
		end
		if Player:GetAttribute(`InMainMenu`) == true then Shared.CloseStand() end
	end)
end

return Shared
