
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)

---| Type Annotation |---

export type States = 
	| 'Knockback'
| 'Stun' 
| 'ParryStun'
| 'Ragdoll' 
| 'Paralyzed' 
| 'Freeze' 
| 'NoParry'
| 'Slow'
| 'SkillInUse';

local StateFunctions = {} :: {
	[States | string]: {
		Priority: number;
		CallBack: (Character: Model, Added: boolean?) -> ();

	}
}

local Local = {}
local Shared = {}

function Shared.OnStart()

	for Name, StateData in StateFunctions do
		StateManager.SetStatesPriority(Name, StateData.Priority)
		StateManager.onState(Name, StateData.CallBack)

	end

end

---| States Functions |---

StateFunctions[`Stun`] = {
	-- (audit) above ParryStun / Knockback (both 4, they don't lock movement): with equal priorities the active state depended
	-- on table order, so an overlapping ParryStun could take over and Stun's release callback gave the speed back mid-stun
	Priority = 4.5;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 5 or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)

		end
	end;

}

StateFunctions[`ParryStun`] = {
	Priority = 4;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.AutoRotate = not Added
		if Added then
			Humanoid:SetAttribute(`Sprint`, false)

		end
	end;

}

StateFunctions[`Ragdoll`] = {
	Priority = 7;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 0 or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
			-- RagdollController.Ragdoll(Character, Added)
		end
	end;
}

StateFunctions[`Paralyzed`] = {
	Priority = 6;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 0 or 14.4
		Humanoid.JumpPower = Added and 0 or 50
		Humanoid.AutoRotate = not Added

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`Freeze`] = {
	Priority = 5;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 0 or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`Slow`] = {
	Priority = 3;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 5 or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`Attacking`] = {
	Priority = 2;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 10 or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`SkillInUse`] = {
	Priority = 3;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end
		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`NoParry`] = {
	Priority = 1;
	CallBack = function(Character: Model, Added: boolean?)
	end;
}

StateFunctions[`Knockback`] = {
	Priority = 4;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

--| Downed / Carry / Grip (see Services.Features.Downed) |--

local function LockMovement(Character: Model, Added: boolean?)
	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	Humanoid.WalkSpeed = Added and 0 or 14.4
	Humanoid.JumpPower = Added and 0 or 50
	Humanoid.AutoRotate = not Added

	if Added then
		Humanoid:SetAttribute(`Sprint`, false)
	end
end

-- Downed characters crawl slowly and can't jump.
StateFunctions[`Downed`] = {
	Priority = 10;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local DownedConfig = require(ReplicatedStorage.Config.Downed)
		Humanoid.WalkSpeed = Added and DownedConfig.CrawlSpeed or 14.4
		Humanoid.JumpPower = Added and 0 or 50
		Humanoid.AutoRotate = true

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}
StateFunctions[`Carried`] = { Priority = 11; CallBack = LockMovement }
StateFunctions[`Gripped`] = { Priority = 11; CallBack = LockMovement }
StateFunctions[`Gripping`] = { Priority = 9; CallBack = LockMovement }
StateFunctions[`InActivity`] = { Priority = 9; CallBack = LockMovement } -- sitting a class minigame

StateFunctions[`Carrying`] = {
	Priority = 3;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local DownedConfig = require(ReplicatedStorage.Config.Downed)
		Humanoid.WalkSpeed = Added and DownedConfig.CarryWalkSpeed or 14.4
		Humanoid.JumpPower = Added and 0 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
		end
	end;
}

StateFunctions[`FlashStep`] = {
	Priority = 7;
	CallBack = function(Character: Model, Added: boolean?)
		local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Added and 40 or 14.4
		Humanoid.JumpPower = Added and 50 or 50

		if Added then
			Humanoid:SetAttribute(`Sprint`, false)
			-- RagdollController.Ragdoll(Character, Added)
		end
	end;
}

return Shared
