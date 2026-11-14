--[[
	BeastStagger (server): combat concept 22 (2.15.0). Fists give you a role against the night once you own a katana:
	they break a beast's footing faster than blades.

	Every hit on a beast (workspace.Live.NHBeasts / NHWolves) fills a hidden stagger meter on it (the model attribute
	NHStagger, 0-100):
	  a fist hit +12, a heavy fist hit (the 4th, an ender, a heavy) +22, any other weapon +4.
	It cools 25 a second once 3 s pass without a hit. Full: the beast staggers.
	  * Paralyzed for 2 s: Features.Beasts plays its GuardBroken and it stops, even through its StunGuard;
	  * it takes 25% more damage meanwhile (NHStaggerUntil);
	  * STAGGER on the readout, a burst on the beast (client "Beast Stagger"), and +15 Heat for the one who did it.
	It can't be staggered again for 6 s after it recovers. DamageLogic calls Before / DamageMult / After.
	Off switch: ReplicatedStorage attribute NHBeastStaggerOff.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local BeastStagger = {}

BeastStagger.MAX = 100
BeastStagger.GAIN = { Fist = 12; FistHeavy = 22; Other = 4 }
BeastStagger.COOL_AFTER = 3
BeastStagger.COOL_PER_SECOND = 25
BeastStagger.STAGGER = 2
BeastStagger.REARM = 6
BeastStagger.DAMAGE_TAKEN = 1.25
BeastStagger.HEAT = 15

local LastHit = setmetatable({}, { __mode = `k` }) :: { [Model]: number }
local ReadyAt = setmetatable({}, { __mode = `k` }) :: { [Model]: number }

local function On(): boolean
	return ReplicatedStorage:GetAttribute(`NHBeastStaggerOff`) ~= true
end

function BeastStagger.IsBeast(Model: Instance?): boolean
	local P = Model and Model.Parent
	return P ~= nil and (P.Name == `NHBeasts` or P.Name == `NHWolves`)
end

function BeastStagger.Staggered(Model: Instance?): boolean
	local U = Model and Model:GetAttribute(`NHStaggerUntil`)
	return typeof(U) == `number` and workspace:GetServerTimeNow() < U
end

function BeastStagger.DamageMult(Target: Instance?): number
	return if BeastStagger.Staggered(Target) then BeastStagger.DAMAGE_TAKEN else 1
end

-- before the hit is dealt: how much it adds, and whether it fills the meter (then the readout says STAGGER)
function BeastStagger.Before(DamageData: any): number?
	local Target, Character = DamageData.Target, DamageData.Character
	if not (On() and Character and BeastStagger.IsBeast(Target)) then return nil end
	if BeastStagger.Staggered(Target) or os.clock() < (ReadyAt[Target] or 0) then return nil end
	local Fist = Character:GetAttribute(`Weapon`) == `Fist`
	local Gain = if not Fist then BeastStagger.GAIN.Other
		elseif DamageData.Heavy or DamageData.Stun or (DamageData.LinearVelocity and (DamageData.LinearVelocity.Velocity or 0) >= 30) then BeastStagger.GAIN.FistHeavy
		else BeastStagger.GAIN.Fist
	local After = (tonumber(Target:GetAttribute(`NHStagger`)) or 0) + Gain
	if After >= BeastStagger.MAX and not DamageData.Tag then DamageData.Tag = `STAGGER` end
	return Gain
end

-- after the hit landed: fill the meter; full, the beast staggers
function BeastStagger.After(DamageData: any, Gain: number?, Heat: any?)
	if not Gain then return end
	local Target, Character = DamageData.Target, DamageData.Character
	local H = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
	if not (H and H.Health > 0) then return end
	LastHit[Target] = os.clock()
	local Meter = (tonumber(Target:GetAttribute(`NHStagger`)) or 0) + Gain
	if Meter < BeastStagger.MAX then
		Target:SetAttribute(`NHStagger`, Meter)
		return
	end
	Target:SetAttribute(`NHStagger`, 0)
	Target:SetAttribute(`NHStaggerUntil`, workspace:GetServerTimeNow() + BeastStagger.STAGGER)
	ReadyAt[Target] = os.clock() + BeastStagger.STAGGER + BeastStagger.REARM
	StateManager.CreateState(Target, `Paralyzed`, BeastStagger.STAGGER)
	if Heat and Character then pcall(Heat.Add, Character, BeastStagger.HEAT) end
	Packets.Replicate:Fire(`Misc`, `Beast Stagger`, { User = Target; Attacker = Character })
end

-- the meter cools once the hits stop
local Acc = 0
RunService.Heartbeat:Connect(function(Dt)
	Acc += Dt
	if Acc < 0.25 then return end
	local Step = Acc
	Acc = 0
	local Now = os.clock()
	for Model, At in LastHit do
		if not Model.Parent then LastHit[Model] = nil continue end
		if Now - At < BeastStagger.COOL_AFTER then continue end
		local M = tonumber(Model:GetAttribute(`NHStagger`)) or 0
		if M <= 0 then LastHit[Model] = nil continue end
		Model:SetAttribute(`NHStagger`, math.max(0, M - BeastStagger.COOL_PER_SECOND * Step))
	end
end)

return BeastStagger
