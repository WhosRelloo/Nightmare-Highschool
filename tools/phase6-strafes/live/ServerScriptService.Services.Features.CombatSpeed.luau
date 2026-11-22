--[[
	CombatSpeed (server): you move slower while combat-tagged (Services.Features.CombatTag sets the player's
	CombatTagUntil). Every script that writes Humanoid.WalkSpeed writes a constant (sprint 25/40.5, walk 12,
	states 14.4 / 5 / 0 ...), so we remember the raw value each one wrote and apply the multiplier on top.
	Speeds at or below FLOOR (stuns, crawls) are left alone.
]]
local Players = game:GetService(`Players`)

local MULT = 0.8
local FLOOR = 8

local Shared = {}

local function inCombat(P: Player): boolean
	local U = P:GetAttribute(`CombatTagUntil`)
	return typeof(U) == `number` and U > workspace:GetServerTimeNow() -- CombatTag's clock
end

local function hook(P: Player, Char: Model)
	local Hum = Char:WaitForChild(`Humanoid`, 10) :: Humanoid?
	if not Hum then return end
	local Raw = Hum.WalkSpeed
	local Applied = Raw
	local Busy = false
	local function apply()
		-- (kit 1.79) Wounded walks 10% slower out of combat; bandaging slows you (Services.Features.Kit)
		local Tagged = inCombat(P)
		local M = if Tagged then MULT else (if Char:GetAttribute(`NHWounded`) == true then 0.9 else 1)
		local Slow = Char:GetAttribute(`NHKitSlow`)
		if typeof(Slow) == `number` then M *= math.clamp(Slow, 0.3, 1) end
		-- (training 1.81) trained legs sprint a little faster (Progression sets NH_SprintMult; sprints are 25 / 40.5)
		local SprintM = Char:GetAttribute(`NH_SprintMult`)
		if typeof(SprintM) == `number` and Raw >= 24 then M *= math.clamp(SprintM, 1, 1.2) end
		local Want = if M ~= 1 and Raw > FLOOR then math.max(FLOOR, Raw * M) else Raw
		if math.abs(Hum.WalkSpeed - Want) > 1e-3 then
			Busy = true
			Hum.WalkSpeed = Want
			Busy = false
		end
		Applied = Want
		Hum:SetAttribute(`NH_SpeedMult`, if Want ~= Raw then M else nil)
	end
	Hum:GetPropertyChangedSignal(`WalkSpeed`):Connect(function()
		if Busy then return end
		if math.abs(Hum.WalkSpeed - Applied) < 1e-3 then return end -- our own value echoed back
		Raw = Hum.WalkSpeed
		apply()
	end)
	local Expiry: thread? = nil
	local function onTag()
		apply()
		if Expiry then pcall(task.cancel, Expiry) Expiry = nil end
		local U = P:GetAttribute(`CombatTagUntil`)
		if typeof(U) == `number` then
			local Left = U - workspace:GetServerTimeNow()
			if Left > 0 and Left < 600 then Expiry = task.delay(Left + 0.05, onTag) end
		end
	end
	local C = P:GetAttributeChangedSignal(`CombatTagUntil`):Connect(onTag)
	Char.Destroying:Connect(function() C:Disconnect() end)
	Char:GetAttributeChangedSignal(`NHWounded`):Connect(apply)
	Char:GetAttributeChangedSignal(`NHKitSlow`):Connect(apply)
	Char:GetAttributeChangedSignal(`NH_SprintMult`):Connect(apply)
	onTag()
end

function Shared.OnStart()
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function(Char) task.spawn(hook, P, Char) end)
		if P.Character then task.spawn(hook, P, P.Character) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
end

return Shared
