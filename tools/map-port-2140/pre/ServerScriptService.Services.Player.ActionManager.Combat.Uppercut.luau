local ReplicatedStorage = game:GetService("ReplicatedStorage")

---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local AnimMarkers = require(game:GetService(`ServerStorage`).Packages.AnimMarkers) -- marker fallbacks (Fist)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)

local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local HitBoxService = require(ServerStorage.Packages.HitBox)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local AirCombat = require(ServerStorage.Packages.AirCombat)

---| Type Annotation |---

type ActionManager = {
	Character: Model | Instance;
	Action: string ?;
	Trove: any;
	Thread: thread;
	Activate: (self: ActionManager, Action: string, ...any) -> (boolean ?);
	Cancel: (self: ActionManager, Action: string) -> (boolean ?);
	CanActivate: (self: ActionManager, Action: string) -> (boolean ?);
	Cooldown: (self: ActionManager, Action: string, Duration: number) -> (ActionManager);
	Destroy: (self: ActionManager) -> ();
	Cooldowns: { [string]: {boolean} ? };
	Tasks: { typeof(task.spawn( function() end) ) };
	Connection: RBXScriptConnection;
	Track: Animation;
	HitBox: HitBoxService.HitBoxProperties;
	Touched: HitBoxService.HitBoxConnection;
	Lunge: any;
}

---| Action |---

local UPPERCUT_COOLDOWN = 1

return {

	Activate = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		local Profile = EntityManager.GetProfile(self.Character)
		if not Profile then return end

		local RootPart = Humanoid.RootPart

		LinearVelocity.StopTaggedBodyMovers(self.Character, `LongJump`)
		LinearVelocity.StopTaggedBodyMovers(self.Character, `UppercutLunge`)
		LinearVelocity.StopTaggedBodyMovers(self.Character, `Dash`)
		TrackService.StopTaggedTracks(self.Character, `Jump`)
		TrackService.StopTaggedTracks(self.Character, `Attack`)

		local Track = TrackService.Play(ReplicatedStorage.Assets.Animations.Default.Uptilt, self.Character, `Attack`, 0)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(1.3)
		
		self.Track = Track

		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 1.2

		local lunge = LinearVelocity.new(self.Character, `UppercutLunge`)
		lunge.MaxForce = Vector3.new(1, 1, 1) * 1e5
		lunge.Vector = `LookVector`
		lunge.Speed = 70

		self.Lunge = lunge

		lunge:SendToClients({
			OnlyClients = true;
			Remove = 0.25;

			Tweens = {
				[1] = {
					Value = `Speed`;
					TweenInfo = TweenInfo.new(0.15, Enum.EasingStyle.Quad, Enum.EasingDirection.Out);
					Target = 0;
				};
			};
		})

		local HitBox = HitBoxService.New()
		HitBox.CFrame = RootPart
		HitBox.Size = vector.create(8, 8, 8)
		HitBox.Params = OverlapParams.new()
		HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
		HitBox.Params.FilterDescendantsInstances = {self.Character}
		HitBox.Offset = CFrame.new(0, 0, -4)
		HitBox.HitBoxDetection = `Default`

		self.HitBox = HitBox



		self.Connection = AnimMarkers.Reached(Track, function(Name: 'Hit' | 'EndLag') 
			if Name == `Hit` then
				if StateManager.HasState(self.Character, {'Stun', 'ParryStun'}) then
					return
				end

				HitBox:Go()
			end

			if Name == `EndLag` then
				self:Cooldown(script.Name, UPPERCUT_COOLDOWN)
			end
		end)

		self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
			if not self.Character then 
				if self.HitBox then self.HitBox:Disconnect(); self.HitBox = nil end
				return
			end

			local Target = Humanoid.Parent

			if TagService:HasTag(Target, `InAir`) then
				return
			end

			if StateManager.HasState(Target, {`Uppercutting`}) then
				return
			end

			local DamageData = {
				Character = self.Character;
				Target = Target;
				Damage = 10;

				Stun = 1.5;
				StunLocked = false;
				States = { Stun = 1.5; };
			} :: DamageLogic.DamageData

			if not DamageLogic.Processed(DamageData) then
				return 
			end

			DamageLogic.TakeAction(DamageData)



			if Target and Target.Parent and not TagService:HasTag(Target, `InAir`) then
				AirCombat.Launch(self.Character, Target)
			end
		end)

		StateManager.CreateState(self.Character, `Attacking`, EndLag)
		StateManager.CreateState(self.Character, `Freeze`, EndLag)
		StateManager.CreateState(self.Character, `Uppercutting`, EndLag)

		task.wait(EndLag)

		if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
		if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
		if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
		if self.Lunge then self.Lunge = nil end
	end;

	OnCancel = function(self: ActionManager)
		StateManager.RemoveState(self.Character, `Attacking`)
		StateManager.RemoveState(self.Character, `Uppercutting`)

		if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
		if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
		if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
		if self.Track then self.Track:Destroy() end

		LinearVelocity.StopTaggedBodyMovers(self.Character, `UppercutLunge`)
		if self.Lunge then 
			self.Lunge = nil 
		end
	end;

	Conditions = function(self: ActionManager)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
		if not Humanoid then return end

		if not Humanoid:GetAttribute(`Equip`) :: boolean then
			return
		end

		if TagService:HasTag(self.Character, `InAir`) then
			return false
		end

		return not StateManager.HasState(self.Character, {'Stun', 'ParryStun', 'Ragdoll', 'Paralyzed', 'Attacking', 'SkillInUse', 'Dodge', 'Sliding', 'Uppercutting'})
	end;

	Class = `Attack`;
}

