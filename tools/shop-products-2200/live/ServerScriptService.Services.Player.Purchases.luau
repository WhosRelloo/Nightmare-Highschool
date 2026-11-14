--[[
	Purchases (server): the game's only MarketplaceService.ProcessReceipt. Config: ReplicatedStorage.Config.Shop.

	A receipt is granted at most once: its PurchaseId is stored in the student's save
	(PlayerData.Purchases, newest last, capped). If no save slot is loaded yet (still on the
	main menu) the receipt is left for later (NotProcessedYet) and Roblox offers it again.
	Grants go to the student you are playing when you buy:
		Spin = "Clan"                     -> Identity.AddSpins
		Spin = "Height"                   -> Identity.AddHeightSpins
		Spin = "Race" | "Variant" | "Trait" -> Lineage.GrantSpins (ReplicatedStorage.Lineage)
		Kind = "NameChange"               -> Identity.AddNameChanges
		Kind = "Bundle"                   -> each of Product.Grants ({ Spin; Amount }) as above
	The client is told through ReplicatedStorage.NHIdentity.Updated.
]]

---| Services |---

local MarketplaceService = game:GetService(`MarketplaceService`)
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Shop = require(ReplicatedStorage.Config.Shop)
local Data = require(ServerScriptService.Services.Player.Data)
local Identity = require(ServerScriptService.Services.Player.Identity)
local Lineage = require(ReplicatedStorage.Lineage)
local Fx = require(ServerScriptService.Services.Features.Fx)

local KEEP_RECEIPTS = 100

local Local = {}
local Shared = {}

function Local.Grant(Player: Player, Product): boolean
	if Product.Kind == `Bundle` then
		-- (2026-11-14) several spin kinds in one product. The save is checked first, the only way a part can fail, so a
		-- retried receipt never gives the earlier parts twice.
		if not Data.GetProfile(Player) then return false end
		for _, Part in Product.Grants or {} do
			if not Local.Grant(Player, { Spin = Part.Spin; Amount = Part.Amount }) then
				warn(`[Purchases] bundle {Product.Key}: the {Part.Spin} part failed`)
			end
		end
		return true
	end
	if Product.Spin == `Clan` then
		return Identity.AddSpins(Player, Product.Amount)
	elseif Product.Spin == `Height` then
		return Identity.AddHeightSpins(Player, Product.Amount)
	elseif Product.Spin == `Race` or Product.Spin == `Variant` or Product.Spin == `Trait` then
		-- the Lineage owner's hook (UI kit session); falls back to writing the save directly
		if Lineage.GrantSpins then return Lineage.GrantSpins(Player, Product.Spin, Product.Amount) == true end
		local Profile = Data.GetProfile(Player)
		if not Profile then return false end
		local L = Lineage.Sanitize(Profile.Lineage)
		L.Spins[Product.Spin] = math.clamp((L.Spins[Product.Spin] or 0) + Product.Amount, 0, 999)
		Data.UpdateState(Player, { type = `SetLineage`; lineage = L })
		return true
	elseif Product.Kind == `NameChange` then
		return Identity.AddNameChanges(Player, Product.Amount)
	elseif Product.Kind == `Cape` then
		return Identity.AddCape(Player, Product.Key)
	end
	return false
end

function Local.Describe(Product)
	local N = Product.Amount or 1
	if Product.Kind == `Bundle` then
		local Parts = {}
		for _, Part in Product.Grants or {} do table.insert(Parts, `{Part.Amount} {Part.Spin}`) end
		return { Title = `{Product.Label or `Spin`} Bundle`; Text = `Added to your student: {table.concat(Parts, `, `)} spins.` }
	end
	if Product.Kind == `Cape` then
		return { Title = Product.Cape or `Cape`; Text = `Yours for good. Wear it from the Wardrobe (K), Outfit tab.` }
	end
	local What = if Product.Spin then `{Product.Spin} spin` elseif Product.Kind == `NameChange` then `name change` else Product.Key
	return { Title = `+{N} {What}{if N == 1 then `` else `s`}`; Text = `Added to your student. Thank you for supporting the school!` }
end

-- (audit) ProfileService's developer-product pattern: the receipt id also goes in the profile's meta tags, and the answer
-- waits until a save containing it has been written (MetaData.MetaTagsLatest). Data and meta tags are written together,
-- so the grant is saved too. Released first (leaving, slot change) with it unsaved: NotProcessedYet, Roblox offers it
-- again. Without the meta-tag API (another ProfileService build) it answers PurchaseGranted as before.
function Local.WaitSaved(Player: Player, Id: string): Enum.ProductPurchaseDecision
	local Profile = Data.GetProfileObject and Data.GetProfileObject(Player)
	if not (Profile and typeof(Profile.MetaData) == `table` and Profile.MetaTagsUpdated and Profile.SetMetaTag and Profile.IsActive) then
		return Enum.ProductPurchaseDecision.PurchaseGranted
	end
	local Meta = Profile.MetaData
	local Old = typeof(Meta.MetaTags) == `table` and Meta.MetaTags.ProfilePurchaseIds
	local Ids = if typeof(Old) == `table` then table.clone(Old) else {}
	if not table.find(Ids, Id) then
		table.insert(Ids, Id)
		while #Ids > KEEP_RECEIPTS do table.remove(Ids, 1) end
		pcall(Profile.SetMetaTag, Profile, `ProfilePurchaseIds`, Ids)
	end
	local function saved(): boolean
		local Latest = Meta.MetaTagsLatest
		local List = typeof(Latest) == `table` and Latest.ProfilePurchaseIds
		return typeof(List) == `table` and table.find(List, Id) ~= nil
	end
	local Result = nil
	local Conn = Profile.MetaTagsUpdated:Connect(function()
		if saved() then Result = Enum.ProductPurchaseDecision.PurchaseGranted
		elseif not Profile:IsActive() then Result = Enum.ProductPurchaseDecision.NotProcessedYet end
	end)
	if Profile.Save then pcall(Profile.Save, Profile) end -- hurry the save along where this ProfileService has it
	local Start = os.clock()
	while Result == nil do
		if saved() then Result = Enum.ProductPurchaseDecision.PurchaseGranted break end
		-- still unconfirmed after 2 minutes: ask again later (the id is in Purchases, so it is not granted twice)
		if os.clock() - Start > 120 then Result = Enum.ProductPurchaseDecision.NotProcessedYet break end
		task.wait(0.5)
	end
	Conn:Disconnect()
	return Result
end

function Shared.Process(Info): Enum.ProductPurchaseDecision
	local Player = Players:GetPlayerByUserId(Info.PlayerId)
	local Product = Shop.ById[Info.ProductId]
	if not Product then
		warn(`[Purchases] unknown product {Info.ProductId}: add it to Config.Shop`)
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	local Profile = Player and Data.GetProfile(Player)
	if not Profile then return Enum.ProductPurchaseDecision.NotProcessedYet end

	local Done = typeof(Profile.Purchases) == `table` and table.clone(Profile.Purchases) or {}
	local Id = tostring(Info.PurchaseId)
	-- (audit) already granted on this save: still confirm only once that is really saved
	if table.find(Done, Id) then return Local.WaitSaved(Player, Id) end

	local Ok, Granted = pcall(Local.Grant, Player, Product)
	if not Ok or not Granted then
		warn(`[Purchases] grant failed for {Product.Key}: {Granted}`)
		return Enum.ProductPurchaseDecision.NotProcessedYet
	end
	table.insert(Done, Id)
	while #Done > KEEP_RECEIPTS do table.remove(Done, 1) end
	Data.UpdateState(Player, { type = `SetPurchases`; purchases = Done })
	Identity.Notify(Player)
	-- VFX P1-8: confirm the grant (only now that it has really happened)
	pcall(Fx.Fire, Player, `Purchase`, Local.Describe(Product))
	-- (audit) PurchaseGranted only once the save holding this grant has reached the DataStore
	return Local.WaitSaved(Player, Id)
end

---| Testing |---

-- Runs the real receipt path with a made-up receipt (product ids may still be 0 in Config.Shop).
function Shared.ProcessForTests(Player: Player, Key: string, PurchaseId: string)
	local Product = Shop.ByKey[Key]
	if not Product then return `unknown product` end
	local FakeId = -(table.find(Shop.Products, Product) :: number)
	Shop.ById[FakeId] = Product
	local Result = Shared.Process({ PlayerId = Player.UserId; ProductId = FakeId; PurchaseId = PurchaseId })
	Shop.ById[FakeId] = nil
	return Result.Name
end

function Shared.OnStart()
	MarketplaceService.ProcessReceipt = Shared.Process
end

return Shared
