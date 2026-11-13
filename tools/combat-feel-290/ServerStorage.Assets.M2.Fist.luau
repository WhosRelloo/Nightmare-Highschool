
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local AnimMarkers = require(game:GetService(`ServerStorage`).Packages.AnimMarkers) -- marker fallbacks (Fist)

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local DamageLogic = require(ServerStorage.Packages.DamageLogic)

local HitBoxService = require(ServerStorage.Packages.HitBox)
local Aerial = require(script[`Aerial Fist`])
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

local ENDLAG_COOLDOWNS = 3

return function (self: ActionManager, Paramaters: { Aerial: boolean; Running: boolean })
	local Weapon = script.Name
	local Config = WeaponsConfig[Weapon]
	
	if not Config then 
		return
	end
	
	if Paramaters.Aerial then
		-- in the air: the aerial heavy, or nothing while it cools down (it used to fall through to a ground M2 mid-air)
		if not self.Cooldowns[`Aerial M2`] then Aerial(self) end
		return
	end
	
	local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	local Track = TrackService.Play(Config.Animations.M2, self.Character, `Attack`, 0.12) -- eased in
	Track:SetPriority(Enum.AnimationPriority.Action4) -- above the stance and walk loops, so the whole crit reads
	
	Packets.Replicate:Fire(`Indicators`, `CriticalIndicator`, {
		User = self.Character;
	})
	local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) nil without a marker = an endless Freeze
	local SwingRate = (Track.Track and Track.Track.Speed) or 1
	self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (AnimMarkers.Time(Track, 'Hit') or 0.3) / (if SwingRate > 0 then SwingRate else 1)) -- (feel set)
	self.Track = Track
	-- (audit) the cooldown starts with the swing (EndLag + the extra), so an interrupted heavy still cools down
	self:Cooldown(`M2`, EndLag + ENDLAG_COOLDOWNS)
	
	local HitBox = HitBoxService.New()
	local RootPart = Humanoid.RootPart
	
		HitBox.CFrame = RootPart
		HitBox.Size = Config.Size or vector.create(6, 10, 7)

		HitBox.Params = OverlapParams.new()
		HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
		HitBox.Params.FilterDescendantsInstances = {self.Character}

		HitBox.Offset = Config.Offset or CFrame.new(0, 0, -3.5)
		HitBox.HitBoxDetection = `Default`

	self.HitBox = HitBox
	self.Connection = AnimMarkers.Reached(Track, function(Name: 'Hit') 
		if Name == `Hit` then
			if StateManager.HasState(self.Character, 'Stun') then
				return
			end
			
			-- (audit) the critical indicator already fired when the swing started (it showed twice)
			HitBox:Go()
		end

	end)
	
	self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
		if not self.Character then self.HitBox:Disconnect(); self.HitBox = nil end

		local DamageData = {

			--| Entities |--

			Character = self.Character;
			Target = Humanoid.Parent;

			--| Stats |--

			Damage = Config.Damage * 1.3;
			LinearVelocity = { Velocity = 100; Duration = .1 };

			Stun = 1;
			StunLocked = false;

			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };
		} :: DamageLogic.DamageData

		if not DamageLogic.Processed(DamageData) then
			return 
		end

		DamageLogic.TakeAction(DamageData)
	end)
	
	StateManager.CreateState(self.Character, `Attacking`, EndLag)
	StateManager.CreateState(self.Character, `Freeze`, EndLag)
	
	task.wait(EndLag)
	
	if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
	if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
	if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
end
