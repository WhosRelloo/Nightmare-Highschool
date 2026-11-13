--[[
	Ender (server): the fist string enders (fist moveset 2.10, concept 6). ActionManager's M2 handler (Local.TryEnder)
	starts one right after hit 1, 2 or 3 of the string lands; it cancels that swing's recovery.
	  BodyBlow  after hit 3: a hook to the ribs. Clean, it doubles them over (1 s stun); into a guard it's +35 posture.
	  Shove     after hit 1: knocks them well away to open space.
	The launcher after hit 2 is the Uppercut action itself. All share M2's cooldown (an ender is the string's heavy).
	(2.12) Bespoke clips: Fist.Moves.BodyBlow / Fist.Moves.Shove, at speed 1. Each starts on its M1's pose (M1.3 at 0.40 s,
	M1.1 at 0.45 s) and ends on the fist idle, slides included. Hit / EndLag are keyframe names (AnimMarkers). While a
	Moves id is empty (not published yet) the old stand-in plays: Fist M1.3 / M1.4 at the Speed below.
]]
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerStorage = game:GetService(`ServerStorage`)

local AnimMarkers = require(ServerStorage.Packages.AnimMarkers)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)
local DamageLogic = require(ServerStorage.Packages.DamageLogic)
local HitBoxService = require(ServerStorage.Packages.HitBox)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Trails = require(ServerStorage.Packages.Trails)

local ENDER_COOLDOWN = 2.5

local KINDS = {
	BodyBlow = { Anim = `BodyBlow`; Clip = `3`; Speed = 0.95; Tag = `BODY BLOW`; Tell = true;
		Hit = { DamageMult = 1.2; Posture = 35; States = { Stun = 1 }; LinearVelocity = { Velocity = 8; Duration = 0.15 }; React = `1`; Heavy = true } };
	Shove = { Anim = `Shove`; Clip = `4`; Speed = 1.1; Tag = `SHOVE`;
		Hit = { DamageMult = 0.34; Posture = 10; Stun = 0.6; States = { Stun = 0.6 }; LinearVelocity = { Velocity = 70; Duration = 0.25 } } };
}

-- the bespoke clip at speed 1, or the stand-in at its speed while the bespoke one isn't published
local function Clip(Def)
	local Fist = ReplicatedStorage.Assets.Animations.Weapons.Fist
	local Moves = Fist:FindFirstChild(`Moves`)
	local A = Moves and Moves:FindFirstChild(Def.Anim)
	if A and A.AnimationId ~= `` then return A, 1 end
	return Fist.M1[Def.Clip], Def.Speed
end

local function Cleanup(self)
	Trails.Disable(self.Character)
	if self.Connection then self.Connection:Disconnect() self.Connection = nil end
	if self.Touched then self.Touched:Disconnect() self.Touched = nil end
	if self.HitBox then self.HitBox:Destroy() self.HitBox = nil end
end

return {
	Activate = function(self, Kind: string)
		local Def = KINDS[Kind]
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`)
		if not (Def and Humanoid and Humanoid.RootPart) then return end
		local Config = WeaponsConfig.Fist
		self:Cooldown(`M2`, ENDER_COOLDOWN)

		local Anim, Speed = Clip(Def)
		-- the bespoke clip starts on the swing's committed pose; the short fade covers an ender thrown a little early or late
		local Track = TrackService.Play(Anim, self.Character, `Attack`, Speed == 1 and 0.08 or 0.05)
		Track:SetPriority(Enum.AnimationPriority.Action4)
		Track:SetSpeed(Speed)
		self.Track = Track
		Trails.Enable(self.Character)
		if Def.Tell then Packets.Replicate:Fire(`Indicators`, `CriticalIndicator`, { User = self.Character }) end

		local Rate = (Track.Track and Track.Track.Speed) or Speed
		if Rate <= 0 then Rate = 1 end
		local EndLag = (AnimMarkers.Time(Track, `EndLag`) or 0.5) / Rate
		-- its wind-up can be counter-hit like any swing (DamageLogic.TakeAction)
		self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + (AnimMarkers.Time(Track, `Hit`) or 0.35) / Rate)

		local HitBox = HitBoxService.New()
		HitBox.CFrame = Humanoid.RootPart
		HitBox.Size = Config.Size or vector.create(5, 8, 6)
		HitBox.Offset = Config.Offset or CFrame.new(0, 0, -2.8)
		HitBox.Params = OverlapParams.new()
		HitBox.Params.FilterType = Enum.RaycastFilterType.Exclude
		HitBox.Params.FilterDescendantsInstances = { self.Character }
		HitBox.HitBoxDetection = `Default`
		self.HitBox = HitBox

		self.Connection = AnimMarkers.Reached(Track, function(Name: string)
			if Name == `Hit` and not StateManager.HasState(self.Character, { `Stun`, `ParryStun` }) then HitBox:Go() end
		end)
		self.Touched = HitBox.Touched:Connect(function(_, Hum: Humanoid?)
			if not (self.Character and Hum) then return end
			local H = Def.Hit
			local DamageData = {
				Character = self.Character; Target = Hum.Parent;
				Damage = Config.Damage * H.DamageMult; Posture = H.Posture;
				Stun = H.Stun; StunLocked = false;
				States = table.clone(H.States);
				LinearVelocity = table.clone(H.LinearVelocity);
				React = H.React; Tag = Def.Tag; Heavy = H.Heavy;
			}
			if not DamageLogic.Processed(DamageData) then return end
			DamageLogic.TakeAction(DamageData)
		end)

		StateManager.CreateState(self.Character, `Attacking`, EndLag)
		StateManager.CreateState(self.Character, `Freeze`, EndLag)
		task.wait(EndLag)
		Cleanup(self)
	end;

	OnCancel = function(self)
		Cleanup(self)
		if self.Track then self.Track:Destroy() self.Track = nil end
		StateManager.RemoveAllStates(self.Character, `Attacking`)
		StateManager.RemoveAllStates(self.Character, `Freeze`)
		self.Character:SetAttribute(`NHWindupUntil`, nil)
	end;

	Conditions = function(self)
		local Humanoid = self.Character:FindFirstChildWhichIsA(`Humanoid`)
		if not (Humanoid and Humanoid:GetAttribute(`Equip`)) then return false end
		return not StateManager.HasState(self.Character, { `Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `SkillInUse` })
	end;

	Class = `Attack`;
}
