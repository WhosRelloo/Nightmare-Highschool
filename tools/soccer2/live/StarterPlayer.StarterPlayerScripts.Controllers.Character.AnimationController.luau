
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local RunService = game:GetService(`RunService`)
local UserInputService = game:GetService(`UserInputService`)
local KeyframeSequenceProvider = game:GetService(`KeyframeSequenceProvider`)

---| Modules |---

local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Trove = require(ReplicatedStorage.Packages.Trove)

local StateController = require(script.Parent.Parent.StateController)
-- (phase6-strafes) stride-matched cadence and the directional walk (strafes, the reversed-walk backpedal):
-- docs/superpowers/specs/2026-11-22-strafes-npc-gestures-design.md §1
local LocoCfg = require(ReplicatedStorage.Config.Locomotion)
local Loco = require(ReplicatedStorage.Functions.Locomotion)
local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local BUSY = { `Dodge`, `Sliding`, `Ragdoll`, `Downed`, `Carried`, `Gripped`, `Gripping`, `Paralyzed` } -- LockOn's list

---| Type Annotation |---

export type AnimationManager = {

	--| Animators |--

	Humanoid: Humanoid;
	Animator: Animator;

	--| Properties |--

	Pose: AnimationTrack ?;
	Tracks: { Animation } ?;

	TimePosition: { [AnimationTrack]: number };
	TrackTable: { [string]: AnimationTrack };

	CharacterTrove: any;

	PlayTrack: (self: AnimationManager, NewPose: string, Time: number) -> (AnimationManager);
	SetSpeed: (self: AnimationManager, Speed: number) -> (AnimationManager);

	SetTracks: (self: AnimationManager, Tracks: { Animation }) -> (AnimationManager);
	Stop: (self: AnimationManager) -> (AnimationManager);

	UpdateTrack: (self: AnimationManager, Pose: string, Animation: Animation) -> (AnimationManager);
	StopAllTracks: (self: AnimationManager) -> (AnimationManager);
}

local Player = Players.LocalPlayer
local Mouse = Player:GetMouse()

local Animate = {}
Animate.__index = Animate

function Animate.new(): AnimationManager
	local self = setmetatable({}, Animate) :: AnimationManager

	self.TrackTable = {}
	self.TimePosition = {}

	return self
end

local Local = {}
local Shared = {}
Shared.Controller = Animate.new()

-- (phase6-strafes) the clip rate that keeps the feet planted at this ground speed (Functions.Locomotion.Rate)
local LegLen = 2
-- (soccer-2.0) a mode's own walk (Controllers.Character.SoccerPack): Stride per gait (Walk, Back, StrafeLeft, StrafeRight),
-- a real backpedal track (Back) and replacement strafes (Left / Right), as animation ids. nil clears it.
local Over = nil :: { Stride: { [string]: number }?, Back: string?, Left: string?, Right: string? }?
local function rate(Speed: number, Gait: string): number
	local S = (Over and Over.Stride and Over.Stride[Gait]) or LocoCfg.Stride[Gait] or LocoCfg.Stride.Walk
	return Loco.Rate(Speed, S, LegLen, LocoCfg)
end
Shared.Rate = rate
function Shared.Override(O)
	Over = O
	if Shared.Controller.Animator then Local.LoadDirectional(Shared.Controller) end
end
function Shared.Overridden(): boolean return Over ~= nil end

function Shared.OnStart()

	if Player.Character then
		Shared.OnCharacterAdded(Player.Character)

	end

	StateController.ProfileUpdated:Connect(function(Profile: StateController.PlayerData, StateAction: StateController.StateAction)
		if StateAction.type == `UpdateWeapon` then
			-- (audit) nil-check the body first, and leave the pack alone while transformed: the claw stance owns it then and
			-- Controllers.Character.Transformation puts the weapon pack back when it ends
			local Character = Player.Character
			if not Character then return end
			if Character:GetAttribute(`Transformation`) or Character:GetAttribute(`WolfForm`) then return end
			if Over then return end -- (soccer-2.0) a match pack owns it; SoccerPack puts the weapon pack back afterwards
			local Humanoid = Character:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
			local Animator = Humanoid and Humanoid:FindFirstChildWhichIsA(`Animator`) :: Animator
			-- (a different Animator = the new body isn't set up yet; OnCharacterAdded loads the pack from the profile)
			if not Humanoid or not Animator or Shared.Controller.Animator ~= Animator then return end

			local Pack: (Folder & { Movement: Folder })? = 
				ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(Profile.Weapon)

			if not Pack then
				Pack = ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(`Fist`)
			end

			if not Pack then
				Pack = ReplicatedStorage.Assets.Animations.Default
			end

			local AnimationPack = if Pack and Pack:FindFirstChild(`Movement`) then Pack.Movement else ReplicatedStorage.Assets.Animations.Default.Movement
			local AnimationManager = Shared.Controller :: AnimationManager

			AnimationManager:StopAllTracks()
				:SetTracks(AnimationPack)
				:PlayTrack(`Idle`, .1)

			-- (audit) Character / Humanoid / Animator are checked at the top now

			-- re-kick the walk track (see Misc.Equip, 1.97.1): shared NHKickSpeed so two kicks at once never put a 0 back
			if Humanoid.MoveDirection.Magnitude > 0 and Humanoid:GetAttribute(`NHKickSpeed`) == nil then
				Humanoid:SetAttribute(`NHKickSpeed`, Humanoid.WalkSpeed)
				Humanoid.WalkSpeed = 0

				task.delay(.01, function()
					local Back = Humanoid:GetAttribute(`NHKickSpeed`)
					Humanoid:SetAttribute(`NHKickSpeed`, nil)
					if Back and Humanoid.WalkSpeed == 0 then Humanoid.WalkSpeed = Back end
				end)
			end
		end

	end)

	Player.CharacterAdded:Connect(Shared.OnCharacterAdded)
end

function Shared.OnCharacterAdded(Character: Model)
	local Character = Character or Player.Character
	if not Character then return end

	local Humanoid = Character:WaitForChild(`Humanoid`) :: Humanoid
	local Animator = Humanoid:WaitForChild(`Animator`) :: Animator

	local Profile = StateController.GetProfile()
	local RootPart = Humanoid.RootPart :: BasePart

	if Character:WaitForChild(`Animate`, 2) then
		Character.Animate:Destroy()

	end
	-- (audit) the waits above yield: when two characters spawn back to back (menu stage -> school), the older one
	-- could finish here last and take the animations with it, leaving the new character with none
	if Player.Character ~= Character or not Character.Parent then return end

	local Pack: (Folder & { Movement: Folder })? = nil
	local IsEquipped = Humanoid:GetAttribute(`Equip`) :: boolean

	if IsEquipped and Profile and Profile.Weapon then
		Pack = ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(Profile.Weapon)

		if not Pack then
			Pack = ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(`Fist`)
		end
	end

	if not Pack then
		Pack = ReplicatedStorage.Assets.Animations.Default
	end

	local AnimationPack = if Pack and Pack:FindFirstChild(`Movement`) then Pack.Movement else ReplicatedStorage.Assets.Animations.Default.Movement
	local AnimationManager = Shared.Controller :: AnimationManager

	AnimationManager.Humanoid = Humanoid
	AnimationManager.Animator = Animator

	if AnimationManager.CharacterTrove then
		AnimationManager.CharacterTrove:Destroy()
	end
	AnimationManager.CharacterTrove = Trove.new()

	AnimationManager:StopAllTracks()
		:SetTracks(AnimationPack)
		:PlayTrack(`Idle`, .1)

	-- (phase6-strafes) the leg length for the cadence (heights change it), and the directional walk
	local function readLeg()
		local Leg = Character:FindFirstChild(`Left Leg`)
		LegLen = if Leg and Leg:IsA(`BasePart`) then Leg.Size.Y else 2
	end
	readLeg()
	task.delay(2, readLeg) -- the height is applied a moment after spawn
	AnimationManager.CharacterTrove:Connect(Character:GetAttributeChangedSignal(`Height`), function() task.defer(readLeg) end)
	Local.Directional(AnimationManager, Character, Humanoid)

	-- Add cleanup for when character is destroyed
	AnimationManager.CharacterTrove:Connect(Character.AncestryChanged, function(_, parent)
		if not parent and AnimationManager.CharacterTrove then
			AnimationManager.CharacterTrove:Destroy()
			AnimationManager.CharacterTrove = nil
		end
	end)

	-- crouch (Services.Player.Crouch sets the Humanoid attribute Crouch): Crouch / CrouchWalk replace Idle / Walk,
	-- and the camera dips a little
	local LastSpeed = 0
	local function CrouchPose(Speed: number): boolean
		if Humanoid:GetAttribute(`Crouch`) ~= true then return false end
		if Speed > .01 and AnimationManager.TrackTable.CrouchWalk then
			AnimationManager:PlayTrack(`CrouchWalk`, .15)
				:SetSpeed(rate(math.max(Speed, 1), `CrouchWalk`)) -- (phase6-strafes) was / 7
			return true
		elseif Speed <= .01 and AnimationManager.TrackTable.Crouch then
			if AnimationManager.Pose ~= `Crouch` then AnimationManager:PlayTrack(`Crouch`, .15) end
			return true
		end
		return false
	end
	AnimationManager.CharacterTrove:Connect(Humanoid:GetAttributeChangedSignal(`Crouch`), function()
		local On = Humanoid:GetAttribute(`Crouch`) == true
		-- (audit) the camera dip is left to Controllers.Gui.Camera (it eases CameraOffset toward the torso every frame, which
		-- already follows the crouch pose); this tween was overwritten on the next frame and only fought it
		if not CrouchPose(LastSpeed) then
			AnimationManager:PlayTrack(if LastSpeed > .01 then `Walk` else `Idle`, .15)
		end
	end)

	AnimationManager.CharacterTrove:Connect(Humanoid.Running, function(Speed: number)
		LastSpeed = Speed
		if CrouchPose(Speed) then return end
		if Speed > .01 and Humanoid.WalkSpeed > 0 then
			-- (locomotion-pace) the clip by Config.Locomotion.Gaits, the same rule every humanoid NPC uses (AI.Animate, Schedules)
			local Gait = Loco.Gait(Humanoid.WalkSpeed, Speed, LocoCfg)
			if Gait == `FastSprint` then

				AnimationManager:PlayTrack(`FastSprint`, .2)
					:SetSpeed(rate(Speed, `FastSprint`)) -- (phase6-strafes) stride-matched (was / 30)

			elseif Gait == `Sprint` then
				AnimationManager:PlayTrack(`Sprint`, .1)
					:SetSpeed(rate(Speed, `Sprint`)) -- (phase6-strafes) was / 24

			elseif AnimationManager.Pose ~= `Walk8` then -- (phase6-strafes) the directional walk drives its own tracks
				AnimationManager:PlayTrack(`Walk`, .1)
					:SetSpeed(rate(Speed, `Walk`)) -- was / 10

			end

		elseif AnimationManager.Pose ~= `Idle` then
			AnimationManager:PlayTrack(`Idle`, .1)

		end

	end)

	AnimationManager.CharacterTrove:Connect(Humanoid.Jumping, function()
		if AnimationManager.Pose == `Sprint` or AnimationManager.Pose == `FastSprint` then return end
		--AnimationManager.TrackTable.Jump:Play()
		AnimationManager:PlayTrack(`Jump`)

	end)

	local FallToken = 0
	AnimationManager.CharacterTrove:Connect(Humanoid.FreeFalling, function()
		if AnimationManager.Pose == `Sprint` or AnimationManager.Pose == `FastSprint` then return end
		-- (2026-11-05) let the jump play out: the fall used to replace it the instant you left the ground. Fall takes
		-- over once the jump clip ends or you start coming down.
		local Jump = AnimationManager.TrackTable.Jump
		if AnimationManager.Pose == `Jump` and Jump and Jump.IsPlaying then
			FallToken += 1
			local Me = FallToken
			task.spawn(function()
				local Root = Humanoid.RootPart
				while Me == FallToken and Jump.IsPlaying and AnimationManager.Pose == `Jump` and Root and Root.AssemblyLinearVelocity.Y > -4
					and Humanoid:GetState() == Enum.HumanoidStateType.Freefall do
					task.wait()
				end
				if Me == FallToken and AnimationManager.Pose == `Jump` and Humanoid:GetState() == Enum.HumanoidStateType.Freefall then
					AnimationManager:PlayTrack(`Fall`, .3)
				end
			end)
			return
		end
		AnimationManager:PlayTrack(`Fall`, .3)

	end)

	-- (2026-11-05) the owner's landing animation: a one-shot over the legs when you touch down from a jump or fall
	-- (skipped while sprinting, like the jump). It plays on top of whatever pose comes next, so nothing waits on it.
	AnimationManager.CharacterTrove:Connect(Humanoid.StateChanged, function(Old, New)
		if New ~= Enum.HumanoidStateType.Landed or Old ~= Enum.HumanoidStateType.Freefall then return end
		if AnimationManager.Pose == `Sprint` or AnimationManager.Pose == `FastSprint` then return end
		local Land = AnimationManager.TrackTable.Land
		if not Land then return end
		local Jump = AnimationManager.TrackTable.Jump
		if Jump and Jump.IsPlaying then Jump:Stop(0.1) end
		Land:Play(0.05)
	end)
end

function Animate.PlayTrack(self: AnimationManager, NewPose: string, Time: number)
	-- (phase6-strafes) the directional walk keeps the Walk track itself; any other pose ends it first
	if self.Pose == `Walk8` then
		if NewPose == `Walk` then return self end
		Local.EndDirectional(self, Time)
	end
	local CurrentTrack = self.TrackTable[self.Pose]
	local CurrentSpeed = if CurrentTrack then CurrentTrack.Speed else 0

	if not self.TrackTable[NewPose] then 
		return self
	end

	if self.Pose ~= NewPose then
		if CurrentTrack then
			self.TimePosition[self.Pose] = CurrentTrack.TimePosition
			CurrentTrack:Stop(Time)
		end

		self.Pose = NewPose

		CurrentTrack = self.TrackTable[self.Pose]
		CurrentTrack:Play(Time)

		local TimePosition = self.TimePosition[self.Pose]
		if TimePosition then
			CurrentTrack.TimePosition = TimePosition 

		end

		CurrentSpeed = 1.0
	end

	return self
end

function Animate.SetSpeed(self: AnimationManager, Speed: number)
	local CurrentTrack = self.TrackTable[self.Pose]
	local CurrentSpeed = if CurrentTrack then CurrentTrack.Speed else 0

	if not CurrentTrack then 
		return self 
	end

	if Speed ~= CurrentSpeed then
		CurrentSpeed = Speed
		CurrentTrack:AdjustSpeed(CurrentSpeed)

	end

	return self
end

function Animate.UpdateTrack(self: AnimationManager, Pose: string, Animation: Animation)
	if not self.TrackTable[Pose] then
		return self
	end

	if Pose == self.Pose then
		self:Stop()
	end

	if self.TrackTable[Pose] then
		self.TrackTable[Pose]:Destroy()
	end

	self.TrackTable[Pose] = self.Animator:LoadAnimation(Animation)

	if self.Pose then
		local CurrentTrack = self.TrackTable[self.Pose]
		local CurrentSpeed = CurrentTrack.Speed

		CurrentTrack:Play()
		CurrentTrack:AdjustSpeed(CurrentSpeed)
	end

	return self
end

function Animate.SetTracks(self: AnimationManager, Tracks: { Animation })
	local Tracks = Tracks or script:FindFirstChild(`Tracks`)
	if not Tracks then 
		return self 
	end

	self:Stop()
	self.Tracks = Tracks
	-- (audit) drop the whole old pack first: a pose the new pack lacks (e.g. CrouchWalk) kept playing the old clip
	for _, Old in self.TrackTable do
		pcall(function() Old:Stop(0) Old:Destroy() end)
	end
	table.clear(self.TrackTable)

	for _, Animation: Animation in Tracks:GetChildren() do

		if Animation:IsA(`Animation`) then
			-- Stop and destroy old track before replacing to prevent memory leak
			if self.TrackTable[Animation.Name] then
				if self.TrackTable[Animation.Name].IsPlaying then
					self.TrackTable[Animation.Name]:Stop(0)
				end
				self.TrackTable[Animation.Name]:Destroy()
				self.TrackTable[Animation.Name] = nil
			end

			local MovementTag = { `Walk`; `Sprint`; `FastSprint`; `Fall`; `Crouch`; `CrouchWalk` }
			self.TrackTable[Animation.Name] = self.Animator:LoadAnimation(Animation)

			if Animation.Name == `Idle` then
				self.TrackTable[Animation.Name].Priority = Enum.AnimationPriority.Idle;
			end

			if Animation.Name == `Jump` then
				self.TrackTable[Animation.Name].Priority = Enum.AnimationPriority.Idle;
			end

			if Animation.Name == `Land` then -- (2026-11-05) over Idle and Walk, under attacks
				self.TrackTable[Animation.Name].Priority = Enum.AnimationPriority.Movement;
				self.TrackTable[Animation.Name].Looped = false
			end

			if table.find(MovementTag, Animation.Name) then
				self.TrackTable[Animation.Name].Priority = Enum.AnimationPriority.Core;
			end

		end

	end

	self.TimePosition = {}
	if self.Pose == `Walk8` then self.Pose = `Walk` end -- (phase6-strafes) the pack swap ends the directional walk
	if self.Pose and not self.TrackTable[self.Pose] then self.Pose = nil end -- (audit) the new pack lacks this pose
	Local.LoadDirectional(self) -- (phase6-strafes) StopAllTracks / the cleared table took the strafes with them

	if self.Pose then
		local CurrentTrack = self.TrackTable[self.Pose]
		local CurrentSpeed = CurrentTrack.Speed

		CurrentTrack:Play()
		CurrentTrack:AdjustSpeed(CurrentSpeed)
	end

	return self
end

function Animate.Stop(self: AnimationManager)

	for _,Track in self.TrackTable do
		if Track and Track.IsPlaying then
			Track:Stop()
		end
	end

	return self
end

function Animate.StopAllTracks(self: AnimationManager)

	for _,Track in self.Animator:GetPlayingAnimationTracks() do
		Track:Stop()
	end

	return self
end

---| (phase6-strafes) the directional walk |---
-- In lock-on, shift lock or first person (any input), moving at walk speed blends Walk, the reversed Walk (back) and
-- the square-chest strafes by the move angle, their foot contacts phase-locked; the server caps the speed at
-- Config.Locomotion.StrafeSpeed while it runs (NHStrafe -> Features.CombatSpeed). Off during cuts and approaches.

local Directional = { Left = nil :: AnimationTrack?, Right = nil :: AnimationTrack?, Back = nil :: AnimationTrack? } -- Back: (soccer-2.0) only with an Override
local Studio = RunService:IsStudio()
local StrafeOn, Since, Sent = false, 0, nil :: boolean?
local Remote: RemoteEvent? = nil

local function strafeId(Square: string, Studio: string, Original: string): string?
	local Id = LocoCfg.Ids[Square]
	if Id and Id ~= 0 then return `rbxassetid://{Id}` end
	if RunService:IsStudio() then
		local F = ReplicatedStorage:FindFirstChild(`NHLocoClips`)
		local KS = F and F:FindFirstChild(LocoCfg.Studio[Square])
		if KS then
			local Ok, Temp = pcall(function() return KeyframeSequenceProvider:RegisterKeyframeSequence(KS) end)
			if Ok then return Temp end
		end
	end
	local A = ReplicatedStorage.Assets.Animations.Movement:FindFirstChild(Studio)
	if A and A:IsA(`Animation`) and A.AnimationId ~= `` then return A.AnimationId end
	local O = LocoCfg.Ids[Original]
	return if O and O ~= 0 then `rbxassetid://{O}` else nil
end

function Local.LoadDirectional(self)
	for K, T in Directional do pcall(function() T:Stop(0) T:Destroy() end) Directional[K] = nil end
	if not self.Animator then return end
	for Side, Keys in { Left = { `StrafeLeftSquare`, `StrafeLeft`, `StrafeLeft` }, Right = { `StrafeRightSquare`, `StrafeRight`, `StrafeRight` } } do
		local Id = (Over and Over[Side]) or strafeId(Keys[1], Keys[2], Keys[3])
		if Id then
			local A = Instance.new(`Animation`)
			A.Name = `Strafe{Side}`
			A.AnimationId = Id
			local Ok, T = pcall(function() return self.Animator:LoadAnimation(A) end)
			if Ok and T then
				T.Priority = Enum.AnimationPriority.Core
				T.Looped = true
				Directional[Side] = T
			end
		end
	end
	-- (soccer-2.0) a real backpedal clip (the reversed Walk otherwise)
	if Over and Over.Back then
		local A = Instance.new(`Animation`)
		A.Name = `Back`
		A.AnimationId = Over.Back
		local Ok, T = pcall(function() return self.Animator:LoadAnimation(A) end)
		if Ok and T then T.Priority = Enum.AnimationPriority.Core T.Looped = true Directional.Back = T end
	end
end

local function send(On: boolean)
	if Sent == On then return end
	Sent = On
	if not Remote then
		local R = ReplicatedStorage:FindFirstChild(`Remotes`)
		Remote = R and R:FindFirstChild(`NHStrafe`) :: RemoteEvent?
	end
	if Remote then Remote:FireServer({ On = On }) end
end

function Local.EndDirectional(self, Fade: number?)
	for _, T in Directional do if T and T.IsPlaying then T:Stop(Fade or LocoCfg.Fade) end end
	local Walk = self.TrackTable and self.TrackTable.Walk
	if Walk then Walk:AdjustWeight(1, Fade or LocoCfg.Fade) end
	if self.Pose == `Walk8` then self.Pose = `Walk` end
	StrafeOn = false
	send(false)
end

local function flags(Character: Model, Humanoid: Humanoid)
	local P = Players.LocalPlayer
	local F = {}
	for _, N in LocoCfg.Blockers do
		F[N] = P:GetAttribute(N) or Character:GetAttribute(N)
	end
	F.Busy = StateManager.HasState(Character, BUSY)
	local Locked = false
	pcall(function() Locked = require(script.Parent.InputController.Combat.LockOn.Core).Locked() ~= nil end)
	if RunService:IsStudio() and P:GetAttribute(`NHStrafeTest`) == `Lock` then Locked = true end -- checks/strafecheck.lua
	-- something else turned AutoRotate off (skateboard, football dive): not a facing mode
	if Humanoid.AutoRotate == false and not Locked then F.Busy = true end
	local Cam = workspace.CurrentCamera
	local Head = Character:FindFirstChild(`Head`) :: BasePart?
	return {
		Locked = Locked;
		MouseLocked = UserInputService.MouseBehavior == Enum.MouseBehavior.LockCenter;
		FirstPerson = Cam ~= nil and Head ~= nil and (Cam.CFrame.Position - Head.Position).Magnitude < LocoCfg.FirstPersonDist;
		Blocked = Loco.Blocked(F, LocoCfg);
	}
end

function Local.Directional(self, Character: Model, Humanoid: Humanoid)
	Local.LoadDirectional(self)
	StrafeOn, Since, Sent = false, 0, nil
	self.CharacterTrove:Connect(RunService.PreAnimation, function(Dt: number)
		local Root = Humanoid.RootPart
		local Walk = self.TrackTable.Walk
		if not (Root and Walk and Directional.Left and Directional.Right) then return end
		local Move = Humanoid.MoveDirection
		local Gait = if self.Pose == `Walk8` then `Walk` else self.Pose
		local F = flags(Character, Humanoid)
		F.Gait = Gait
		local Want = Loco.StrafeMode(F) and Move.Magnitude > 0.1 and Humanoid:GetAttribute(`Crouch`) ~= true
		if Want then Since += Dt else Since = 0 end
		if not StrafeOn then
			if Want and Since >= LocoCfg.EnterHold and self.Pose == `Walk` then
				StrafeOn = true
				self.Pose = `Walk8`
				send(true)
			else
				return
			end
		elseif not Want then
			Local.EndDirectional(self)
			return
		end
		-- the blend
		local L = Root.CFrame:VectorToObjectSpace(Move)
		local A = math.atan2(L.X, -L.Z)
		local W = Loco.Weights(A)
		local V = Root.AssemblyLinearVelocity
		local Ground = Vector3.new(V.X, 0, V.Z).Magnitude
		local Back = Directional.Back -- (soccer-2.0) a real backpedal clip takes the Back weight
		local WalkW = W.Walk + (if Back then 0 else W.Back)
		local Sign = if not Back and W.Back > W.Walk then -1 else 1
		if not Walk.IsPlaying then Walk:Play(0.1) end
		Walk:AdjustWeight(math.max(WalkW, 0.001), 0.1)
		Walk:AdjustSpeed(Sign * rate(Ground, `Walk`))
		for Side, T in Directional do
			local Wt = if Side == `Left` then W.Left elseif Side == `Right` then W.Right else W.Back
			if Wt > 0.02 then
				if not T.IsPlaying then T:Play(LocoCfg.Fade, Wt) end
				T:AdjustWeight(Wt, 0.1)
				T:AdjustSpeed(rate(Ground, if Side == `Back` then `Back` else `Strafe{Side}`))
				-- phase-lock the strafe's left-foot contact to the walk's (forward diagonals only; the backpedal is reversed)
				if Side ~= `Back` and Sign > 0 and WalkW > 0.05 and T.Length > 0 and Walk.Length > 0 then
					T.TimePosition = Loco.Phase(Walk.TimePosition, Walk.Length, T.Length, LocoCfg.ContactPhase.Walk, LocoCfg.ContactPhase[`Strafe{Side}`] or LocoCfg.ContactPhase.Strafe)
				end
			elseif T.IsPlaying then
				T:Stop(LocoCfg.Fade)
			end
		end
	end)
	self.CharacterTrove:Add(function() StrafeOn = false send(false) end)
end

-- (soccer-2.0) Studio checks (tools/soccer2/checks/soccer_play_pack*.lua)
function Shared.DirectionalForTests() return Directional end

return Shared
