
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local AnimMarkers = require(game:GetService(`ServerStorage`).Packages.AnimMarkers) -- marker fallbacks (Fist)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local bLua = require(ReplicatedStorage.Packages.bLua)

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local HitBoxService = require(ServerStorage.Packages.HitBox)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)

local RunningM1 = require(script[`Running M1`])
local AerialM1 = require(script[`Aerial M1`])

local VowManager = require(ServerScriptService.Services.Features.Vow)
local AirCombat = require(ServerStorage.Packages.AirCombat)

local Trails = require(ServerStorage.Packages.Trails)
local Packets = require(ReplicatedStorage.Remotes.Packets)



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

local ENDLAG_COOLDOWNS = 1

return {

	Activate = function(self: ActionManager, Paramaters: { Aerial: boolean; Running: boolean })
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if Paramaters.Aerial and not self.Cooldowns[`Aerial M1`] then AerialM1(self) return end
		if Paramaters.Running and not self.Cooldowns[`Running M1`] then	RunningM1(self) return end

		local Profile = EntityManager.GetProfile(self.Character)
		if not Profile then return end

		local RootPart = Humanoid.RootPart
		local Weapon = Profile.Weapon

		local Config = WeaponsConfig[Weapon]
		if not Config then return end

		local NewCombo = bLua.ComboCounter(
			self.Character:GetAttribute(`Combo`),
			self.Character:GetAttribute(`Tick`),
			Config.MaxCombo,
			1
		)

		self.Character:SetAttribute(`Combo`, NewCombo)
		VowManager.VowAction(self.Character, `Before M1`)

		LinearVelocity.StopTaggedBodyMovers(self.Character, `LongJump`)
		TrackService.StopTaggedTracks(self.Character, `Jump`)

		local LastCombo = NewCombo == Config.MaxCombo :: boolean
		local Track = TrackService.Play(Config.Animations.M1[NewCombo], self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action3)

		if Config.AnimationSpeed then
			Track:SetSpeed(Config.AnimationSpeed)
		end
		Trails.Enable(self.Character)

		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) no marker = nil = an endless Attacking state
		self.Track = Track

		local HitBox = HitBoxService.New()
		HitBox.CFrame = RootPart
		HitBox.Size = Config.Size or vector.create(6, 10, 7)

		HitBox.Params = OverlapParams.new()
		HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
		HitBox.Params.FilterDescendantsInstances = {self.Character}

		HitBox.Offset = Config.Offset or CFrame.new(0, 0, -3.5)
		HitBox.HitBoxDetection = `Default`


		self.HitBox = HitBox
		self.Connection = AnimMarkers.Reached(Track, function(Name: 'Hit' | 'EndLag') 
			if Name == `Hit` then
				if StateManager.HasState(self.Character, {'Stun', 'ParryStun'}) then
					return
				end

				HitBox:Go()
				self.Character:SetAttribute(`Tick`, tick())
			end


			if Name == `EndLag` then
				--self.Character:SetAttribute(`Tick`, tick())

				if not LastCombo then return end

				self:Cooldown(script.Name, ENDLAG_COOLDOWNS)
			end

		end)

		self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
			if not self.Character then 
				if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
				if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
				return
			end

			local Target = Humanoid.Parent

			local inAir = AirCombat.IsActive(self.Character, Target)
			local isFinisher = inAir and AirCombat.CheckFinisher(Target)

			local DamageData = {
				Character = self.Character;
				Target = Target;

				Damage = if isFinisher then Config.Damage * 1.5 else Config.Damage;
				Posture = Config.Posture;
				LinearVelocity = if isFinisher then { Velocity = 80; Duration = .4; UpVector = -1 }
					elseif inAir then { Velocity = 2; Duration = .05 }
					elseif not LastCombo then { Velocity = 4; Duration = .1 } 
					else { Velocity = 60; Duration = .2 };

				Stun = if isFinisher then 2 elseif LastCombo then 1.5 else nil;
				StunLocked = false;

				States = { Stun = if isFinisher then 1.5 else .8 };

				NoAnimation = isFinisher;

				AirPush = inAir and not isFinisher;
				AirDownslam = isFinisher;
			} :: DamageLogic.DamageData

			if not DamageLogic.Processed(DamageData) then
				return 
			end

			VowManager.VowAction(self.Character, `M1`, Humanoid)
			DamageLogic.TakeAction(DamageData)
		end)

		StateManager.CreateState(self.Character, `Attacking`, EndLag)
		task.wait(EndLag)
		Trails.Disable(self.Character)

		if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
		if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
		if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
	end;

	OnCancel = function(self: ActionManager)
		Trails.Disable(self.Character)


		if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
		if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
		if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end

		if self.Track then self.Track:Destroy() end
		-- (audit) a feinted / cancelled M1 also undoes what it set up, like M2's OnCancel: the track reference (the running M1's
		-- delayed Freeze and the aerial dive check it), the lunge / hover / dive movers and its Freeze / Attacking states
		self.Track = nil
		LinearVelocity.StopTaggedBodyMovers(self.Character, `RunLunge`)
		LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialHover`)
		LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialDive`)
		StateManager.RemoveAllStates(self.Character, `Attacking`)
		StateManager.RemoveAllStates(self.Character, `Freeze`)
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
