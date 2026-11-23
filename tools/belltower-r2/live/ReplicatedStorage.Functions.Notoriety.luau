--!strict
--[[ (2.37) Notoriety's maths (Config.Notoriety). Pure: no services, no instances. Used by Services.School.Notoriety. ]]
local Config = require(game:GetService("ReplicatedStorage"):WaitForChild("Config"):WaitForChild("Notoriety")) :: any

local Notoriety = {}

function Notoriety.Gain(Type: string, Ctx: { [string]: any }): number
	local Base = Config.Heat[Type] or 0
	local Mult = 1
	if Ctx.Night then Mult *= Config.NightGain end
	if Ctx.Probation then Mult *= Config.ProbationGain end
	return Base * Mult
end

function Notoriety.Tier(Heat: number): number
	for I = #Config.Tiers, 1, -1 do
		if Heat >= Config.Tiers[I] then return I end
	end
	return 0
end

function Notoriety.Bonus(Tier: number): number
	return Config.TierBonus[Tier] or 0
end

function Notoriety.CoolMult(Mods: { [string]: any }): number
	if Mods.Alibi then return Config.AlibiMult end
	if Mods.Hidden or Mods.Dorms or Mods.OffCampus then return Config.HideMult end
	return 1
end

function Notoriety.Cool(Heat: number, Dt: number, Since: number, Mult: number): number
	local Rate = (if Since < Config.SearchSeconds then Config.CoolSearch else Config.CoolQuiet) * Mult
	return math.max(0, Heat - Rate * Dt)
end

function Notoriety.State(Seen: boolean, Since: number, Identified: boolean): string
	if Seen then return "Lit" end
	if Since < Config.SearchSeconds then return "Search" end
	return if Identified then "Tarnished" else "Hollow"
end

function Notoriety.SearchRadius(Since: number): number
	local T = math.clamp(Since / Config.SearchSeconds, 0, 1)
	return Config.SearchRadius.Min + (Config.SearchRadius.Max - Config.SearchRadius.Min) * T
end

function Notoriety.BookType(Misdeed: string): string
	return Config.BookAs[Misdeed] or Misdeed
end

function Notoriety.TierName(Tier: number): string
	return Config.TierNames[Tier] or ""
end

return Notoriety
