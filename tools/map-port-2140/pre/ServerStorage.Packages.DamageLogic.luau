
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
local Shared = {}

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

	if table.find(Tags, `AutoParry`) or  table.find(Tags, `Parry`) then
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
		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon })
		return
	end

	local Weapon = CharacterProfile.Weapon

	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon })
	StateManager.CreateState(Target, `InCombat`, 60)

	local inAir = AirCombat.IsActive(Character, Target)

	ActionManager.CancelClass(Target, `Movement`)
	if not inAir then
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
		local hitTrack = TrackService.Play(HitReacts[HitCount], Target, `Stun`, 0)
		hitTrack:SetPriority(Enum.AnimationPriority.Action4)
	end

	if (DamageData.LinearVelocity or DamageData.ApplyImpulse) and not StateManager.HasState(Target, `Paralyzed`) then
		if DamageData.Stun and not TagService:HasTag(Target, `InAir`) then
			local kbTrack = TrackService.Play(ReplicatedStorage.Assets.Animations.Default.Knockback, Target, `Stun`, 0)
			kbTrack:SetPriority(Enum.AnimationPriority.Action4)
		end

		Shared.KnockBack(DamageData, Target, `Stun`)

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
	StateManager.CreateState(Character, `ParryStun`, .75)

	ActionManager.CancelCurrentAction(Character)
	ActionManager.CancelAction(Target, `Block`)

	ActionManager.CancelCooldown(Target, `Block`)
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




return Shared
