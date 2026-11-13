--[[
	Inventory (server). Services.Features.Inventory
	Your Locker: consumables (Config.Items, saved in PlayerData.Inventory = { Items = { [id] = n }, Pinned = { id } })
	plus your 3D gear (owned / worn, kept by Services.Features.Gear in Identity; shown, not changed, here).

	  * Pinned snacks (up to 4) are Tools in your Backpack, so they sit on the existing hotbar (KitHud reads the
	    Tool's Rarity / Count attributes). Equip one and click to eat or drink it.
	  * Heal food restores health over a few seconds (half while combat-tagged) and shares a "full" cooldown.
	  * Drinks give one snack buff at a time (Shared.Effects, added into Progression.Effects while active).
	    Player attributes NHSnackBuff (item id) and NHSnackBuffUntil (server time) for the UI.
	  * Bought at the concession stand (Services.Features.Concession, tag NHConcession, within 16 studs).
	  * (1.33) Prank kits: at most DailyLimit a day from the stand (Inventory.Daily, by the 6 AM event day). Used from
	    the hotbar at a prank spot, or by holding E on one (Services.Social.CliquePranks takes one with Shared.Take).
	Remotes ReplicatedStorage.NHInventory (attribute Ready):
	  Get (RF) -> state, Use (RF id), Pin (RF id, on), Drop (RF id, n), Buy (RF id, n), Changed (RE) -> state
]]
local CollectionService = game:GetService(`CollectionService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local Notifications = require(ServerScriptService.Services.Features.Notifications)
local Items = require(ReplicatedStorage.Config.Items)

local EAT_ANIM = 126575676069500 -- the owner's "eating lunch" clip

local Shared = {}
local Local = {}
local Remotes = nil
local Buffs = {} :: { [Player]: { Id: string, Until: number } }
local Cooldowns = {} :: { [Player]: { [string]: number } }
local Busy = {} :: { [Player]: boolean }
local LastCall = {} :: { [Player]: number }
local LastDrop = {} :: { [Player]: { Id: string, N: number, Until: number } } -- (inventory QOL 1.93) Undo

---| data |---

function Shared.Get(P: Player)
	local Profile = Data.GetProfile(P)
	return Profile and Items.Sanitize(Profile.Inventory)
end

function Local.Save(P: Player, Inv)
	Data.UpdateState(P, { type = `SetInventory`; inventory = Inv })
	Local.SyncTools(P, Inv)
	Local.Push(P)
end

function Shared.State(P: Player)
	local Inv = Shared.Get(P)
	if not Inv then return nil end
	local I = Identity.Get(P)
	local Profile = Data.GetProfile(P)
	local B = Buffs[P]
	local Cd = Cooldowns[P] or {}
	return {
		Items = Inv.Items; Pinned = Inv.Pinned; Boards = Inv.Boards; Fav = Inv.Fav or {}; -- (inventory QOL 1.93)
		Gear = I and I.Gear or {}; GearOn = I and I.GearOn or {};
		Yen = Profile and Profile.Yen or 0; Weapon = Profile and Profile.Weapon or nil;
		Buff = B and B.Until > workspace:GetServerTimeNow() and { Id = B.Id; Until = B.Until } or nil;
		HealReady = Cd.Heal or 0; -- server time
		Tasted = Inv.Tasted or {}; -- (inventory QOL batch 5) the taste book
		BuffReady = Cd.Buff or 0; -- (inventory QOL 1.94) the one-sip wait, for the snack wheel
	}
end

function Local.Push(P: Player)
	if Remotes and P.Parent then
		local S = Shared.State(P)
		if S then Remotes.Changed:FireClient(P, S) end
	end
end

-- (inventory audit 1.90) a pin on a snack you've run out of keeps its pouch slot for the restock, but gives way when
-- the pouch is full and you pin (or are given) something else. Returns true if one was freed.
function Local.FreeEmptyPin(Inv): boolean
	for I, Pid in Inv.Pinned do
		if (Inv.Items[Pid] or 0) <= 0 then table.remove(Inv.Pinned, I) return true end
	end
	return false
end

-- give items (quests, admin, rewards). Returns how many fit.
function Shared.Grant(P: Player, Id: string, N: number?): number
	local Inv = Shared.Get(P)
	local It = Items.ById[Id]
	if not (Inv and It) then return 0 end
	local Have = Inv.Items[Id] or 0
	local Add = math.clamp(math.floor(N or 1), 0, Items.MaxStack - Have)
	if Add <= 0 then return 0 end
	Inv.Items[Id] = Have + Add
	-- (beasts) a trophy stays in the Locker, never on the hotbar
	if It.Kind ~= `Trophy` and not table.find(Inv.Pinned, Id) and (#Inv.Pinned < Items.MaxPinned or Local.FreeEmptyPin(Inv)) then table.insert(Inv.Pinned, Id) end
	Local.Save(P, Inv)
	return Add
end

-- your skateboards (Config.Boards; Services.Features.Skateboard buys and equips through these)
function Shared.Boards(P: Player)
	local Inv = Shared.Get(P)
	return Inv and Inv.Boards
end

function Shared.SetBoards(P: Player, Boards): boolean
	local Inv = Shared.Get(P)
	if not Inv then return false end
	Inv.Boards = require(ReplicatedStorage.Config.Boards).Sanitize(Boards)
	Local.Save(P, Inv)
	return true
end

-- (kit 1.79) the everyday kit's record (Services.Features.Kit). Quiet = only save (the kit's once-a-second fuel burn)
function Shared.SetKit(P: Player, Kit, Quiet: boolean?): boolean
	-- (inventory audit 1.90) the once-a-second fuel burn only updates the kit in the profile (ProfileService autosaves
	-- it); it no longer re-sanitizes the whole inventory and sends it to the client every second
	if Quiet then
		local Profile = Data.GetProfile(P)
		if Profile and typeof(Profile.Inventory) == `table` then
			Profile.Inventory.Kit = require(ReplicatedStorage.Config.Kit).Sanitize(Kit)
			return true
		end
	end
	local Inv = Shared.Get(P)
	if not Inv then return false end
	Inv.Kit = require(ReplicatedStorage.Config.Kit).Sanitize(Kit)
	if Quiet then Data.UpdateState(P, { type = `SetInventory`; inventory = Inv }) return true end
	Local.Save(P, Inv)
	return true
end

-- (kit 1.79) a buff from the kit (the flask's coffee): the same one-buff-at-a-time rule as the drinks
function Shared.GiveBuff(P: Player, Id: string): boolean
	local It = Items.ById[Id]
	if not (It and It.Kind == `Buff`) then return false end
	Local.Buff(P, It)
	Local.Push(P)
	return true
end

-- (kit 1.79) eating from the snack tin: the eating clip and the shared "full" cooldown, then Consume() and the heal
function Shared.KitEat(P: Player, Heal: number, Duration: number, Consume: () -> boolean, NoAnim: boolean?): (boolean, string?)
	local Char = P.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not Hum or Hum.Health <= 0 or Busy[P] then return false, nil end
	if Char:GetAttribute(`DownedUntil`) or Char:GetAttribute(`Downed`) then return false, `Not while you're down.` end
	local Now = workspace:GetServerTimeNow()
	Cooldowns[P] = Cooldowns[P] or {}
	local Cd = Cooldowns[P].Heal or 0
	if Cd > Now then return false, `You're still full ({math.ceil(Cd - Now)} s).` end
	Busy[P] = true
	Cooldowns[P].Heal = Now + Items.Cooldown.Heal + Items.UseTime
	Local.MarkReady(P) -- (inventory QOL 1.91)
	if not NoAnim then Local.Anim(Hum) end -- (inventory audit 1.90) the tin plays its own clip
	task.delay(Items.UseTime, function()
		Busy[P] = nil
		if not (P.Parent and Hum.Parent and Hum.Health > 0) then return end
		if not Consume() then return end
		Local.Heal(P, Hum, { Heal = Heal; Duration = Duration })
	end)
	return true, nil
end

---| hotbar tools |---

function Local.Prop(It): BasePart
	-- (batch 54) the item's modelled hand prop (ReplicatedStorage.NHSnacks.<Id>.Handle, glass welded under it) when it's in
	local Lib = ReplicatedStorage:FindFirstChild(`NHSnacks`)
	local Tpl = Lib and Lib:FindFirstChild(It.Id)
	local Mesh = Tpl and Tpl:FindFirstChild(`Handle`)
	if Mesh then
		local H = Mesh:Clone()
		for _, D in { H, table.unpack(H:GetDescendants()) } do
			if D:IsA(`BasePart`) then D.Anchored = false D.CanCollide, D.CanQuery, D.CanTouch, D.Massless = false, false, false, true end
		end
		return H
	end
	local P = Instance.new(`Part`)
	P.Name = `Handle`
	P.CanCollide, P.CanQuery, P.CanTouch, P.Massless = false, false, false, true
	P.Color = It.Prop.Color
	P.Material = Enum.Material.SmoothPlastic
	local Shape = It.Prop.Shape
	if Shape == `Can` then
		P.Shape = Enum.PartType.Cylinder
		P.Size = Vector3.new(0.75, 0.42, 0.42)
	elseif Shape == `Bottle` then
		P.Shape = Enum.PartType.Cylinder
		P.Size = Vector3.new(0.95, 0.36, 0.36)
		P.Material = Enum.Material.Glass
		P.Transparency = 0.25
	elseif Shape == `Box` then
		P.Size = Vector3.new(0.75, 0.32, 0.55)
		P.Material = Enum.Material.Wood
	else
		P.Shape = Enum.PartType.Ball
		P.Size = Vector3.new(0.55, 0.55, 0.55)
	end
	return P
end

function Local.AddHandle(T: Tool, It)
	local H = Local.Prop(It)
	H.Parent = T
	if H:GetAttribute(`NHGrip`) then T.Grip = H:GetAttribute(`NHGrip`) -- (batch 54) the modelled prop's own grip
	elseif It.Prop.Shape == `Can` or It.Prop.Shape == `Bottle` then T.GripRight = Vector3.new(0, 0, 1) T.GripUp = Vector3.new(1, 0, 0) end
end

-- (inventory QOL 1.91) a pinned snack you've run out of stays on the hotbar, greyed, with nothing in the hand: its
-- Handle goes (NHEmpty = true) and comes back when you restock
function Local.SetEmpty(P: Player, T: Tool, Empty: boolean)
	if (T:GetAttribute(`NHEmpty`) == true) == Empty then return end
	local It = Items.ById[T:GetAttribute(`NHItem`)]
	if not It then return end
	local Char = P.Character
	if Char and T.Parent == Char then
		local Hum = Char:FindFirstChildOfClass(`Humanoid`)
		if Hum then Hum:UnequipTools() end
	end
	if Empty then
		local H = T:FindFirstChild(`Handle`)
		if H then H:Destroy() end
	else
		Local.AddHandle(T, It)
	end
	T.RequiresHandle = not Empty
	T:SetAttribute(`NHEmpty`, if Empty then true else nil)
	T.ToolTip = if Empty then `None left. Restock at the stand.` else Items.Describe(It)
end

-- (inventory QOL 1.91) every snack tool carries when it's usable again (NHReadyAt, server time) and how long that
-- wait is (NHCooldown), so the hotbar can shade the slot
function Local.MarkReady(P: Player)
	local Cd = Cooldowns[P] or {}
	local Now = workspace:GetServerTimeNow()
	for _, Holder in { P:FindFirstChildOfClass(`Backpack`), P.Character } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			local It = T:IsA(`Tool`) and Items.ById[T:GetAttribute(`NHItem`) or ``]
			if It then
				local At = Cd[It.Kind]
				T:SetAttribute(`NHReadyAt`, if At and At > Now then At else nil)
				T:SetAttribute(`NHCooldown`, (Items.Cooldown[It.Kind] or 0) + Items.UseTime)
			end
		end
	end
end

function Local.MakeTool(P: Player, It): Tool
	local T = Instance.new(`Tool`)
	T.Name = It.Name
	T.CanBeDropped = false
	T.ToolTip = Items.Describe(It)
	T:SetAttribute(`NHItem`, It.Id)
	T:SetAttribute(`Rarity`, It.Rarity)
	Local.AddHandle(T, It)
	T.Activated:Connect(function()
		local Ok, Msg = Shared.Use(P, It.Id)
		if not Ok and Msg then Notifications.Notify(P, { Title = Msg; Kind = `Info`; Duration = 2.5 }) end
	end)
	return T
end

-- one Tool per pinned item you have, in pin order; counts kept on the Count attribute
function Local.SyncTools(P: Player, Inv)
	Inv = Inv or Shared.Get(P)
	local Pack = P:FindFirstChildOfClass(`Backpack`)
	if not (Inv and Pack) then return end
	local Want = {}
	-- (inventory QOL 1.91) every pin gets a tool, empty ones too (shown greyed until you restock)
	for _, Id in Inv.Pinned do if Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` then Want[Id] = true end end
	local Have = {}
	for _, Holder in { Pack, P.Character } do
		for _, T in (Holder and Holder:GetChildren()) or {} do
			local Id = T:IsA(`Tool`) and T:GetAttribute(`NHItem`)
			if Id then
				if Want[Id] and not Have[Id] then
					Have[Id] = T
					T:SetAttribute(`Count`, Inv.Items[Id] or 0)
					Local.SetEmpty(P, T, (Inv.Items[Id] or 0) <= 0)
				else
					T:Destroy()
				end
			end
		end
	end
	for _, Id in Inv.Pinned do
		if Want[Id] and not Have[Id] then
			local T = Local.MakeTool(P, Items.ById[Id])
			T:SetAttribute(`Count`, Inv.Items[Id] or 0)
			Local.SetEmpty(P, T, (Inv.Items[Id] or 0) <= 0)
			T.Parent = Pack
		end
	end
	Local.MarkReady(P)
end

---| using |---

function Local.Anim(Hum: Humanoid)
	local Animator = Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return end
	local A = Instance.new(`Animation`)
	A.AnimationId = `rbxassetid://{EAT_ANIM}`
	local Ok, Tr = pcall(function() return Animator:LoadAnimation(A) end)
	if not Ok then return end
	Tr.Priority = Enum.AnimationPriority.Action
	Tr:Play(0.15)
	task.delay(Items.UseTime, function() Tr:Stop(0.25) end)
end

function Shared.Use(P: Player, Id: any): (boolean, string?)
	local It = typeof(Id) == `string` and Items.ById[Id]
	if not It then return false, `Unknown item.` end
	local Inv = Shared.Get(P)
	if not Inv or (Inv.Items[Id] or 0) <= 0 then return false, `None left. Restock at the stand.` end -- (inventory QOL 1.91)
	local Char = P.Character
	local Hum = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not Hum or Hum.Health <= 0 then return false, nil end
	if P:GetAttribute(`InMainMenu`) == true then return false, nil end
	if Char:GetAttribute(`DownedUntil`) or Char:GetAttribute(`Downed`) then return false, `Not while you're down.` end
	if Busy[P] then return false, `Still eating.` end -- (inventory QOL 1.91) no silent refusals
	if It.Kind == `Trophy` then return false, `A trophy. It stays in your Locker.` end
	if It.Kind == `Prank` then
		local Ok, Pranks = pcall(require, ServerScriptService.Services.Social.CliquePranks)
		if not (Ok and Pranks and Pranks.UseKit) then return false, nil end
		return Pranks.UseKit(P)
	end
	local Now = workspace:GetServerTimeNow()
	Cooldowns[P] = Cooldowns[P] or {}
	local Cd = Cooldowns[P][It.Kind] or 0
	if Cd > Now then
		return false, if It.Kind == `Heal` then `You're still full ({math.ceil(Cd - Now)} s).` else `One sip at a time.`
	end
	Busy[P] = true
	Cooldowns[P][It.Kind] = Now + Items.Cooldown[It.Kind] + Items.UseTime
	Local.MarkReady(P) -- (inventory QOL 1.91)
	-- (batch 54 trays) a lunch tray plays its own eating clip (Features.Tray.OnUse); a grimace item reacts first
	local TrayOk, TrayPlayed = pcall(function() return require(ServerScriptService.Services.Features.Tray).OnUse(P, Hum, It) end)
	if not (TrayOk and TrayPlayed) then Local.Anim(Hum) end
	task.delay(Items.UseTime, function()
		Busy[P] = nil
		if not (P.Parent and Hum.Parent and Hum.Health > 0) then return end
		local Inv2 = Shared.Get(P)
		if not Inv2 or (Inv2.Items[Id] or 0) <= 0 then return end
		Inv2.Items[Id] -= 1
		if Inv2.Items[Id] <= 0 then Inv2.Items[Id] = nil end
		local Fresh = Local.MarkTasted(Inv2, It) -- (inventory QOL batch 5) the taste book
		Local.Save(P, Inv2)
		if Fresh then Local.TasteMilestone(P, Inv2) end
		if It.Kind == `Heal` then
			Local.Heal(P, Hum, It)
		else
			Local.Buff(P, It)
			-- (1.39) a daily special: say what it did for your race
			if It.Special then
				local Note = Items.RaceNote(It, P:GetAttribute(`Race`))
				Notifications.Notify(P, { Title = It.Name; Text = Note or `Today's special. {Items.Describe(It)}.`; Kind = `Info`; Duration = 4 })
			end
		end
	end)
	return true, nil
end

function Local.Heal(P: Player, Hum: Humanoid, It)
	local Steps = math.max(1, math.floor(It.Duration / 0.5))
	task.spawn(function()
		for _ = 1, Steps do
			if not (Hum.Parent and Hum.Health > 0) then return end
			local Char = Hum.Parent
			if Char:GetAttribute(`DownedUntil`) or Char:GetAttribute(`Downed`) then return end
			local Tagged = (P:GetAttribute(`CombatTagUntil`) or 0) > workspace:GetServerTimeNow()
			local Amount = It.Heal / Steps * (if Tagged then 0.5 else 1)
			Hum.Health = math.min(Hum.MaxHealth, Hum.Health + Amount)
			task.wait(0.5)
		end
	end)
end

function Local.Buff(P: Player, It)
	local Until = workspace:GetServerTimeNow() + It.Duration
	Buffs[P] = { Id = It.Id; Until = Until }
	P:SetAttribute(`NHSnackBuff`, It.Id)
	P:SetAttribute(`NHSnackBuffUntil`, Until)
	Local.Reapply(P)
	task.delay(It.Duration + 0.1, function()
		local B = Buffs[P]
		if B and B.Until == Until then
			Buffs[P] = nil
			if P.Parent then
				P:SetAttribute(`NHSnackBuff`, nil)
				P:SetAttribute(`NHSnackBuffUntil`, nil)
				Local.Reapply(P)
				Local.Push(P)
			end
		end
	end)
end

function Local.Reapply(P: Player)
	pcall(function()
		local Progression = require(ServerScriptService.Services.Player.Progression)
		Progression.Apply(P)
		Progression.Notify(P)
	end)
end

-- the active snack buff's effects (Progression.Effects adds them in)
function Shared.Effects(P: Player)
	local B = Buffs[P]
	if not B or B.Until <= workspace:GetServerTimeNow() then return {} end
	local It = Items.ById[B.Id]
	if not It then return {} end
	-- (1.39) a special's race twist
	return Items.EffectsFor(It, P:GetAttribute(`Race`))
end

-- (1.33) take items away (a prank kit spent at a prank spot). Returns how many were taken.
function Shared.Take(P: Player, Id: string, N: number?): number
	local Inv = Shared.Get(P)
	if not (Inv and Items.ById[Id]) then return 0 end
	local Have = Inv.Items[Id] or 0
	local Take = math.clamp(math.floor(N or 1), 0, Have)
	if Take <= 0 then return 0 end
	Inv.Items[Id] = if Have - Take > 0 then Have - Take else nil
	Local.Save(P, Inv)
	return Take
end

function Local.EventDay(): number
	local Clock = require(ServerScriptService.Services.School.SchoolClock)
	local State = Clock.GetState()
	return require(ReplicatedStorage.Config.Cliques).EventDay(State) or State.Day
end

-- how many more of a daily-limited item the stand will sell you today
function Shared.LeftToday(P: Player, Id: string): number?
	local It = Items.ById[Id]
	if not (It and It.DailyLimit) then return nil end
	local Inv = Shared.Get(P)
	local Daily = Inv and Inv.Daily
	local Bought = if Daily and Daily.Day == Local.EventDay() then (Daily[Id] or 0) else 0
	return math.max(0, It.DailyLimit - Bought)
end

---| buying, pinning, dropping |---

function Shared.NearStand(P: Player): boolean
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	if not Root then return false end
	for _, S in CollectionService:GetTagged(`NHConcession`) do
		local Pos = if S:IsA(`BasePart`) then S.Position elseif S:IsA(`Model`) then S:GetPivot().Position else nil
		if Pos and (Pos - Root.Position).Magnitude <= 16 then return true end
	end
	return false
end

function Shared.Buy(P: Player, Id: any, N: any): (boolean, string)
	local It = typeof(Id) == `string` and Items.ById[Id]
	if not It or not It.Price then return false, `Not sold here.` end -- (beasts) trophies have no price
	-- (1.39) a daily special is only sold on its day
	if not Items.OnSale(It) then
		local T = Items.TodaySpecial()
		return false, if T then `That's not on today. Today's special is {T.Name}.` else `That's not on today.`
	end
	local Count = if typeof(N) == `number` and N == N then math.clamp(math.floor(N), 1, Items.MaxStack) else 1
	if not Shared.NearStand(P) then return false, `You're too far from the stand.` end
	local Inv = Shared.Get(P)
	local Profile = Data.GetProfile(P)
	if not (Inv and Profile) then return false, `Your record isn't loaded yet.` end
	local Room = Items.MaxStack - (Inv.Items[Id] or 0)
	if Room <= 0 then return false, `You can't carry more {It.Name}.` end
	Count = math.min(Count, Room)
	local Left = Shared.LeftToday(P, Id)
	if Left then
		if Left <= 0 then return false, `That's all the {It.Name}s for today ({It.DailyLimit} a day).` end
		Count = math.min(Count, Left)
	end
	-- (1.28) clique discount (Config.Cliques.PriceFactor: the Ordinary run the lunch line)
	local Unit = math.ceil(It.Price * require(game:GetService(`ReplicatedStorage`).Config.Cliques).PriceFactor(P, `Concession`))
	local Cost = Unit * Count
	if (Profile.Yen or 0) < Cost then return false, `Not enough Yen.` end
	Data.UpdateState(P, { type = `UpdateYen`; amount = -Cost })
	Shared.Grant(P, Id, Count)
	if It.DailyLimit then
		local Inv2 = Shared.Get(P)
		if Inv2 then
			local Day = Local.EventDay()
			if not (Inv2.Daily and Inv2.Daily.Day == Day) then Inv2.Daily = { Day = Day } end
			Inv2.Daily[Id] = (Inv2.Daily[Id] or 0) + Count
			Local.Save(P, Inv2)
		end
	end
	return true, `Bought {Count} {It.Name}.`
end

-- (inventory QOL 1.92) "Restock my pins": every pinned item on sale, bought up to To each (Buy's checks apply: the stand,
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
		if It and It.Price and not It.DailyLimit and Need > 0 and Items.OnSale(It) then -- limited items aren't restocked
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
	return true, `Restocked {table.concat(Got, `, `)} (\u{A5}{Spent}).` .. (if Why then `  {Why}` else ``)
end

function Shared.Pin(P: Player, Id: any, On: any): (boolean, string?)
	local Inv = Shared.Get(P)
	if not (Inv and typeof(Id) == `string` and Items.ById[Id]) then return false, `Unknown item.` end
	if On and Items.ById[Id].Kind == `Trophy` then return false, `Trophies stay in your Locker.` end
	if On and (Inv.Items[Id] or 0) <= 0 then return false, `You don't have any.` end -- (inventory audit 1.90)
	local At = table.find(Inv.Pinned, Id)
	if On and not At then
		if #Inv.Pinned >= Items.MaxPinned and not Local.FreeEmptyPin(Inv) then return false, `Your hotbar holds {Items.MaxPinned} snacks. Unpin one first.` end
		table.insert(Inv.Pinned, Id)
	elseif not On and At then
		table.remove(Inv.Pinned, At)
	end
	Local.Save(P, Inv)
	return true
end

function Shared.Drop(P: Player, Id: any, N: any): (boolean, string?)
	local Inv = Shared.Get(P)
	if not (Inv and typeof(Id) == `string` and Inv.Items[Id]) then return false, `You don't have any.` end
	local Count = if typeof(N) == `number` and N == N then math.clamp(math.floor(N), 1, Items.MaxStack) else 1
	Count = math.min(Count, Inv.Items[Id])
	Inv.Items[Id] = math.max(0, Inv.Items[Id] - Count)
	if Inv.Items[Id] == 0 then Inv.Items[Id] = nil end
	Local.Save(P, Inv)
	LastDrop[P] = { Id = Id; N = Count; Until = os.clock() + 5 } -- (inventory QOL 1.93) Undo for 5 s
	return true
end

-- (inventory QOL batch 5) the taste book: the first time you eat or drink something it's ticked off. Returns true if
-- it was new.
function Local.MarkTasted(Inv, It): boolean
	if not (It and (It.Kind == `Heal` or It.Kind == `Buff`) and not It.Hidden) then return false end
	Inv.Tasted = Inv.Tasted or {}
	if Inv.Tasted[It.Id] then return false end
	Inv.Tasted[It.Id] = true
	return true
end

function Local.TasteCount(Inv): (number, number)
	local Have, Total = 0, 0
	for _, It in Items.Tasteable() do
		Total += 1
		if Inv.Tasted and Inv.Tasted[It.Id] then Have += 1 end
	end
	return Have, Total
end

-- how many milestones you've reached (each one is +1 max health and a title)
function Local.TasteReached(Inv): number
	local Have, Total = Local.TasteCount(Inv)
	local N = 0
	for _, M in Items.TasteMilestones do
		if Have >= (if M.At == `All` then Total else M.At) then N += 1 end
	end
	return N
end

-- a new taste: hand out any milestone just reached (the title, the health) and say so
function Local.TasteMilestone(P: Player, Inv)
	local Have, Total = Local.TasteCount(Inv)
	for _, M in Items.TasteMilestones do
		local At = if M.At == `All` then Total else M.At
		if Have == At then
			pcall(function() require(ServerScriptService.Services.Social.Reputation).AwardTitle(P, M.Title) end)
			Notifications.Notify(P, { Title = `Taste book: {Have} / {Total}`; Text = `"{M.Title}" earned, and +1 max health for good.`; Kind = `Good`; Duration = 6 })
			Local.Reapply(P)
		end
	end
end

-- the taste book's lasting bonus (Progression adds it in as its own source)
function Shared.TasteEffects(P: Player): { [string]: number }
	local Inv = Shared.Get(P)
	local N = Inv and Local.TasteReached(Inv) or 0
	return if N > 0 then { MaxHealth = N } else {}
end

-- (inventory QOL batch 5) feeding a student: they take a snack from your hands. A food their clique loves is worth +2
-- standing with that clique, once a day per clique. A student who can't stand you won't take it.
function Shared.Feed(P: Player, Model: any, Id: any): (boolean, string?)
	local It = typeof(Id) == `string` and Items.ById[Id]
	if not (It and (It.Kind == `Heal` or It.Kind == `Buff`)) then return false, `They can't eat that.` end
	local Inv = Shared.Get(P)
	if not Inv or (Inv.Items[Id] or 0) <= 0 then return false, `None left. Restock at the stand.` end
	if not (typeof(Model) == `Instance` and Model:IsA(`Model`) and Model:GetAttribute(`NHBrain`)) then return false, nil end
	local Root = P.Character and P.Character:FindFirstChild(`HumanoidRootPart`)
	local Them = Model:FindFirstChild(`HumanoidRootPart`)
	local Hum = Model:FindFirstChildOfClass(`Humanoid`)
	if not (Root and Them and Hum and Hum.Health > 0) or (Root.Position - Them.Position).Magnitude > 12 then return false, `Get closer.` end
	local Ok, Verdict, Clique = pcall(function() return require(ServerScriptService.Services.AI.StudentBrain).Fed(P, Model, It) end)
	if not Ok or Verdict == nil then return false, nil end
	if Verdict == `Refuse` then
		Notifications.Notify(P, { Title = `They won't take it from you.`; Kind = `Info`; Duration = 3 })
		return false, `They won't take it from you.`
	end
	local Inv2 = Shared.Get(P)
	if not Inv2 or (Inv2.Items[Id] or 0) <= 0 then return false, nil end
	Inv2.Items[Id] -= 1
	if Inv2.Items[Id] <= 0 then Inv2.Items[Id] = nil end
	local Msg = `They took the {It.Name}.`
	if Verdict == `Loved` and Clique then
		local Day = Local.EventDay()
		if not (Inv2.Fed and Inv2.Fed.Day == Day) then Inv2.Fed = { Day = Day } end
		if not Inv2.Fed[Clique] then
			Inv2.Fed[Clique] = true
			pcall(function() require(ServerScriptService.Services.Social.Cliques).Add(P, Clique, 2, `Shared a snack`) end)
			local Def = require(ReplicatedStorage.Config.Cliques).Defs[Clique]
			Msg = `They loved the {It.Name}. +2 with {Def and Def.Name or Clique}.`
		else
			Msg = `They loved the {It.Name}. (Their clique's thanks already counted today.)`
		end
	end
	Local.Save(P, Inv2)
	Local.Anim(Hum) -- they eat it
	Notifications.Notify(P, { Title = Msg; Kind = if Verdict == `Loved` then `Good` else `Info`; Duration = 4 })
	return true, Msg
end

-- (inventory QOL 1.94) Best food: the cheapest food you carry that covers the health you're missing (food heals half
-- while you're combat-tagged); if nothing covers it, the biggest heal you have. Uses it through Shared.Use.
function Shared.UseBest(P: Player): (boolean, string?)
	local Inv = Shared.Get(P)
	local Hum = P.Character and P.Character:FindFirstChildOfClass(`Humanoid`)
	if not (Inv and Hum) or Hum.Health <= 0 then return false, nil end
	local Missing = Hum.MaxHealth - Hum.Health
	if Missing < 1 then return false, `You're not hurt.` end
	local Tagged = (P:GetAttribute(`CombatTagUntil`) or 0) > workspace:GetServerTimeNow()
	local Best, Covers, Cost, Heal = nil, false, math.huge, 0
	for Id, N in Inv.Items do
		local It = Items.ById[Id]
		if It and It.Kind == `Heal` and N > 0 then
			local H = (It.Heal or 0) * (if Tagged then 0.5 else 1)
			local Price = It.Price or 0
			if H >= Missing then
				if not Covers or Price < Cost or (Price == Cost and H < Heal) then Best, Covers, Cost, Heal = It, true, Price, H end
			elseif not Covers and H > Heal then
				Best, Cost, Heal = It, Price, H
			end
		end
	end
	if not Best then return false, `No food on you. The stand by the west doors sells it.` end
	local Ok, Msg = Shared.Use(P, Best.Id)
	if Ok then return true, `{Best.Name}: +{math.floor(Heal)} health` end
	return false, Msg
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

function Shared.OnStart()
	local F = Instance.new(`Folder`)
	F.Name = `NHInventory`
	local function rf(N) local R = Instance.new(`RemoteFunction`) R.Name = N R.Parent = F return R end
	local Get, Use, Pin, Drop, Buy = rf(`Get`), rf(`Use`), rf(`Pin`), rf(`Drop`), rf(`Buy`)
	local Restock = rf(`Restock`) -- (inventory QOL 1.92)
	local Undo, Fav = rf(`Undo`), rf(`Fav`) -- (inventory QOL 1.93)
	local UseBest = rf(`UseBest`) -- (inventory QOL 1.94)
	local Feed = rf(`Feed`) -- (inventory QOL batch 5)
	local Changed = Instance.new(`RemoteEvent`) Changed.Name = `Changed` Changed.Parent = F
	Remotes = { Changed = Changed }
	local function limited(P: Player): boolean
		local Now = os.clock()
		if LastCall[P] and Now - LastCall[P] < 0.15 then return true end
		LastCall[P] = Now
		return false
	end
	Get.OnServerInvoke = function(P) return Shared.State(P) end
	-- (inventory audit 1.90) a click inside the rate limit says so instead of doing nothing
	Use.OnServerInvoke = function(P, Id) if limited(P) then return false, `One moment...` end return Shared.Use(P, Id) end
	Pin.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Pin(P, Id, On == true) end
	Drop.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Drop(P, Id, N) end
	Buy.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Buy(P, Id, N) end
	Restock.OnServerInvoke = function(P, To) if limited(P) then return false, `One moment...` end return Shared.Restock(P, To) end
	Undo.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.Undo(P) end
	Fav.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Fav(P, Id, On == true) end
	UseBest.OnServerInvoke = function(P) if limited(P) then return false, `One moment...` end return Shared.UseBest(P) end
	Feed.OnServerInvoke = function(P, Model, Id) if limited(P) then return false, `One moment...` end return Shared.Feed(P, Model, Id) end
	F:SetAttribute(`Ready`, true)
	F.Parent = ReplicatedStorage

	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function()
			task.defer(function()
				P:WaitForChild(`Backpack`, 10)
				task.wait(0.5)
				Local.SyncTools(P)
			end)
		end)
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) task.defer(Local.SyncTools, P) end
	Data.ProfileLoaded:Connect(function(P) task.defer(function() Local.SyncTools(P) Local.Push(P) end) end)
	Players.PlayerRemoving:Connect(function(P) Buffs[P] = nil Cooldowns[P] = nil Busy[P] = nil LastCall[P] = nil LastDrop[P] = nil end)
end

return Shared
