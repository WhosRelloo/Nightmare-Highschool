--[[
	Care (server). Services.Features.Infirmary.Care  (phase6-strafes)
	The DEFAULT treatment rules behind Infirmary.Treat. A placeholder by design: the coming injury system replaces this
	module through Infirmary.SetCare. Every number is an owner default (2026-11-22) in Config.Gestures.Treat; confirm
	after playing.
	  CanTreat(P) -> (ok, reason?)   refused while combat-tagged, downed or carried, on cooldown, or not hurt
	  Apply(P)                       full health; NHBandagedUntil = now + Kit.Aid.Clears; NHWounded cleared; cooldown
	  Cost(P) -> number              free (Treat.Price)
	  Reset(P)                       clears the cooldown (Studio checks)
	Cooldowns are per player for the session (not saved).
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Config = require(ReplicatedStorage.Config.Gestures)
local KitConfig = require(ReplicatedStorage.Config.Kit)

local Care = {}
local Last = {} :: { [Player]: number }

local function now(): number return workspace:GetServerTimeNow() end

function Care.CanTreat(P: Player): (boolean, string?)
	local T = Config.Treat
	local Char = P.Character
	local H = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not H or H.Health <= 0 then return false, nil end
	if (P:GetAttribute(`CombatTagUntil`) or 0) > now() then return false, `Not while you're fighting.` end
	if Char:GetAttribute(`DownedUntil`) or H:GetAttribute(`Downed`) or Char:GetAttribute(`CarriedBy`) then
		return false, `Lie still, help is coming.`
	end
	if Last[P] and now() - Last[P] < T.Cooldown then return false, `Come back in a few minutes.` end
	if H.Health >= H.MaxHealth - 0.01 and not Char:GetAttribute(`NHWounded`) then return false, `You're fine. Off you go.` end
	return true, nil
end

function Care.Apply(P: Player)
	local Char = P.Character
	local H = Char and Char:FindFirstChildOfClass(`Humanoid`)
	if not H then return end
	if Config.Treat.Heal == `Full` then H.Health = H.MaxHealth else H.Health = math.min(H.MaxHealth, H.Health + (tonumber(Config.Treat.Heal) or 0)) end
	local Clears = KitConfig.Aid and KitConfig.Aid.Clears or 120
	Char:SetAttribute(`NHBandagedUntil`, now() + Clears)
	Char:SetAttribute(`NHWounded`, nil)
	Last[P] = now()
end

function Care.Cost(_P: Player): number
	return Config.Treat.Price or 0
end

function Care.Reset(P: Player)
	Last[P] = nil
end

Players.PlayerRemoving:Connect(function(P) Last[P] = nil end)

return Care
