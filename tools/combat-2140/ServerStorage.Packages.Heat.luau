--[[
	Heat (server): combat concept 18 (2.14.0). A second resource besides posture, earned by fighting well.
	The character attribute NHHeat (0-100) fills from:
	  a hit you land +6, a counter-hit +12, a perfect dodge +10, a parry +20      (DamageLogic hooks)
	and drains 5 a second once you've gone 6 s without earning any; a full bar holds 20 s first. Players only.
	A full bar makes your next Z / X / C skill an EX (ActionManager.Activate calls TrySpend as a skill starts):
	  * +30% damage on that skill's hits (NHEXUntil, until the skill ends: EndEX);
	  * armour through its wind-up: hits still hurt, but don't stun or cancel it (NHEXArmorUntil, 0.6 s);
	  * a gold flare ("Heat EX", client). Spending empties the bar.
	The client draws it (Controllers.Gui.HeatMeter, the brazier on the health bar's right cap).
	Off switch: ReplicatedStorage attribute NHHeatOff.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)

local Packets = require(ReplicatedStorage.Remotes.Packets)

local Heat = {}

Heat.MAX = 100
Heat.GAIN = { Hit = 6; Counter = 12; Dodge = 10; Parry = 20 }
Heat.DRAIN_AFTER = 6
Heat.DRAIN_PER_SECOND = 5
Heat.EX_DAMAGE = 1.3
Heat.EX_MAX = 4 -- seconds an EX can last if its skill never reports ending
Heat.ARMOR = 0.6

local LastGain = setmetatable({}, { __mode = `k` }) :: { [Model]: number }

local function On(): boolean
	return ReplicatedStorage:GetAttribute(`NHHeatOff`) ~= true
end

function Heat.Get(Character: Model): number
	return tonumber(Character:GetAttribute(`NHHeat`)) or 0
end

function Heat.Add(Character: Instance?, Amount: number)
	if not (On() and Character and Character:IsA(`Model`) and Character.Parent) then return end
	if not Players:GetPlayerFromCharacter(Character) then return end
	if Heat.EXActive(Character) then return end -- an EX doesn't refill the bar it just spent
	local Before = Heat.Get(Character)
	local After = math.clamp(Before + Amount, 0, Heat.MAX)
	if After ~= Before then Character:SetAttribute(`NHHeat`, After) end
	LastGain[Character] = os.clock()
end

-- a skill is starting: spend a full bar on an EX. Returns true when it did.
function Heat.TrySpend(Character: Model, Skill: string): boolean
	if not (On() and Heat.Get(Character) >= Heat.MAX) then return false end
	local Now = workspace:GetServerTimeNow()
	Character:SetAttribute(`NHHeat`, 0)
	Character:SetAttribute(`NHEXUntil`, Now + Heat.EX_MAX)
	Character:SetAttribute(`NHEXArmorUntil`, Now + Heat.ARMOR)
	Character:SetAttribute(`NHEXSkill`, Skill)
	Packets.Replicate:Fire(`Misc`, `Heat EX`, { User = Character; Skill = Skill })
	return true
end

function Heat.EndEX(Character: Model)
	Character:SetAttribute(`NHEXUntil`, nil)
	Character:SetAttribute(`NHEXArmorUntil`, nil)
	Character:SetAttribute(`NHEXSkill`, nil)
end

local function Before(Character: Instance?, Name: string): boolean
	local U = Character and Character:GetAttribute(Name)
	return typeof(U) == `number` and workspace:GetServerTimeNow() < U
end

function Heat.EXActive(Character: Instance?): boolean
	return Before(Character, `NHEXUntil`)
end

function Heat.Armored(Character: Instance?): boolean
	return Before(Character, `NHEXArmorUntil`)
end

-- the drain: 5 a second after 6 s without a gain; a full bar holds for FULL_HOLD before it starts to cool, so it waits
-- for your skill instead of melting away
Heat.FULL_HOLD = 20
local FullAt = setmetatable({}, { __mode = `k` }) :: { [Model]: number }
local Acc = 0
RunService.Heartbeat:Connect(function(Dt)
	Acc += Dt
	if Acc < 0.25 then return end
	local Step = Acc
	Acc = 0
	local Now = os.clock()
	for _, P in Players:GetPlayers() do
		local C = P.Character
		if not C then continue end
		local H = Heat.Get(C)
		local Full = H >= Heat.MAX
		if Full then FullAt[C] = FullAt[C] or Now else FullAt[C] = nil end
		local Idle = if Full then Now - FullAt[C] else Now - (LastGain[C] or 0)
		if H > 0 and Idle >= (if Full then Heat.FULL_HOLD else Heat.DRAIN_AFTER) then
			C:SetAttribute(`NHHeat`, math.max(0, H - Heat.DRAIN_PER_SECOND * Step))
		end
	end
end)

return Heat
