--[[
	The everyday kit (client UI). Controllers.Gui.KitUi                    (owner approved 2026-11-11)
	Server: Services.Features.Kit (remotes ReplicatedStorage.NHKit). Config: Config.Kit.

	  Counters   MORROW & VANE, THE WICK & KETTLE, the Office, the Archive desk: a prompt with attribute NHKitShop opens
	             the counter's window (buy, refill, borrow / return, pay a fine). Closes when you walk away.
	  Map        the Campus Map tool: click it to open the paper map, drawn from workspace.Regions (so it works in both
	             places): every place by kind, a live "you are here" arrow, your next class. Click a place to pin a
	             waypoint (the compass follows it); click the pin to clear it.
	  Compass    while you hold the Pocket Compass: a brass dial over the hotbar with the target's name and distance, and
	             the model's needle turns to it. Target: your pin, your tracked quest, your next class (school day), your
	             dorm (evening and night), else north.
	  Card       while you hold the Timetable Card: Now / Next. Click it for the full Timetable (Gui.Timetable).
	  Chips      above the hotbar: the held item's charge (oil, cups...), the hall pass countdown, the warmer, the keys
	             you're carrying.
	  Locker     Gui.Locker's Kit tab calls Shared.Entries / Shared.Card / Shared.ModelFor.
	Built from the UI kit (Panel, Button, ItemSlot, Plate, Text).
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ProximityPromptService = game:GetService(`ProximityPromptService`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)

local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local KitCfg = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Kit`))
local RegionsCfg = require(ReplicatedStorage.Config:WaitForChild(`Regions`))
local CliqueCfg = require(ReplicatedStorage.Config:WaitForChild(`Cliques`))
local SchoolTime = require(ReplicatedStorage:WaitForChild(`Functions`):WaitForChild(`SchoolTime`))
local Classes = require(ReplicatedStorage.Config:WaitForChild(`Classes`))
local ItemsCfg = require(ReplicatedStorage.Config:WaitForChild(`Items`)) -- (inventory QOL 1.91) the snack buff chip

local Player = Players.LocalPlayer
local Theme = Kit.Theme
local C = Theme.Colors
local Fonts = Theme.Fonts
local YEN = `\u{A5}`
local PAPER = Color3.fromRGB(222, 206, 170)
local INK = Color3.fromRGB(40, 30, 26)
local CRIMSON = Color3.fromRGB(96, 14, 26)

local Shared = {}
local Local = {}
Shared.State = nil
Shared.Waypoint = nil :: Vector3?
local Counter = nil
local CounterAt: BasePart? = nil
local CounterShop: string? = nil
local MapUi = nil
local Hud = nil

---| helpers |---

function Local.Remote(Name: string)
	local F = ReplicatedStorage:FindFirstChild(`NHKit`)
	return F and F:GetAttribute(`Ready`) and F:FindFirstChild(Name)
end

function Shared.Act(...): (boolean, string?)
	local R = Local.Remote(`Act`)
	if not R then return false, `The kit isn't ready yet.` end
	local Ok, A, B = pcall(R.InvokeServer, R, ...)
	if not Ok then return false, nil end
	return A, B
end

function Shared.Refresh()
	local R = Local.Remote(`Get`)
	if not R then return end
	local Ok, S = pcall(R.InvokeServer, R)
	if Ok and typeof(S) == `table` then Shared.State = S end
end

local function Price(Shop: string, Base: number): number
	return math.ceil(Base * CliqueCfg.PriceFactor(Player, `Kit{Shop}`))
end

function Local.Label(Parent: Instance, Text: string, Size: number, Props)
	local T = Kit.Text({ Text = Text; TextSize = Size; TextColor3 = C.Text; TextWrapped = true; RichText = true;
		TextXAlignment = Enum.TextXAlignment.Left; TextYAlignment = Enum.TextYAlignment.Top; Parent = Parent })
	for K, V in Props or {} do T[K] = V end
	return T
end

function Local.Screen(Name: string, Order: number, Enabled: boolean?): ScreenGui
	local G = Instance.new(`ScreenGui`)
	G.Name = Name
	G.ResetOnSpawn = false
	G.DisplayOrder = Order
	G.ZIndexBehavior = Enum.ZIndexBehavior.Sibling
	G.Enabled = Enabled == true
	G.Parent = Player:WaitForChild(`PlayerGui`)
	Kit.AutoScale(G)
	return G
end

-- a 3D view of a kit item in a slot (the imported model, or its stand-in)
function Shared.ModelFor(Id: string): Instance?
	local Lib = ReplicatedStorage:FindFirstChild(`NHKit`)
	local Store = Lib and Lib:FindFirstChild(`Models`)
	local T = Store and Store:FindFirstChild(Id)
	if T then
		local M = T:Clone()
		for _, D in M:GetDescendants() do if D:IsA(`BasePart`) then D.Anchored = true end end
		return M
	end
	local P = Instance.new(`Part`)
	P.Anchored = true
	P.Size = Vector3.new(0.6, 0.8, 0.3)
	P.Material = Enum.Material.SmoothPlastic
	P.Color = Color3.fromRGB(150, 120, 70)
	return P
end

function Local.View(Slot: GuiObject, Id: string)
	local Old = Slot:FindFirstChild(`NHView`)
	if Old then Old:Destroy() end
	local M = Shared.ModelFor(Id)
	if not M then return end
	local V = Instance.new(`ViewportFrame`)
	V.Name = `NHView`
	V.BackgroundTransparency = 1
	V.AnchorPoint = Vector2.new(0.5, 0.5)
	V.Position = UDim2.fromScale(0.5, 0.47)
	V.Size = UDim2.fromScale(0.74, 0.74)
	V.ZIndex = 6
	V.Ambient = Color3.fromRGB(150, 140, 130)
	V.LightColor = Color3.fromRGB(255, 236, 210)
	V.LightDirection = Vector3.new(-1, -1, -0.6)
	local Cam = Instance.new(`Camera`)
	Cam.FieldOfView = 30
	M.Parent = V
	local CF, Size
	if M:IsA(`Model`) then CF, Size = M:GetBoundingBox() else CF, Size = M.CFrame, M.Size end
	local R = math.max(Size.X, Size.Y, Size.Z)
	Cam.CFrame = CFrame.lookAt(CF.Position + Vector3.new(-0.7, 0.45, -1.0).Unit * R * 2.3, CF.Position)
	Cam.Parent = V
	V.CurrentCamera = Cam
	V.Parent = Slot
end

---| the school day |---

function Local.Clock()
	local Clock = ReplicatedStorage:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return nil end
	return SchoolTime.GetState(Epoch, workspace:GetServerTimeNow())
end

-- the next Class segment after now (today; nil after the last bell)
function Shared.NextClass(S)
	S = S or Local.Clock()
	if not S then return nil end
	for I = (S.SegmentIndex or 0) + 1, #SchoolTime.Segments do
		local Seg = SchoolTime.Segments[I]
		if Seg.Kind == `Class` then
			local P = Classes.Periods and Classes.Periods[Seg.Name]
			return { Name = Seg.Name; Start = Seg.Start; Subject = P and P.Subject; Room = P and P.Room }
		end
	end
	return nil
end

function Shared.CurrentClass(S)
	S = S or Local.Clock()
	if not (S and S.Segment and S.Segment.Kind == `Class`) then return nil end
	local P = Classes.Periods and Classes.Periods[S.Segment.Name]
	return { Name = S.Segment.Name; Subject = P and P.Subject; Room = P and P.Room; Left = S.MinutesLeft }
end

function Local.RoomName(Room: string?): string
	if not Room then return `` end
	local N = Classes.Rooms and Classes.Rooms[Room]
	return if typeof(N) == `string` then N elseif typeof(N) == `table` and N.Name then N.Name else `Room {string.sub(Room, 2)}`
end

---| regions (the map and the compass) |---

function Local.Boxes()
	local Out = {}
	local F = workspace:FindFirstChild(`Regions`)
	for _, B in (F and F:GetDescendants()) or {} do
		if B:IsA(`BasePart`) then
			local Id = B:GetAttribute(`RegionId`) or B.Name
			local Def = RegionsCfg.Defs and RegionsCfg.Defs[Id]
			if Def then table.insert(Out, { Part = B; Id = Id; Def = Def }) end
		end
	end
	return Out
end

function Local.RoomPos(Room: string?): Vector3?
	if not Room then return nil end
	for _, B in Local.Boxes() do if B.Id == Room then return B.Part.Position end end
	for _, D in workspace:GetDescendants() do
		if D:IsA(`BasePart`) and D:GetAttribute(`RoomId`) == Room then return D.Position end
	end
	return nil
end

-- what the compass points at: { Pos, Name } or nil (north)
function Shared.Target()
	if Shared.Waypoint then return { Pos = Shared.Waypoint; Name = `Your pin` } end
	local PG = Player:FindFirstChild(`PlayerGui`)
	local QT = PG and PG:FindFirstChild(`QuestTracker`, true)
	local QM = QT and QT:FindFirstChild(`QuestMarker`, true)
	if QM and QM:IsA(`BillboardGui`) and QM.Adornee and QM.Adornee:IsA(`BasePart`) and QM.Enabled ~= false then
		return { Pos = QM.Adornee.Position; Name = `Your quest` }
	end
	local S = Local.Clock()
	if S then
		local Kind = S.Segment and S.Segment.Kind
		if Kind == `BeforeSchool` or Kind == `Class` or Kind == `Passing` or Kind == `Break` or Kind == `Morning` then
			local Cls = Shared.CurrentClass(S) or Shared.NextClass(S)
			local Pos = Cls and Local.RoomPos(Cls.Room)
			if Pos then return { Pos = Pos; Name = `{Cls.Subject or Cls.Name} · {Local.RoomName(Cls.Room)}` } end
		elseif Kind == `Evening` or Kind == `Night` or Kind == `AfterSchool` then
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
			local Best, BestD = nil, math.huge
			for _, D in CollectionService:GetTagged(`NHHomeDoor`) do
				local Pos = if D:IsA(`Model`) then D:GetPivot().Position elseif D:IsA(`BasePart`) then D.Position else nil
				if Pos and Root and (Pos - Root.Position).Magnitude < BestD then Best, BestD = Pos, (Pos - Root.Position).Magnitude end
			end
			if Best then return { Pos = Best; Name = `Your dorm` } end
		end
	end
	return nil
end

---| the counters |---

function Local.BuildCounter()
	local G = Local.Screen(`NHKitCounter`, 12)
	local Panel, Api = Kit.Panel({ title = `Counter`; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(940, 620); Parent = G })
	local Body = Api.Content
	local Sub = Local.Label(Body, ``, 17, { Name = `Sub`; TextColor3 = C.TextDim; Size = UDim2.new(1, -200, 0, 24); Position = UDim2.fromOffset(8, 0) })
	local _, YenApi = Kit.Plate({ text = `{YEN} 0`; Size = UDim2.fromOffset(150, 34); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 0, -4); Parent = Body })
	local Grid = Instance.new(`ScrollingFrame`)
	Grid.Name = `Grid`
	Grid.BackgroundTransparency = 1
	Grid.BorderSizePixel = 0
	Grid.Position = UDim2.fromOffset(0, 36)
	Grid.Size = UDim2.new(1, 0, 1, -96)
	Grid.CanvasSize = UDim2.new()
	Grid.AutomaticCanvasSize = Enum.AutomaticSize.Y
	Grid.ScrollBarThickness = 5
	Grid.ScrollBarImageColor3 = C.IronDim
	local L = Instance.new(`UIGridLayout`)
	L.CellSize = UDim2.fromOffset(210, 236)
	L.CellPadding = UDim2.fromOffset(12, 10)
	L.HorizontalAlignment = Enum.HorizontalAlignment.Center
	L.SortOrder = Enum.SortOrder.LayoutOrder
	L.Parent = Grid
	Grid.Parent = Body
	local Status = Local.Label(Body, ``, 17, { Name = `Status`; TextColor3 = C.Gold; TextXAlignment = Enum.TextXAlignment.Center;
		Size = UDim2.new(1, -220, 0, 24); Position = UDim2.new(0, 10, 1, -44) })
	Kit.Button({ text = `Close`; style = `ghost`; Size = UDim2.fromOffset(160, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.CloseCounter() end })
	Counter = { Gui = G; Panel = Api; Grid = Grid; Yen = YenApi; Status = Status; Sub = Sub }
end

function Local.Cell(Order: number, Title: string, Line: string, Id: string?, Buttons)
	local Cell = Instance.new(`Frame`)
	Cell.BackgroundTransparency = 1
	Cell.LayoutOrder = Order
	Cell.Parent = Counter.Grid
	local Slot = Kit.ItemSlot({ item = { name = Title; rarity = (Id and KitCfg.ById[Id] and KitCfg.ById[Id].Rarity) or `Common` }; size = 84;
		AnchorPoint = Vector2.new(0.5, 0); Position = UDim2.new(0.5, 0, 0, 2); Parent = Cell })
	if Id then Local.View(Slot, Id) end
	Local.Label(Cell, Title, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 92); Size = UDim2.new(1, 0, 0, 22) })
	Local.Label(Cell, Line, 14, { TextColor3 = Color3.fromRGB(150, 205, 140); TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(4, 116); Size = UDim2.new(1, -8, 0, 52) })
	local W = (210 - 8 - 6 * (#Buttons - 1)) / #Buttons
	for I, B in Buttons do
		Kit.Button({ text = B.text; style = B.style or `gold`; enabled = B.enabled ~= false; textSize = 15; Size = UDim2.fromOffset(W, 38);
			Position = UDim2.fromOffset(4 + (I - 1) * (W + 6), 176); Parent = Cell; onClick = B.onClick })
	end
end

function Local.Do(...)
	local Ok, Msg = Shared.Act(...)
	if Counter then Counter.Status.Text = Msg or (if Ok then `Done.` else ``) end
	if Ok then pcall(Kit.PlaySound, `Confirm`) end
	Shared.Refresh()
	Local.FillCounter()
	if Counter and Msg then Counter.Status.Text = Msg end
end

function Local.FillCounter()
	if not (Counter and CounterShop) then return end
	for _, Ch in Counter.Grid:GetChildren() do if Ch:IsA(`Frame`) then Ch:Destroy() end end
	local S = Shared.State
	local K = S and S.Kit
	Counter.Yen.Label.Text = `{YEN} {S and S.Yen or 0}`
	local Def = KitCfg.Shops[CounterShop]
	Counter.Panel:SetTitle(Def.Name)
	Counter.Sub.Text = `<i>{Def.Sub}. {Def.Text}</i>`
	local Order = 0
	local function nx() Order += 1 return Order end
	if CounterShop == `Archive` then
		local Card = K and K.Card
		if not Card then
			Local.Cell(nx(), `Library Card`, `Sign up to borrow. Free.`, nil, { { text = `Sign up`; onClick = function() Local.Do(`Refill`, `LibraryCard`) end } })
		end
		if K and K.Book then
			local B = KitCfg.BookById[K.Book.Id]
			local Left = K.Book.Due - (S.Day or 0)
			Local.Cell(nx(), B and B.Name or `Your book`, if Left < 0 then `Overdue by {-Left} day{if Left == -1 then `` else `s`}: \u{A5}{math.min(KitCfg.Book.FineMax, -Left * KitCfg.Book.FinePerDay)} fine` else `Due back in {Left} school day{if Left == 1 then `` else `s`}`,
				`LibraryBook`, { { text = `Return`; onClick = function() Local.Do(`Return`) end } })
		end
		if K and K.Fine > 0 then
			Local.Cell(nx(), `Fine owed`, `\u{A5}{K.Fine}. No new loans until it's paid.`, nil, { { text = `Pay {YEN}{K.Fine}`; style = `crimson`; onClick = function() Local.Do(`PayFine`) end } })
		end
		for _, B in KitCfg.Books do
			local Line = if B.Subject then `+3% class EXP while pinned, +10% on {B.Subject} lessons` else `+3% class EXP while pinned`
			Local.Cell(nx(), B.Name, Line, `LibraryBook`, { { text = `Borrow`; enabled = Card and not (K and K.Book) and not (K and K.Fine > 0);
				onClick = function() Local.Do(`Borrow`, B.Id) end } })
		end
		return
	end
	for _, It in KitCfg.Items do
		if It.Shop ~= CounterShop or not It.Price then continue end
		local Own = K and K.Owned[It.Id]
		local Can = not Own or (It.Id == `HallPass` and K.Pass.Punches <= 0 and K.Pass.Day ~= S.Day)
		Local.Cell(nx(), It.Name, It.Use, It.Id, { { text = if Can then `{YEN}{Price(It.Shop, It.Price)}` else `Owned`; enabled = Can;
			onClick = function() Local.Do(`Buy`, It.Id) end } })
	end
	for _, R in KitCfg.Refills do
		if R.Shop ~= CounterShop or R.Id == `LibraryCard` then continue end
		local Need = R.Needs and not (K and K.Owned[R.Needs])
		if R.Id == `NewKeys` and K and not K.Keys.Lost and K.Owned.KeyRing then
			Local.Cell(nx(), R.Name, `You have your keys.`, `KeyRing`, { { text = `Not needed`; enabled = false } })
			continue
		end
		Local.Cell(nx(), R.Name, (if Need then `Needs the {KitCfg.ById[R.Needs].Name}. ` else ``) .. R.Text, R.Needs or (if R.Id == `NewKeys` then `KeyRing` else nil),
			{ { text = `{YEN}{Price(R.Shop, R.Price)}`; enabled = not Need; onClick = function() Local.Do(`Refill`, R.Id) end } })
	end
	if S and S.Carrying and CounterShop == `Office` then
		Local.Cell(0, `Hand in keys`, `Someone's dorm keys. The Office pays {YEN}{KitCfg.Keys.Reward}.`, `KeyRing`,
			{ { text = `Hand in`; onClick = function() Local.Do(`HandInKeys`) end } })
	end
end

function Shared.OpenCounter(Shop: string, At: Instance?)
	if not KitCfg.Shops[Shop] then return end
	if not Counter then Local.BuildCounter() end
	CounterShop = Shop
	CounterAt = if At and At:IsA(`BasePart`) then At else nil
	Shared.Refresh()
	Counter.Status.Text = ``
	Local.FillCounter()
	Counter.Gui.Enabled = true
	pcall(Kit.PlaySound, `Tick`)
end

function Shared.CloseCounter()
	CounterShop, CounterAt = nil, nil
	if Counter then Counter.Gui.Enabled = false end
end

---| the Locker's Kit tab (Gui.Locker) |---

function Shared.Entries()
	local Out = {}
	local K = Shared.State and Shared.State.Kit
	if not K then return Out end
	for _, It in KitCfg.Items do
		if K.Owned[It.Id] then
			local Name = It.Name
			if It.Id == `LibraryBook` and K.Book then Name = (KitCfg.BookById[K.Book.Id] or {}).Name or Name end
			table.insert(Out, { name = Name; rarity = It.Rarity; count = KitCfg.Count(It.Id, K); kind = `Kit`; id = It.Id; order = 500 + It.Order;
				worn = It.Worn and not K.Keys.Lost })
		end
	end
	return Out
end

function Shared.Def(Id: string)
	return KitCfg.ById[Id]
end

-- the selected kit item's line and buttons in the Locker's action strip
function Shared.Card(A: Frame, Id: string, Info: TextLabel, Redraw: () -> ())
	local It = KitCfg.ById[Id]
	local K = Shared.State and Shared.State.Kit
	if not (It and K) then return end
	local Pinned = table.find(K.Pinned, Id) ~= nil
	local Charge = KitCfg.Charge(Id, K)
	Info.Text = (if Charge then Charge .. `  \u{00B7}  ` else ``) .. It.Use
	local X = 0
	local function btn(Text: string, Style: string?, Fn)
		Kit.Button({ text = Text; style = Style; Size = UDim2.fromOffset(112, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -X, 0.5, 0); Parent = A;
			onClick = function()
				local Ok, Msg = Fn()
				Shared.Refresh()
				Redraw()
				local Line = A:FindFirstChild(`Info`, true)
				if Msg and Line and Line:IsA(`TextLabel`) then Line.Text = Msg end
			end })
		X += 120
	end
	if It.Hotbar then btn(if Pinned then `Unpin` else `To hotbar`, nil, function() return Shared.Act(`Pin`, Id, not Pinned) end) end
	if It.Pocket then btn(if K.Warmer.Lit then `Let cool` else `Light`, `gold`, function() return Shared.Act(`Use`, Id) end) end
end

---| art (art/ui/hud/make_kit_ui.py, group 15981569; Config.Kit.Art). Missing ids fall back to plain shapes. |---

function Local.Art(Name: string): string?
	local Id = KitCfg.Art and KitCfg.Art[Name]
	return if typeof(Id) == `number` and Id > 0 then `rbxassetid://{Id}` else nil
end

-- an ImageLabel of a kit art piece, or a plain stand-in Frame (Fallback = { Color, Round, Transparency })
function Local.Img(Parent: Instance, Name: string, Props, Fallback)
	local Id = Local.Art(Name)
	local G
	if Id then
		G = Instance.new(`ImageLabel`)
		G.BackgroundTransparency = 1
		G.Image = Id
		G.ScaleType = Enum.ScaleType.Stretch
	else
		G = Instance.new(`Frame`)
		G.BorderSizePixel = 0
		G.BackgroundColor3 = (Fallback and Fallback.Color) or Color3.fromRGB(40, 34, 30)
		G.BackgroundTransparency = (Fallback and Fallback.Transparency) or 0
		if Fallback and Fallback.Round then Instance.new(`UICorner`, G).CornerRadius = UDim.new(1, 0) end
		if Fallback and Fallback.Stroke then
			local S = Instance.new(`UIStroke`) S.Color = Fallback.Stroke S.Thickness = 3 S.Parent = G
		end
	end
	G.Name = Name
	for K, V in Props or {} do G[K] = V end
	G.Parent = Parent
	return G
end

-- a brass-framed ink plate (9-slice) with an optional tinted icon and a line of text
function Local.Plate(Parent: Instance, Size: UDim2, Props)
	local P = Local.Img(Parent, `KitPlate`, { Size = Size }, { Color = Color3.fromRGB(18, 15, 20); Stroke = Color3.fromRGB(150, 112, 50) })
	if P:IsA(`ImageLabel`) then
		P.ScaleType = Enum.ScaleType.Slice
		P.SliceCenter = Rect.new(84, 44, 684, 116)
		P.SliceScale = math.max(0.2, Size.Y.Offset / 160)
	end
	for K, V in Props or {} do P[K] = V end
	local Icon = Local.Img(P, `IconOil`, { Name = `Icon`; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 22, 0.5, 0);
		Size = UDim2.fromOffset(26, 26); ZIndex = (P.ZIndex or 1) + 1 }, { Color = C.Gold; Transparency = 1 })
	local Text = Kit.Text({ Name = `Label`; Text = ``; Font = Enum.Font.Garamond; TextSize = 18; TextColor3 = C.Gold; TextStrokeTransparency = 0.6;
		TextXAlignment = Enum.TextXAlignment.Left; AnchorPoint = Vector2.new(0, 0.5); Position = UDim2.new(0, 56, 0.5, 0);
		Size = UDim2.new(1, -76, 1, -8); ZIndex = (P.ZIndex or 1) + 1; Parent = P })
	Text.FontFace = Theme.FontFaces.BodyBold
	return P, Icon, Text
end

function Local.SetIcon(Icon: GuiObject, Name: string?, Color: Color3?)
	if not Icon:IsA(`ImageLabel`) then Icon.Visible = false return end
	local Id = Name and Local.Art(Name)
	Icon.Visible = Id ~= nil
	if Id then Icon.Image = Id Icon.ImageColor3 = Color or C.Gold end
end

---| the map |---

local KIND_FILL = {
	School = Color3.fromRGB(196, 176, 140); Restricted = Color3.fromRGB(186, 160, 132); Forbidden = Color3.fromRGB(178, 132, 120);
	Sports = Color3.fromRGB(176, 184, 136); Turf = Color3.fromRGB(206, 186, 156); Grounds = Color3.fromRGB(210, 196, 160);
}
local KIND_TILE = { School = `MapHatch`; Restricted = `MapHatch`; Forbidden = `MapHatch`; Turf = `MapHatch`; Sports = `MapStipple` }

function Local.BuildMap()
	local G = Local.Screen(`NHKitMap`, 14)
	local Panel, Api = Kit.Panel({ title = `Campus Map`; Name = `Panel`; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
		Size = UDim2.fromOffset(1220, 830); Parent = G })
	local Body = Api.Content
	local Head = Local.Label(Body, ``, 19, { Name = `Next`; Font = Fonts.Title; TextColor3 = C.Gold; Position = UDim2.fromOffset(8, 2); Size = UDim2.new(1, -220, 0, 28) })
	-- the sheet: the paper art (its own border, title and rose), 1.6 : 1
	local Holder = Instance.new(`Frame`)
	Holder.Name = `Holder`
	Holder.BackgroundTransparency = 1
	Holder.Position = UDim2.fromOffset(4, 34)
	Holder.Size = UDim2.new(1, -8, 1, -92)
	Holder.Parent = Body
	local Sheet = Local.Img(Holder, `MapSheet`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1) },
		{ Color = PAPER; Stroke = INK })
	Sheet.Name = `Sheet`
	local Ar = Instance.new(`UIAspectRatioConstraint`) Ar.AspectRatio = 1.6 Ar.Parent = Sheet
	-- the plan: the clear middle of the sheet, where the places are drawn
	local Plan = Instance.new(`Frame`)
	Plan.Name = `Plan`
	Plan.BackgroundTransparency = 1
	Plan.ClipsDescendants = true
	Plan.Position = UDim2.fromScale(0.07, 0.19)
	Plan.Size = UDim2.fromScale(0.86, 0.66)
	Plan.ZIndex = 2
	Plan.Parent = Sheet
	Local.Label(Body, `<i>Click a place to pin it for your compass. Click the pin to clear it.</i>`, 16,
		{ TextColor3 = C.TextDim; Position = UDim2.new(0, 10, 1, -44); Size = UDim2.new(1, -220, 0, 22) })
	Kit.Button({ text = `Fold it up`; style = `ghost`; Size = UDim2.fromOffset(170, 40); AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, -8, 1, -52); Parent = Body;
		onClick = function() Shared.ToggleMap(false) end })
	local You = Local.Img(Plan, `MapYou`, { AnchorPoint = Vector2.new(0.5, 0.5); Size = UDim2.fromOffset(42, 42); ZIndex = 30 },
		{ Color = CRIMSON; Round = true })
	You.Name = `You`
	local YouL = Kit.Text({ Text = `you are here`; Font = Enum.Font.Garamond; TextSize = 20; TextColor3 = CRIMSON; Size = UDim2.fromOffset(130, 22);
		AnchorPoint = Vector2.new(0, 0.5); ZIndex = 30; Parent = Plan })
	YouL.FontFace = Font.new(Theme.FontFaces.Body.Family, Enum.FontWeight.Bold, Enum.FontStyle.Italic)
	local Pin = Instance.new(`ImageButton`)
	Pin.Name = `Pin`
	Pin.BackgroundTransparency = 1
	Pin.Image = Local.Art(`MapPin`) or ``
	Pin.AnchorPoint = Vector2.new(0.5, 0.95)
	Pin.Size = UDim2.fromOffset(46, 46)
	Pin.ZIndex = 31
	Pin.Visible = false
	Pin.Parent = Plan
	if Pin.Image == `` then Pin.BackgroundTransparency = 0 Pin.BackgroundColor3 = CRIMSON Pin.Size = UDim2.fromOffset(16, 16) Instance.new(`UICorner`, Pin).CornerRadius = UDim.new(1, 0) end
	Pin.Activated:Connect(function() Shared.Waypoint = nil Local.DrawPin() pcall(Kit.PlaySound, `Tick`) end)
	local Click = Instance.new(`TextButton`)
	Click.Name = `Click`
	Click.BackgroundTransparency = 1
	Click.Text = ``
	Click.Size = UDim2.fromScale(1, 1)
	Click.ZIndex = 3
	Click.Parent = Plan
	MapUi = { Gui = G; Sheet = Sheet; Plan = Plan; Head = Head; You = You; YouL = YouL; Pin = Pin; Click = Click; Bounds = nil }
	Click.Activated:Connect(function()
		local M = UserInputService:GetMouseLocation()
		local Inset = game:GetService(`GuiService`):GetGuiInset()
		local W = Local.FromMap(Vector2.new(M.X, M.Y - Inset.Y))
		if W then Shared.Waypoint = W Local.DrawPin() pcall(Kit.PlaySound, `Tick`) end
	end)
end

-- world <-> plan: X to the right, -Z up (the map's north)
function Local.Bounds()
	local Lo, Hi = Vector2.new(math.huge, math.huge), Vector2.new(-math.huge, -math.huge)
	for _, B in Local.Boxes() do
		if B.Id == `Grounds` then continue end
		local CF, S = B.Part.CFrame, B.Part.Size / 2
		for _, Cx in { -1, 1 } do for _, Cz in { -1, 1 } do
			local P = (CF * CFrame.new(S.X * Cx, 0, S.Z * Cz)).Position
			Lo = Vector2.new(math.min(Lo.X, P.X), math.min(Lo.Y, P.Z))
			Hi = Vector2.new(math.max(Hi.X, P.X), math.max(Hi.Y, P.Z))
		end end
	end
	if Lo.X == math.huge then return nil end
	local Pad = (Hi - Lo) * 0.04 + Vector2.new(10, 10)
	return { Lo = Lo - Pad; Hi = Hi + Pad }
end

function Local.Fit()
	local B = MapUi and MapUi.Bounds
	if not B then return nil end
	local Size = MapUi.Plan.AbsoluteSize
	local Span = B.Hi - B.Lo
	local K = math.min(Size.X / Span.X, Size.Y / Span.Y)
	local Scale = MapUi.Gui:FindFirstChildOfClass(`UIScale`)
	return B, K, (Size - Span * K) / 2, if Scale then Scale.Scale else 1
end

function Local.ToSheet(P: Vector3): UDim2?
	local B, K, Off, U = Local.Fit()
	if not B then return nil end
	return UDim2.fromOffset((Off.X + (P.X - B.Lo.X) * K) / U, (Off.Y + (P.Z - B.Lo.Y) * K) / U)
end

function Local.FromMap(Screen: Vector2): Vector3?
	local B, K, Off = Local.Fit()
	if not B then return nil end
	local L = Screen - MapUi.Plan.AbsolutePosition - Off
	local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
	return Vector3.new(B.Lo.X + L.X / K, Root and Root.Position.Y or 0, B.Lo.Y + L.Y / K)
end

function Local.DrawMap()
	local Plan = MapUi.Plan
	for _, Ch in Plan:GetChildren() do if Ch:GetAttribute(`NHMapPiece`) then Ch:Destroy() end end
	MapUi.Bounds = Local.Bounds()
	if not MapUi.Bounds then
		local L = Local.Label(Plan, `<i>The map is blank. No places are marked in this world yet.</i>`, 24, { TextColor3 = INK; TextXAlignment = Enum.TextXAlignment.Center;
			Position = UDim2.fromScale(0, 0.45); Size = UDim2.new(1, 0, 0, 40); ZIndex = 4 })
		L:SetAttribute(`NHMapPiece`, true)
		return
	end
	local _, K, _, U = Local.Fit()
	local Next = Shared.CurrentClass() or Shared.NextClass()
	local List = Local.Boxes()
	table.sort(List, function(A, Bb) return (A.Def.Priority or 0) < (Bb.Def.Priority or 0) end)
	for _, R in List do
		if R.Id == `Grounds` then continue end
		local P = R.Part
		local Look = P.CFrame.LookVector
		local Yaw = math.deg(math.atan2(Look.X, -Look.Z))
		local Kind = R.Def.Kind
		local Mine = Next and Next.Room == R.Id
		local Red = Kind == `Turf` or Kind == `Forbidden` or Kind == `Restricted`
		local F = Instance.new(`Frame`)
		F:SetAttribute(`NHMapPiece`, true)
		F.AnchorPoint = Vector2.new(0.5, 0.5)
		F.Position = Local.ToSheet(P.Position)
		F.Size = UDim2.fromOffset(P.Size.X * K / U, P.Size.Z * K / U)
		F.Rotation = Yaw
		F.BackgroundColor3 = if Mine then Color3.fromRGB(222, 182, 98) else KIND_FILL[Kind] or PAPER
		F.BackgroundTransparency = if Kind == `Turf` then 0.75 else 0.18
		F.BorderSizePixel = 0
		F.ZIndex = 4 + (R.Def.Priority or 0)
		local Tile = KIND_TILE[Kind] and Local.Art(KIND_TILE[Kind])
		if Tile then
			local T = Instance.new(`ImageLabel`)
			T.BackgroundTransparency = 1
			T.Image = Tile
			T.ScaleType = Enum.ScaleType.Tile
			T.TileSize = UDim2.fromOffset(44, 44)
			T.Size = UDim2.fromScale(1, 1)
			T.ImageColor3 = if Red then Color3.fromRGB(150, 40, 50) else Color3.new(1, 1, 1)
			T.ImageTransparency = if Kind == `Turf` then 0.3 else 0.1
			T.ZIndex = F.ZIndex
			T.Parent = F
		end
		local S = Instance.new(`UIStroke`)
		S.Color = if Mine then Color3.fromRGB(176, 130, 40) elseif Red then CRIMSON else INK
		S.Thickness = if Mine then 4 else 2.5
		S.Parent = F
		F.Parent = Plan
		local Name = string.upper(string.gsub(R.Def.Title or R.Def.Name, `^The `, ``))
		local Small = math.min(P.Size.X, P.Size.Z) * K / U
		local Lb = Kit.Text({ Text = Name; TextSize = math.clamp(math.floor(Small / 4.2), 11, 22); TextColor3 = S.Color; TextWrapped = true;
			TextXAlignment = Enum.TextXAlignment.Center; AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5);
			Size = UDim2.fromScale(0.96, 0.96); ZIndex = F.ZIndex + 1; Parent = F })
		Lb.FontFace = Theme.FontFaces.BodyBold
		Lb.Rotation = -Yaw
	end
	MapUi.Head.Text = if Next then `{if Shared.CurrentClass() then `Now` else `Next`}: {Next.Subject or Next.Name}, {Local.RoomName(Next.Room)}` ..
		(if Next.Start then ` at {Next.Start}` else ``) .. `  \u{00B7}  ringed in gold on the map` else `No more lessons today.`
	Local.DrawPin()
end

function Local.DrawPin()
	if not MapUi then return end
	local W = Shared.Waypoint
	MapUi.Pin.Visible = W ~= nil and MapUi.Bounds ~= nil
	if W and MapUi.Bounds then MapUi.Pin.Position = Local.ToSheet(W) end
end

function Shared.ToggleMap(On: boolean?)
	if not MapUi then Local.BuildMap() end
	if On == nil then On = not MapUi.Gui.Enabled end
	MapUi.Gui.Enabled = On
	if On then
		task.defer(function() Local.DrawMap() end)
		pcall(Kit.PlaySound, `Tick`)
	end
end

---| the HUD: the brass compass, the timetable card, the chips |---

local CHIP_ICON = { Lantern = `IconOil`; Thermos = `IconCup`; SnackTin = `IconBiscuit`; FirstAid = `IconBandage`; HallPass = `IconPass`;
	HandWarmer = `IconFlame`; LibraryBook = `IconBook`; KeyRing = `IconKeys` }

function Local.BuildHud()
	local G = Local.Screen(`NHKitHud`, 6, true)
	local Root = Instance.new(`Frame`)
	Root.Name = `Root`
	Root.BackgroundTransparency = 1
	Root.AnchorPoint = Vector2.new(0.5, 1)
	Root.Position = UDim2.new(0.5, 0, 1, -214)   -- clear of the health bar, the posture rail and the hotbar
	Root.Size = UDim2.fromOffset(640, 330)
	Root.Parent = G
	-- the compass: the card turns so N points north, the needle turns to the target, the crystal and bezel sit on top
	local Dial = Instance.new(`Frame`)
	Dial.Name = `Dial`
	Dial.BackgroundTransparency = 1
	Dial.AnchorPoint = Vector2.new(0.5, 1)
	Dial.Position = UDim2.new(0.5, 470, 1, -150)   -- right of the health bar, above the Yen plate
	Dial.Size = UDim2.fromOffset(190, 190)
	Dial.Visible = false
	Dial.Parent = G
	local Face = Local.Img(Dial, `CompassFace`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ZIndex = 2 },
		{ Color = Color3.fromRGB(226, 214, 186); Round = true })
	if not Face:IsA(`ImageLabel`) then Face.Size = UDim2.fromScale(0.74, 0.74) end
	local Needle = Local.Img(Dial, `CompassNeedle`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ZIndex = 3 },
		{ Transparency = 1 })
	if not Needle:IsA(`ImageLabel`) then
		local Tip = Instance.new(`Frame`) Tip.BackgroundColor3 = Color3.fromRGB(150, 22, 34) Tip.BorderSizePixel = 0 Tip.AnchorPoint = Vector2.new(0.5, 1)
		Tip.Position = UDim2.fromScale(0.5, 0.5) Tip.Size = UDim2.new(0, 6, 0.32, 0) Tip.ZIndex = 3 Tip.Parent = Needle
	end
	Local.Img(Dial, `CompassGlass`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ZIndex = 4 }, { Transparency = 1 })
	Local.Img(Dial, `CompassBezel`, { AnchorPoint = Vector2.new(0.5, 0.5); Position = UDim2.fromScale(0.5, 0.5); Size = UDim2.fromScale(1, 1); ZIndex = 5 },
		{ Transparency = 1; Round = true; Stroke = Color3.fromRGB(196, 150, 70) })
	local LabelPlate, LabelIcon, DialL = Local.Plate(G, UDim2.fromOffset(340, 48), { AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 470, 1, -344); Visible = false })
	LabelIcon.Visible = false
	DialL.Position = UDim2.new(0, 34, 0.5, 0)
	DialL.Size = UDim2.new(1, -68, 1, -8)
	DialL.TextXAlignment = Enum.TextXAlignment.Center
	-- the timetable card
	local Card = Local.Img(Root, `CardHud`, { AnchorPoint = Vector2.new(0.5, 1); Position = UDim2.new(0.5, 0, 1, -54); Size = UDim2.fromOffset(460, 120); Visible = false },
		{ Color = Color3.fromRGB(232, 222, 196); Stroke = Color3.fromRGB(150, 112, 50) })
	local CardTitle = Kit.Text({ Text = `CLASS TIMETABLE`; Font = Fonts.Title; TextSize = 17; TextColor3 = Color3.fromRGB(240, 226, 196);
		TextXAlignment = Enum.TextXAlignment.Left; Position = UDim2.new(0, 30, 0, 8); Size = UDim2.new(1, -120, 0, 26); ZIndex = 2; Parent = Card })
	local CardL = Local.Label(Card, ``, 16, { TextColor3 = Color3.fromRGB(40, 30, 26); Position = UDim2.new(0, 30, 0, 40); Size = UDim2.new(1, -110, 1, -46); ZIndex = 2 })
	CardL.FontFace = Theme.FontFaces.BodyBold
	-- the chips, in a row above the hotbar
	local Chips = Instance.new(`Frame`)
	Chips.Name = `Chips`
	Chips.BackgroundTransparency = 1
	Chips.AnchorPoint = Vector2.new(0.5, 1)
	Chips.Position = UDim2.new(0.5, 0, 1, 0)
	Chips.Size = UDim2.fromOffset(960, 44)
	Chips.Parent = Root
	local CL = Instance.new(`UIListLayout`)
	CL.FillDirection = Enum.FillDirection.Horizontal
	CL.HorizontalAlignment = Enum.HorizontalAlignment.Center
	CL.Padding = UDim.new(0, 8)
	CL.Parent = Chips
	Hud = { Gui = G; Root = Root; Dial = Dial; Face = Face; Needle = Needle; Label = LabelPlate; DialL = DialL; Card = Card; CardL = CardL;
		CardTitle = CardTitle; Chips = Chips; Pool = {} }
end

function Local.Chip(I: number, Text: string?, Color: Color3?, Icon: string?)
	local Ch = Hud.Pool[I]
	if not Text then if Ch then Ch.Root.Visible = false end return end
	if not Ch then
		local P, Ic, L = Local.Plate(Hud.Chips, UDim2.fromOffset(230, 44), { LayoutOrder = I })
		Ch = { Root = P; Icon = Ic; Label = L }
		Hud.Pool[I] = Ch
	end
	Ch.Root.Visible = true
	Ch.Label.Text = Text
	Ch.Label.TextColor3 = Color or C.Text
	Local.SetIcon(Ch.Icon, Icon, Color)
	Ch.Root.Size = UDim2.fromOffset(math.clamp(80 + #Text * 8.5, 150, 480), 44) -- (inventory QOL 1.91) room for the buff chip
end

function Local.Held(): Tool?
	local Char = Player.Character
	if not Char then return nil end
	for _, T in Char:GetChildren() do if T:IsA(`Tool`) and T:GetAttribute(`NHKit`) then return T end end
	return nil
end

local function bearing(V: Vector3): number return math.deg(math.atan2(V.X, -V.Z)) end

function Local.StepHud()
	if not Hud then Local.BuildHud() end
	local T = Local.Held()
	local Id = T and T:GetAttribute(`NHKit`)
	local Shown = not (Player:GetAttribute(`InMainMenu`) == true or Player:GetAttribute(`InDialogue`) == true)
	Hud.Root.Visible = Shown
	-- the compass
	local Compass = Id == `Compass` and Shown
	Hud.Dial.Visible = Compass
	Hud.Label.Visible = Compass
	if Compass then
		local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
		local Cam = workspace.CurrentCamera
		local Tg = Shared.Target()
		local Want = if Tg and Root then (Tg.Pos - Root.Position) else Vector3.new(0, 0, -1)
		local Look = Cam and Cam.CFrame.LookVector or Vector3.new(0, 0, -1)
		local Heading = bearing(Look)
		Hud.Face.Rotation = -Heading                      -- N on the card points to world north
		Hud.Needle.Rotation = bearing(Want) - Heading     -- the needle points to the target
		local Dist = if Tg and Root then math.floor(Vector3.new(Want.X, 0, Want.Z).Magnitude / 3 + 0.5) else nil
		Hud.DialL.Text = if Tg then `{Tg.Name}  \u{00B7}  {Dist} paces` else `North`
		-- the model's needle (its own weld, turned on this client)
		local N = T:FindFirstChild(`Compass_Needle`, true)
		local W = N and N:FindFirstChild(`NHNeedleWeld`)
		local Handle = T:FindFirstChild(`Handle`) :: BasePart?
		if W and W:IsA(`Weld`) and Handle then
			local Base = W:GetAttribute(`NHBaseC0`)
			if Base == nil then Base = W.C0 W:SetAttribute(`NHBaseC0`, Base) end
			W.C0 = Base * CFrame.Angles(0, -math.rad(bearing(Want) - bearing(Handle.CFrame.LookVector)), 0)
		end
	end
	-- the timetable card
	Hud.Card.Visible = Id == `Timetable`
	if Id == `Timetable` then
		local S = Local.Clock()
		local Now = Shared.CurrentClass(S)
		local Nx = Shared.NextClass(S)
		local Lines = {}
		table.insert(Lines, if Now then `Now   {Now.Subject or Now.Name}, {Local.RoomName(Now.Room)}  \u{00B7}  {Now.Left or 0} min left`
			else `Now   {S and S.Segment and S.Segment.Name or ``}`)
		table.insert(Lines, if Nx then `Next  {Nx.Subject or Nx.Name}, {Local.RoomName(Nx.Room)} at {Nx.Start}` else `Next  No more lessons today`)
		table.insert(Lines, `<font color="#6e5e52"><i>Click for the full timetable</i></font>`)
		Hud.CardL.Text = table.concat(Lines, `\n`)
	end
	-- the chips
	local I = 0
	local function chip(Text, Color, Icon) I += 1 Local.Chip(I, Text, Color, Icon) end
	if T then
		local Ch = T:GetAttribute(`NHCharge`)
		if Id == `Lantern` and T:GetAttribute(`Lit`) then Ch = `Lit  \u{00B7}  ` .. (Ch or ``) end
		if Ch then chip(Ch, C.Gold, CHIP_ICON[Id]) end
	end
	local Until = Player:GetAttribute(`NHPassUntil`)
	local Left = if typeof(Until) == `number` then Until - workspace:GetServerTimeNow() else 0
	if Left > 0 then chip(`Hall pass  {math.ceil(Left)} s`, C.Gold, `IconPass`) end
	local Char = Player.Character
	if Char and Char:GetAttribute(`NHWarm`) then chip(`Hand warmer lit`, Color3.fromRGB(240, 160, 90), `IconFlame`) end
	if Char and Char:GetAttribute(`NHChilled`) then chip(`Chilled`, Color3.fromRGB(170, 200, 235), `IconFrost`) end
	if Char and Char:GetAttribute(`NHWounded`) then chip(`Wounded`, C.Danger, `IconHeart`) end
	if Player:GetAttribute(`NHKitKeys`) then chip(`Carrying someone's keys`, C.Gold, `IconKeys`) end
	-- (inventory QOL 1.91) the snack buff: what it gives you (your race's twist included) and the time left; it pulses red
	-- in the last 15 s
	local BId, BUntil = Player:GetAttribute(`NHSnackBuff`), Player:GetAttribute(`NHSnackBuffUntil`)
	local BLeft = if typeof(BUntil) == `number` then BUntil - workspace:GetServerTimeNow() else 0
	local BIt = typeof(BId) == `string` and ItemsCfg.ById[BId]
	if BIt and BLeft > 0 then
		local Eff = ItemsCfg.Describe({ Kind = `Buff`; Effects = ItemsCfg.EffectsFor(BIt, Player:GetAttribute(`Race`)); Duration = 60 })
		Eff = string.gsub(Eff, ` for .*$`, ``)
		if Eff == `` then Eff = `no effect` end
		local Pulse = BLeft < 15 and math.floor(os.clock() * 2) % 2 == 0
		chip(`{BIt.Name}  \u{00B7}  {Eff}  \u{00B7}  {math.floor(BLeft / 60)}:{string.format(`%02d`, math.floor(BLeft % 60))}`,
			if Pulse then C.Danger else Color3.fromRGB(150, 205, 140), `IconCup`)
	end
	for J = I + 1, 8 do Local.Chip(J, nil) end
end

---| client clicks on held items |---

function Local.HookTool(T: Instance)
	if not T:IsA(`Tool`) or not T:GetAttribute(`NHKit`) or T:GetAttribute(`NHKitHooked`) then return end
	T:SetAttribute(`NHKitHooked`, true)
	T.Activated:Connect(function()
		local Id = T:GetAttribute(`NHKit`)
		if Id == `CampusMap` then Shared.ToggleMap()
		elseif Id == `Timetable` then
			pcall(function() require(script.Parent:WaitForChild(`Timetable`)).Toggle() end)
		end
	end)
	T.Unequipped:Connect(function()
		if T:GetAttribute(`NHKit`) == `CampusMap` and MapUi then Shared.ToggleMap(false) end
	end)
end

---| the keys you're carrying: Return prompts on their owner, Hand in at a box |---

local KeyPrompts = {}
function Local.StepKeys()
	local Owner = Player:GetAttribute(`NHKitKeys`)
	local Want = {}
	if Owner then
		local O = Players:GetPlayerByUserId(Owner)
		local R = O and O.Character and O.Character:FindFirstChild(`HumanoidRootPart`)
		if R then Want[R] = { Text = `Return keys`; Act = `ReturnKeys`; Arg = Owner } end
		for _, Box in CollectionService:GetTagged(`NHLostFoundBox`) do
			local P = if Box:IsA(`BasePart`) then Box elseif Box:IsA(`Model`) then (Box.PrimaryPart or Box:FindFirstChildWhichIsA(`BasePart`, true)) else nil
			if P then Want[P] = { Text = `Hand in keys`; Act = `HandInKeys` } end
		end
	end
	for Part, Pr in KeyPrompts do
		if not Want[Part] or not Part.Parent then Pr:Destroy() KeyPrompts[Part] = nil end
	end
	for Part, W in Want do
		if not KeyPrompts[Part] then
			local Pr = Instance.new(`ProximityPrompt`)
			Pr.Name = `NHKitKeysLocal`
			Pr.ActionText = W.Text
			Pr.ObjectText = `Dorm keys`
			Pr.HoldDuration = 0.3
			Pr.MaxActivationDistance = 8
			Pr.RequiresLineOfSight = false
			Pr.Triggered:Connect(function() Shared.Act(W.Act, W.Arg) end)   -- the server toasts the result
			Pr.Parent = Part
			KeyPrompts[Part] = Pr
		end
	end
end

---| start |---

function Shared.OnStart()
	local F = ReplicatedStorage:WaitForChild(`NHKit`, 60)
	if not F then return end
	F:WaitForChild(`Changed`).OnClientEvent:Connect(function(S)
		if typeof(S) ~= `table` then return end
		Shared.State = S
		if Counter and Counter.Gui.Enabled then
			local Status = Counter.Status.Text
			Local.FillCounter()
			Counter.Status.Text = Status
		end
		pcall(function()
			local Locker = require(script.Parent:WaitForChild(`Locker`))
			if Locker.IsOpen() and Locker.KitChanged then Locker.KitChanged() end
		end)
	end)
	task.spawn(Shared.Refresh)
	ProximityPromptService.PromptTriggered:Connect(function(Prompt)
		local Shop = Prompt:GetAttribute(`NHKitShop`)
		if Shop then Shared.OpenCounter(Shop, Prompt.Parent) end
	end)
	local function watch(Holder: Instance)
		for _, T in Holder:GetChildren() do Local.HookTool(T) end
		Holder.ChildAdded:Connect(Local.HookTool)
	end
	Player.CharacterAdded:Connect(function(Char) watch(Char) task.defer(function() local B = Player:WaitForChild(`Backpack`, 10) if B then watch(B) end end) end)
	if Player.Character then watch(Player.Character) end
	local B = Player:FindFirstChild(`Backpack`)
	if B then watch(B) end
	local Acc = 0
	RunService.RenderStepped:Connect(function(Dt)
		local Ok, Err = pcall(Local.StepHud)
		if not Ok then warn(`[KitUi] {Err}`) end
		Acc += Dt
		if Acc < 0.5 then return end
		Acc = 0
		pcall(Local.StepKeys)
		if Counter and Counter.Gui.Enabled then
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)
			if not (Root and CounterAt) or (Root.Position - CounterAt.Position).Magnitude > KitCfg.Range then Shared.CloseCounter() end
		end
		if MapUi and MapUi.Gui.Enabled then
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			if Root and MapUi.Bounds then
				local Pos = Local.ToSheet(Root.Position)
				local Cam = workspace.CurrentCamera
				local L = Cam and Cam.CFrame.LookVector or Root.CFrame.LookVector
				MapUi.You.Position = Pos
				MapUi.You.Rotation = math.deg(math.atan2(L.X, -L.Z))
				MapUi.YouL.Position = Pos + UDim2.fromOffset(18, 0)
			end
		end
		if Player:GetAttribute(`InMainMenu`) == true then
			Shared.CloseCounter()
			if MapUi then MapUi.Gui.Enabled = false end
		end
	end)
end

return Shared
