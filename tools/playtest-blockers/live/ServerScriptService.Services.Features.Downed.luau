--[[
	Downed / Carry / Grip (server authoritative)

	- Combat damage goes through Downed.ApplyDamage. Damage that would kill a
	  character downs them instead (Health kept at Config.DownedHealth).
	- A downed character can crawl slowly (downed idle / crawl animations) and gets back
	  up after Config.DownedDuration.
	- Anyone nearby can Carry (V) a downed character or Grip (B) them.
	  A finished grip kills the target and credits the gripper.
	- Taking damage drops a carried body / interrupts a grip.

	Signals (for quests, discipline, NPC AI, kill tracking):
		Downed.OnDowned(Target, Attacker?)
		Downed.OnRecovered(Target)
		Downed.OnExecuted(Gripper, Target)
		Downed.OnDefeated(Target, Killer?)   -- fired for every character death in workspace.Live
]]

---| Services |---

local Players = game:GetService(`Players`)
local RunService = game:GetService(`RunService`)
local ContentProvider = game:GetService(`ContentProvider`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)
local ServerStorage = game:GetService(`ServerStorage`)

---| Modules |---

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local SignalPlus = require(ReplicatedStorage.Packages.SignalPlus)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Config = require(ReplicatedStorage.Config.Downed)

local ActionManager = require(ServerScriptService.Services.Player.ActionManager)
local EntityLoader = require(ServerScriptService.Services.Managers.EntityLoader)
local AirCombat = require(ServerStorage.Packages.AirCombat)

---| State |---

local BUSY_STATES = { `Downed`, `Carried`, `Gripped`, `Carrying`, `Gripping` }
local CANT_INTERACT_STATES = { `Stun`, `ParryStun`, `Paralyzed`, `Freeze`, `Ragdoll`, `InActivity` }

local DownedRecords = {} :: { [Model]: { Attacker: Model?, Until: number, States: { any }, Thread: thread?, Idle: AnimationTrack?, Crawl: AnimationTrack? } }
local Carries = {} :: { [Model]: { Target: Model, Weld: Weld, Saved: { [BasePart]: { Massless: boolean, Group: string } }, States: { any }, CarryTrack: AnimationTrack?, CarriedTrack: AnimationTrack? } }
local CarriedBy = {} :: { [Model]: Model }
local Grips = {} :: { [Model]: { Target: Model, States: { any }, Thread: thread?, GripperTrack: AnimationTrack?, VictimTrack: AnimationTrack? } }
local GrippedBy = {} :: { [Model]: Model }

local Killers = setmetatable({}, { __mode = `k` }) :: { [Model]: Model }
local LastAttacker = setmetatable({}, { __mode = `k` }) :: { [Model]: Model }
local LastRequest = {} :: { [Player]: number }
local CharacterConnections = {} :: { [Model]: { RBXScriptConnection } }

local Local = {}
local Shared = {}

Shared.OnDowned = SignalPlus()
Shared.OnRecovered = SignalPlus()
Shared.OnExecuted = SignalPlus()
Shared.OnDefeated = SignalPlus()
Shared.OnDamage = SignalPlus() -- (Target, Damage, Attacker?) every combat hit that deals damage

---| Helpers |---

function Local.GetHumanoid(Model: Model?): Humanoid?
	return Model and Model:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid?
end

function Local.GetRoot(Model: Model?): BasePart?
	return Model and Model:FindFirstChild(`HumanoidRootPart`) :: BasePart?
end

function Local.IsAlive(Model: Model?): boolean
	local Humanoid = Local.GetHumanoid(Model)
	return Model ~= nil and Model.Parent ~= nil and Humanoid ~= nil and Humanoid.Health > 0
end

function Local.DestroyStates(States: { any }?)
	for _, Handle in States or {} do
		pcall(function() Handle:Destroy() end)
	end
end

function Local.SetServerOwner(Model: Model)
	local Root = Local.GetRoot(Model)
	if Root then
		pcall(function() Root:SetNetworkOwner(nil) end)
	end
end

function Local.RestoreOwner(Model: Model)
	local Root = Local.GetRoot(Model)
	if not Root then return end

	local Player = Players:GetPlayerFromCharacter(Model)
	pcall(function() Root:SetNetworkOwner(Player) end)
end

function Local.GroundY(Position: Vector3, Ignore: { Instance }): number
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = { workspace.Live, table.unpack(Ignore) }

	local Result = workspace:Raycast(Position + Vector3.new(0, 3, 0), Vector3.new(0, -50, 0), Params)
	return if Result then Result.Position.Y else Position.Y - 3
end

-- (playtest-blockers) an offset in a character's space, its translation scaled with the character (Model:GetScale)
function Local.Scaled(Model: Model, Offset: CFrame): CFrame
	local Scale = 1
	pcall(function() Scale = Model:GetScale() end)
	return CFrame.new(Offset.Position * Scale) * Offset.Rotation
end

-- Puts a character upright on the ground at Position, facing Facing.
-- (The downed animations lay the body down visually; the root stays upright.)
function Local.PlaceAt(Model: Model, Position: Vector3, Facing: Vector3)
	local Root = Local.GetRoot(Model)
	if not Root then return end

	local Flat = Vector3.new(Facing.X, 0, Facing.Z)
	if Flat.Magnitude < 0.01 then Flat = Vector3.new(0, 0, -1) end

	local Y = Local.GroundY(Position, { Model }) + 3
	local Stand = Vector3.new(Position.X, Y, Position.Z)

	Root.AssemblyLinearVelocity = Vector3.zero
	Root.AssemblyAngularVelocity = Vector3.zero
	Model:PivotTo(CFrame.lookAt(Stand, Stand + Flat.Unit))
end

---| Animations |---

local AnimationCache = {} :: { [string]: Animation }

function Local.GetAnimationById(Id: string?): Animation?
	if not Id then return nil end

	if not AnimationCache[Id] then
		local Animation = Instance.new(`Animation`)
		Animation.AnimationId = Id
		AnimationCache[Id] = Animation
	end
	return AnimationCache[Id]
end

function Local.GetAnimation(Name: string): Animation?
	return Local.GetAnimationById(Config.Animations and Config.Animations[Name])
end

function Local.LoadAnimation(Model: Model, Animation: Animation?, Looped: boolean): AnimationTrack?
	local Humanoid = Local.GetHumanoid(Model)
	local Animator = Humanoid and Humanoid:FindFirstChildOfClass(`Animator`)
	if not Animator or not Animation then return nil end

	local Ok, Track = pcall(function() return Animator:LoadAnimation(Animation) end)
	if not Ok then
		warn(`[Downed] Could not load animation {Animation.AnimationId}: {Track}`)
		return nil
	end

	Track.Looped = Looped
	Track.Priority = Enum.AnimationPriority.Action4
	return Track
end

function Local.LoadTrack(Model: Model, Name: string): AnimationTrack?
	return Local.LoadAnimation(Model, Local.GetAnimation(Name), true)
end

function Local.GetGripPair(Gripper: Model): { Gripper: string, Victim: string }?
	local Weapon = nil
	pcall(function()
		local Profile = EntityLoader.GetProfile(Gripper)
		Weapon = Profile and Profile.Weapon
	end)

	local Pairs = Config.GripAnimations or {}
	return Pairs[Weapon] or Pairs[Config.DefaultGripWeapon]
end

function Local.DestroyTrack(Track: AnimationTrack?)
	if not Track then return end
	pcall(function()
		Track:Stop(0.15)
		Track:Destroy()
	end)
end

function Local.StopTrack(Track: AnimationTrack?)
	if Track and Track.IsPlaying then Track:Stop(0.2) end
end

-- Picks idle vs crawl from how fast the body is moving. Hidden while carried/gripped.
function Local.UpdateAnimations()
	-- carry: idle pair while standing, run pair while moving
	for Carrier, C in Carries do
		local Root = Local.GetRoot(Carrier)
		if not Root or not (C.CarryRunTrack and C.CarriedRunTrack) then continue end
		local V = Root.AssemblyLinearVelocity
		local Run = Vector3.new(V.X, 0, V.Z).Magnitude > (Config.CarryRunAt or 4)
		if Run ~= C.Running then
			C.Running = Run
			local OnC, OffC = if Run then C.CarryRunTrack else C.CarryTrack, if Run then C.CarryTrack else C.CarryRunTrack
			local OnV, OffV = if Run then C.CarriedRunTrack else C.CarriedTrack, if Run then C.CarriedTrack else C.CarriedRunTrack
			Local.StopTrack(OffC)
			Local.StopTrack(OffV)
			if OnC and not OnC.IsPlaying then OnC:Play(0.2) end
			if OnV and not OnV.IsPlaying then OnV:Play(0.2) end
		end
	end
	for Target, Record in DownedRecords do
		local Root = Local.GetRoot(Target)
		if not Root then continue end

		-- Carried: the body is a plank on the carrier's shoulder.
		-- Gripped: the victim grip animation plays instead.
		if CarriedBy[Target] or GrippedBy[Target] then
			Local.StopTrack(Record.Idle)
			Local.StopTrack(Record.Crawl)
			continue
		end

		local Velocity = Root.AssemblyLinearVelocity
		local Moving = Vector3.new(Velocity.X, 0, Velocity.Z).Magnitude >= (Config.CrawlMinSpeed or 0.75)
		local Want = if Moving and not GrippedBy[Target] then Record.Crawl else Record.Idle
		local Other = if Want == Record.Crawl then Record.Idle else Record.Crawl

		Local.StopTrack(Other)
		if Want and not Want.IsPlaying then Want:Play(0.2) end
	end
end

function Local.FaceTowards(Model: Model, Position: Vector3)
	local Root = Local.GetRoot(Model)
	if not Root then return end

	local Flat = Vector3.new(Position.X, Root.Position.Y, Position.Z)
	if (Flat - Root.Position).Magnitude < 0.05 then return end
	Model:PivotTo(CFrame.lookAt(Root.Position, Flat))
end

-- Can this character start a carry/grip right now?
function Local.CanAct(Actor: Model): boolean
	if not Local.IsAlive(Actor) then return false end
	if StateManager.HasState(Actor, BUSY_STATES) then return false end
	if StateManager.HasState(Actor, CANT_INTERACT_STATES) then return false end
	return true
end

function Local.FindDownedNear(Actor: Model, Range: number): Model?
	local Root = Local.GetRoot(Actor)
	if not Root then return nil end

	local Best, BestDistance = nil, Range
	for Target in DownedRecords do
		if Target == Actor or CarriedBy[Target] or GrippedBy[Target] then continue end
		if not Local.IsAlive(Target) then continue end

		local TargetRoot = Local.GetRoot(Target)
		if not TargetRoot then continue end

		local Distance = (TargetRoot.Position - Root.Position).Magnitude
		if Distance <= BestDistance then
			Best, BestDistance = Target, Distance
		end
	end

	return Best
end

---| Queries |---

function Shared.IsDowned(Model: Model): boolean
	return DownedRecords[Model] ~= nil
end

function Shared.IsBusy(Model: Model): boolean
	return StateManager.HasState(Model, BUSY_STATES) == true
end

function Shared.GetKiller(Model: Model): Model?
	return Killers[Model] or LastAttacker[Model]
end

function Shared.CanBeDowned(Model: Model): boolean
	if not Config.Enabled then return false end
	if Model:GetAttribute(`NoDowned`) == true then return false end
	if Players:GetPlayerFromCharacter(Model) then return true end
	return Config.NPCsCanBeDowned
end

---| Damage entry point |---

-- Use this instead of Humanoid:TakeDamage for combat damage.
-- Returns true if this damage downed the target.
function Shared.ApplyDamage(Target: Model, Damage: number, Attacker: Model?): boolean
	local Humanoid = Local.GetHumanoid(Target)
	if not Humanoid or Humanoid.Health <= 0 then return false end
	if DownedRecords[Target] then return false end
	if Target:GetAttribute(`NH_Evolving`) then return false end -- mid tier-up cutscene: untouchable (Services.Player.Evolution)

	-- progression: the attacker's damage bonus and the target's damage taken (Services.Player.Progression)
	if Attacker and Attacker ~= Target then Damage *= Attacker:GetAttribute(`NH_DamageDealt`) or 1 end
	Damage *= Target:GetAttribute(`NH_DamageTaken`) or 1
	-- races: bonuses vs undead / monsters and protection from undead (ReplicatedStorage.Lineage)
	if Attacker and Attacker ~= Target then Damage *= require(ReplicatedStorage.Lineage).DamageScale(Attacker, Target) end

	if Attacker and Attacker ~= Target then
		LastAttacker[Target] = Attacker
	end

	-- Getting hit breaks a carry or grip.
	if Carries[Target] and Config.DropOnCarrierHit then
		Shared.Drop(Target)
	end
	if Grips[Target] then
		Shared.CancelGrip(Target)
	end

	if Humanoid.Health - Damage <= 0 and Shared.CanBeDowned(Target) and not Target:FindFirstChildOfClass(`ForceField`) then
		Humanoid.Health = math.min(Humanoid.Health, Config.DownedHealth)
		Shared.Down(Target, Attacker)
		Shared.OnDamage:Fire(Target, Damage, Attacker)
		return true
	end

	Humanoid:TakeDamage(Damage)
	Shared.OnDamage:Fire(Target, Damage, Attacker)
	return false
end

---| Downed |---

function Shared.Down(Target: Model, Attacker: Model?)
	if DownedRecords[Target] then return end

	local Humanoid = Local.GetHumanoid(Target)
	local Root = Local.GetRoot(Target)
	if not Humanoid or not Root or Humanoid.Health <= 0 then return end

	-- Stop whatever they were doing (including carrying / gripping someone else).
	if Carries[Target] then Shared.Drop(Target) end
	if Grips[Target] then Shared.CancelGrip(Target) end

	ActionManager.CancelCurrentAction(Target)
	pcall(TrackService.StopAllTracks, Target)
	pcall(AirCombat.StopCharacter, Target)

	local Record = {
		Attacker = Attacker;
		Until = workspace:GetServerTimeNow() + Config.DownedDuration;
		States = { StateManager.CreateState(Target, `Downed`) };
		Thread = nil;
		Idle = Local.LoadTrack(Target, `Idle`);
		Crawl = Local.LoadTrack(Target, `Crawl`);
	}
	DownedRecords[Target] = Record

	Humanoid:SetAttribute(`Downed`, true)
	Humanoid:SetAttribute(`Sprint`, false)
	Target:SetAttribute(`DownedUntil`, Record.Until)

	Root.AssemblyLinearVelocity = Vector3.zero
	if Record.Idle then Record.Idle:Play(0.2) end

	Record.Thread = task.delay(Config.DownedDuration, function()
		Record.Thread = nil
		if DownedRecords[Target] == Record and not GrippedBy[Target] then
			Shared.Recover(Target)
		end
	end)

	Shared.OnDowned:Fire(Target, Attacker)
end

function Shared.Recover(Target: Model)
	local Record = DownedRecords[Target]
	if not Record then return end

	local Carrier = CarriedBy[Target]
	if Carrier then Shared.Drop(Carrier, true) end

	local Gripper = GrippedBy[Target]
	if Gripper then Local.EndGrip(Gripper) end

	Local.ClearDowned(Target)

	local Humanoid = Local.GetHumanoid(Target)
	if Humanoid and Humanoid.Health > 0 then
		local MaxHealth = Humanoid.MaxHealth
		if MaxHealth < math.huge then
			Humanoid.Health = math.max(Humanoid.Health, MaxHealth * Config.RecoverHealthFraction)
		end

		Local.RestoreOwner(Target)
		-- VFX P2-8 "Second chance": students who get back up get a candle-gold wisp (Controllers.World.GetUp);
		-- Progression marks a Fated revive with NHFated first
		local Root = Local.GetRoot(Target)
		if Root and Players:GetPlayerFromCharacter(Target) then
			local Fated = Target:GetAttribute(`NHFated`) == true
			pcall(function() require(ServerScriptService.Services.Features.Fx).FireNear(Root.Position, 120, `GetUp`, { Character = Target; Fated = Fated }) end)
		end
		Target:SetAttribute(`NHFated`, nil)
		Shared.OnRecovered:Fire(Target)
	end
end

function Local.ClearDowned(Target: Model)
	local Record = DownedRecords[Target]
	if not Record then return end

	DownedRecords[Target] = nil
	if Record.Thread then pcall(task.cancel, Record.Thread) end
	Local.DestroyStates(Record.States)

	for _, Track in { Record.Idle, Record.Crawl } do
		pcall(function()
			Track:Stop(0.2)
			Track:Destroy()
		end)
	end

	local Humanoid = Local.GetHumanoid(Target)
	if Humanoid then
		Humanoid:SetAttribute(`Downed`, nil)
		Humanoid.PlatformStand = false
	end
	Target:SetAttribute(`DownedUntil`, nil)
end

-- Gets the target up if their downed timer already ran out (e.g. after a drop).
function Local.RecoverIfExpired(Target: Model)
	local Record = DownedRecords[Target]
	if Record and workspace:GetServerTimeNow() >= Record.Until then
		Shared.Recover(Target)
	end
end

---| Carry |---

function Shared.ToggleCarry(Carrier: Model): boolean
	if Carries[Carrier] then
		Shared.Drop(Carrier)
		return true
	end

	if not Local.CanAct(Carrier) then return false end

	local Target = Local.FindDownedNear(Carrier, Config.CarryRange)
	if not Target then return false end

	return Shared.Carry(Carrier, Target)
end

function Shared.Carry(Carrier: Model, Target: Model): boolean
	if not Local.CanAct(Carrier) then return false end
	if not DownedRecords[Target] or CarriedBy[Target] or GrippedBy[Target] then return false end
	if Target:GetAttribute(`Protected`) then return false end -- duels / ring fights: no carrying off

	local Torso = Carrier:FindFirstChild(`Torso`) or Local.GetRoot(Carrier)
	local TargetRoot = Local.GetRoot(Target)
	if not Torso or not TargetRoot then return false end

	ActionManager.CancelCurrentAction(Carrier)

	-- The body must not push the carrier around.
	local Saved = {}
	for _, Part in Target:GetDescendants() do
		if Part:IsA(`BasePart`) then
			Saved[Part] = { Massless = Part.Massless, Group = Part.CollisionGroup }
			Part.Massless = true
			Part.CollisionGroup = `Ragdoll`
		end
	end

	Local.SetServerOwner(Target)

	-- The carried humanoid must not try to balance itself against the weld.
	local CarriedHumanoid = Local.GetHumanoid(Target)
	if CarriedHumanoid then CarriedHumanoid.PlatformStand = true end

	local Weld = Instance.new(`Weld`)
	Weld.Name = `CarryWeld`
	Weld.Part0 = Torso
	Weld.Part1 = TargetRoot
	-- With the Carried animation the body stays upright here and the animation drapes it
	-- over the shoulder. Without it, fall back to holding the body flat across the shoulders.
	local CarriedTrack = Local.LoadTrack(Target, `Carried`)
	local CarryTrack = Local.LoadTrack(Carrier, `Carry`)
	local CarriedRunTrack = Local.LoadTrack(Target, `CarriedRun`)
	local CarryRunTrack = Local.LoadTrack(Carrier, `CarryRun`)

	Weld.C0 = Local.Scaled(Carrier, if CarriedTrack
		then (Config.CarryOffset or CFrame.new(0, 1.5, 0))
		else CFrame.new(0, 1.6, 0.2) * CFrame.Angles(0, 0, math.rad(90)))
	Weld.Parent = Torso

	Carries[Carrier] = {
		Target = Target;
		Weld = Weld;
		Saved = Saved;
		States = { StateManager.CreateState(Carrier, `Carrying`), StateManager.CreateState(Target, `Carried`) };
		CarryTrack = CarryTrack;
		CarriedTrack = CarriedTrack;
		CarryRunTrack = CarryRunTrack;
		CarriedRunTrack = CarriedRunTrack;
		Running = false;
	}
	CarriedBy[Target] = Carrier

	Local.StopTrack(DownedRecords[Target] and DownedRecords[Target].Idle)
	Local.StopTrack(DownedRecords[Target] and DownedRecords[Target].Crawl)
	if CarriedTrack then CarriedTrack:Play(0.15) end
	if CarryTrack then CarryTrack:Play(0.15) end

	Carrier:SetAttribute(`Carrying`, Target.Name)
	Target:SetAttribute(`CarriedBy`, Carrier.Name)
	return true
end

-- SkipRecover: used by Recover itself to avoid recursion.
function Shared.Drop(Carrier: Model, SkipRecover: boolean?)
	local Record = Carries[Carrier]
	if not Record then return end

	Carries[Carrier] = nil
	local Target = Record.Target
	CarriedBy[Target] = nil

	if Record.Weld then Record.Weld:Destroy() end
	Local.DestroyStates(Record.States)
	Local.DestroyTrack(Record.CarryTrack)
	Local.DestroyTrack(Record.CarriedTrack)
	Local.DestroyTrack(Record.CarryRunTrack)
	Local.DestroyTrack(Record.CarriedRunTrack)

	for Part, Values in Record.Saved do
		if Part.Parent then
			Part.Massless = Values.Massless
			Part.CollisionGroup = Values.Group
		end
	end

	if Carrier.Parent then Carrier:SetAttribute(`Carrying`, nil) end
	if Target.Parent then Target:SetAttribute(`CarriedBy`, nil) end

	local CarriedHumanoid = Local.GetHumanoid(Target)
	if CarriedHumanoid then CarriedHumanoid.PlatformStand = false end

	if Local.IsAlive(Target) and DownedRecords[Target] then
		local CarrierRoot = Local.GetRoot(Carrier)
		local TargetRoot = Local.GetRoot(Target)
		local Position = if CarrierRoot then CarrierRoot.Position + CarrierRoot.CFrame.LookVector * 3 else TargetRoot and TargetRoot.Position
		local Facing = if CarrierRoot then CarrierRoot.CFrame.LookVector else Vector3.new(0, 0, -1)

		if Position then Local.PlaceAt(Target, Position, Facing) end
		Local.RestoreOwner(Target) -- players can crawl again

		if not SkipRecover then Local.RecoverIfExpired(Target) end
	end
end

---| Grip |---

-- Override (race actions, Services.Features.RaceAction): { Gripper = anim id, Victim = anim id?, Kind = name,
--   Offset = CFrame? (2.2.0 racial grips: the victim's root in the gripper's root space; the victim is WELDED there for
--   the whole clip so the paired animations keep contact) }
function Shared.StartGrip(Gripper: Model, Override: { Gripper: string, Victim: string?, Kind: string, Offset: CFrame? }?): boolean
	if Grips[Gripper] then return false end

	-- Gripping the body you're carrying puts it down first.
	local Target
	if Carries[Gripper] then
		Target = Carries[Gripper].Target
		Shared.Drop(Gripper, true)
	else
		if not Local.CanAct(Gripper) then return false end
		Target = Local.FindDownedNear(Gripper, Config.GripRange)
	end

	if not Target or not DownedRecords[Target] or CarriedBy[Target] or GrippedBy[Target] then return false end
	if Target:GetAttribute(`Protected`) then return false end -- duels / ring fights: nobody gets finished
	if not Local.CanAct(Gripper) then return false end

	local Root = Local.GetRoot(Gripper)
	if not Root then return false end

	ActionManager.CancelCurrentAction(Gripper)
	pcall(TrackService.StopAllTracks, Gripper)

	-- Line the victim up for the paired animation.
	local Weld, Saved = nil, nil
	-- (playtest-blockers) every grip holds its victim now: a normal grip used to set the victim down 3 studs ahead and
	-- leave it free, so a downed player could crawl out of the execution (a moved NPC slid from 3 to 0.3 studs, into
	-- the gripper) and the paired clips drifted apart. Racial grips without an authored Offset still just place.
	local Hold = if Override then Override.Offset
		else (Config.GripVictimOffset or CFrame.new(0, 0, -3) * CFrame.Angles(0, math.pi, 0))
	if Hold then
		-- (2.2.0) racial grip: hold the victim against the gripper at the authored offset (scaled with the gripper)
		local TargetRoot = Local.GetRoot(Target)
		if TargetRoot then
			local Off = Local.Scaled(Gripper, Hold)
			Saved = {}
			for _, Part in Target:GetDescendants() do
				if Part:IsA(`BasePart`) then
					Saved[Part] = { Massless = Part.Massless, Group = Part.CollisionGroup }
					Part.Massless = true
					Part.CollisionGroup = `Ragdoll`
				end
			end
			Local.SetServerOwner(Target)
			local VH = Local.GetHumanoid(Target)
			if VH then VH.PlatformStand = true end
			TargetRoot.AssemblyLinearVelocity = Vector3.zero
			Target:PivotTo(Root.CFrame * Off)
			Weld = Instance.new(`Weld`)
			Weld.Name = `GripWeld`
			Weld.Part0 = Root
			Weld.Part1 = TargetRoot
			Weld.C0 = Off
			Weld.Parent = Root
		end
	else
		local VictimCFrame = Root.CFrame * (Config.GripVictimOffset or CFrame.new(0, 0, -3) * CFrame.Angles(0, math.pi, 0))
		Local.PlaceAt(Target, VictimCFrame.Position, VictimCFrame.LookVector)
	end

	local Record = {
		Target = Target;
		Kind = Override and Override.Kind; -- nil = a normal grip finisher
		States = { StateManager.CreateState(Gripper, `Gripping`), StateManager.CreateState(Target, `Gripped`) };
		Thread = nil;
		GripperTrack = nil;
		VictimTrack = nil;
		Weld = Weld; -- (2.2.0) racial grips hold the victim with a weld
		Saved = Saved;
	}
	Grips[Gripper] = Record
	GrippedBy[Target] = Gripper

	local Pair = Override or Local.GetGripPair(Gripper)
	if Pair then
		Record.GripperTrack = Local.LoadAnimation(Gripper, Local.GetAnimationById(Pair.Gripper), false)
		Record.VictimTrack = if Pair.Victim then Local.LoadAnimation(Target, Local.GetAnimationById(Pair.Victim), false) else nil -- no victim clip: they stay in their downed pose
		if Record.GripperTrack then Record.GripperTrack:Play(0.1) end
		if Record.VictimTrack then Record.VictimTrack:Play(0.1) end
	end

	-- Kill when the gripper's animation ends (fallback: Config.GripDuration).
	local Duration = Config.GripDuration
	if Config.GripUsesAnimationLength and Record.GripperTrack then
		local Waited = 0
		while Record.GripperTrack.Length <= 0 and Waited < 0.3 do
			Waited += task.wait()
		end
		if Record.GripperTrack.Length > 0 then
			Duration = Record.GripperTrack.Length
		end
	end

	if Grips[Gripper] ~= Record then
		return false -- interrupted while the animation was loading
	end

	Target:SetAttribute(`GrippedBy`, Gripper.Name) -- (2.2.0) first: Features.RaceAction looks the victim up on GripEndsAt
	Gripper:SetAttribute(`GripEndsAt`, workspace:GetServerTimeNow() + Duration)

	Record.Thread = task.delay(Duration, function()
		Record.Thread = nil
		if Grips[Gripper] == Record then
			Local.FinishGrip(Gripper)
		end
	end)

	return true
end

-- Removes the grip link without deciding the outcome.
-- Finished: the grip completed (the victim is about to die), so a racial grip's victim keeps its last pose.
function Local.EndGrip(Gripper: Model, Finished: boolean?): Model?
	local Record = Grips[Gripper]
	if not Record then return nil end

	Grips[Gripper] = nil
	GrippedBy[Record.Target] = nil
	if Record.Thread then pcall(task.cancel, Record.Thread) end
	Local.DestroyStates(Record.States)

	Local.DestroyTrack(Record.GripperTrack)
	if Finished and Record.Weld and Record.VictimTrack then
		local VT = Record.VictimTrack
		pcall(function() VT:AdjustSpeed(0) end) -- hold the final (lying) frame through the death
		task.delay(1.5, function() Local.DestroyTrack(VT) end)
	else
		Local.DestroyTrack(Record.VictimTrack)
	end

	-- (2.2.0) release a welded racial-grip victim: weight and collisions back, set down where the clip left it
	if Record.Weld then
		pcall(function() Record.Weld:Destroy() end)
		for Part, Values in Record.Saved or {} do
			if Part.Parent then
				Part.Massless = Values.Massless
				Part.CollisionGroup = Values.Group
			end
		end
		local Target = Record.Target
		local VH = Local.GetHumanoid(Target)
		if VH then VH.PlatformStand = false end
		if Local.IsAlive(Target) and not Finished then
			local TR = Local.GetRoot(Target)
			if TR then Local.PlaceAt(Target, TR.Position, TR.CFrame.LookVector) end
			Local.RestoreOwner(Target) -- players can crawl again
		end
	end

	if Gripper.Parent then Gripper:SetAttribute(`GripEndsAt`, nil) end
	if Record.Target.Parent then Record.Target:SetAttribute(`GrippedBy`, nil) end
	return Record.Target
end

function Shared.CancelGrip(Gripper: Model)
	local Target = Local.EndGrip(Gripper)
	if Target then Local.RecoverIfExpired(Target) end
end

function Local.FinishGrip(Gripper: Model)
	local Kind = Grips[Gripper] and Grips[Gripper].Kind
	local Target = Local.EndGrip(Gripper, true)
	if not Target or not Local.IsAlive(Target) then return end

	Killers[Target] = Gripper
	Shared.OnExecuted:Fire(Gripper, Target, Kind)

	local Humanoid = Local.GetHumanoid(Target)
	if Humanoid then Humanoid.Health = 0 end
end

---| Lifecycle |---

-- Character died or was removed: break every link it is part of.
function Local.Release(Model: Model)
	if Carries[Model] then Shared.Drop(Model, true) end
	if CarriedBy[Model] then Shared.Drop(CarriedBy[Model], true) end
	if Grips[Model] then Shared.CancelGrip(Model) end
	if GrippedBy[Model] then Local.EndGrip(GrippedBy[Model]) end
	Local.ClearDowned(Model)
end

function Local.Track(Model: Instance)
	if not Model:IsA(`Model`) or CharacterConnections[Model] then return end

	local Humanoid = Model:FindFirstChildWhichIsA(`Humanoid`) or Model:WaitForChild(`Humanoid`, 5)
	if not Humanoid or not Humanoid:IsA(`Humanoid`) then return end

	local Connections = {}
	CharacterConnections[Model] = Connections

	table.insert(Connections, Humanoid.Died:Connect(function()
		Local.Release(Model)
		Shared.OnDefeated:Fire(Model, Shared.GetKiller(Model))
	end))

	table.insert(Connections, Model.AncestryChanged:Connect(function(_, Parent)
		if Parent then return end
		Local.Release(Model)
		for _, Connection in Connections do Connection:Disconnect() end
		CharacterConnections[Model] = nil
	end))
end

function Local.OnRequest(Player: Player, Callback: (Model) -> boolean)
	local Now = os.clock()
	if LastRequest[Player] and Now - LastRequest[Player] < Config.RequestCooldown then return end
	LastRequest[Player] = Now

	local Character = Player.Character
	if not Character or not Character:IsDescendantOf(workspace) then return end
	Callback(Character)
end

function Shared.OnStart()
	Packets.Carry.OnServerEvent:Connect(function(Player: Player)
		Local.OnRequest(Player, Shared.ToggleCarry)
	end)

	Packets.Grip.OnServerEvent:Connect(function(Player: Player)
		Local.OnRequest(Player, Shared.StartGrip)
	end)

	Players.PlayerRemoving:Connect(function(Player: Player)
		LastRequest[Player] = nil
	end)

	RunService.Heartbeat:Connect(function()
		if next(DownedRecords) then
			Local.UpdateAnimations()
		end
	end)

	-- Preload every downed / grip animation so lengths are known on first use.
	task.spawn(function()
		local ToLoad = {}
		for _, Id in Config.Animations or {} do
			table.insert(ToLoad, Local.GetAnimationById(Id))
		end
		for _, Pair in Config.GripAnimations or {} do
			table.insert(ToLoad, Local.GetAnimationById(Pair.Gripper))
			table.insert(ToLoad, Local.GetAnimationById(Pair.Victim))
		end
		pcall(function() ContentProvider:PreloadAsync(ToLoad) end)
	end)

	local Live = workspace:WaitForChild(`Live`)
	for _, Model in Live:GetChildren() do
		task.spawn(Local.Track, Model)
	end
	Live.ChildAdded:Connect(function(Model)
		task.spawn(Local.Track, Model)
	end)
end

return Shared
