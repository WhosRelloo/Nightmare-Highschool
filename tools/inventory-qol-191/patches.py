# Inventory QOL batch 1 (1.91.0): empty pins shown, cooldown shade, buff chip, no silent refusals.
INV = "ServerScriptService.Services.Features.Inventory"
HUD = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitHud"
KUI = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.KitUi"
LOCK = "StarterPlayer.StarterPlayerScripts.Controllers.Gui.Locker"

EDITS = [
# ---- Inventory (server) ----
(INV, """	local H = Local.Prop(It)
	H.Parent = T
	if H:GetAttribute(`NHGrip`) then T.Grip = H:GetAttribute(`NHGrip`) -- (batch 54) the modelled prop's own grip
	elseif It.Prop.Shape == `Can` or It.Prop.Shape == `Bottle` then T.GripRight = Vector3.new(0, 0, 1) T.GripUp = Vector3.new(1, 0, 0) end
	T.Activated:Connect(function()""", """	Local.AddHandle(T, It)
	T.Activated:Connect(function()"""),
(INV, """function Local.MakeTool(P: Player, It): Tool""", """function Local.AddHandle(T: Tool, It)
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

function Local.MakeTool(P: Player, It): Tool"""),
(INV, """	local Want = {}
	for _, Id in Inv.Pinned do if (Inv.Items[Id] or 0) > 0 then Want[Id] = true end end""",
      """	local Want = {}
	-- (inventory QOL 1.91) every pin gets a tool, empty ones too (shown greyed until you restock)
	for _, Id in Inv.Pinned do if Items.ById[Id] and Items.ById[Id].Kind ~= `Trophy` then Want[Id] = true end end"""),
(INV, """				if Want[Id] and not Have[Id] then
					Have[Id] = T
					T:SetAttribute(`Count`, Inv.Items[Id])
				else""", """				if Want[Id] and not Have[Id] then
					Have[Id] = T
					T:SetAttribute(`Count`, Inv.Items[Id] or 0)
					Local.SetEmpty(P, T, (Inv.Items[Id] or 0) <= 0)
				else"""),
(INV, """			local T = Local.MakeTool(P, Items.ById[Id])
			T:SetAttribute(`Count`, Inv.Items[Id])
			T.Parent = Pack
		end
	end
end""", """			local T = Local.MakeTool(P, Items.ById[Id])
			T:SetAttribute(`Count`, Inv.Items[Id] or 0)
			Local.SetEmpty(P, T, (Inv.Items[Id] or 0) <= 0)
			T.Parent = Pack
		end
	end
	Local.MarkReady(P)
end"""),
(INV, """	Cooldowns[P].Heal = Now + Items.Cooldown.Heal + Items.UseTime
	if not NoAnim then Local.Anim(Hum) end""", """	Cooldowns[P].Heal = Now + Items.Cooldown.Heal + Items.UseTime
	Local.MarkReady(P) -- (inventory QOL 1.91)
	if not NoAnim then Local.Anim(Hum) end"""),
(INV, """	if not Inv or (Inv.Items[Id] or 0) <= 0 then return false, `You don't have any.` end
	local Char = P.Character""", """	if not Inv or (Inv.Items[Id] or 0) <= 0 then return false, `None left. Restock at the stand.` end -- (inventory QOL 1.91)
	local Char = P.Character"""),
(INV, """	if Busy[P] then return false, nil end
	if It.Kind == `Trophy` then""", """	if Busy[P] then return false, `Still eating.` end -- (inventory QOL 1.91) no silent refusals
	if It.Kind == `Trophy` then"""),
(INV, """	Cooldowns[P][It.Kind] = Now + Items.Cooldown[It.Kind] + Items.UseTime
""", """	Cooldowns[P][It.Kind] = Now + Items.Cooldown[It.Kind] + Items.UseTime
	Local.MarkReady(P) -- (inventory QOL 1.91)
"""),
# ---- KitHud (client): the hotbar shade ----
(HUD, """			if not CountWatch[Item] then CountWatch[Item] = Item:GetAttributeChangedSignal(`Count`):Connect(function() Local.Schedule() end) end""",
      """			-- (inventory QOL 1.91) an empty pin or a new cooldown also restyles the slot
			if not CountWatch[Item] then CountWatch[Item] = Item.AttributeChanged:Connect(function(A)
				if A == `Count` or A == `NHEmpty` or A == `NHReadyAt` then Local.Schedule() end
			end) end"""),
(HUD, """		Ui.Hotbar:SetItem(Index, if Tool then Local.ToolItem(Tool) else nil)""",
      """		Ui.Hotbar:SetItem(Index, if Tool then Local.ToolItem(Tool) else nil)
		Local.SlotState(Index, Tool)"""),
(HUD, """function Local.Schedule()
	if Pending then return end""", """-- (inventory QOL 1.91) a snack slot greys out when the pin is empty ("Restock") and drains a dark shade with the seconds
-- left while it's cooling down (the shared "full" wait for food, the one-sip wait for drinks)
local Shades = {} :: { [number]: Tool }
function Local.SlotState(Index: number, Tool: Tool?)
	local Slot = Ui.HotbarRoot and Ui.HotbarRoot:FindFirstChild(`Slot{Index}`, true)
	if not Slot then return end
	local Shade = Slot:FindFirstChild(`NHShade`)
	if not (Tool and Tool:GetAttribute(`NHItem`)) then
		if Shade then Shade.Visible = false end
		Shades[Index] = nil
		return
	end
	if not Shade then
		Shade = Instance.new(`Frame`)
		Shade.Name = `NHShade`
		Shade.BackgroundColor3 = Color3.new(0, 0, 0)
		Shade.BorderSizePixel = 0
		Shade.AnchorPoint = Vector2.new(0.5, 1)
		Shade.Position = UDim2.new(0.5, 0, 1, -4)
		Shade.ZIndex = 6
		Shade.Visible = false
		Shade.Parent = Slot
		local L = Instance.new(`TextLabel`)
		L.Name = `Text`
		L.BackgroundTransparency = 1
		L.AnchorPoint = Vector2.new(0.5, 1)
		L.Position = UDim2.fromScale(0.5, 1)
		L.Size = UDim2.new(1, 0, 0, 24)
		L.Font = Enum.Font.GothamBold
		L.TextSize = 15
		L.TextColor3 = Colors.Text or Color3.fromRGB(232, 222, 196)
		L.TextStrokeTransparency = 0.4
		L.ZIndex = 7
		L.Parent = Shade
	end
	Shades[Index] = Tool
	Local.StepShade(Index)
end

function Local.StepShade(Index: number)
	local Tool = Shades[Index]
	local Slot = Tool and Ui and Ui.HotbarRoot and Ui.HotbarRoot:FindFirstChild(`Slot{Index}`, true)
	local Shade = Slot and Slot:FindFirstChild(`NHShade`)
	if not Shade then return end
	local Label = Shade:FindFirstChild(`Text`) :: TextLabel
	if Tool:GetAttribute(`NHEmpty`) then
		Shade.Visible = true
		Shade.BackgroundTransparency = 0.45
		Shade.Size = UDim2.new(1, -8, 1, -8)
		Label.Text = `Restock`
		return
	end
	local Left = (Tool:GetAttribute(`NHReadyAt`) or 0) - workspace:GetServerTimeNow()
	if Left <= 0 then Shade.Visible = false return end
	local Full = math.max(Tool:GetAttribute(`NHCooldown`) or Left, 0.1)
	Shade.Visible = true
	Shade.BackgroundTransparency = 0.35
	Shade.Size = UDim2.new(1, -8, math.clamp(Left / Full, 0, 1), -8 * math.clamp(Left / Full, 0, 1))
	Label.Text = tostring(math.ceil(Left))
end

function Local.Schedule()
	if Pending then return end"""),
(HUD, """	Player.CharacterAdded:Connect(function(Character) task.spawn(Local.BindCharacter, Character) end)
	if Player.Character then task.spawn(Local.BindCharacter, Player.Character) end
""", """	Player.CharacterAdded:Connect(function(Character) task.spawn(Local.BindCharacter, Character) end)
	if Player.Character then task.spawn(Local.BindCharacter, Player.Character) end
	-- (inventory QOL 1.91) drain the cooldown shades
	game:GetService(`RunService`).Heartbeat:Connect(function()
		for Index in Shades do Local.StepShade(Index) end
	end)
"""),
# ---- KitUi (client): the snack buff chip ----
(KUI, """local Classes = require(ReplicatedStorage.Config:WaitForChild(`Classes`))""",
      """local Classes = require(ReplicatedStorage.Config:WaitForChild(`Classes`))
local ItemsCfg = require(ReplicatedStorage.Config:WaitForChild(`Items`)) -- (inventory QOL 1.91) the snack buff chip"""),
(KUI, """	Ch.Root.Size = UDim2.fromOffset(math.clamp(80 + #Text * 8.5, 150, 320), 44)""",
      """	Ch.Root.Size = UDim2.fromOffset(math.clamp(80 + #Text * 8.5, 150, 480), 44) -- (inventory QOL 1.91) room for the buff chip"""),
(KUI, """	if Player:GetAttribute(`NHKitKeys`) then chip(`Carrying someone's keys`, C.Gold, `IconKeys`) end
	for J = I + 1, 8 do Local.Chip(J, nil) end""", """	if Player:GetAttribute(`NHKitKeys`) then chip(`Carrying someone's keys`, C.Gold, `IconKeys`) end
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
		chip(`{BIt.Name}  \\u{00B7}  {Eff}  \\u{00B7}  {math.floor(BLeft / 60)}:{string.format(`%02d`, math.floor(BLeft % 60))}`,
			if Pulse then C.Danger else Color3.fromRGB(150, 205, 140), `IconCup`)
	end
	for J = I + 1, 8 do Local.Chip(J, nil) end"""),
# ---- Locker (client): the pouch shows an empty pin greyed ----
(LOCK, """		local N = Id and State.Items[Id] or 0
		local It = N > 0 and Items.ById[Id] or nil -- a pinned snack you've run out of shows as an empty pouch slot
		P.Api:SetItem(if It then { name = It.Name; rarity = It.Rarity; count = N } else nil)
		if It then Local.View(P.Root, `Snack`, Id) else local V = P.Root:FindFirstChild(`NHView`) if V then V:Destroy() end end""",
       """		local N = Id and State.Items[Id] or 0
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
				Local.Label(Shade, `Restock\\n<font size="11">click to unpin</font>`, 14, { TextXAlignment = Enum.TextXAlignment.Center;
					TextYAlignment = Enum.TextYAlignment.Bottom; Position = UDim2.fromOffset(0, -4); Size = UDim2.fromScale(1, 1); ZIndex = 7 })
			end
			Shade.Visible = true
		elseif Shade then
			Shade.Visible = false
		end"""),
]
