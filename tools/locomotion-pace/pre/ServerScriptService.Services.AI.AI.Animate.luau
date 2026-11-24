local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local EntityLoader = require(ServerScriptService.Services.Managers.EntityLoader)

local Character = script.Parent :: Model
local Humanoid = Character:WaitForChild(`Humanoid`) :: Humanoid
local Animator = Humanoid:WaitForChild(`Animator`) :: Animator

type AnimationTracks = {
	Idle: AnimationTrack?;
	Walk: AnimationTrack?;
	Sprint: AnimationTrack?;
	FastSprint: AnimationTrack?;
	Jump: AnimationTrack?;
	Fall: AnimationTrack?;
}

local Cache = {
	Tracks = {} :: AnimationTracks;
	CurrentPose = nil :: string?;
	AnimationFolder = nil :: Folder?;
}

local Local = {}

function Local.GetAnimationPack(): Folder?
	local Data = EntityLoader.GetProfile(Character)
	local WeaponName = Data and Data.Weapon or nil

	local Pack: Folder? = nil

	if WeaponName then
		Pack = ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(WeaponName) :: Folder?
	end

	if not Pack then
		Pack = ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(`Fist`) :: Folder?
	end

	if not Pack then
		Pack = ReplicatedStorage.Assets.Animations.Default :: Folder?
	end

	local AnimationFolder = if Pack and Pack:FindFirstChild(`Movement`) 
		then Pack.Movement :: Folder 
		else ReplicatedStorage.Assets.Animations.Default.Movement :: Folder

	return AnimationFolder
end

-- An NPC's normal idle and walk are a player's unarmed ones (owner, 2026-11-03): always the Default movement pack,
-- not their weapon pack (NPC profiles carry a Katana, so they stood in a sword stance and walked with a blade).
local UNARMED = { Idle = true; Walk = true }
local WALK_PACE = 5.3 -- studs/s the Default walk clip covers at 1x

function Local.LoadAnimation(animName: string): AnimationTrack?
	local Folder = if UNARMED[animName] then ReplicatedStorage.Assets.Animations.Default.Movement else Cache.AnimationFolder
	if not Folder then return nil end

	local Anim = Folder:FindFirstChild(animName)
	if not Anim or not Anim:IsA(`Animation`) then return nil end

	return Animator:LoadAnimation(Anim :: Animation)
end

function Local.PlayTrack(trackName: string, fadeTime: number?)
	fadeTime = fadeTime or 0.1

	if Cache.CurrentPose == trackName then return end

	if Cache.CurrentPose and Cache.Tracks[Cache.CurrentPose] then
		Cache.Tracks[Cache.CurrentPose]:Stop(fadeTime)
	end

	if Cache.Tracks[trackName] then
		Cache.Tracks[trackName]:Play(fadeTime)
		Cache.CurrentPose = trackName
	end
end

function Local.LoadTracks()
	Cache.Tracks.Idle = Local.LoadAnimation(`Idle`)
	Cache.Tracks.Walk = Local.LoadAnimation(`Walk`)
	Cache.Tracks.Sprint = Local.LoadAnimation(`Sprint`)
	Cache.Tracks.FastSprint = Local.LoadAnimation(`FastSprint`)
	Cache.Tracks.Jump = Local.LoadAnimation(`Jump`)
	Cache.Tracks.Fall = Local.LoadAnimation(`Fall`)

	if Cache.Tracks.Idle then
		Cache.Tracks.Idle.Priority = Enum.AnimationPriority.Core
		Cache.Tracks.Idle:Play()
		Cache.CurrentPose = `Idle`
	end

	if Cache.Tracks.Walk then
		Cache.Tracks.Walk.Priority = Enum.AnimationPriority.Core
	end

	if Cache.Tracks.Sprint then
		Cache.Tracks.Sprint.Priority = Enum.AnimationPriority.Core
	end

	if Cache.Tracks.FastSprint then
		Cache.Tracks.FastSprint.Priority = Enum.AnimationPriority.Core
	end

	if Cache.Tracks.Jump then
		Cache.Tracks.Jump.Priority = Enum.AnimationPriority.Core
	end

	if Cache.Tracks.Fall then
		Cache.Tracks.Fall.Priority = Enum.AnimationPriority.Core
	end
end

function Local.OnRunning(speed: number)
	if speed > 0.01 and Humanoid.WalkSpeed > 0 then
		if Humanoid.WalkSpeed > 40 or speed > 40 then
			Local.PlayTrack(`FastSprint`, 0.2)
			if Cache.Tracks.FastSprint then
				Cache.Tracks.FastSprint:AdjustSpeed(speed / 30)
			end
		elseif Humanoid.WalkSpeed > 20 or speed > 20 then
			Local.PlayTrack(`Sprint`, 0.1)
			if Cache.Tracks.Sprint then
				Cache.Tracks.Sprint:AdjustSpeed(speed / 24)
			end
		else
			Local.PlayTrack(`Walk`, 0.1)
			if Cache.Tracks.Walk then
				-- the walk clip covers about 5.3 studs/s at 1x (measured on this 0.9-scale rig, 2026-11-03): play it at
				-- the pace they're moving so the feet keep to the ground (speed / 10 had them sliding at twice the stride)
				Cache.Tracks.Walk:AdjustSpeed(speed / WALK_PACE)
			end
		end
	else
		if Cache.Tracks.Idle then
			Local.PlayTrack(`Idle`, 0.1)
		end
	end
end

function Local.OnSprintChanged()
	task.wait(0.05)

	local RootPart = Character:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not RootPart then return end

	local Velocity = RootPart.AssemblyLinearVelocity.Magnitude
	local IsMoving = Velocity > 1

	if not IsMoving then return end

	if Humanoid.WalkSpeed > 40 or Velocity > 40 then
		if Cache.Tracks.FastSprint then
			Local.PlayTrack(`FastSprint`, 0.2)
			Cache.Tracks.FastSprint:AdjustSpeed(Velocity / 30)
		end
	elseif Humanoid.WalkSpeed > 20 or Velocity > 20 then
		if Cache.Tracks.Sprint then
			Local.PlayTrack(`Sprint`, 0.15)
			Cache.Tracks.Sprint:AdjustSpeed(Velocity / 24)
		end
	else
		if Cache.Tracks.Walk then
			Local.PlayTrack(`Walk`, 0.15)
			Cache.Tracks.Walk:AdjustSpeed(Velocity / 10)
		end
	end
end

function Local.OnJumping()
	if Cache.Tracks.Jump then
		Cache.Tracks.Jump:Play(0.1)
	end
end

function Local.OnFreeFalling()
	if Cache.Tracks.Fall then
		Local.PlayTrack(`Fall`, 0.3)
	end
end

function Local.OnDied()
	for _, track in Cache.Tracks do
		if track then
			track:Stop(0)
		end
	end
end


Cache.AnimationFolder = Local.GetAnimationPack()
Local.LoadTracks()

Humanoid.Running:Connect(Local.OnRunning)
Humanoid:GetAttributeChangedSignal(`Sprint`):Connect(Local.OnSprintChanged)
Humanoid.Jumping:Connect(Local.OnJumping)
Humanoid.FreeFalling:Connect(Local.OnFreeFalling)
Humanoid.Died:Connect(Local.OnDied)
