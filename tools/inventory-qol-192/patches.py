# Inventory QOL batch 2 (1.92.0): the stand: tabs, restock, quantity picker, dimming, lunch from the timetable.
import os
HERE = os.path.dirname(os.path.abspath(__file__))
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

def _src(path):
    return open(os.path.join(HERE, "inv6", path + ".luau"), encoding="utf-8", newline="").read()

def _between(path, start, stop):
    s = _src(path)
    a = s.index(start)
    b = s.index(stop, a)
    return s[a:b]

NEW_STAND = r'''-- (inventory QOL 1.92) the stand: tabs by kind of food, a quantity picker on every item, dimmed when you can't afford it
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
		if It and It.Price and Items.OnSale(It) then
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
		Kit.Button({ text = `-`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(6, 154); Parent = Cell; onClick = function() setN(Q.N - 1) end })
		Q.NLabel = Local.Label(Cell, `1`, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(40, 154); Size = UDim2.fromOffset(36, 32) })
		Kit.Button({ text = `+`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(78, 154); Parent = Cell; onClick = function() setN(Q.N + 1) end })
		Kit.Button({ text = `Max`; Size = UDim2.fromOffset(76, 32); Position = UDim2.fromOffset(118, 154); Parent = Cell; onClick = function()
			local Unit = Price(`Concession`, It.Price)
			local Room = Items.MaxStack - ((State and State.Items[It.Id]) or 0)
			setN(math.max(1, math.min(Room, if Unit > 0 then math.floor(((State and State.Yen) or 0) / Unit) else Room)))
		end })
		local _, BuyApi = Kit.Button({ text = ``; style = `gold`; Size = UDim2.fromOffset(188, 36); Position = UDim2.fromOffset(6, 194); Parent = Cell;
			onClick = function()
				local Ok, Msg = Local.Call(`Buy`, It.Id, Q.N)
				Stand.Status.Text = Msg or ``
				if Ok then pcall(Kit.PlaySound, `Confirm`) Q.N = 1 Local.UpdateCell(Q) end
			end })
		Q.Buy = BuyApi
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
	local T = `{math.floor(Secs / 60)}:{string.format(`%02d`, math.floor(Secs % 60))}`
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

'''

EDITS = [
# ---- Config.Items: the stand's tabs, and lunch from the timetable ----
(ITEMS, """function Items.LunchOpen(): boolean
	return game:GetService(`ReplicatedStorage`):GetAttribute(`NHLunchOpen`) == true
end
""", """-- (inventory QOL 1.92) the lunch period comes from the school timetable (the Lunch segment, 11:25 to 12:00 on school
-- days); ReplicatedStorage's NHLunchOpen = true still forces it open. LunchInfo returns whether it's open and the real
-- seconds until it opens (shut) or closes (open), or nil when there's no lunch in the next few days.
local LunchCache = { At = -1e9 }
function Items.LunchInfo(): (boolean, number?)
	local RS = game:GetService(`ReplicatedStorage`)
	local Forced = RS:GetAttribute(`NHLunchOpen`) == true
	local Clock = RS:FindFirstChild(`SchoolClock`)
	local Epoch = Clock and Clock:GetAttribute(`Epoch`)
	if not Epoch then return Forced, nil end
	local Now = workspace:GetServerTimeNow()
	if Now - LunchCache.At < 1 and LunchCache.Epoch == Epoch then
		local Left = LunchCache.Secs and (LunchCache.Secs - (Now - LunchCache.At)) or nil
		return Forced or LunchCache.Open, Left
	end
	local ST = require(RS.Functions.SchoolTime)
	local S = ST.GetState(Epoch, Now)
	-- game minutes per real second, measured over the next ten real minutes
	local Ahead = ST.GetState(Epoch, Now + 600)
	local Rate = ((Ahead.Day - S.Day) * 1440 + Ahead.MinuteOfDay - S.MinuteOfDay) / 600
	local Open, Secs = false, nil
	if Rate > 0 then
		if S.Segment and S.Segment.Kind == `Lunch` then
			Open, Secs = true, (S.Segment.End - S.MinuteOfDay) / Rate
		else
			for D = 0, 3 do
				local Found = false
				for M = (if D == 0 then math.floor(S.MinuteOfDay) + 1 else 0), 1439, 5 do
					local At = ST.GetState(ST.EpochFor(Now, S.Day + D, M), Now)
					if At.Segment and At.Segment.Kind == `Lunch` then
						Secs = (D * 1440 + At.Segment.Start - S.MinuteOfDay) / Rate
						Found = true
						break
					end
				end
				if Found then break end
			end
		end
	end
	LunchCache = { At = Now; Epoch = Epoch; Open = Open; Secs = Secs }
	return Forced or Open, Secs
end

function Items.LunchOpen(): boolean
	return (Items.LunchInfo())
end

-- (inventory QOL 1.92) the stand's tabs. Category says which tab an item sits under; anything not listed goes by kind
-- (food under Hot food, buffs under Drinks), and the lunch meals under Lunch.
Items.StandTabs = { `All`, `Hot food`, `Snacks`, `Sweets`, `Drinks`, `Lunch` }
Items.Category = {
	Onigiri = `Hot food`; YakisobaBun = `Hot food`; Bento = `Hot food`; TakoyakiBoat = `Hot food`;
	Nikuman = `Hot food`; CurryBread = `Hot food`; CupRamen = `Hot food`; RoastSweetPotato = `Hot food`;
	YakitoriSkewers = `Hot food`; PumpkinSoup = `Hot food`; GarlicBread = `Hot food`; MeatLoaf = `Hot food`;
	MelonBread = `Snacks`; Senbei = `Snacks`; GraveCrisps = `Snacks`; Popcorn = `Snacks`; PrankKit = `Snacks`;
	BatGummies = `Sweets`; CandyApple = `Sweets`; GhostMints = `Sweets`; KonpeitoStars = `Sweets`; LicoriceWhips = `Sweets`;
	ChocolateBar = `Sweets`; Dango = `Sweets`; Taiyaki = `Sweets`; PuddingCup = `Sweets`; TombstoneCookie = `Sweets`;
	CreamPuff = `Sweets`; MoonCake = `Sweets`; EctoJelly = `Sweets`;
	Ramune = `Drinks`; BarleyTea = `Drinks`; CannedCoffee = `Drinks`; RedLantern = `Drinks`; StrawberryMilk = `Drinks`;
	HotCocoa = `Drinks`; MelonSoda = `Drinks`; BlackCatCola = `Drinks`; GreenTea = `Drinks`; HolyLemonade = `Drinks`;
}
function Items.CategoryOf(It): string
	if It.Lunch then return `Lunch` end
	return Items.Category[It.Id] or (if It.Kind == `Heal` then `Hot food` elseif It.Kind == `Prank` then `Snacks` else `Drinks`)
end
"""),
# ---- Inventory (server): Restock ----
(INV, """function Shared.Pin(P: Player, Id: any, On: any): (boolean, string?)""", """-- (inventory QOL 1.92) "Restock my pins": every pinned item on sale, bought up to To each (Buy's checks apply: the stand,
-- your Yen, daily limits). Stops at the first item you can't afford.
Shared.RESTOCK_TO = 5
function Shared.Restock(P: Player, To: any): (boolean, string)
	local Target = if typeof(To) == `number` and To == To then math.clamp(math.floor(To), 1, Items.MaxStack) else Shared.RESTOCK_TO
	local Inv = Shared.Get(P)
	local Profile = Data.GetProfile(P)
	if not (Inv and Profile) then return false, `Your record isn't loaded yet.` end
	if not Shared.NearStand(P) then return false, `You're too far from the stand.` end
	local Yen0 = Profile.Yen or 0
	local Got, Why = {}, nil
	for _, Id in table.clone(Inv.Pinned) do
		local It = Items.ById[Id]
		local Need = Target - ((Shared.Get(P) or Inv).Items[Id] or 0)
		if It and It.Price and Need > 0 and Items.OnSale(It) then
			local Ok, Msg = Shared.Buy(P, Id, Need)
			if Ok then
				local N = tonumber(string.match(Msg, `^Bought (%d+)`)) or Need
				table.insert(Got, `{N} {It.Name}`)
			else
				Why = Why or Msg
				if Msg == `Not enough Yen.` then break end
			end
		end
	end
	if #Got == 0 then return false, Why or `Your pins are already stocked.` end
	local Spent = Yen0 - ((Data.GetProfile(P) or Profile).Yen or 0)
	return true, `Restocked {table.concat(Got, `, `)} (\\u{A5}{Spent}).` .. (if Why then `  {Why}` else ``)
end

function Shared.Pin(P: Player, Id: any, On: any): (boolean, string?)"""),
(INV, """	local Get, Use, Pin, Drop, Buy = rf(`Get`), rf(`Use`), rf(`Pin`), rf(`Drop`), rf(`Buy`)""",
      """	local Get, Use, Pin, Drop, Buy = rf(`Get`), rf(`Use`), rf(`Pin`), rf(`Drop`), rf(`Buy`)
	local Restock = rf(`Restock`) -- (inventory QOL 1.92)"""),
(INV, """	Buy.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Buy(P, Id, N) end""",
      """	Buy.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Buy(P, Id, N) end
	Restock.OnServerInvoke = function(P, To) if limited(P) then return false, `One moment...` end return Shared.Restock(P, To) end"""),
# ---- Locker: the stand ----
(LOCK, _between(LOCK, "function Local.BuildStand()", "function Shared.OpenStand("), NEW_STAND),
(LOCK, """			if Stand and Stand.Gui.Enabled then
				local Status = Stand.Status.Text
				Local.FillStand()
				Stand.Status.Text = Status
			end""", """			if Stand and Stand.Gui.Enabled then Local.UpdateStand() end -- (inventory QOL 1.92) in place, no rebuild"""),
(LOCK, """		if Stand and Stand.Gui.Enabled then
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)""", """		if Stand and Stand.Gui.Enabled then
			-- (inventory QOL 1.92) the lunch countdown; lunch opening or closing rebuilds the list
			local WasOpen = Stand.LunchOpen
			Stand.LunchOpen = Items.LunchOpen()
			if WasOpen ~= nil and WasOpen ~= Stand.LunchOpen then Local.FillStand() else Stand.Lunch.Text = Local.LunchLine() end
			local Root = Player.Character and Player.Character:FindFirstChild(`HumanoidRootPart`)"""),
]
# batch 2 polish: named picker buttons, centred quantity, hours in long waits
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"
EDITS = [
(LOCK, """		Kit.Button({ text = `-`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(6, 154); Parent = Cell; onClick = function() setN(Q.N - 1) end })
		Q.NLabel = Local.Label(Cell, `1`, 18, { Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(40, 154); Size = UDim2.fromOffset(36, 32) })
		Kit.Button({ text = `+`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(78, 154); Parent = Cell; onClick = function() setN(Q.N + 1) end })
		Kit.Button({ text = `Max`; Size = UDim2.fromOffset(76, 32); Position = UDim2.fromOffset(118, 154); Parent = Cell; onClick = function()""",
       """		local MinusB = Kit.Button({ text = `-`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(6, 154); Parent = Cell; onClick = function() setN(Q.N - 1) end })
		Q.NLabel = Local.Label(Cell, `1`, 20, { Name = `Qty`; Font = Fonts.Title; TextXAlignment = Enum.TextXAlignment.Center; TextYAlignment = Enum.TextYAlignment.Center;
			Position = UDim2.fromOffset(40, 154); Size = UDim2.fromOffset(36, 32) })
		local PlusB = Kit.Button({ text = `+`; Size = UDim2.fromOffset(32, 32); Position = UDim2.fromOffset(78, 154); Parent = Cell; onClick = function() setN(Q.N + 1) end })
		if typeof(MinusB) == `Instance` then MinusB.Name = `Minus` end
		if typeof(PlusB) == `Instance` then PlusB.Name = `Plus` end
		local MaxB = Kit.Button({ text = `Max`; Size = UDim2.fromOffset(76, 32); Position = UDim2.fromOffset(118, 154); Parent = Cell; onClick = function()"""),
(LOCK, """			setN(math.max(1, math.min(Room, if Unit > 0 then math.floor(((State and State.Yen) or 0) / Unit) else Room)))
		end })
		local _, BuyApi = Kit.Button({""", """			setN(math.max(1, math.min(Room, if Unit > 0 then math.floor(((State and State.Yen) or 0) / Unit) else Room)))
		end })
		if typeof(MaxB) == `Instance` then MaxB.Name = `Max` end
		local BuyB, BuyApi = Kit.Button({"""),
(LOCK, """		Q.Buy = BuyApi
""", """		Q.Buy = BuyApi
		if typeof(BuyB) == `Instance` then BuyB.Name = `Buy` end
"""),
(LOCK, """	local T = `{math.floor(Secs / 60)}:{string.format(`%02d`, math.floor(Secs % 60))}`""",
       """	local T = if Secs >= 3600 then `{math.floor(Secs / 3600)} h {math.floor(Secs % 3600 / 60)} min`
		else `{math.floor(Secs / 60)}:{string.format(`%02d`, math.floor(Secs % 60))}`"""),
]
# batch 2: the restock leaves out daily-limited items (prank kits, the daily special)
INV = "ServerScriptService.Services.Features.Inventory"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"
EDITS = [
(INV, """		if It and It.Price and Need > 0 and Items.OnSale(It) then
			local Ok, Msg = Shared.Buy(P, Id, Need)""", """		if It and It.Price and not It.DailyLimit and Need > 0 and Items.OnSale(It) then -- limited items aren't restocked
			local Ok, Msg = Shared.Buy(P, Id, Need)"""),
(LOCK, """		if It and It.Price and Items.OnSale(It) then
			local Need = math.max(0, RESTOCK_TO - ((State.Items and State.Items[Id]) or 0))""", """		if It and It.Price and not It.DailyLimit and Items.OnSale(It) then -- prank kits and specials aren't restocked
			local Need = math.max(0, RESTOCK_TO - ((State.Items and State.Items[Id]) or 0))"""),
]
