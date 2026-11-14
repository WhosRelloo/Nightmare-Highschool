
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local RunService = game:GetService(`RunService`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)

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

	Connection: RBXScriptConnection;
	Track: Animation;

	HitBox: HitBoxService.HitBoxProperties;
	Touched: HitBoxService.HitBoxConnection;
}

---| Action |---

local BLOCK_COOLDOWN = .1
local PARRY_LOCKOUT = .5 -- (combat audit) after a parry window that caught nothing, the next press guards without one

return {

	Activate = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local RootPart = Humanoid.RootPart
		local CharacterProfile = EntityManager.GetProfile(self.Character)
		local Weapon = CharacterProfile and CharacterProfile.Weapon 
		local Config = WeaponsConfig[Weapon]
		if not Config then return end

		self.BlockStartedAt = os.clock() -- (combat B7) a delayed 4th hit goes through a guard raised early
		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParry`)
		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParryExhausted`)

		local Animations = 
			Config.Animations 
			or 
			{
				Block = ReplicatedStorage.Assets.Animations.Weapons.Fist.Block;
				Parry = ReplicatedStorage.Assets.Animations.Weapons.Fist.ParryAttempt;
			}

		-- (combat audit) parry spam: mashing block re-opened a fresh 0.25 s parry window every 0.35 s (~70% of the time
		-- parrying). A window now locks the next one out for PARRY_LOCKOUT after it closes; you still guard at once. A parry
		-- that lands lifts the lock (DamageLogic.Parry).
		local Token = {}
		self.BlockToken = Token
		local Now = os.clock()
		if Now >= (self.ParryLockUntil or 0) then
			self.ParryLockUntil = Now + 0.25 + PARRY_LOCKOUT
			local Parry = TrackService.Play(Animations.Parry, self.Character, `Parry`, 0.08)
			Parry:SetPriority(Enum.AnimationPriority.Action4)
			TagService:AddTag(self.Character, `Parry`, .25, true)

			task.wait(.25)
			-- (combat audit) a parry tap that already let go kept running here and flashed the guard pose (and Slow) over
			-- whatever you did next, an M1 for example
			if self.Action ~= `Block` or self.BlockToken ~= Token then return end
		end

		local Block = TrackService.Play(Animations.Block, self.Character, `Block`, 0.12)
		Block:SetPriority(Enum.AnimationPriority.Action2)

		if TrackService.isTaggedPlaying(self.Character, `Parry`) then
			TrackService.StopTaggedTracks(self.Character, `Parry`, 0.15)
		end
		StateManager.CreateState(self.Character, `Slow`)

		repeat
			RunService.Heartbeat:Wait()
		until self.Action ~= `Block`

		TrackService.StopTaggedTracks(self.Character, `Block`)
		StateManager.RemoveState(self.Character, `Slow`)

		self:Cooldown(script.Name, BLOCK_COOLDOWN)
	end;

	Release = function(self: ActionManager)
		TrackService.StopTaggedTracks(self.Character, `Parry`, 0.12) -- (combat audit) a parry tap's pose ends with the tap
		if TagService:HasTag(self.Character, {`Parry`}) then
			TagService:RemoveTag(self.Character, `Parry`)

		end

		TrackService.StopTaggedTracks(self.Character, `Block`)
		StateManager.RemoveState(self.Character, `Slow`)
		self:Cooldown(script.Name, BLOCK_COOLDOWN)
	end;

	OnCancel = function(self: ActionManager)
		TrackService.StopTaggedTracks(self.Character, `Parry`, 0.12) -- (combat audit)
		if TagService:HasTag(self.Character, {`Parry`}) then
			TagService:RemoveTag(self.Character, `Parry`)

		end

		TrackService.StopTaggedTracks(self.Character, `Block`)
		StateManager.RemoveState(self.Character, `Slow`)
		self:Cooldown(script.Name, BLOCK_COOLDOWN)
	end;

	Conditions = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if not Humanoid:GetAttribute(`Equip`) :: boolean then
			return
		end

		return not StateManager.HasState(self.Character, {'Ragdoll', 'Paralyzed', 'SkillInUse'})
	end;

	Class = `General`;
}
