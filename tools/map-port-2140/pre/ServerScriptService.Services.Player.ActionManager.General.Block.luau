
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

return {

	Activate = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local RootPart = Humanoid.RootPart
		local CharacterProfile = EntityManager.GetProfile(self.Character)
		local Weapon = CharacterProfile and CharacterProfile.Weapon 
		local Config = WeaponsConfig[Weapon]
		if not Config then return end

		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParry`)
		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParryExhausted`)

		local Animations = 
			Config.Animations 
			or 
			{
				Block = ReplicatedStorage.Assets.Animations.Weapons.Fist.Block;
				Parry = ReplicatedStorage.Assets.Animations.Weapons.Fist.ParryAttempt;
			}

		local Parry = TrackService.Play(Animations.Parry, self.Character, `Parry`, 0.08)
		Parry:SetPriority(Enum.AnimationPriority.Action4)
		TagService:AddTag(self.Character, `Parry`, .25, true)

		task.wait(.25)

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
		if TagService:HasTag(self.Character, {`Parry`}) then
			TagService:RemoveTag(self.Character, `Parry`)

		end

		TrackService.StopTaggedTracks(self.Character, `Block`)
		StateManager.RemoveState(self.Character, `Slow`)
		self:Cooldown(script.Name, BLOCK_COOLDOWN)
	end;

	OnCancel = function(self: ActionManager)
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
