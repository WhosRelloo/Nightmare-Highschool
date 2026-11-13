
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

-- (combat B10) the charged heavy: keep M2 held and the wind-up holds there and charges in three steps
local CHARGE_AT = 0.12 -- seconds into the swing where the pose holds
local CHARGE_STEP = 0.4 -- per step
local CHARGE_MAX = 1.2 -- three steps
local function Holding(self): boolean
	return self.M2Held == true and os.clock() - (self.M2LastPacket or 0) < 0.25
end

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

	-- (combat B10) still holding M2 just into the wind-up: the swing holds there and charges (0.4 s a step, up to three).
	-- Each step adds 15% damage and guard damage; the third breaks a guard outright. A tap swings as before. You can be
	-- counter-hit while charging (the wind-up window stays open).
	local Level = 0
	if Holding(self) then
		task.wait(CHARGE_AT)
		local Raw = Track.Track
		if Raw and Holding(self) then
			local Speed = Raw.Speed
			Raw:AdjustSpeed(0)
			self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + CHARGE_MAX + 0.5)
			StateManager.CreateState(self.Character, `Freeze`, CHARGE_MAX + 0.1)
			local Start = os.clock()
			while Holding(self) and os.clock() - Start < CHARGE_MAX + 0.02 do
				local L = math.min(3, math.floor((os.clock() - Start) / CHARGE_STEP + 1e-6))
				if L > Level then
					Level = L
					Packets.Replicate:Fire(`Misc`, `Charge`, { User = self.Character; Level = L })
				end
				task.wait()
			end
			-- the step reached, counted once more after the loop (its last frame can land just past a step)
			local Final = math.min(3, math.floor(math.min(os.clock() - Start, CHARGE_MAX) / CHARGE_STEP + 1e-6))
			if Final > Level then
				Level = Final
				Packets.Replicate:Fire(`Misc`, `Charge`, { User = self.Character; Level = Final })
			end
			StateManager.RemoveAllStates(self.Character, `Freeze`)
			Raw:AdjustSpeed(if Speed > 0 then Speed else 1)
			local HitAt = (AnimMarkers.Time(Track, 'Hit') or 0.3) / (if SwingRate > 0 then SwingRate else 1)
			self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + math.max(0.05, HitAt - CHARGE_AT))
		end
	end
	
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

			Damage = Config.Damage * 1.3 * (1 + 0.15 * Level); -- (combat B10) +15% a charge step
			LinearVelocity = { Velocity = 100; Duration = .1 };

			Stun = 1;
			StunLocked = false;

			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };

			-- (combat B10) a charged heavy: more guard damage each step; the full charge breaks a guard outright
			Posture = if Level > 0 then 20 + 15 * Level else nil;
			InstantPostureBreak = Level >= 3;
			Tag = if Level >= 3 then `FULL CHARGE` elseif Level > 0 then `CHARGED` else nil;
			Heavy = true;
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
