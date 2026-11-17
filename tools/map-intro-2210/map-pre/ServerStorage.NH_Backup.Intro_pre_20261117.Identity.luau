--[[
	Player.Identity: the Map place's stand-in (NH core add-on, 2026-11-05).

	The real Identity (names, clans, spins, the register) belongs to the full game and pulls in most of it. The Map's
	wardrobe only needs to know what a student owns (Features.Gear asks), so this answers that from the in-memory
	profile (Services.Player.Data, no saving). Everything is unlocked there (see Data.LoadSlot).
]]

local ServerScriptService = game:GetService(`ServerScriptService`)

local Data = require(ServerScriptService.Services.Player.Data)

local Shared = {}

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

function Shared.FullName(I): string
	return if I and I.First and I.First ~= `` then I.First else ``
end

return Shared
