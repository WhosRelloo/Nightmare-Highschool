
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local AnimMarkers = require(game:GetService(`ServerStorage`).Packages.AnimMarkers) -- marker fallbacks (Fist)
local LinearVelocity = require(game:GetService(`ReplicatedStorage`).Functions.LinearVelocity)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local Packets = require(ReplicatedStorage.Remotes.Packets)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local HitBoxService = require(ServerStorage.Packages.HitBox)

local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local bLua = require(ReplicatedStorage.Packages.bLua)

local Trails = require(ServerStorage.Packages.Trails)


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

	Linear: VectorForce;
	Track: Animation;

	HitBox: HitBoxService.HitBoxProperties;
	Touched: HitBoxService.HitBoxConnection;
}

---| Action |---

local ENDLAG_COOLDOWNS = 8

local function PersonalAction(self: ActionManager)
	local Player = Players:GetPlayerFromCharacter(self.Character)

	local Hit = (AnimMarkers.Time(self.Track, `Hit`) or 0.3) :: number -- (audit) nil without a marker
	local Speed = self.Track.Track.Speed :: number
	if not Speed or Speed <= 0 then Speed = 1 end -- (audit) never divide by 0

	local Paramaters = {
		Time = Hit / Speed;
		Speed = self.RunSpeed;
	}
	self.RunSpeed = nil

	if Player then
		Packets.Replicate:FireClient(Player, `Shared`, script.Name, Paramaters)  
		return 
	end 

	require(ReplicatedStorage.Functions.EmitManager.Shared.M1[script.Name]) (self.Character, Paramaters)
end

return function (self: ActionManager)
	local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local Profile = EntityManager.GetProfile(self.Character)
	if not Profile then return end

	local RootPart = Humanoid.RootPart
	local Weapon = Profile.Weapon

	local Config = WeaponsConfig[Weapon]
	if not Config then return end

	local Track = TrackService.Play(Config.Animations.RunningM1, self.Character, `Attack`, 0)
	Track:SetPriority(Enum.AnimationPriority.Action3)
	self.Track = Track
	Trails.Enable(self.Character)

	local EndLag = AnimMarkers.Time(Track, `EndLag`) or 0.6 -- (audit) nil without a marker = an endless Freeze / Attacking
	local Hit = AnimMarkers.Time(Track, `Hit`)
	-- per-weapon running attack (Config.RunningAttack): carry your sprint into the swing
	local RA = Config.RunningAttack
	self.RunSpeed = nil
	local Rate = if Track.Track.Speed > 0 then Track.Track.Speed else 1
	self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (Hit or 0.3) / Rate) -- (feel set) counter-hit window
	if RA then
		local Until = (Hit or 0.3) / Rate
		self.RunSpeed = RA.Lunge -- the shared running lunge carries it (stops at whoever is in front)
	end

	local HitBox = HitBoxService.New()
	HitBox.CFrame = RootPart
	HitBox.Size = Config.Size or vector.create(6, 10, 7)

	HitBox.Params = OverlapParams.new()
	HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
	HitBox.Params.FilterDescendantsInstances = {self.Character}

	HitBox.Offset = CFrame.new(0, 0, -3.5)
	HitBox.HitBoxDetection = `Default`

	self.HitBox = HitBox
	self.Connection = AnimMarkers.Reached(Track, function(Name: 'Hit' | 'EndLag') 
		if Name == `Hit` then
			if StateManager.HasState(self.Character, {'Stun', 'ParryStun'}) then
				return
			end

			HitBox:Go()
			if RA then -- a second sweep a beat later so a fast lunge can't skip past the target
				LinearVelocity.StopTaggedBodyMovers(self.Character, `RunLunge`)
				task.delay(0.07, function() if self.HitBox == HitBox then HitBox:Go() end end)
			end
		end

		if Name == `EndLag` then
			self:Cooldown(script.Name, ENDLAG_COOLDOWNS)

		end

	end)

	self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
		if not self.Character then return end -- (combat audit) HitBox has no Disconnect: this line used to error

		local DamageData = {

			--| Entities |--

			Character = self.Character;
			Target = Humanoid.Parent;

			--| Stats |--

			Damage = if RA then Config.Damage * RA.DamageMult else Config.Damage;
			Posture = RA and RA.Posture or nil;
			LinearVelocity = RA and RA.Knockback or { Velocity = 4; Duration = .1 };

			Stun = RA and RA.Stun or nil;
			StunLocked = false;

			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };
		} :: DamageLogic.DamageData

		if not DamageLogic.Processed(DamageData) then
			return 
		end

		DamageLogic.TakeAction(DamageData)
	end)

	PersonalAction(self)

	StateManager.CreateState(self.Character, `Attacking`, EndLag)
	if RA then
		-- moving through the wind-up, planted only for the recovery after the hit
		local HitAt = (Hit or 0.3) / Rate
		task.delay(HitAt, function()
			if self.Track == Track then StateManager.CreateState(self.Character, `Freeze`, math.max(0.05, EndLag - HitAt)) end
		end)
	else
		StateManager.CreateState(self.Character, `Freeze`, EndLag)
	end

	task.wait(EndLag)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `RunLunge`)

	Trails.Disable(self.Character)


	if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
	if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
	if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
end
