
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local bLua = require(ReplicatedStorage.Packages.bLua)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)

local TrackService = require(ReplicatedStorage.Packages.TrackService)

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

function FetchModule(Container: Folder | { ModuleScript }, Name: string, ...)
	local Module = Container:FindFirstChild(Name, true) :: ModuleScript
	if not Module or not Module:IsA(`ModuleScript`) then return end

	local Success, Result = pcall(function()
		return require(Module) or nil
	end)

	if not Success then return end

	if typeof(Result) ~= `function` and Result ~= nil then
		return warn(`M2's Module for {Name} is {typeof(Result)}`)
	end

	return Result(...)
end

return {

	Activate = function(self: ActionManager, Paramaters: { Aerial: boolean; Running: boolean })
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if Paramaters.Aerial and TagService:HasTag(self.Character, `InAir`) then 
			return 
		end

		local CharacterProfile = EntityManager.GetProfile(self.Character)
		if not CharacterProfile then return end

		local RootPart = Humanoid.RootPart
		local Weapon = CharacterProfile.Weapon

		LinearVelocity.StopTaggedBodyMovers(self.Character, `LongJump`)
		TrackService.StopTaggedTracks(self.Character, `Jump`)

		FetchModule(ServerStorage.Assets.M2, Weapon, self, Paramaters)
	end;

	OnCancel = function(self: ActionManager)
		if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
		if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
		if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end

		if self.Track then self.Track:Destroy() end

		StateManager.RemoveAllStates(self.Character, `Attacking`)
		StateManager.RemoveAllStates(self.Character, `Freeze`)

		local Trails = require(ServerStorage.Packages.Trails)
		Trails.Disable(self.Character)
		LinearVelocity.StopTaggedBodyMovers(self.Character, `M2Movement`)
		self.Character:SetAttribute(`NHWindupUntil`, nil) -- (feel set)
	end;

	Conditions = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if not Humanoid:GetAttribute(`Equip`) :: boolean then
			return
		end

		return not StateManager.HasState(self.Character, {'Stun', 'ParryStun', 'Ragdoll', 'Paralyzed', 'SkillInUse'})
	end;

	Class = `Attack`;
}
