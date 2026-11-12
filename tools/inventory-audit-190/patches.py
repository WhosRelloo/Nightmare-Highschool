# Inventory audit fixes (2026-11-12). Each edit must match exactly once in the live source.
INV = "ServerScriptService.Services.Features.Inventory"
ITEMS = "ReplicatedStorage.Config.Items"
KIT = "ServerScriptService.Services.Features.Kit"
HM = "ServerScriptService.Services.School.HallMonitor"
PAD = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.GamepadControls"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

EDITS = [
# ---- Inventory (server) ----
(INV, """-- give items (quests, admin, rewards). Returns how many fit.
function Shared.Grant(""", """-- (inventory audit 1.90) a pin on a snack you've run out of keeps its pouch slot for the restock, but gives way when
-- the pouch is full and you pin (or are given) something else. Returns true if one was freed.
function Local.FreeEmptyPin(Inv): boolean
	for I, Pid in Inv.Pinned do
		if (Inv.Items[Pid] or 0) <= 0 then table.remove(Inv.Pinned, I) return true end
	end
	return false
end

-- give items (quests, admin, rewards). Returns how many fit.
function Shared.Grant("""),
(INV, """	if It.Kind ~= `Trophy` and not table.find(Inv.Pinned, Id) and #Inv.Pinned < Items.MaxPinned then table.insert(Inv.Pinned, Id) end""",
      """	if It.Kind ~= `Trophy` and not table.find(Inv.Pinned, Id) and (#Inv.Pinned < Items.MaxPinned or Local.FreeEmptyPin(Inv)) then table.insert(Inv.Pinned, Id) end"""),
(INV, """	if On and Items.ById[Id].Kind == `Trophy` then return false, `Trophies stay in your Locker.` end""",
      """	if On and Items.ById[Id].Kind == `Trophy` then return false, `Trophies stay in your Locker.` end
	if On and (Inv.Items[Id] or 0) <= 0 then return false, `You don't have any.` end -- (inventory audit 1.90)"""),
(INV, """		if #Inv.Pinned >= Items.MaxPinned then return false,""",
      """		if #Inv.Pinned >= Items.MaxPinned and not Local.FreeEmptyPin(Inv) then return false,"""),
(INV, """	Use.OnServerInvoke = function(P, Id) if limited(P) then return false end return Shared.Use(P, Id) end
	Pin.OnServerInvoke = function(P, Id, On) if limited(P) then return false end return Shared.Pin(P, Id, On == true) end
	Drop.OnServerInvoke = function(P, Id, N) if limited(P) then return false end return Shared.Drop(P, Id, N) end""",
      """	-- (inventory audit 1.90) a click inside the rate limit says so instead of doing nothing
	Use.OnServerInvoke = function(P, Id) if limited(P) then return false, `One moment...` end return Shared.Use(P, Id) end
	Pin.OnServerInvoke = function(P, Id, On) if limited(P) then return false, `One moment...` end return Shared.Pin(P, Id, On == true) end
	Drop.OnServerInvoke = function(P, Id, N) if limited(P) then return false, `One moment...` end return Shared.Drop(P, Id, N) end"""),
(INV, """function Shared.SetKit(P: Player, Kit, Quiet: boolean?): boolean
	local Inv = Shared.Get(P)""",
      """function Shared.SetKit(P: Player, Kit, Quiet: boolean?): boolean
	-- (inventory audit 1.90) the once-a-second fuel burn only updates the kit in the profile (ProfileService autosaves
	-- it); it no longer re-sanitizes the whole inventory and sends it to the client every second
	if Quiet then
		local Profile = Data.GetProfile(P)
		if Profile and typeof(Profile.Inventory) == `table` then
			Profile.Inventory.Kit = require(ReplicatedStorage.Config.Kit).Sanitize(Kit)
			return true
		end
	end
	local Inv = Shared.Get(P)"""),
(INV, """function Shared.KitEat(P: Player, Heal: number, Duration: number, Consume: () -> boolean): (boolean, string?)""",
      """function Shared.KitEat(P: Player, Heal: number, Duration: number, Consume: () -> boolean, NoAnim: boolean?): (boolean, string?)"""),
(INV, """	Cooldowns[P].Heal = Now + Items.Cooldown.Heal + Items.UseTime
	Local.Anim(Hum)
	task.delay(Items.UseTime, function()
		Busy[P] = nil
		if not (P.Parent and Hum.Parent and Hum.Health > 0) then return end
		if not Consume() then return end""",
      """	Cooldowns[P].Heal = Now + Items.Cooldown.Heal + Items.UseTime
	if not NoAnim then Local.Anim(Hum) end -- (inventory audit 1.90) the tin plays its own clip
	task.delay(Items.UseTime, function()
		Busy[P] = nil
		if not (P.Parent and Hum.Parent and Hum.Health > 0) then return end
		if not Consume() then return end"""),
# ---- Config.Items: never keep a trophy pin from an old save ----
(ITEMS, """			if Items.ById[Id] and not table.find(Out.Pinned, Id) and #Out.Pinned < Items.MaxPinned then table.insert(Out.Pinned, Id) end""",
        """			if Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` and not table.find(Out.Pinned, Id) and #Out.Pinned < Items.MaxPinned then table.insert(Out.Pinned, Id) end"""),
# ---- Kit (server) ----
(KIT, """		local Ok, Msg = Shared.Use(P, Id)
		if not Ok and Msg then notify(P, Msg) end
	end)
	T.Equipped:Connect(function() Local.OnEquip(P, T, Id, true) end)""",
      """		local Ok, Msg = Shared.Use(P, Id)
		if Msg then notify(P, Msg) end -- (inventory audit 1.90) the book's "due back" line is a success message
	end)
	T.Equipped:Connect(function() Local.OnEquip(P, T, Id, true) end)"""),
(KIT, """		if Model:IsA(`Model`) and Model:GetAttribute(`MonitorTarget`) == P.UserId then
			local At = Model:GetAttribute(`MonitorChaseAt`)""",
      """		if Model:IsA(`Model`) and Model:GetAttribute(`MonitorTarget`) == P.UserId then
			-- (inventory audit 1.90) a pass covers being out of class, not a fight or paint (School.HallMonitor)
			if (Model:GetAttribute(`MonitorReason`) or `Truancy`) ~= `Truancy` then return false, `A pass won't get you out of this.` end
			local At = Model:GetAttribute(`MonitorChaseAt`)"""),
(KIT, """		else
			pcall(function() Inventory().GiveBuff(P, Kit.Thermos.CoffeeBuff) end)
		end""",
      """		else
			-- (inventory audit 1.90) the coffee never replaces a snack buff you paid for
			local Cur, Until = P:GetAttribute(`NHSnackBuff`), P:GetAttribute(`NHSnackBuffUntil`) or 0
			if Cur == nil or Cur == Kit.Thermos.CoffeeBuff or Until <= now() then
				pcall(function() Inventory().GiveBuff(P, Kit.Thermos.CoffeeBuff) end)
			end
		end"""),
(KIT, """	local Owner = Players:GetPlayerByUserId(C.Owner)
	local K = Owner and Shared.Get(Owner)""",
      """	local Owner = Players:GetPlayerByUserId(C.Owner)
	if not Owner then Local.Push(F) return true, `Their owner has gone home. The Office will keep them.` end -- (inventory audit 1.90)
	local K = Shared.Get(Owner)"""),
(KIT, """	elseif Action == `Use` then return Shared.Use(P, A)""",
      """	elseif Action == `Use` then -- (inventory audit 1.90) only pocket items are used from the Locker; the rest from the hand
		local It = typeof(A) == `string` and Kit.ById[A]
		if not (It and It.Pocket) then return false, nil end
		return Shared.Use(P, A)"""),
(KIT, """		LastCall[P], Busy[P], Cool[P], Lit[P], Chill[P], Dirty[P], Carrying[P] = nil, nil, nil, nil, nil, nil, nil""",
      """		LastCall[P], Busy[P], Cool[P], Lit[P], Chill[P], Dirty[P], Carrying[P] = nil, nil, nil, nil, nil, nil, nil
		-- (inventory audit 1.90) the leaver's keys on the ground go with them
		local D = Dropped[P.UserId]
		if D then if D.Model.Parent then D.Model:Destroy() end Dropped[P.UserId] = nil end"""),
(KIT, """RayParams.IgnoreWater = true""", """RayParams.IgnoreWater = true
RayParams.RespectCanCollide = true -- (inventory audit 1.90) an invisible trigger overhead isn't a roof"""),
# ---- HallMonitor: say why it's chasing ----
(HM, """	M.Model:SetAttribute(`MonitorChaseAt`, os.clock()) -- (kit 1.79) the pass works only in the first seconds""",
     """	M.Model:SetAttribute(`MonitorChaseAt`, os.clock()) -- (kit 1.79) the pass works only in the first seconds
	M.Model:SetAttribute(`MonitorReason`, Reason) -- (inventory audit 1.90) the hall pass only covers Truancy"""),
# ---- Gamepad: B closes the stand ----
(PAD, """	NHConcessionMenu = { `Gui`, `Locker` };""", """	NHConcessionMenu = { `Gui`, `Locker`; Fn = `CloseStand` }; -- (inventory audit 1.90) B closes the stand, not the Locker"""),
# ---- Locker (client) ----
(LOCK, """local ConfirmDrop = nil
""", """local ConfirmDrop = nil
local LastIndex = nil -- (inventory audit 1.90) where the selection was, so it stays put when a stack runs out
local OpenToken = 0 -- (inventory audit 1.90) a close during the opening round trip wins
local GuiService = game:GetService(`GuiService`)
"""),
(LOCK, """function Local.Screen(Name: string, Order: number): ScreenGui""", """function Local.Screen(Name: string, Order: number, ScaleOpts: {}?): ScreenGui"""),
(LOCK, """	Kit.AutoScale(G)
	return G""", """	Kit.AutoScale(G, ScaleOpts)
	return G"""),
(LOCK, """	local G = Local.Screen(`NHLocker`, 12)""", """	-- (inventory audit 1.90) the whole 1200 x 680 row fits on a phone (its panels are placed by offset, so the panel
	-- clamp can't shrink them one by one)
	local G = Local.Screen(`NHLocker`, 12, { fitWidth = 1200; fitHeight = 680 })
	G:SetAttribute(`NHNoPanelClamp`, true)"""),
(LOCK, """		onSelect = function(Item) if Item then Selected = { kind = Item.kind; id = Item.id } ConfirmDrop = nil Local.ShowCard() end end })""",
       """		onSelect = function(Item, I) if Item then LastIndex = I Selected = { kind = Item.kind; id = Item.id } ConfirmDrop = nil Local.ShowCard() end end })"""),
(LOCK, """else (if It.Kind == `Heal` then `Food` elseif It.Kind == `Trophy` then `Trophy` else `Drink`)}`), 12,""",
       """else (if It.Kind == `Heal` then `Food` elseif It.Kind == `Trophy` then `Trophy` elseif It.Kind == `Prank` then `Prank kit` else `Buff`)}`), 12,"""),
(LOCK, """	local List = Local.Entries()
	Ui.Grid:SetItems(List)""", """	local List = Local.Entries()
	local Sel = GuiService.SelectedObject -- (inventory audit 1.90) a gamepad cursor in the grid stays in the grid
	local InGrid = Sel ~= nil and Sel:IsDescendantOf(Ui.GridRoot)
	Ui.Grid:SetItems(List)"""),
(LOCK, """	if Keep then Ui.Grid:Select(Keep) elseif List[1] then Ui.Grid:Select(1) else Selected = nil Local.ShowCard() end""",
       """	if Keep then Ui.Grid:Select(Keep) elseif List[1] then Ui.Grid:Select(math.clamp(LastIndex or 1, 1, #List)) else Selected = nil Local.ShowCard() end
	if InGrid then
		local S = Ui.GridRoot:FindFirstChild(`Slot{Keep or math.clamp(LastIndex or 1, 1, math.max(#List, 1))}`, true)
		if S and S:IsA(`GuiObject`) then GuiService.SelectedObject = S end
	end"""),
(LOCK, """				local Pid = State and State.Pinned and State.Pinned[I]
				if Pid then Selected = { kind = `Snack`; id = Pid } Tab = 1 Ui.Tabs:Select(1, true) Local.Refresh() end""",
       """				local Pid = State and State.Pinned and State.Pinned[I]
				if not Pid then return end
				-- (inventory audit 1.90) an empty pin (you ran out) is cleared by clicking it
				if (State.Items[Pid] or 0) <= 0 then Local.Call(`Pin`, Pid, false) return end
				Selected = { kind = `Snack`; id = Pid } Tab = 1 Ui.Tabs:Select(1, true) Local.Refresh()"""),
(LOCK, """-- the selected item's actions, under the grid
function Local.ShowCard()
	if not Ui then return end
	local A = Ui.Actions
	Local.Clear(A)
	if not (Selected and State) then
		Local.Label(A, `<i>Your backpack is empty. The concession stand by the west doors sells snacks; gear comes from chests and the School Store.</i>`, 15,
			{ TextColor3 = C.TextDim; Position = UDim2.fromOffset(4, 6); Size = UDim2.new(1, -8, 1, -12) })
		return
	end""", """-- (inventory audit 1.90) a line under the selected item (a refusal from the server)
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
	end"""),
(LOCK, """		Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
			onClick = function()
				if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
				ConfirmDrop = nil
				Local.Call(`Drop`, Id, 1)
			end })
		return
	end""", """		local DropB = Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
			onClick = function()
				if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
				ConfirmDrop = nil
				Local.ShowCard()
				local Ok, Msg = Local.Call(`Drop`, Id, 1)
				if not Ok then Local.Say(Msg or `Couldn't drop it. Try again.`) end
			end })
		if typeof(DropB) == `Instance` then DropB.Name = `Drop` end
		return
	end"""),
(LOCK, """	Kit.Button({ text = `Use`; style = `gold`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -232, 0.5, 0); Parent = A;
		onClick = function()
			local Ok, Msg = Local.Call(`Use`, Id)
			if not Ok and Msg then Info.Text = Msg end
		end })
	Kit.Button({ text = if Pinned then `Unpin` else `To pouch`; Size = UDim2.fromOffset(112, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -112, 0.5, 0); Parent = A;
		onClick = function()
			local Ok, Msg = Local.Call(`Pin`, Id, not Pinned)
			if not Ok and Msg then Info.Text = Msg end
		end })
	Kit.Button({ text = if ConfirmDrop == Id then `Sure?` else `Drop`; style = `crimson`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, 0, 0.5, 0); Parent = A;
		onClick = function()
			if ConfirmDrop ~= Id then ConfirmDrop = Id Local.ShowCard() return end
			ConfirmDrop = nil
			Local.Call(`Drop`, Id, 1)
		end })
end""", """	local UseB = Kit.Button({ text = `Use`; style = `gold`; Size = UDim2.fromOffset(104, 40); AnchorPoint = Vector2.new(1, 0.5); Position = UDim2.new(1, -232, 0.5, 0); Parent = A;
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
end"""),
(LOCK, """function Shared.Toggle(On: boolean?)
	if not Ui then Local.Build() end
	if On == nil then On = not Ui.Gui.Enabled end
	if On and Player:GetAttribute(`InMainMenu`) == true then return end
	if On then
		local S = Local.Call(`Get`)
		if S then State = S end
		pcall(KitUi.Refresh) -- (kit 1.79)
		Local.Refresh()
		pcall(Kit.PlaySound, `Tick`)
	else
		Ui.Tip.Visible = false
		pcall(function() Ui.Preview:Unwatch() end)
	end
	Ui.Gui.Enabled = On
end""", """-- (inventory audit 1.90) opens at once and fills in after the round trip; a close in between wins. Not while
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
end"""),
(LOCK, """		if Player:GetAttribute(`InMainMenu`) == true then
			if Ui then Ui.Gui.Enabled = false end
			Shared.CloseStand()
		end""", """		-- (inventory audit 1.90) dying or the main menu closes the Locker properly (its preview too)
		if Ui and Ui.Gui.Enabled then
			local Hum = Player.Character and Player.Character:FindFirstChildOfClass(`Humanoid`)
			if not Hum or Hum.Health <= 0 or Player:GetAttribute(`InMainMenu`) == true then Shared.Toggle(false) end
		end
		if Player:GetAttribute(`InMainMenu`) == true then Shared.CloseStand() end"""),
]

# Kit: the snack tin passes NoAnim when it has its own clip
EDITS.append((KIT, """		if K2 and K2.Biscuits > 0 then K2.Biscuits -= 1 Local.Save(P, K2) return true end
		return false
	end)
	return Ok, Msg""", """		if K2 and K2.Biscuits > 0 then K2.Biscuits -= 1 Local.Save(P, K2) return true end
		return false
	end, (Kit.Anims and Kit.Anims.SnackTin or 0) ~= 0) -- (inventory audit 1.90) the tin's own clip, not the eating one too
	return Ok, Msg"""))
