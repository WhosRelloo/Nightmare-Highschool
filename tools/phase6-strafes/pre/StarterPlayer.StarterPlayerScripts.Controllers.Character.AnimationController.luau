
---| Services |---

local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

---| Modules |---

local LinearVelocity = require(ReplicatedStorage.Functions.LinearVelocity)
local TrackService = require(ReplicatedStorage.Packages.TrackService)
local Packets = require(ReplicatedStorage.Remotes.Packets)
local Trove = require(ReplicatedStorage.Packages.Trove)

local StateController = require(script.Parent.Parent.StateController)

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
				:SetSpeed(math.max(Speed, 1) / 7)
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
			if Humanoid.WalkSpeed > 40 or Speed > 40 then

				AnimationManager:PlayTrack(`FastSprint`, .2)
					:SetSpeed(Speed / 30)

			elseif Humanoid.WalkSpeed > 20 or Speed > 20 then
				AnimationManager:PlayTrack(`Sprint`, .1)
					:SetSpeed(Speed / 24)

			else
				AnimationManager:PlayTrack(`Walk`, .1)
					:SetSpeed(Speed / 10)

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
	if self.Pose and not self.TrackTable[self.Pose] then self.Pose = nil end -- (audit) the new pack lacks this pose

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

return Shared
