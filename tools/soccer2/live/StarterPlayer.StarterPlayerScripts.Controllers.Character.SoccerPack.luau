--[[
	Soccer pack (client, soccer-2.0): the match walk and idle. While the local player is in a soccer match (the Player
	attribute InSport names a venue whose SportVenue is "Soccer"), the movement pack is Default's with Idle = Soccer
	Idle (Offensive Idle with the ball, Goalkeeper Idle for the keeper in their zone) and Walk = Jog Forward. Through
	AnimationController.Override the jog keeps its own stride, Jog Backward is the backpedal, and the keeper's side
	steps replace the strafes. Leaving the match puts back the pack Transformation's restorePack would pick.
	Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §5.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local Player = Players.LocalPlayer
local Controllers = script.Parent.Parent
local Clips = require(Controllers:WaitForChild(`Gui`):WaitForChild(`Soccer`):WaitForChild(`Clips`))

local Shared = {}
local Local = {}

local On = false
local IdleSlot = nil :: string?
local Keeper = false
local SportsMod = nil :: any

local function ac(): any?
	local Ok, AC = pcall(require, script.Parent:WaitForChild(`AnimationController`))
	return if Ok then AC else nil
end
local function sports(): any?
	if SportsMod == nil then
		local Ok, S = pcall(require, Controllers.Gui:WaitForChild(`Sports`))
		SportsMod = if Ok then S else false
	end
	return SportsMod or nil
end
local function anim(Name: string, Id: string): Animation
	local A = Instance.new(`Animation`)
	A.Name = Name
	A.AnimationId = Id
	return A
end

function Local.IsSoccer(): boolean
	local V = Player:GetAttribute(`InSport`)
	if type(V) ~= `string` then return false end
	local Root = workspace:FindFirstChild(`Sports`)
	local Venue = Root and Root:FindFirstChild(V)
	return Venue ~= nil and Venue:GetAttribute(`SportVenue`) == `Soccer`
end

function Local.IsKeeper(): boolean
	local S = sports()
	local St = S and S.State()
	return St ~= nil and St.Keeper == true and St.InZone == true
end

function Local.WantIdle(): string
	if Local.IsKeeper() then return `KeeperIdle` end
	local Char = Player.Character
	if Char and Char:GetAttribute(`HasSportBall`) then return `IdleBall` end
	return `Idle`
end

function Local.Pack(): Folder?
	local Idle, Jog = Clips.Id(`Idle`), Clips.Id(`Jog`)
	if not (Idle and Jog) then return nil end
	local F = Instance.new(`Folder`)
	F.Name = `SoccerMovement`
	for _, A in ReplicatedStorage.Assets.Animations.Default.Movement:GetChildren() do
		if A:IsA(`Animation`) and A.Name ~= `Idle` and A.Name ~= `Walk` then A:Clone().Parent = F end
	end
	anim(`Idle`, Idle).Parent = F
	anim(`Walk`, Jog).Parent = F
	return F
end

function Local.Override()
	local AC = ac()
	if not AC then return end
	local D = Clips.Data()
	local St = (D and D.Stride) or {}
	local O = { Stride = { Walk = St.SoccerJog; Back = St.SoccerJogBack }; Back = (Clips.Id(`JogBack`)) }
	Keeper = Local.IsKeeper()
	if Keeper then
		O.Left = (Clips.Id(`KeeperStepLeft`))
		O.Right = (Clips.Id(`KeeperStepRight`))
		O.Stride.StrafeLeft = St.KeeperStep
		O.Stride.StrafeRight = St.KeeperStep
	end
	AC.Override(O)
end

-- swap the Idle track in place (no restart of a playing walk)
function Local.SetIdle(Slot: string)
	local AC = ac()
	local AM = AC and AC.Controller
	if not (AM and AM.Animator and AM.TrackTable and AM.TrackTable.Idle) then return end
	local Id = Clips.Id(Slot) or Clips.Id(`Idle`)
	if not Id then return end
	IdleSlot = Slot
	pcall(function()
		local Old = AM.TrackTable.Idle
		local Playing = AM.Pose == `Idle` and Old.IsPlaying
		local New = AM.Animator:LoadAnimation(anim(`Idle`, Id))
		New.Priority = Enum.AnimationPriority.Idle
		New.Looped = true
		AM.TrackTable.Idle = New
		Old:Stop(0.2)
		task.delay(0.3, function() pcall(function() Old:Destroy() end) end)
		if Playing then New:Play(0.2) end
	end)
end

function Local.Apply()
	local AC = ac()
	local AM = AC and AC.Controller
	local Char = Player.Character
	-- the AnimationController must already be on this body (it rebuilds the pack a moment after a respawn)
	if not (AM and AM.Animator and Char and AM.Animator:IsDescendantOf(Char) and AM.TrackTable.Idle) then return end
	local Pack = Local.Pack()
	if not Pack then return end
	On = true
	Local.Override()
	pcall(function()
		AM:StopAllTracks():SetTracks(Pack):PlayTrack(`Idle`, 0.2)
		for _, N in { `Idle`, `Walk` } do local T = AM.TrackTable[N] if T then T.Looped = true end end
	end)
	IdleSlot = `Idle`
	local Want = Local.WantIdle()
	if Want ~= IdleSlot then Local.SetIdle(Want) end
end

function Local.Restore()
	On = false
	IdleSlot = nil
	Keeper = false
	local AC = ac()
	if not AC then return end
	AC.Override(nil)
	local AM = AC.Controller
	local Char = Player.Character
	if not (AM and AM.Animator and Char) then return end
	-- the same choice as Transformation's restorePack: the weapon pack when equipped, else Default
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	local W = Char:GetAttribute(`Weapon`)
	local Pack = (Hum and Hum:GetAttribute(`Equip`) and W and ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(W)) or ReplicatedStorage.Assets.Animations.Default
	pcall(function() AM:StopAllTracks():SetTracks(Pack.Movement):PlayTrack(`Idle`, 0.15) end)
end

function Local.Step()
	local Want = Local.IsSoccer()
	if Want and not On then Local.Apply()
	elseif not Want and On then Local.Restore()
	elseif not Want then
		-- a respawn can clear On before InSport goes: never leave the override set outside a match
		local AC = ac()
		if AC and AC.Overridden() then AC.Override(nil) end
	end
	if not On then return end
	if Local.IsKeeper() ~= Keeper then Local.Override() end
	local Idle = Local.WantIdle()
	if Idle ~= IdleSlot then Local.SetIdle(Idle) end
end

function Shared.OnStart()
	-- a light poll (4 Hz): InSport, the keeper's zone and the ball come from three places
	task.spawn(function()
		while true do
			local Ok, Err = pcall(Local.Step)
			if not Ok then warn(`[SoccerPack] {Err}`) end
			task.wait(0.25)
		end
	end)
	-- a new body starts on the default pack; the next tick re-applies (Apply waits for the controller to be on it)
	Player.CharacterAdded:Connect(function()
		On = false
		IdleSlot = nil
		Keeper = false
		local AC = ac()
		if AC then AC.Override(nil) end -- the next Step turns the pack back on if the match goes on
	end)
end

-- (soccer-2.0) Studio checks
function Shared.StateForTests() return { On = On; Idle = IdleSlot; Keeper = Keeper } end

return Shared
