
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local ServerStorage = game:GetService(`ServerStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local TagService = require(ReplicatedStorage.Packages.Core.TagService)

local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local bLua = require(ReplicatedStorage.Packages.bLua)

local TrackService = require(ReplicatedStorage.Packages.TrackService)
local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
local _Cache = require(ReplicatedStorage.Packages.Core._Local).new(`AirWeld`)

local Packets = require(ReplicatedStorage.Remotes.Packets)
local AirCombat = require(ServerStorage.Packages.AirCombat)
local AirWeld = require(ServerStorage.Services.AirWeld)
local HitReacts = ReplicatedStorage.Assets.Animations.Default.Hit:GetChildren()

local EntityManager = require(ServerScriptService.Services.Managers.EntityLoader)
local AI = require(ServerScriptService.Services.AI.AI)
local Downed = require(ServerScriptService.Services.Features.Downed)

---| Type Annotation |---

export type DamageData = {

	--| Entities |--

	Character: Model;
	Target: Model;

	--| Stats |--

	Damage: number;
	Posture: number?;
	InstantPostureBreak: boolean?;
	LinearVelocity: { Velocity: number; Duration: number; UpVector: number ? } ?;

	Stun: number ?;
	StunLocked: boolean ?;

	OnHit: (Data: DamageData) -> () ?;
	NoAnimation: boolean ?;

	States: { [string]: number } ?;
	IgnoreStates: { Ragdoll: boolean; IFrames: boolean; Block: boolean } ?;
	AirPush: boolean ?;
	AirDownslam: boolean ?;
	AirWeld: boolean ?;
}

local Local = {}
local MAX_REACH = 30 -- studs between attacker and target for a player's hit to count
local COUNTER_STUN = 1.5 -- (feel set) a counter-hit stuns half as long again
local Shared = {}

-- (feel set) the hit reaction follows where the hit came from. The four clips in Default.Hit, measured from their
-- keyframes: 1 and 2 double over forward (hips shift to the body's left / right), 3 and 4 snap the head back to the
-- left / right. Before, they simply cycled 1-4 whatever the direction.
local HIT_BY_SIDE = {
	Front = { `3`, `1`, `4`, `2` }; -- an exchange rocks side to side: head, body, head, body
	Back = { `1`, `2` }; -- shoved forward
	Right = { `3`, `1` }; -- hit on its right side: knocked to its left
	Left = { `4`, `2` }; -- hit on its left side: knocked to its right
}
function Local.HitReact(Attacker: Model, Target: Model, Count: number, React: string?): Animation
	local Fallback = HitReacts[((Count - 1) % #HitReacts) + 1]
	-- (fist moveset) a move can ask for its own reaction (the body blow and the clinch double them over: clip 1)
	local Forced = React and ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(React)
	if Forced then return Forced end
	local Ok, Rel = pcall(function() return Target:GetPivot():PointToObjectSpace(Attacker:GetPivot().Position) end)
	if not Ok then return Fallback end
	local Side = if -Rel.Z >= math.abs(Rel.X) then `Front` elseif Rel.Z >= math.abs(Rel.X) then `Back` elseif Rel.X > 0 then `Right` else `Left`
	local List = HIT_BY_SIDE[Side]
	return ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(List[((Count - 1) % #List) + 1]) or Fallback
end

-- (combat B11) a wall splat: a hard horizontal knockback (40+) that drives the target into a wall within its travel pins
-- them there (0.9 s stun, a head snap against the wall), so the attacker can follow up. Client: Misc."Wall Splat".
function Local.WallSplat(DamageData: DamageData, Target: Model)
	local LV = DamageData.LinearVelocity
	if not LV or LV.UpVector or (LV.Velocity or 0) < 40 or DamageData.AirPush or DamageData.AirDownslam then return end
	local Root = Target:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return end
	local Dir = (LV.Unit or DamageData.Character:GetPivot().LookVector) * Vector3.new(1, 0, 1)
	if Dir.Magnitude < 0.1 then return end
	Dir = Dir.Unit
	local Reach = math.min(LV.Velocity * (LV.Duration or 0.3), 14) + 1.5
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), workspace:FindFirstChild(`Visuals`) }
	Params.IgnoreWater = true
	local Hit = workspace:Raycast(Root.Position, Dir * Reach, Params)
	if not (Hit and Hit.Instance and Hit.Instance.CanCollide and math.abs(Hit.Normal.Y) < 0.5) then return end
	local Travel = math.max(0, (Hit.Position - Root.Position).Magnitude - 1.2)
	task.delay(math.min(Travel / LV.Velocity, 0.4), function()
		if not Target.Parent or Downed.IsDowned(Target) or not Root.Parent then return end
		LinearVelocity.StopTaggedBodyMovers(Target, `Stun`)
		local At = Hit.Position + Hit.Normal * 1.1
		local Out = Vector3.new(Hit.Normal.X, 0, Hit.Normal.Z)
		local Pos = Vector3.new(At.X, Root.Position.Y, At.Z)
		Target:PivotTo(if Out.Magnitude > 0.1 then CFrame.lookAt(Pos, Pos + Out) else CFrame.new(Pos))
		StateManager.CreateState(Target, `Stun`, 0.9)
		local Snap = ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(`3`)
		if Snap then
			TrackService.StopTaggedTracks(Target, `Stun`, 0)
			local T = TrackService.Play(Snap, Target, `Stun`, 0)
			T:SetPriority(Enum.AnimationPriority.Action4)
		end
		Packets.Replicate:Fire(`Misc`, `Wall Splat`, { User = Target; Attacker = DamageData.Character; Point = Hit.Position; Normal = Hit.Normal })
	end)
end

function Shared.Processed(DamageData: DamageData): boolean?
	DamageData.States = DamageData.States or {}
	DamageData.IgnoreStates = DamageData.IgnoreStates or {}

	local Character = DamageData.Character
	if not Character then return end

	local Target = DamageData.Target
	if not Target then return end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local TargetHumanoid = Target:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not TargetHumanoid then return end

	local CharacterCFrame = Character:GetPivot()
	local TargetCFrame = Target:GetPivot()

	-- reach guard (Known bug #14): a player's hit can't land on someone more than MAX_REACH studs away
	-- (hitboxes sit a few studs in front of you; the longest lunge and dive stay well inside this)
	if Players:GetPlayerFromCharacter(Character) and (TargetCFrame.Position - CharacterCFrame.Position).Magnitude > MAX_REACH then
		return false
	end
	local Tags = TagService:ReturnTags(Target)

	local FacingAttacker = math.deg((TargetCFrame.Position-CharacterCFrame.Position):Angle(TargetCFrame.LookVector)) >= 55
	if TargetHumanoid.Health <= 0 then return end

	-- Downed / carried / gripped bodies can't be hit (finish them with a grip instead).
	if StateManager.HasState(Target, {`Downed`, `Carried`, `Gripped`}) then
		return false
	end

	-- (audit) a student sitting a class minigame can't be hit, and a duelist can only be hit by their own duel opponent
	-- (Services.Quests.Duels links the pair with a DuelOpponent ObjectValue; the ring champion NPC is linked the same way)
	if StateManager.HasState(Target, `InActivity`) then
		return false
	end
	if Target:GetAttribute(`Dueling`) and not Shared.IsDuelOpponent(Target, Character) then
		return false
	end

	if table.find(Tags, `IFrames`) and not DamageData.IgnoreStates.IFrames then
		Shared.PerfectDodge(Character, Target)
		return false
	end

	if (table.find(Tags, `AutoParry`) or table.find(Tags, `Parry`)) and not DamageData.IgnoreStates.Parry then -- (fist moveset) a grab goes through a parry
		Shared.Parry(DamageData, if table.find(Tags, `Parry`) then true else false)
		return false
	end

	if StateManager.HasState(Target, `Ragdoll`) and not DamageData.IgnoreStates.Ragdoll then
		return false
	end

	if ActionManager.isActionPlaying(Target, `Block`) and not DamageData.IgnoreStates.Block and FacingAttacker then
		local Posture = TargetHumanoid:GetAttribute(`Posture`) or 0
		if DamageData.Stun then StateManager.CreateState(Target, `Stun`, DamageData.Stun) end

		if DamageData.InstantPostureBreak then
			StateManager.RemoveState(Target, `Slow`)
			ActionManager.CancelAction(Target, `Block`)
			Shared.PostureBreak(DamageData)
			return false
		end

		local PostureGain = (DamageData.Posture or (DamageData.Damage * 1.7)) * (Target:GetAttribute(`NH_PostureGain`) or 1) -- progression (Grit, traits)
		-- (2.14.0, combat concept 16) hand gear: wraps take less, gloves and knuckles deal more
		do
			local HandGear = require(script.Parent.HandGear)
			PostureGain *= HandGear.Mult(Target, `GuardTaken`) * HandGear.Mult(Character, `GuardDealt`)
		end
		local NewPosture = math.clamp(Posture + PostureGain, 0, 100)
		TargetHumanoid:SetAttribute(`Posture`, NewPosture)


		local ChipDamage = DamageData.Damage * 0.15
		if Downed.ApplyDamage(Target, ChipDamage, Character) then
			return false
		end

		local TargetProfile = EntityManager.GetProfile(Target)
		local Weapon = TargetProfile and TargetProfile.Weapon or `Fist`

		Packets.Replicate:Fire(`Misc`, `Block Hit`, {
			User = Target;
			Attacker = Character;
			Weapon = Weapon;
		})

		-- Break on the hit that fills the bar (this used to check the old value, one hit late).
		if NewPosture >= 100 then
			StateManager.RemoveState(Target, `Slow`)
			ActionManager.CancelAction(Target, `Block`)

			Shared.PostureBreak(DamageData)
		end

		return false
	end

	if not Players:GetPlayerFromCharacter(Target) and Target.Name == `PostureBreak` then
		Shared.PostureBreak(DamageData)
		return false
	end

	return true
end

-- (audit) true when Attacker is Target's opponent in the current duel (Services.Quests.Duels sets the link)
function Shared.IsDuelOpponent(Target: Model, Attacker: Model): boolean
	local Link = Target:FindFirstChild(`DuelOpponent`)
	return Link ~= nil and Link:IsA(`ObjectValue`) and Link.Value == Attacker
end

function Shared.TakeAction(DamageData: DamageData)
	DamageData.States = DamageData.States or {}

	local Character = DamageData.Character
	if not Character then return end

	local Target = DamageData.Target
	if not Target then return end

	local CharacterProfile = EntityManager.GetProfile(Character)
	if not CharacterProfile then return end

	local Humanoid = Target:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	-- (feel set) a counter-hit: the target was winding up its own swing and hadn't reached its hit frame yet
	-- (NHWindupUntil, server time, set by M1 / Running M1 / M2 / Uppercut as the swing starts). It stuns longer and gets
	-- a bigger hit-stop, a flash and its own sound (StateController Damage Type).
	local Counter = false
	local WindupUntil = Target:GetAttribute(`NHWindupUntil`)
	if typeof(WindupUntil) == `number` and workspace:GetServerTimeNow() < WindupUntil and StateManager.HasState(Target, `Attacking`) then
		Counter = true
		Target:SetAttribute(`NHWindupUntil`, nil)
		if DamageData.Stun then DamageData.Stun *= COUNTER_STUN end
		DamageData.States.Stun = (DamageData.States.Stun or 0.4) * COUNTER_STUN
	end

	local WasDowned = false
	if DamageData.StunLocked and Humanoid.Health - DamageData.Damage < 0 then
		Humanoid.Health = 0.1
	else
		WasDowned = Downed.ApplyDamage(Target, DamageData.Damage, Character)
	end

	local TargetIsNPC = not Players:GetPlayerFromCharacter(Target)
	local AttackerIsNPC = not Players:GetPlayerFromCharacter(Character)

	if TargetIsNPC and Character and not AttackerIsNPC then
		pcall(function()
			AI.OnNPCDamaged(Target, Character, DamageData.Damage)
		end)
	end
	if TargetIsNPC and AI.OnNPCHit then -- (1.23) every hit, so an NPC guards up after a string (threat stays player-only)
		pcall(AI.OnNPCHit, Target, Character, DamageData.Damage)
	end

	-- A downing hit skips stun / knockback / hit reactions: the body is already on the floor.
	if WasDowned then
		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon; Attacker = Character; Heavy = true; Counter = Counter; Damage = DamageData.Damage; Tag = DamageData.Tag }) -- (combat audit, feel set)
		return
	end

	local Weapon = CharacterProfile.Weapon

	-- (combat audit) Attacker and Heavy drive the hit-stop and camera kick (StateController Damage Type)
	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon; Attacker = Character; Heavy = DamageData.Heavy == true or DamageData.Stun ~= nil or DamageData.AirDownslam == true;
		Counter = Counter; Damage = DamageData.Damage; Tag = DamageData.Tag }) -- (feel set) the counter-hit and the number, for the readouts
	StateManager.CreateState(Target, `InCombat`, 60)

	local inAir = AirCombat.IsActive(Character, Target)

	ActionManager.CancelClass(Target, `Movement`)
	-- (2.14.0, combat concept 18) an EX skill's wind-up is armoured: the hit hurts, but doesn't cancel it
	if not inAir and not require(script.Parent.Heat).Armored(Target) then
		ActionManager.CancelClass(Target, `Attack`)
	end

	for Name, Duration in DamageData.States do
		StateManager.CreateState(Target, Name, Duration)
	end

	if DamageData.AirPush then
		AirCombat.AddHit(Target)
		AirCombat.Reposition(Character, Target)
	end

	if DamageData.AirDownslam then
		AirCombat.Stop(Character, Target)
	end

	local AirTarget = TagService:HasTag(Character, `AirWeld`)
	if AirTarget == Target then
		TagService:AddTag(Character, `AirWeld`, 1.5, Target)
	elseif DamageData.AirWeld and not AirTarget then
		StateManager.RemoveState(Target, `Paralyzed`)

		TagService:AddTag(Character, `AirWeld`, 1.5, Target)

		local TargetRoot = Target:FindFirstChild(`HumanoidRootPart`)
		if TargetRoot then
			TargetRoot.Anchored = false
		end

		local Weld = AirWeld.New()
		_Cache:SetScope(Character, `Instance`, Weld)
		Weld:Activate(Character, Target)

		local existingConnection = _Cache:GetScope(Character, `AirWeldConnection`)
		if existingConnection then
			existingConnection:Disconnect()
		end

		local connection = TagService.OnTagChanged(Character, function()
			local HasAirWeld = TagService:HasTag(Character, `AirWeld`)
			if HasAirWeld then
				return
			end

			local CachedWeld = _Cache:GetScope(Character, `Instance`)
			if CachedWeld then
				CachedWeld:Destroy()
				_Cache:SetScope(Character, `Instance`, nil)
			end

			-- Clean up the connection itself
			local conn = _Cache:GetScope(Character, `AirWeldConnection`)
			if conn then
				conn:Disconnect()
				_Cache:SetScope(Character, `AirWeldConnection`, nil)
			end
		end)

		_Cache:SetScope(Character, `AirWeldConnection`, connection)
	end

	if DamageData.OnHit then
		bLua.spawn(DamageData.OnHit, DamageData)
	end

	if not DamageData.NoAnimation and not (DamageData.Stun and DamageData.LinearVelocity) then
		local HitCount = Target:GetAttribute(`HitCounter`) or 1
		TrackService.StopTaggedTracks(Target, `Stun`, 0)

		if HitCount > #HitReacts then
			HitCount = 1
		end

		Target:SetAttribute(`HitCounter`, HitCount + 1)
		local hitTrack = TrackService.Play(Local.HitReact(Character, Target, HitCount, DamageData.React), Target, `Stun`, 0) -- (feel set) by direction
		hitTrack:SetPriority(Enum.AnimationPriority.Action4)
	end

	if (DamageData.LinearVelocity or DamageData.ApplyImpulse) and not StateManager.HasState(Target, `Paralyzed`) then
		if DamageData.Stun and not TagService:HasTag(Target, `InAir`) then
			local kbTrack = TrackService.Play(ReplicatedStorage.Assets.Animations.Default.Knockback, Target, `Stun`, 0)
			kbTrack:SetPriority(Enum.AnimationPriority.Action4)
		end

		Shared.KnockBack(DamageData, Target, `Stun`)
		Local.WallSplat(DamageData, Target) -- (combat B11)

		if DamageData.MoveAttacker then
			Shared.KnockBack(Character, `Attack`)

		end
	end
end

function Shared.Parry(DamageData: DamageData, Parry: boolean?)
	local Character = DamageData.Character
	if not Character then return end

	local Target = DamageData.Target
	if not Target then return end

	local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local TargetHumanoid = Target:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not TargetHumanoid then return end

	if AirCombat.IsActive(Character, Target) then
		AirCombat.Stop(Character, Target)

		TrackService.StopMultipleTags(Target, {`Parry`, `Attack`, `Stun`})
		TrackService.StopMultipleTags(Character, {`Parry`, `Attack`, `Stun`})

		StateManager.CreateState(Target, `ParryStun`, .35)
		StateManager.CreateState(Character, `ParryStun`, .35)

		ActionManager.CancelCurrentAction(Character)
		ActionManager.CancelAction(Target, `Block`)

		local userRoot = Character:FindFirstChild("HumanoidRootPart")
		local targetRoot = Target:FindFirstChild("HumanoidRootPart")

		if userRoot and targetRoot then
			local direction = (targetRoot.Position - userRoot.Position).Unit

			LinearVelocity.StopTaggedBodyMovers(Character, `AirParryKnockback`)
			LinearVelocity.StopTaggedBodyMovers(Target, `AirParryKnockback`)

			local userVelocity = -direction * 25 + Vector3.new(0, 10, 0)
			local userKnockback = LinearVelocity.new(Character, `AirParryKnockback`)
			userKnockback.Unit = userVelocity.Unit
			userKnockback.Speed = userVelocity.Magnitude
			userKnockback.MaxForce = Vector3.new(1, 1, 1) * 1e5
			userKnockback:SendToClients({ Remove = 0.15 })

			local targetVelocity = direction * 25 + Vector3.new(0, 10, 0)
			local targetKnockback = LinearVelocity.new(Target, `AirParryKnockback`)
			targetKnockback.Unit = targetVelocity.Unit
			targetKnockback.Speed = targetVelocity.Magnitude
			targetKnockback.MaxForce = Vector3.new(1, 1, 1) * 1e5
			targetKnockback:SendToClients({ Remove = 0.15 })
		end

		Packets.Replicate:Fire(`Misc`, `Parry`, {
			User = Character;
			Target = Target;
		})

		if Parry then
			TagService:AddTag(Target, `AutoParry`, .4)
			local Posture = TargetHumanoid:GetAttribute(`Posture`) or 0
			local PostureGain = -(DamageData.Posture or (DamageData.Damage * 1))
			local PostureRegen = 8
			local NewPosture = math.clamp(Posture + PostureGain - PostureRegen, 0, 100)
			TargetHumanoid:SetAttribute(`Posture`, NewPosture)
		end

		return
	end

	TrackService.StopMultipleTags(Target, {`Parry`, `Attack`, `Stun`})
	TrackService.StopMultipleTags(Character, {`Parry`, `Attack`, `Stun`})

	local Posture = TargetHumanoid:GetAttribute(`Posture`) or 0
	StateManager.RemoveState(Target, `ParryExhausted`)

	StateManager.CreateState(Target, `ParryStun`, .4)
	Target:SetAttribute(`NHRiposteUntil`, workspace:GetServerTimeNow() + 0.9) -- (fist moveset) the parrier's next M1 is a riposte
	StateManager.CreateState(Character, `ParryStun`, .75)

	ActionManager.CancelCurrentAction(Character)
	ActionManager.CancelAction(Target, `Block`)

	ActionManager.CancelCooldown(Target, `Block`)
	pcall(function() ActionManager.new(Target).ParryLockUntil = nil end) -- (combat audit) a landed parry lifts the parry lockout
	Packets.Replicate:Fire(`Misc`, `Parry`, {
		User = Character;
		Target = Target;

	})

	if Parry then
		TagService:AddTag(Target, `AutoParry`, .4)

		local PostureGain = -(DamageData.Posture or (DamageData.Damage * 1))
		local PostureRegen = 8
		local NewPosture = math.clamp(Posture + PostureGain - PostureRegen, 0, 100)
		TargetHumanoid:SetAttribute(`Posture`, NewPosture)
	end

	local CharacterCFrame = Character:GetPivot()
	local TargetCFrame = Target:GetPivot()

	DamageData.LinearVelocity = {
		Unit = (CharacterCFrame.Position - TargetCFrame.Position).Unit;
		Velocity = 6;
		Duration = .18;
	}

	Shared.KnockBack(DamageData, Character, `ParryStun`)
end

function Shared.PostureBreak(DamageData: DamageData)
	local Target = DamageData.Target
	if not Target then return end

	local Humanoid = Target:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	local OldPosture = Humanoid:GetAttribute(`Posture`) or 0
	Humanoid:SetAttribute(`Posture`, 0)
	TrackService.StopTaggedTracks(Target, `Block`)

	local GuardBreakAnim = ReplicatedStorage.Assets.Animations.Default:FindFirstChild(`Posture Break`)
	local LoadedTrack = Humanoid.Animator:LoadAnimation(GuardBreakAnim)
	local Duration = if LoadedTrack.Length > 0 then LoadedTrack.Length else 1.5 -- (audit) Length is 0 until the clip has loaded (first break on a server = 0 s paralyze)
	LoadedTrack:Destroy()

	StateManager.CreateState(Target, `Paralyzed`, Duration)
	Packets.Replicate:Fire(`Misc`, `Posture Break`, { User = Target; Duration = Duration })
end

function Shared.PerfectDodge(Character: Model, Target: Model)
	if not Character or not Target then return end
	TagService:AddTag(Target, `PerfectDodge`, 1.5)

	TrackService.StopAllTracks(Character)

	TrackService.StopAllTracks(Target)
end

function Shared.KnockBack(DamageData: DamageData, Character: Model,Tag: string)
	local CharacterCFrame = DamageData.Character:GetPivot()
	if not DamageData.LinearVelocity then return end


	bLua.spawn(function()

		local LinearData = DamageData.LinearVelocity
		local Linear = LinearVelocity.new(Character, Tag) do
			Linear.MaxForce = Vector3.new(1, (LinearData.UpVector) and 1,1) * 1e5
			Linear.Unit = LinearData.Unit or CharacterCFrame.LookVector + Vector3.new(0, LinearData.UpVector or 0, 0)

			Linear.Speed = LinearData.Velocity
			Linear.StopOnCast = DamageData.StopOnCast

			Linear:SendToClients({
				Remove = LinearData.Duration or 0.3,
				Tweens = LinearData.Tweens,
				Set = LinearData.Set

			})

		end

	end)
end




-- (2.14.0, combat concepts 16 and 18) brass knuckles' fist damage, an EX skill's damage and armour, and Heat: landed
-- hits, counter-hits, parries and perfect dodges fill it (ServerStorage.Packages.Heat)
do
	local Heat = require(script.Parent.Heat)
	local HandGear = require(script.Parent.HandGear)
	local BeastStagger = require(script.Parent.BeastStagger) -- (2.15.0, combat concept 22)
	local TagAssist = require(script.Parent.TagAssist) -- (2.15.0, combat concept 21) who you last hit, for the call
	local RawTakeAction, RawParry, RawDodge = Shared.TakeAction, Shared.Parry, Shared.PerfectDodge
	Shared.TakeAction = function(DamageData: DamageData)
		local Character = DamageData and DamageData.Character
		local Target = DamageData and DamageData.Target
		if Character and DamageData.Damage then
			DamageData.Damage *= HandGear.Mult(Character, `Damage`)
			if Heat.EXActive(Character) then DamageData.Damage *= Heat.EX_DAMAGE end
		end
		-- (2.15.0) a staggered beast takes more; this hit may fill its stagger meter (BeastStagger)
		if Target and DamageData.Damage then DamageData.Damage *= BeastStagger.DamageMult(Target) end
		local StaggerGain = BeastStagger.Before(DamageData)
		if Target and Heat.Armored(Target) then -- the EX wind-up: no stun, no knockback, no react
			DamageData.Stun = nil
			DamageData.StunLocked = false
			DamageData.LinearVelocity = nil
			DamageData.NoAnimation = true
			DamageData.States = {}
		end
		local W = Target and Target:GetAttribute(`NHWindupUntil`)
		local Counter = typeof(W) == `number` and workspace:GetServerTimeNow() < W and StateManager.HasState(Target, `Attacking`)
		local Result = RawTakeAction(DamageData)
		if Character then Heat.Add(Character, if Counter then Heat.GAIN.Counter else Heat.GAIN.Hit) end
		BeastStagger.After(DamageData, StaggerGain, Heat)
		if Character and Target then TagAssist.NoteHit(Character, Target) end
		return Result
	end
	Shared.Parry = function(DamageData: DamageData, Parry: boolean?)
		local Result = RawParry(DamageData, Parry)
		if Parry and DamageData and DamageData.Target then Heat.Add(DamageData.Target, Heat.GAIN.Parry) end
		return Result
	end
	Shared.PerfectDodge = function(Character: Model, Target: Model)
		local Result = RawDodge(Character, Target)
		if Target then Heat.Add(Target, Heat.GAIN.Dodge) end
		return Result
	end
end

-- (2.13.0, combat concept 14) the Studio combat log: what each hit came to. Wraps the two entry points; nothing
-- changes when the log is off (outside Studio it's always off).
do
	local CombatLog = require(script.Parent.CombatLog)
	local RawProcessed, RawTakeAction = Shared.Processed, Shared.TakeAction
	Shared.Processed = function(DamageData: DamageData): boolean?
		if not CombatLog.On() then return RawProcessed(DamageData) end
		local Target = DamageData and DamageData.Target
		local Why = `out of reach / can't be hit`
		pcall(function()
			local Tags = TagService:ReturnTags(Target)
			if table.find(Tags, `IFrames`) then Why = `dodged (i-frames)`
			elseif table.find(Tags, `Parry`) or table.find(Tags, `AutoParry`) then Why = `parried`
			elseif ActionManager.isActionPlaying(Target, `Block`) then Why = `blocked`
			end
		end)
		local Hum = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
		local P0 = Hum and Hum:GetAttribute(`Posture`) or 0
		local Result = RawProcessed(DamageData)
		local P1 = Hum and Hum:GetAttribute(`Posture`) or 0
		CombatLog.Log(DamageData and DamageData.Character, `hit`, string.format(`-> %s: %s (%.1f dmg%s, posture %.0f -> %.0f)`,
			Target and Target.Name or `?`, if Result then `LANDS` else `stopped, ` .. Why, DamageData and DamageData.Damage or 0,
			if DamageData and DamageData.Tag then `, ` .. DamageData.Tag else ``, P0, P1))
		return Result
	end
	Shared.TakeAction = function(DamageData: DamageData)
		if not CombatLog.On() then return RawTakeAction(DamageData) end
		local Target = DamageData and DamageData.Target
		local W = Target and Target:GetAttribute(`NHWindupUntil`)
		local Counter = typeof(W) == `number` and workspace:GetServerTimeNow() < W and StateManager.HasState(Target, `Attacking`)
		local Hum = Target and Target:FindFirstChildWhichIsA(`Humanoid`)
		local H0 = Hum and Hum.Health or 0
		local Result = RawTakeAction(DamageData)
		CombatLog.Log(DamageData and DamageData.Character, `damage`, string.format(`-> %s: health %.1f -> %.1f%s%s`,
			Target and Target.Name or `?`, H0, Hum and Hum.Health or 0, if Counter then `, COUNTER-HIT` else ``,
			if DamageData and DamageData.Heavy then `, heavy` else ``))
		return Result
	end
end

return Shared
