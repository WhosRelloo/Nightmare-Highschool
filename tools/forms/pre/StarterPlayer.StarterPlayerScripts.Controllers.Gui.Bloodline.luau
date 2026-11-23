--[[
	Bloodline tab (client): your race, sub-race and tier, the race and variant spins, the race passive and
	your traits. Race is rolled by the server (ReplicatedStorage.Lineage); this only shows it and asks to spin.
	Built into the Identity panel (Controllers.Gui.Identity) by Bloodline.Build(Ctx).
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local Lineage = require(ReplicatedStorage:WaitForChild(`Lineage`))
local Kit = require(ReplicatedStorage:WaitForChild(`UI`):WaitForChild(`Components`))
local Progression = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Progression`))
local C = Kit.Theme.Colors
local Fonts = Kit.Theme.Fonts
local ROMAN = { `I`, `II`, `III` }

local Shared = {}
local Data = nil   -- last known lineage
local SpinBusy = false
local FreshAt = 0  -- when Data last came straight from the server (the profile copy can lag behind it)
local FRESH_HOLD = 3

local function hex(c: Color3) return c:ToHex() end
local function entry(subId)
	local f = subId and Lineage.SubById[subId]
	if not f then return { text = `Unrolled`; sub = `Spin to find out`; color = C.TextDim } end
	local r = Lineage.Rarity[f.Sub.Rarity]
	return { text = f.Sub.Name; sub = `{f.Race.Name}  ·  {f.Sub.Rarity}`; color = r and r.Color or C.Text }
end

function Shared.Busy(): boolean return SpinBusy end

-- choose a race look (the server checks race and tier)
function Shared.SetLook(Ctx, Slot: string, Id: string)
	if SpinBusy then return end
	SpinBusy = true
	task.spawn(function()
		local Ok, Res = Lineage.SetLookClient(Slot, Id)
		SpinBusy = false
		if Ok then
			Data = Lineage.Sanitize(Res)
			FreshAt = os.clock()
			Ctx.Status(`Look updated`, C.Gold)
			Ctx.Render()
		else
			Ctx.Status(tostring(Res), C.Crimson)
		end
	end)
end

function Shared.Spin(Ctx, Kind: string, Slot: number?, Reel)
	if SpinBusy then return end
	SpinBusy = true
	Ctx.Status(`Spinning...`)
	task.spawn(function()
		local Ok, Result = Lineage.Spin(Kind, Slot)
		if not Ok then SpinBusy = false Ctx.Status(tostring(Result), C.Crimson) return end
		local function Done()
			Data = Lineage.Sanitize(Result)
			FreshAt = os.clock()
			SpinBusy = false
			local Race, Sub, Traits = Lineage.Describe(Data)
			Ctx.Status(if Kind == `Trait` then `New trait: {Traits[Slot] and Traits[Slot].Name or "?"}` else `You are {Sub and Sub.Name or "?"} ({Race and Race.Name or "?"})`, C.Gold)
			Ctx.Render()
		end
		if Reel and Kind ~= `Trait` then
			local Pool = {}
			for _, R in Lineage.Races do
				if Kind == `Race` or R.Id == (Data and Data.Race) then
					for _, S in R.Subs do table.insert(Pool, entry(S.Id)) end
				end
			end
			-- rarity on the landing entry: the kit plays the tiered reveal (and the near-miss for Legendary)
			local Final = entry(Result.SubRace)
			local Found = Result.SubRace and Lineage.SubById[Result.SubRace]
			Final.rarity = Found and Found.Sub.Rarity
			-- (audit) a Render can destroy the reel mid-spin and its tween may never complete (SpinBusy stuck): finish once
			-- either way
			local Fired = false
			local function Once() if Fired then return end Fired = true Done() end
			Reel:Spin(Pool, Final, 2.6, Once)
			task.delay(2.6 + 3, Once)
		else
			Done()
		end
	end)
end

function Shared.Build(Ctx)
	local Held = Data and (SpinBusy or os.clock() - FreshAt < FRESH_HOLD)
	Data = if Held then Data else Lineage.Get()
	local L = Data
	local Race, Sub, Traits = Lineage.Describe(L)
	local Free = RunService:IsStudio()
	local function count(k) return if Free then `free` else tostring(L.Spins[k] or 0) end

	-- crest: race name in its colour, sub-race, tier title
	Ctx.Section(`Bloodline`)
	local Crest = Ctx.Row(96)
	Kit.Decorate(Crest, { ornament = `slot`; shadow = false })
	local RaceCol = Race and Race.Color or C.Text
	local Name = Kit.Text({ Text = if Race then string.upper(Race.Name) else `UNROLLED`; Font = Fonts.Title; TextSize = 40; TextColor3 = RaceCol;
		TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 10); Size = UDim2.new(1, 0, 0, 44); Parent = Crest })
	pcall(Kit.Emboss, Name, RaceCol:Lerp(Color3.new(0, 0, 0), 0.5), 1.4)
	local Rarity = Sub and Lineage.Rarity[Sub.Rarity]
	Kit.Text({ Text = if Race then `<font color="#{hex(Rarity and Rarity.Color or C.Text)}">{Sub and Sub.Name or Race.Name}</font>   ·   Tier {ROMAN[L.Tier] or L.Tier}, {Lineage.TierName(L.Race, L.Tier)}` else ``;
		RichText = true; TextSize = 20; TextColor3 = C.Text; TextXAlignment = Enum.TextXAlignment.Center; Position = UDim2.fromOffset(0, 58); Size = UDim2.new(1, 0, 0, 26); Parent = Crest })
	if Race then Ctx.Note(Race.Text) end

	-- hunger: fills from kills and feeding; full = that tier's rite opens (Services.Player.Evolution)
	if Race then
		local Tier = L.Tier or 1
		local HName = Lineage.HungerName[L.Race] or `Hunger`
		if Tier >= 3 then
			Ctx.Note(`<font color="#{hex(C.Gold)}">Your bloodline is fully awakened.</font>`, C.Text)
		else
			local Need = Lineage.HungerNeed[Tier + 1] or 1
			local H = math.floor(L.Hunger or 0)
			local BarRow = Ctx.Row(30)
			Kit.Bar({ fraction = math.clamp(H / Need, 0, 1); color = Race.Color or C.Crimson; caption = `{HName}  {math.min(H, Need)} / {Need}`; height = 24;
				Size = UDim2.new(1, 0, 0, 26); Parent = BarRow })
			if H >= Need then
				Ctx.Note(`<font color="#{hex(C.Gold)}">Your rite is open: check your journal (J) to become {Lineage.TierName(L.Race, Tier + 1)}.</font>`, C.Text)
			else
				Ctx.Note(`Fill your {HName} to open the rite for Tier {ROMAN[Tier + 1]}, {Lineage.TierName(L.Race, Tier + 1)}.`)
			end
		end
	end

	-- spins
	local _, Reel = Kit.SpinReel({ entry = entry(L.SubRace); height = 72; textSize = 36; Size = UDim2.new(1, 0, 0, 84); LayoutOrder = Ctx.Next(); Parent = Ctx.Options })
	local Buttons = Ctx.Row(48)
	Kit.Button({ text = `Spin race ({count("Race")})`; style = `crimson`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Race`, nil, Reel) end;
		Position = UDim2.fromScale(0, 0); Size = UDim2.new(0.5, -6, 0, 44); Parent = Buttons })
	Kit.Button({ text = `Spin variant ({count("Variant")})`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Variant`, nil, Reel) end;
		AnchorPoint = Vector2.new(1, 0); Position = UDim2.fromScale(1, 0); Size = UDim2.new(0.5, -6, 0, 44); Parent = Buttons })
	local Odds = {}
	for _, R in Lineage.Odds() do table.insert(Odds, `{R.Name} {string.format("%g", math.floor(R.Chance * 10 + 0.5) / 10)}%`) end
	Ctx.Note(`Race odds: {table.concat(Odds, ", ")}.  A race spin rolls a new race and variant and starts you over at Tier I (hunger and race looks reset); a variant spin keeps your race and tier.` .. (if Free then `  Spins are free while testing in Studio.` else ``))
	local More = Ctx.Row(48)
	Kit.Button({ text = `Get more spins`; style = `gold`; textSize = 20; onClick = function() Ctx.OpenTab(`Shop`) end; Size = UDim2.new(0.5, -6, 0, 44); Parent = More })

	-- passive
	if Race and Race.Passive then
		Ctx.Section(`Passive: {Race.Passive.Name}`)
		Ctx.Note(Race.Passive.Text)
		local Str, Dra = Lineage.Passives(L.Race, L.SubRace, L.Tier)
		Ctx.Note(`<font color="#{hex(C.Gold)}">{Progression.Describe(Str)}</font>`, C.Text)
		Ctx.Note(`<font color="#{hex(C.Crimson)}">{if next(Dra) then Progression.Describe(Dra) else Race.Passive.DrawbackText}</font>`, C.Text)
		for T = (L.Tier or 1) + 1, 3 do
			local S2 = Lineage.Passives(L.Race, L.SubRace, T)
			Ctx.Note(`At Tier {ROMAN[T]} ({Lineage.TierName(L.Race, T)}): {Progression.Describe(S2)}`)
		end
	end

	-- looks: race-only cosmetics, grander ones unlock at Tier II and III
	local Slots = Lineage.LookSlots[L.Race]
	if Slots then
		Ctx.Section(`Looks`)
		local Worn = Lineage.ResolveLooks(L)
		for _, Slot in Slots do
			local Opts = Lineage.Looks[L.Race][Slot]
			Ctx.Note(`<b>{Lineage.SlotNames[Slot] or Slot}</b>`, C.Text)
			local Swatch = Slot == `Fur`
			local PerRow = if Swatch then 6 else 2
			local Rows = math.ceil(#Opts / PerRow)
			local Row = Ctx.Row(Rows * (if Swatch then 54 else 50))
			local Grid = Instance.new(`UIGridLayout`)
			Grid.CellSize = if Swatch then UDim2.fromOffset(48, 48) else UDim2.new(0.5, -6, 0, 44)
			Grid.CellPadding = UDim2.fromOffset(if Swatch then 10 else 12, 6)
			Grid.SortOrder = Enum.SortOrder.LayoutOrder
			Grid.Parent = Row
			for I, O in Opts do
				local Locked = O.Tier > (L.Tier or 1)
				local On = Worn[Slot] and Worn[Slot].Id == O.Id
				if Swatch then
					local B = Instance.new(`TextButton`)
					B.Name = O.Id; B.LayoutOrder = I; B.Text = ``; B.AutoButtonColor = true
					B.BackgroundColor3 = O.Color; B.BorderSizePixel = 0; B.Parent = Row
					local Cr = Instance.new(`UICorner`); Cr.CornerRadius = UDim.new(0, 6); Cr.Parent = B
					local St = Instance.new(`UIStroke`); St.Thickness = if On then 3 else 1; St.Color = if On then C.Gold else C.IronDim; St.Parent = B
					B.Activated:Connect(function() Shared.SetLook(Ctx, Slot, O.Id) end)
				else
					local Label = if Locked then `{O.Name}  ·  Tier {ROMAN[O.Tier]}` else O.Name
					local Root = Kit.Button({ text = (if On then `◆  ` else ``) .. Label; style = if On then `gold` else `default`; textSize = 19;
						enabled = not Locked; LayoutOrder = I; Parent = Row;
						onClick = function() Shared.SetLook(Ctx, Slot, O.Id) end })
				end
			end
		end
		Ctx.Note(`Looks show on your character in school. Higher tiers unlock as your bloodline evolves.`)
	end

	-- traits (moved here from the Wardrobe's Lineage tab)
	Ctx.Section(`Traits`)
	for Slot = 1, Lineage.TraitSlots do
		local T = Traits[Slot]
		local Row = Ctx.Row(72)
		local Col = T and Lineage.Rarity[T.Rarity]
		Kit.Text({ Text = if T then `{T.Name}   <font color="#{hex(Col and Col.Color or C.Text)}">{T.Rarity}</font>` else `Empty slot`; RichText = true; TextSize = 22;
			TextColor3 = C.Text; Size = UDim2.new(1, -176, 0, 28); Parent = Row })
		local Desc = if T then T.Text else `Spin to fill this slot.`
		if T and T.Effects then
			local Ok, Fx = pcall(Progression.Describe, T.Effects)
			if Ok and Fx ~= `` then Desc = `{T.Text}  <font color="#{hex(C.Gold)}">{Fx}</font>` end
		end
		Kit.Text({ Text = Desc; RichText = true; TextWrapped = true; TextSize = 18; TextColor3 = C.TextDim:Lerp(C.Text, 0.45);
			Position = UDim2.fromOffset(0, 30); Size = UDim2.new(1, -176, 0, 40); Parent = Row })
		Kit.Button({ text = `Reroll ({count("Trait")})`; textSize = 20; onClick = function() Shared.Spin(Ctx, `Trait`, Slot) end;
			AnchorPoint = Vector2.new(1, 0); Position = UDim2.new(1, 0, 0, 12); Size = UDim2.fromOffset(164, 44); Parent = Row })
	end
	Ctx.Note(`Race, variant and traits are rolled, never chosen. Your tier grows as your bloodline evolves.`)
end

return Shared
