
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local AnimMarkers = require(game:GetService(`ServerStorage`).Packages.AnimMarkers) -- marker fallbacks (Fist)

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local Packets = require(ReplicatedStorage.Remotes.Packets)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local HitBoxService = require(ServerStorage.Packages.HitBox)

local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local bLua = require(ReplicatedStorage.Packages.bLua)

local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)

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

local ENDLAG_COOLDOWNS = 2

local function PersonalAction(self: ActionManager)
	local Player = Players:GetPlayerFromCharacter(self.Character)

	local Hit = (AnimMarkers.Time(self.Track, `Hit`) or 0.3) :: number -- (audit) nil without a marker
	local Speed = self.Track.Track.Speed :: number
	if not Speed or Speed <= 0 then Speed = 1 end -- (audit) never divide by 0

	local Paramaters = {
		Time = Hit / Speed;
	}

	if Player then
		Packets.Replicate:FireClient(Player, `Shared`, `Aerial M2`, Paramaters)  
		return 
	end 

	require(ReplicatedStorage.Functions.EmitManager.Shared.M2[`Aerial M2`]) (self.Character, Paramaters)
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


	local Track = TrackService.Play(Config.Animations.AerialM2 or Config.Animations.M2, self.Character, `Attack`, 0)
	Track:SetSpeed(1)

	LinearVelocity.StopTaggedBodyMovers(self.Character, `LongJump`)
	TrackService.StopTaggedTracks(self.Character, `Jump`)

	self.Track = Track

	local AerialEndLag = AnimMarkers.Time(Track, `EndLag`) or 1 -- (audit) nil without a marker (1 = the fallback the cooldown below already used)
	-- Known bug #8: the gate in Assets.M2.<Weapon> checks `Aerial M2` (this used script.Name, at the EndLag marker, so it never closed)
	self:Cooldown(`Aerial M2`, (AerialEndLag or 1) + ENDLAG_COOLDOWNS)
	local AerialHit = AnimMarkers.Time(Track, `Hit`) or 0.3 -- (audit) nil without a marker
	local AerialSpeed = if Track.Track.Speed > 0 then Track.Track.Speed else 1 -- (audit) never divide by 0

	Packets.Replicate:Fire(`Velocity`, `DownSlamUp`, { User = self.Character, Time = (AerialHit / AerialSpeed) * 1.8 })

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
			if StateManager.HasState(self.Character, 'Stun') then
				return
			end

			HitBox:Go()
			Packets.Replicate:Fire(`Velocity`, `DownSlamDown`, { User = self.Character, Time = AerialEndLag - AerialHit })

			Packets.Replicate:Fire(`Misc`, `DownSlam`, { User = self.Character })



		end

		if Name == `EndLag` then
			-- (the Aerial M2 cooldown is set when the move starts; this marker raced the end-of-move disconnect)
		end
	end)

	self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
		if not self.Character then self.HitBox:Disconnect(); self.HitBox = nil end

		local DamageData = {

			--| Entities |--

			Character = self.Character;
			Target = Humanoid.Parent;

			--| Stats |--

			Damage = Config.Damage;
			LinearVelocity = { Velocity = 4; Duration = .1 };

			Stun =  nil;
			StunLocked = false;

			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };
		} :: DamageLogic.DamageData

		if not DamageLogic.Processed(DamageData) then
			return 
		end

		DamageLogic.TakeAction(DamageData)
	end)

	PersonalAction(self)

	StateManager.CreateState(self.Character, `Attacking`, AerialEndLag)
	StateManager.CreateState(self.Character, `Freeze`, AerialEndLag)

	task.wait(AerialEndLag)

	if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
	if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
	if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
end
