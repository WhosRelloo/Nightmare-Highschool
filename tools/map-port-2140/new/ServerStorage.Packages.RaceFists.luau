--[[
	RaceFists (server): combat concept 17 (2.14.0). The last hit of the fist string carries the attacker's race: a tint
	(the client's "Race Fist" effect, recoloured by a Crimson or Blue moon event) and one small effect. Sub-races use
	their race. No blood or gore.
	  Vampire   SIP      you heal 25% of the damage
	  Priest    SMITE    +40 guard damage, against the unholy only (vampires, ghouls, werewolves, wraiths, the night's beasts)
	  Werewolf  MAUL     35% harder knockback and 0.35 s more stagger
	  Wraith    CHILL    they're slowed for 1.5 s
	  Ghoul     ROT      their guard doesn't recover for 3 s (Features.Posture)
	  Human     STEADY   +20 guard damage
	Combat.M1 calls Before (changes the hit) and After (once it landed) on the 4th fist hit only.
	Off switch: ReplicatedStorage attribute NHRaceFistsOff.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

local RaceFists = {}

RaceFists.Effects = {
	Vampire = { Tag = `SIP`; Heal = 0.25 };
	Priest = { Tag = `SMITE`; UnholyGuard = 40 };
	Werewolf = { Tag = `MAUL`; Knockback = 1.35; Stagger = 0.35 };
	Wraith = { Tag = `CHILL`; Slow = 1.5 };
	Ghoul = { Tag = `ROT`; Rot = 3 };
	Human = { Tag = `STEADY`; Guard = 20 };
}
local UNHOLY = { Vampire = true; Ghoul = true; Werewolf = true; Wraith = true }

function RaceFists.RaceOf(Model: Instance?): string?
	if not Model then return nil end
	local P = Players:GetPlayerFromCharacter(Model)
	local R = (P and P:GetAttribute(`Race`)) or Model:GetAttribute(`Race`)
	return if typeof(R) == `string` then R else nil
end

function RaceFists.IsUnholy(Model: Instance?): boolean
	if not Model then return false end
	if UNHOLY[RaceFists.RaceOf(Model) or ``] then return true end
	if Model:GetAttribute(`WolfForm`) or Model:GetAttribute(`Beast`) then return true end
	local Parent = Model.Parent
	return Parent ~= nil and (Parent.Name == `NHBeasts` or Parent.Name == `NHWolves`)
end

local function On(): boolean
	return ReplicatedStorage:GetAttribute(`NHRaceFistsOff`) ~= true
end

-- the effect for this attacker's race (nil without one, or when off)
function RaceFists.For(Attacker: Model?)
	if not On() then return nil, nil end
	local Race = RaceFists.RaceOf(Attacker)
	local E = Race and RaceFists.Effects[Race]
	return E, Race
end

-- before the 4th hit is dealt: changes to the hit itself (knockback, stagger, the readout tag)
function RaceFists.Before(DamageData: any)
	local E = RaceFists.For(DamageData.Character)
	if not E then return end
	if E.Knockback and DamageData.LinearVelocity and DamageData.LinearVelocity.Velocity then
		DamageData.LinearVelocity.Velocity *= E.Knockback
	end
	if E.Stagger then
		DamageData.Stun = (DamageData.Stun or 0) + E.Stagger
	end
	if E.UnholyGuard and not RaceFists.IsUnholy(DamageData.Target) then return end -- a priest's smite only names the unholy
	if not DamageData.Tag then DamageData.Tag = E.Tag end
end

-- add guard (posture) to Target; a full bar breaks it through DamageLogic
local function Guard(DamageData: any, Amount: number, DamageLogic: any)
	local Target = DamageData.Target
	local H = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
	if not H or H.Health <= 0 then return end
	local P = (H:GetAttribute(`Posture`) or 0) + Amount * (Target:GetAttribute(`NH_PostureGain`) or 1)
	if P >= 100 then DamageLogic.PostureBreak(DamageData) else H:SetAttribute(`Posture`, P) end
end

-- after the 4th hit landed (DamageLogic.TakeAction ran): the race's effect and the tinted burst
function RaceFists.After(DamageData: any, DamageLogic: any)
	local E, Race = RaceFists.For(DamageData.Character)
	if not E then return end
	local Attacker, Target = DamageData.Character, DamageData.Target
	if E.Heal then
		local H = Attacker and Attacker:FindFirstChildWhichIsA(`Humanoid`)
		if H and H.Health > 0 then H.Health = math.min(H.MaxHealth, H.Health + (DamageData.Damage or 0) * E.Heal) end
	end
	if E.Guard then Guard(DamageData, E.Guard, DamageLogic) end
	if E.UnholyGuard and RaceFists.IsUnholy(Target) then Guard(DamageData, E.UnholyGuard, DamageLogic) end
	if E.Slow and Target then StateManager.CreateState(Target, `Slow`, E.Slow) end
	if E.Rot and Target then Target:SetAttribute(`NHPostureRotUntil`, workspace:GetServerTimeNow() + E.Rot) end
	Packets.Replicate:Fire(`Misc`, `Race Fist`, { User = Target; Attacker = Attacker; Race = Race; Moon = workspace:GetAttribute(`NHMoonEvent`) })
end

return RaceFists
