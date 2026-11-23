
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local Packets = require(ReplicatedStorage.Remotes.Packets)
-- (locomotion-pace) sprint, the fast sprint after FastAfter seconds, and the walk on release (were 25 / 40.5 / 12)
local Speeds = require(ReplicatedStorage.Config.Locomotion).Speeds

---| Type Annotation |---

type  ActionManager = {

	--| Properties |--

	Character: Model | Instance;
	Action: string ?;

	Trove: any;
	Thread: thread;

	Activate: (self: ActionManager, Action: string, ...any) -> (boolean ?);
	Cancel: (self: ActionManager,  Action: string) -> (boolean ?);

	CanActivate: (self: ActionManager, Action: string) -> (boolean ?);
	Cooldown: (self: ActionManager, Action: string, Duration: number) -> (ActionManager);

	Destroy: (self: ActionManager) -> ();

	--| Threads |--

	Cooldowns: { [string]: {boolean} ? };
	Tasks: { typeof(task.spawn( function() end) ) };
}

---| Action |---

return {

	Activate = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Carry = self.Character:GetAttribute(`SprintCarry`) == true -- coming out of a slide
		self.Character:SetAttribute(`SprintCarry`, nil)
		Humanoid.WalkSpeed = if Carry then Speeds.FastSprint else Speeds.Sprint
		Humanoid:SetAttribute(`Sprint`, true)

		local StartTime = if Carry then tick() - Speeds.FastAfter else tick()
		local Packet = Packets.Replicate --:Fire(`Misc`, `FastSprint`, { User = self.Character;  })

		while self.Action == `Sprint` do
			-- (audit) checked first: a stun ends the sprint by clearing this, and the speed below used to be written
			-- once more after it (a stunned player kept moving at the fast sprint)
			if not Humanoid:GetAttribute(`Sprint`) :: boolean then
				break
			end
			local Elapsed = tick() - StartTime

			if Elapsed >= Speeds.FastAfter then
				Humanoid.WalkSpeed = Speeds.FastSprint		
				if Packet then Packet:Fire(`Misc`, `FastSprint`, { User = self.Character;  }); Packet = nil end


			end

			if not Humanoid:GetAttribute(`Sprint`) :: boolean then
				break
			end

			task.wait(.1)
		end
		-- (audit) the speed lines were only removed by Release; a sprint broken by a stun or going down left them on
		if Packet == nil and not Humanoid:GetAttribute(`Sprint`) then
			Packets.Replicate:Fire(`Misc`, `FastSprint`, { User = self.Character; Destroy = true })
		end

		--repeat

		--	Humanoid:GetAttributeChangedSignal(`Sprint`):Wait()
		--	task.wait()
		--until self.Action ~= `Sprint`
	end;

	Release = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Speeds.Walk
		Humanoid:SetAttribute(`Sprint`, false)

		Packets.Replicate:Fire(`Misc`, `FastSprint`, { User = self.Character; Destroy = true })
	end;

	OnCancel = function(self: Optix.SelfAction)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		Humanoid.WalkSpeed = Speeds.Walk
		Humanoid:SetAttribute(`Sprint`, false)

		Packets.Replicate:Fire(`Misc`, `FastSprint`, { User = self.Character; Destroy = true })
	end,

	Conditions = function(self: ActionManager)
		if TagService:HasTag(self.Character, `InAir`) then
			return false
		end

		return not StateManager.HasState(self.Character, {'Stun', 'ParryStun', 'Ragdoll', 'Paralyzed', 'SkillInUse'})
	end;

	Priority = `Low`;
}
