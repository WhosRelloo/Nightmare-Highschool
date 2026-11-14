
---| Services |---

local Debris = game:GetService(`Debris`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---
local Blood = require(game:GetService("ReplicatedStorage"):WaitForChild("Packages"):WaitForChild("Visuals"):WaitForChild("Blood"))

local EmitManager = require(ReplicatedStorage.Functions.EmitManager)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

---| Effect |---

return function (Character: Model, Paramaters: { User: Model; Weapon: string } )
	local Config = WeaponsConfig[Paramaters.Weapon]
	if not Config then return end

	local Humanoid = Paramaters.User:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

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
