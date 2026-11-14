ENDER = "ServerScriptService.Services.Player.ActionManager.Combat.Ender"
FM2 = "ServerStorage.Assets.M2.Fist"
AFIST = "ServerStorage.Assets.M2.Fist.Aerial Fist"
WEAP = "ReplicatedStorage.Config.Weapons"
IM2 = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M2"

EDITS = [
    # --- the string enders play their whole clip (owner: "The string enders should play out in full too") ---
    (ENDER, """		local Rate = (Track.Track and Track.Track.Speed) or Speed
		if Rate <= 0 then Rate = 1 end
		local EndLag = (AnimMarkers.Time(Track, `EndLag`) or 0.5) / Rate""",
     """		local Rate = (Track.Track and Track.Track.Speed) or Speed
		if Rate <= 0 then Rate = 1 end
		-- (2.19.0) the whole clip plays out: the recovery runs to the end of the clip (less 0.02 s), not to its EndLag
		-- marker (Shove 0.47 of 0.83 s, Body Blow 0.50 of 0.87 s, where the next move used to cut in)
		local Len = Track.Track and Track.Track.Length or 0
		if Len <= 0 then task.wait() Len = Track.Track and Track.Track.Length or 0 end
		local EndLag = math.max(AnimMarkers.Time(Track, `EndLag`) or 0.5, Len - 0.02) / Rate"""),

    # --- the fist heavy in an air combo: a downslam that ends the combo, not a 100 stud/s blast ---
    (FM2, """local Packets = require(ReplicatedStorage.Remotes.Packets)""",
     """local Packets = require(ReplicatedStorage.Remotes.Packets)
local AirCombat = require(ServerStorage.Packages.AirCombat) -- (2.19.0) the heavy in an air combo is a downslam

-- (2.19.0) a downslam's knockback: nearly straight down, with a quarter of it along your facing (DamageLogic adds
-- UpVector to your look vector unless Unit is given, which sent a slammed target 45 degrees off, about 22 studs away)
local function SlamUnit(Character: Model): Vector3
	local L = Character:GetPivot().LookVector * Vector3.new(1, 0, 1)
	if L.Magnitude < 1e-3 then return Vector3.new(0, -1, 0) end
	return (L.Unit * 0.25 + Vector3.new(0, -1, 0)).Unit
end"""),
    (FM2, """	self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
		if not self.Character then self.HitBox:Disconnect(); self.HitBox = nil end

		local DamageData = {

			--| Entities |--

			Character = self.Character;
			Target = Humanoid.Parent;

			--| Stats |--

			Damage = Config.Damage * 1.3 * (1 + 0.15 * Level); -- (combat B10) +15% a charge step
			LinearVelocity = { Velocity = 100; Duration = .1 };""",
     """	self.Touched = HitBox.Touched:Connect(function(Hit: BasePart, Humanoid: Humanoid?)
		if not self.Character then self.HitBox:Disconnect(); self.HitBox = nil end
		-- (2.19.0) in an air combo the heavy slams them back to the ground and ends the combo (like the M1 finisher),
		-- instead of the ground heavy's 100 stud/s shove, which sent them flying off across the map
		local InAir = AirCombat.IsActive(self.Character, Humanoid.Parent)

		local DamageData = {

			--| Entities |--

			Character = self.Character;
			Target = Humanoid.Parent;

			--| Stats |--

			Damage = Config.Damage * 1.3 * (1 + 0.15 * Level); -- (combat B10) +15% a charge step
			-- (the slam: nearly straight down with a small push ahead, not 45 degrees off across the map)
			LinearVelocity = if InAir then { Velocity = 90; Duration = .3; UpVector = -1; Unit = SlamUnit(self.Character) } else { Velocity = 100; Duration = .1 };
			AirDownslam = InAir or nil;
			NoAnimation = InAir or nil;"""),

    # --- the air heavy from a jump: hang, then dive down onto whoever is close (no more 30 stud/s forward glide) ---
    (AFIST, """local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)""",
     """local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local AirCombat = require(ServerStorage.Packages.AirCombat) -- (2.19.0)"""),
    (AFIST, """	Packets.Replicate:Fire(`Velocity`, `DownSlamUp`, { User = self.Character, Time = (AerialHit / AerialSpeed) * 1.8 })
""", """	-- (2.19.0) a downslam: hang through the wind-up, then dive straight down so the fist meets the ground on the hit
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
"""),
    (AFIST, """			HitBox:Go()
			Packets.Replicate:Fire(`Velocity`, `DownSlamDown`, { User = self.Character, Time = AerialEndLag - AerialHit })""",
     """			HitBox:Go()
			if AH then task.delay(0.07, function() if self.HitBox == HitBox then HitBox:Go() end end) end -- (2.19.0) a target the dive lands on a frame late
			if Fallback then Packets.Replicate:Fire(`Velocity`, `DownSlamDown`, { User = self.Character, Time = AerialEndLag - AerialHit }) end"""),
    (AFIST, """	HitBox.Offset = Config.Offset or CFrame.new(0, 0, -3.5)
	HitBox.HitBoxDetection = `Default`""", """	HitBox.Offset = AH and AH.Offset or Config.Offset or CFrame.new(0, 0, -3.5)
	if AH and AH.Size then HitBox.Size = AH.Size end -- (2.19.0) the slam's box reaches the ground under you
	HitBox.HitBoxDetection = `Default`"""),
    (AFIST, """			Damage = Config.Damage;
			LinearVelocity = { Velocity = 4; Duration = .1 };

			Stun =  nil;""", """			Damage = if AH then Config.Damage * AH.DamageMult else Config.Damage; -- (2.19.0) the slam hits like a heavy
			LinearVelocity = AH and table.clone(AH.Knockback) or { Velocity = 4; Duration = .1 };
			Posture = AH and AH.Posture or nil;
			Heavy = AH and true or nil;

			Stun = AH and AH.Stun or nil;"""),
    (AFIST, """	StateManager.CreateState(self.Character, `Attacking`, AerialEndLag)
	StateManager.CreateState(self.Character, `Freeze`, AerialEndLag)""", """	StateManager.CreateState(self.Character, `Attacking`, AerialEndLag)
	if Fallback then StateManager.CreateState(self.Character, `Freeze`, AerialEndLag) end -- (2.19.0) the slam holds you itself"""),
    (AFIST, """	task.wait(AerialEndLag)

	if self.Connection""", """	task.wait(AerialEndLag)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialHover`) -- (2.19.0)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialDive`)
	LinearVelocity.StopTaggedBodyMovers(self.Character, `AerialLand`)

	if self.Connection"""),

    # --- the config: the air heavy's numbers, and its whole clip ---
    (WEAP, """			["rbxassetid://106967014880853"] = { Hit = 0.40; EndLag = 1.10 };""",
     """			["rbxassetid://106967014880853"] = { Hit = 0.40; EndLag = 1.26 }; -- (2.19.0) air heavy: the whole 1.28 s clip"""),
    (WEAP, """		-- downslam: hang through the wind-up, dive at 0.56 s, the fist lands at 0.66 s""", """		-- (2.19.0) the air heavy (R in the air): hang through the wind-up, dive at 0.22 s, the fist lands at 0.40 s, onto
		-- someone up to 7 studs ahead (else straight down), and stop dead there. A heavier slam than the jump punch.
		AerialHeavy = { DiveAt = 0.22; Dive = 80; MaxForward = 7; Offset = CFrame.new(0, -4.5, -2.2); Size = vector.create(8, 13, 8); DamageMult = 1.8; Posture = 25; Stun = 1.4; Knockback = { Velocity = 30; Duration = 0.2; UpVector = -1 } };
		-- downslam: hang through the wind-up, dive at 0.56 s, the fist lands at 0.66 s"""),

    # --- the M2 input: in an air combo it's the combo's heavy (a downslam), not the jump heavy; face the target ---
    (IM2, """local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)""",
     """local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService) -- (2.19.0)"""),
    (IM2, """	local InAir = Humanoid.FloorMaterial == Enum.Material.Air
	-- (combat B10) flags: 1 = aerial, 2 = a new press, 4 = let go (0 = a hold-repeat). Holding charges the Fist heavy.
	pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5)
	local Pressed = false
	if InAir then UnPackets.M2:Fire(3) Pressed = true end""",
     """	local InAir = Humanoid.FloorMaterial == Enum.Material.Air
	-- (2.19.0) in an air combo (after an uppercut) the heavy is the combo's: it isn't the jump heavy, and you turn to
	-- face the one you launched first (as the M1 does), so it lands
	local InAirCombat = TagService:HasTag(Character, `InAir`)
	if InAirCombat then
		pcall(function()
			local Root = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
			local Live = workspace:FindFirstChild(`Live`)
			local Best, BestD = nil, 14
			for _, M in (Live and Live:GetChildren()) or {} do
				local R = M ~= Character and M:FindFirstChild(`HumanoidRootPart`) :: BasePart?
				if R and Root and TagService:HasTag(M, `InAir`) then
					local D = (R.Position - Root.Position).Magnitude
					if D < BestD then Best, BestD = R, D end
				end
			end
			if Best and Root then Root.CFrame = CFrame.lookAt(Root.Position, Vector3.new(Best.Position.X, Root.Position.Y, Best.Position.Z)) end
		end)
	end
	-- (combat B10) flags: 1 = aerial, 2 = a new press, 4 = let go (0 = a hold-repeat). Holding charges the Fist heavy.
	pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5)
	local Pressed = false
	if InAir and not InAirCombat then UnPackets.M2:Fire(3) Pressed = true end"""),
]

M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
EDITS += [
    # the M1 air finisher is the same downslam: nearly straight down, not 45 degrees off
    (M1, """local Packets = require(ReplicatedStorage.Remotes.Packets)
""", """local Packets = require(ReplicatedStorage.Remotes.Packets)

-- (2.19.0) the air finisher's knockback: nearly straight down with a quarter of it along your facing (DamageLogic adds
-- UpVector to your look vector unless Unit is given, which sent a slammed target 45 degrees off, about 22 studs away)
local function SlamUnit(Character: Model): Vector3
	local L = Character:GetPivot().LookVector * Vector3.new(1, 0, 1)
	if L.Magnitude < 1e-3 then return Vector3.new(0, -1, 0) end
	return (L.Unit * 0.25 + Vector3.new(0, -1, 0)).Unit
end
"""),
    (M1, """				LinearVelocity = if isFinisher then { Velocity = 80; Duration = .4; UpVector = -1 }""",
     """				LinearVelocity = if isFinisher then { Velocity = 90; Duration = .3; UpVector = -1; Unit = SlamUnit(self.Character) } -- (2.19.0)"""),
]
