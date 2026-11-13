
---| Services |---

local Debris = game:GetService(`Debris`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---
local Blood = require(game:GetService("ReplicatedStorage"):WaitForChild("Packages"):WaitForChild("Visuals"):WaitForChild("Blood"))

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local Players = game:GetService(`Players`)

-- (combat audit) hit-stop: the attack and hit-react tracks hold for a few frames on contact (the house style: light 3,
-- heavy 6 at 60 fps). Only Action3/Action4 tracks (swings, hit reacts) pause; walking and idle carry on.
local HOLD = { [Enum.AnimationPriority.Action3] = true; [Enum.AnimationPriority.Action4] = true }
local function HitStop(Model: Model?, Duration: number)
	local Hum = Model and Model:FindFirstChildWhichIsA(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return end
	local Held = {}
	for _, T in Animator:GetPlayingAnimationTracks() do
		if HOLD[T.Priority] and T.Speed > 0 then
			table.insert(Held, { T, T.Speed })
			T:AdjustSpeed(0)
		end
	end
	if #Held == 0 then return end
	task.delay(Duration, function()
		for _, H in Held do
			if H[1].IsPlaying and H[1].Speed == 0 then H[1]:AdjustSpeed(H[2]) end
		end
	end)
end

---| Effect |---

return function (Character: Model, Paramaters: { User: Model; Weapon: string } )
	local Config = WeaponsConfig[Paramaters.Weapon]
	if not Config then return end

	local Humanoid = Paramaters.User:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	-- (combat audit) contact weight: both bodies hold, and the attacker's and the victim's cameras jolt (Camera Shake setting)
	local Heavy = Paramaters.Heavy == true
	local Hold = if Heavy then 0.1 else 0.05
	HitStop(Paramaters.User, Hold)
	if typeof(Paramaters.Attacker) == `Instance` then HitStop(Paramaters.Attacker, Hold) end
	local Me = Players.LocalPlayer and Players.LocalPlayer.Character
	if Me and (Me == Paramaters.Attacker or Me == Paramaters.User) then
		EmitManager.ShakeCamera(if Heavy then 3 else 1.4, 10, 0, if Heavy then 0.3 else 0.16)
	end

	local DamageType = Config.DamageType 
	-- (audit) a DamageType without its own HitType effect or hit sounds (Slash) falls back to Blunt instead of erroring
	local HitTypes = ReplicatedStorage.Assets.Effects.HitType
	local HitSounds = ReplicatedStorage.Assets.Sounds.Hit
	if not (DamageType and HitTypes:FindFirstChild(DamageType) and HitSounds:FindFirstChild(DamageType)) then DamageType = `Blunt` end
	local RootPart = Humanoid.RootPart
	local HitPosition = RootPart.CFrame

	local HitEffect = EmitManager.SpawnGroup(ReplicatedStorage.Assets.Effects.HitType[DamageType], HitPosition, 5)

	local sound = ReplicatedStorage.Assets.Sounds.Hit[DamageType]:GetChildren() :: Sound
	if #sound > 0 then -- (audit) HitCounter runs past the sound count: wrap it
		EmitManager.CloneSound(sound[((tonumber(Humanoid:GetAttribute("HitCounter")) or 1) - 1) % #sound + 1], HitEffect)
	end
	EmitManager.Emit(HitEffect:GetDescendants())



	if DamageType == "Blood" then
		local Torso = Paramaters.User:FindFirstChild("Torso")

		if Torso then


			if math.random(1, 3) == 1 then
				Blood.createBloodSplatter(Paramaters.User, { Amount = math.random(1, 3) })
			else
				Blood.createBloodSplatter(Paramaters.User, { Amount = math.random(1, 3) })
			end

		end
	end
end
