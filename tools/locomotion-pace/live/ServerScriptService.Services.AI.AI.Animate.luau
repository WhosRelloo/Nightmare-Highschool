local ReplicatedStorage = game:GetService(`ReplicatedStorage`)
local ServerScriptService = game:GetService(`ServerScriptService`)

local EntityLoader = require(ServerScriptService.Services.Managers.EntityLoader)
-- (locomotion-pace) the player's rules: which clip a speed plays (Gait) and the stride-matched rate (Rate)
local LocoCfg = require(ReplicatedStorage.Config.Locomotion)
local Loco = require(ReplicatedStorage.Functions.Locomotion)

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
	Land: AnimationTrack?;
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
-- (locomotion-pace) the leg length the stride scales by (Config.Locomotion.Stride is per 2-stud leg), read again once the
-- body is built and when its height changes
local LegLen = 2
local function readLeg()
	local Leg = Character:FindFirstChild(`Left Leg`)
	if Leg and Leg:IsA(`BasePart`) then LegLen = Leg.Size.Y end
end
local function rate(Speed: number, Gait: string): number
	return Loco.Rate(Speed, LocoCfg.Stride[Gait] or LocoCfg.Stride.Walk, LegLen, LocoCfg)
end
local function sprinting(): boolean
	return Cache.CurrentPose == `Sprint` or Cache.CurrentPose == `FastSprint`
end

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
	Cache.Tracks.Land = Local.LoadAnimation(`Land`) or (function()
		local A = ReplicatedStorage.Assets.Animations.Default.Movement:FindFirstChild(`Land`)
		return if A and A:IsA(`Animation`) then Animator:LoadAnimation(A) else nil
	end)()

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

	if Cache.Tracks.Land then -- a one-shot over the walk, under attacks (as the player's)
		Cache.Tracks.Land.Priority = Enum.AnimationPriority.Movement
		Cache.Tracks.Land.Looped = false
	end
end

-- (locomotion-pace) the player's AnimationController rule: Loco.Gait picks the clip from the set speed and the ground
-- speed (was > 40 / > 20), Loco.Rate plays it stride-matched to these legs (was speed / 30, / 24, / 5.3)
function Local.PlayGait(speed: number, fade: number)
	local Gait = Loco.Gait(Humanoid.WalkSpeed, speed, LocoCfg)
	if not Cache.Tracks[Gait] then Gait = `Walk` end
	Local.PlayTrack(Gait, if Gait == `FastSprint` then 0.2 else fade)
	local T = Cache.Tracks[Gait]
	if T then T:AdjustSpeed(rate(speed, Gait)) end
end

function Local.OnRunning(speed: number)
	if speed > 0.01 and Humanoid.WalkSpeed > 0 then
		Local.PlayGait(speed, 0.1)
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

	local V = RootPart.AssemblyLinearVelocity
	local Velocity = Vector3.new(V.X, 0, V.Z).Magnitude -- (locomotion-pace) ground speed, as Running reports it
	if Velocity <= 1 then return end

	Local.PlayGait(Velocity, 0.15)
end

function Local.OnJumping()
	if sprinting() then return end -- (locomotion-pace) as the player: the run carries through a hop
	if Cache.Tracks.Jump then
		Cache.Tracks.Jump:Play(0.1)
	end
end

function Local.OnFreeFalling()
	if sprinting() then return end
	if Cache.Tracks.Fall then
		Local.PlayTrack(`Fall`, 0.3)
	end
end

-- (locomotion-pace) the landing one-shot when they touch down from a fall, skipped while sprinting (as the player's)
function Local.OnStateChanged(Old: Enum.HumanoidStateType, New: Enum.HumanoidStateType)
	if New ~= Enum.HumanoidStateType.Landed or Old ~= Enum.HumanoidStateType.Freefall then return end
	if sprinting() or not Cache.Tracks.Land then return end
	if Cache.Tracks.Jump and Cache.Tracks.Jump.IsPlaying then Cache.Tracks.Jump:Stop(0.1) end
	Cache.Tracks.Land:Play(0.05)
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
readLeg()
task.delay(2, readLeg) -- the body may be scaled after this script starts
Character:GetAttributeChangedSignal(`Height`):Connect(function() task.defer(readLeg) end)

Humanoid.Running:Connect(Local.OnRunning)
Humanoid:GetAttributeChangedSignal(`Sprint`):Connect(Local.OnSprintChanged)
Humanoid.Jumping:Connect(Local.OnJumping)
Humanoid.FreeFalling:Connect(Local.OnFreeFalling)
Humanoid.StateChanged:Connect(Local.OnStateChanged)
Humanoid.Died:Connect(Local.OnDied)
