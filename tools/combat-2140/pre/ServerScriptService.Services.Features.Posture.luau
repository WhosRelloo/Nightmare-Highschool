--[[
	Posture recovery (server)

	Posture (Humanoid attribute, 0-100) fills when blocking hits (DamageLogic) and
	breaks at 100. This service drains it back down after Config.Combat.PostureRegenDelay
	seconds without new posture damage.
]]

---| Services |---

local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local Config = require(ReplicatedStorage.Config.Combat)
local ActionManager = require(ServerScriptService.Services.Player.ActionManager)

local TICK = 0.2

local LastGain = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: number }
local LastValue = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: number }
local Writing = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: boolean }
local Watched = setmetatable({}, { __mode = `k` }) :: { [Humanoid]: boolean }

local Local = {}
local Shared = {}

function Local.Watch(Model: Instance)
	if not Model:IsA(`Model`) then return end

	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`) or Model:WaitForChild(`Humanoid`, 5)
	if not Humanoid or not Humanoid:IsA(`Humanoid`) or Watched[Humanoid] then return end
	Watched[Humanoid] = true

	LastValue[Humanoid] = Humanoid:GetAttribute(`Posture`) or 0
	Humanoid:GetAttributeChangedSignal(`Posture`):Connect(function()
		if Writing[Humanoid] then return end

		local Value = Humanoid:GetAttribute(`Posture`) or 0
		if Value > (LastValue[Humanoid] or 0) then
			LastGain[Humanoid] = os.clock()
		end
		LastValue[Humanoid] = Value
	end)
end

function Local.Tick()
	local Now = os.clock()

	for Humanoid in Watched do
		if not Humanoid.Parent or Humanoid.Health <= 0 then continue end

		local Posture = Humanoid:GetAttribute(`Posture`) or 0
		if Posture <= 0 then continue end
		if Now - (LastGain[Humanoid] or 0) < Config.PostureRegenDelay then continue end

		local Rate = Config.PostureRegenPerSecond
		if ActionManager.isActionPlaying(Humanoid.Parent, `Block`) then
			Rate *= Config.PostureRegenBlockingScale
		end
		-- (kit 1.79) the Night Chill: guard recovers 25% slower (Config.Kit.Chill.PostureRegen)
		if Humanoid.Parent:GetAttribute(`NHChilled`) == true then Rate *= 0.75 end

		local NewPosture = math.max(0, Posture - Rate * TICK)
		Writing[Humanoid] = true
		Humanoid:SetAttribute(`Posture`, NewPosture)
		Writing[Humanoid] = nil
		LastValue[Humanoid] = NewPosture
	end
end

function Shared.OnStart()
	local Live = workspace:WaitForChild(`Live`)
	for _, Model in Live:GetChildren() do
		task.spawn(Local.Watch, Model)
	end
	Live.ChildAdded:Connect(function(Model)
		task.spawn(Local.Watch, Model)
	end)

	task.spawn(function()
		while true do
			task.wait(TICK)
			Local.Tick()
		end
	end)
end

return Shared
