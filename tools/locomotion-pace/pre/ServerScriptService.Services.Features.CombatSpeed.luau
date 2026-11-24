--[[
	CombatSpeed (server): you move slower while combat-tagged (Services.Features.CombatTag sets the player's
	CombatTagUntil). Every script that writes Humanoid.WalkSpeed writes a constant (sprint 25/40.5, walk 12,
	states 14.4 / 5 / 0 ...), so we remember the raw value each one wrote and apply the multiplier on top.
	Speeds at or below FLOOR (stuns, crawls) are left alone.
]]
local Players = game:GetService(`Players`)

local MULT = 0.8
local FLOOR = 8
-- (phase6-strafes) while the client's directional walk runs (lock-on, shift lock, first person: NHStrafe), the walk band
-- is capped at Config.Locomotion.StrafeSpeed. A cap can only slow a player, so the client's boolean is safe to trust.
local LocoCfg = require(game:GetService(`ReplicatedStorage`).Config.Locomotion)

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
		if Char:GetAttribute(`NHStrafing`) and Raw <= LocoCfg.WalkBandMax and Raw > FLOOR then
			Want = math.min(Want, LocoCfg.StrafeSpeed)
		end
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
	Char:GetAttributeChangedSignal(`NHStrafing`):Connect(apply) -- (phase6-strafes)
	onTag()
end

-- (phase6-strafes) the client's directional walk on / off -> the Character attribute NHStrafing (rate-limited)
local function strafeRemote()
	local RS = game:GetService(`ReplicatedStorage`)
	local Folder = RS:WaitForChild(`Remotes`)
	local R = Folder:FindFirstChild(`NHStrafe`) or Instance.new(`RemoteEvent`)
	R.Name = `NHStrafe`
	R.Parent = Folder
	local Last = {} :: { [Player]: { number } }
	R.OnServerEvent:Connect(function(P: Player, Msg: any)
		local Now = os.clock()
		local L = Last[P] or {}
		Last[P] = L
		while L[1] and Now - L[1] > 1 do table.remove(L, 1) end
		if #L >= LocoCfg.RemoteRate then return end
		table.insert(L, Now)
		local On = typeof(Msg) == `table` and Msg.On == true
		local C = P.Character
		if C then C:SetAttribute(`NHStrafing`, if On then true else nil) end
	end)
	Players.PlayerRemoving:Connect(function(P) Last[P] = nil end)
end

function Shared.OnStart()
	strafeRemote()
	local function onPlayer(P: Player)
		P.CharacterAdded:Connect(function(Char) task.spawn(hook, P, Char) end)
		if P.Character then task.spawn(hook, P, P.Character) end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, P in Players:GetPlayers() do onPlayer(P) end
end

return Shared
