
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
local AirCombat = require(ServerStorage.Packages.AirCombat) -- (2.19.0)

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

	-- (2.19.0) a downslam: hang through the wind-up, then dive straight down so the fist meets the ground on the hit
	-- frame, curving onto someone close in front (Config.Weapons.Fist.AerialHeavy). It used to glide forward at 30
	-- studs a second until it landed (DownSlamUp), 11 to 30 studs from where you jumped.
	local AH = Config.AerialHeavy
	local Fallback = not AH
	if Fallback then
		Packets.Replicate:Fire(`Velocity`, `DownSlamUp`, { User = self.Character, Time = (AerialHit / AerialSpeed) * 1.8 })
	else
		local DiveAt = AH.DiveAt / AerialSpeed
		local HitAt = AerialHit / AerialSpeed
		local Hover = LinearVelocity.new(self.Character, `AerialHover`)
		Hover.MaxForce = Vector3.new(1, 1, 1) * 1e5 -- hold still in the air for the wind-up
		Hover.Velocity = Vector3.zero
		Hover:SendToClients({ Remove = DiveAt })
		task.delay(DiveAt, function()
			if self.Track ~= Track then return end
			local Dive = LinearVelocity.new(self.Character, `AerialDive`)
			Dive.MaxForce = Vector3.new(1, 1, 1) * 1e5
			local Window = math.max(0.08, HitAt - DiveAt)
			local P = RaycastParams.new()
			P.FilterType = Enum.RaycastFilterType.Exclude
			P.FilterDescendantsInstances = { workspace.Live, workspace:FindFirstChild(`Visuals`) or self.Character }
			local Ray = workspace:Raycast(RootPart.Position, Vector3.new(0, -80, 0), P)
			local Drop = if Ray then RootPart.Position.Y - Ray.Position.Y - 3 else AH.Dive * Window
			local Down = -math.clamp(Drop / Window, AH.Dive, 170)
			-- soft aim: someone on the ground ahead of you (within MaxForward studs) -> land right in front of them
			local Best, BestD = nil, AH.MaxForward
			local Look = RootPart.CFrame.LookVector * Vector3.new(1, 0, 1)
			for _, Other in workspace.Live:GetChildren() do
				local OR = Other ~= self.Character and Other:FindFirstChild(`HumanoidRootPart`)
				local OH = OR and Other:FindFirstChildWhichIsA(`Humanoid`)
				if OH and OH.Health > 0 then
					local D = (OR.Position - RootPart.Position) * Vector3.new(1, 0, 1)
					if D.Magnitude < BestD and (D.Magnitude < 2 or (Look.Magnitude > 0 and Look.Unit:Dot(D.Unit) > 0.4)) then Best, BestD = D, D.Magnitude end
				end
			end
			if Best and BestD > 3.5 then -- land 3 studs short of them (closer, and the two bodies shove apart)
				Dive.Velocity = Best.Unit * ((BestD - 3) / Window) + Vector3.new(0, Down, 0)
			else
				Dive.Velocity = Vector3.new(0, Down, 0) -- straight down: no forward carry
			end
			Dive:SendToClients({ Remove = Window + 0.02 }) -- ends as the fist lands: no carry past it
		end)
		task.delay(HitAt, function()
			-- landed: stop dead (no sliding on with the dive's speed) and hold still for the rest of the clip
			LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialDive`)
			if self.Track ~= Track then return end
			local Land = LinearVelocity.new(self.Character, `AerialLand`)
			Land.MaxForce = Vector3.new(1, 0, 1) * 1e5
			Land.Velocity = Vector3.zero
			Land:SendToClients({ Remove = 0.25 })
			StateManager.CreateState(self.Character, `Freeze`, math.max(0.05, AerialEndLag - HitAt))
		end)
	end

	local HitBox = HitBoxService.New()
	HitBox.CFrame = RootPart
	HitBox.Size = Config.Size or vector.create(6, 10, 7)

	HitBox.Params = OverlapParams.new()
	HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
	HitBox.Params.FilterDescendantsInstances = {self.Character}

	HitBox.Offset = AH and AH.Offset or Config.Offset or CFrame.new(0, 0, -3.5)
	if AH and AH.Size then HitBox.Size = AH.Size end -- (2.19.0) the slam's box reaches the ground under you
	HitBox.HitBoxDetection = `Default`

	self.HitBox = HitBox
	self.Connection = AnimMarkers.Reached(Track, function(Name: 'Hit' | 'EndLag')
		if Name == `Hit` then
			if StateManager.HasState(self.Character, 'Stun') then
				return
			end

			HitBox:Go()
			if AH then task.delay(0.07, function() if self.HitBox == HitBox then HitBox:Go() end end) end -- (2.19.0) a target the dive lands on a frame late
			if Fallback then Packets.Replicate:Fire(`Velocity`, `DownSlamDown`, { User = self.Character, Time = AerialEndLag - AerialHit }) end

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

			Damage = if AH then Config.Damage * AH.DamageMult else Config.Damage; -- (2.19.0) the slam hits like a heavy
			LinearVelocity = AH and table.clone(AH.Knockback) or { Velocity = 4; Duration = .1 };
			Posture = AH and AH.Posture or nil;
			Heavy = AH and true or nil;

			Stun = AH and AH.Stun or nil;
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
	if Fallback then StateManager.CreateState(self.Character, `Freeze`, AerialEndLag) end -- (2.19.0) the slam holds you itself

	task.wait(AerialEndLag)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialHover`) -- (2.19.0)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialDive`)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialLand`)

	if self.Connection then self.Connection:Disconnect(); self.Connection = nil end
	if self.Touched then self.Touched:Disconnect(); self.Touched = nil end
	if self.HitBox then self.HitBox:Destroy(); self.HitBox = nil end
end
