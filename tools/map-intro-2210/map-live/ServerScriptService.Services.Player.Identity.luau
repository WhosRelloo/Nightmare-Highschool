--[[
	Player.Identity: the Map place's stand-in (NH core add-on, 2026-11-05).

	The real Identity (names, clans, spins, the register) belongs to the full game and pulls in most of it. The Map's
	wardrobe only needs to know what a student owns (Features.Gear asks), so this answers that from the in-memory
	profile (Services.Player.Data, no saving). Everything is unlocked there (see Data.LoadSlot).

	(2026-11-17, introductions on the Map) The Map has no main menu and no register, so Data.LoadSlot calls
	Shared.Assign: each visit gets a first name from FIRST (not one already in the server) and a clan rolled with
	Config.Clans' own odds, and the player is marked Signed. That lets Services.Social.Strangers work as it does in
	NH Combat Test: a stranger's plate, "[G] Introduce yourself", and the name once you've met. Nothing is saved, so
	every visit is a new student.
]]

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local Players = game:GetService(`Players`)

local Data = require(ServerScriptService.Services.Player.Data)

local Shared = {}

-- first names for Map visitors (any student; the clan is the family name)
local FIRST = {
	`Ada`, `Ambrose`, `Ash`, `Beatrix`, `Blythe`, `Calla`, `Cassius`, `Cordelia`, `Corin`, `Dorian`, `Edie`,
	`Elias`, `Elspeth`, `Emrys`, `Ezra`, `Felix`, `Florence`, `Gideon`, `Greer`, `Hollis`, `Imogen`, `Isolde`,
	`Jasper`, `Juno`, `Kit`, `Lark`, `Lenore`, `Linus`, `Lucian`, `Maren`, `Morrow`, `Nell`, `Octavia`, `Odile`,
	`Orin`, `Perpetua`, `Quill`, `Rhys`, `Rowan`, `Sable`, `Silas`, `Soren`, `Tamsin`, `Thea`, `Theo`, `Ursa`,
	`Vale`, `Wren`,
}

function Shared.Sanitize(I)
	I = if typeof(I) == `table` then I else {}
	I.First = if typeof(I.First) == `string` then I.First else ``
	for _, K in { `Uniforms`, `Capes`, `Gear` } do
		if typeof(I[K]) ~= `table` then I[K] = {} end
	end
	if typeof(I.GearOn) ~= `table` then I.GearOn = {} end
	return I
end

function Shared.Get(Player: Player)
	local Profile = Data.GetProfile(Player)
	if not Profile then return nil end
	Profile.Identity = Shared.Sanitize(Profile.Identity)
	return Profile.Identity
end

function Shared.HasName(Player: Player): boolean
	local I = Shared.Get(Player)
	return I ~= nil and I.First ~= ``
end

-- "First Clan", as NH Combat Test's Identity.FullName gives it
function Shared.FullName(I): string
	if not (I and I.First and I.First ~= ``) then return `` end
	local Ok, Clans = pcall(require, ReplicatedStorage.Config.Clans)
	local Def = Ok and I.Clan and Clans.ById[I.Clan]
	return if Def then `{I.First} {Def.Name}` else I.First
end

-- a clan with Config.Clans' odds (each clan's Chance, in percent)
local function RollClan(): string?
	local Ok, Clans = pcall(require, ReplicatedStorage.Config.Clans)
	if not Ok then return nil end
	local Total = 0
	for _, C in Clans.List do Total += Clans.Chance(C.Id) end
	local R = Random.new():NextNumber() * Total
	for _, C in Clans.List do
		R -= Clans.Chance(C.Id)
		if R <= 0 then return C.Id end
	end
	return Clans.List[#Clans.List] and Clans.List[#Clans.List].Id
end

-- (Map) a name and clan for this visit, then the in-school flags Strangers checks
function Shared.Assign(Player: Player)
	local I = Shared.Get(Player)
	if not I then return end
	if I.First == `` then
		local Taken = {}
		for _, Other in Players:GetPlayers() do
			local OI = Other ~= Player and Shared.Get(Other)
			if OI and OI.First ~= `` then Taken[OI.First] = true end
		end
		local Free = {}
		for _, N in FIRST do if not Taken[N] then table.insert(Free, N) end end
		local Pool = if #Free > 0 then Free else FIRST
		I.First = Pool[Random.new():NextInteger(1, #Pool)]
	end
	if not I.Clan then I.Clan = RollClan() end
	Player:SetAttribute(`Signed`, true)
	-- no main menu on the Map: everyone is in school from the start (Strangers needs InMainMenu == false)
	Player:SetAttribute(`InMainMenu`, false)
	local Ok, Strangers = pcall(require, ServerScriptService.Services.Social.Strangers)
	if Ok and Strangers.Refresh then Strangers.Refresh() end
end

return Shared
