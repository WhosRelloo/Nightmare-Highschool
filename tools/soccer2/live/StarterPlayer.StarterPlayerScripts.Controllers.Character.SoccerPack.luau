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
local ContentProvider = game:GetService(`ContentProvider`)

local Player = Players.LocalPlayer
local Controllers = script.Parent.Parent
local Clips = require(Controllers:WaitForChild(`Gui`):WaitForChild(`Soccer`):WaitForChild(`Clips`))

local Shared = {}
local Local = {}

local On = false
local IdleSlot = nil :: string?
local Keeper = false
local SportsMod = nil :: any
local Preloaded = false
local RestoreFailed = false                           -- (soccer-2.0 final) a failed Restore is retried on the next Step
local IdleCache = {} :: { [string]: AnimationTrack }  -- (soccer-2.0 final) one idle track per idle clip on this body
local IdleFor = nil :: Animator?

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
	-- (soccer-2.0 final) a stride is the FIER clip's, so it is set only when that clip resolved (a partial publish keeps
	-- Default's stride for a gait whose clip is missing)
	local _, JogFier = Clips.Id(`Jog`)
	local Back, BackFier = Clips.Id(`JogBack`)
	local O = { Stride = {}; Back = Back }
	if JogFier then O.Stride.Walk = St.SoccerJog end
	if Back and BackFier then O.Stride.Back = St.SoccerJogBack end
	Keeper = Local.IsKeeper()
	if Keeper then
		local L, LFier = Clips.Id(`KeeperStepLeft`)
		local R, RFier = Clips.Id(`KeeperStepRight`)
		O.Left = L
		O.Right = R
		if L and LFier then O.Stride.StrafeLeft = St.KeeperStep end
		if R and RFier then O.Stride.StrafeRight = St.KeeperStep end
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
		if IdleFor ~= AM.Animator then IdleCache = {} IdleFor = AM.Animator end
		local Old = AM.TrackTable.Idle
		local Playing = AM.Pose == `Idle` and Old.IsPlaying
		-- (soccer-2.0 final) reuse this body's track for the clip (no LoadAnimation per possession change)
		local New = IdleCache[Id]
		if not New then
			New = AM.Animator:LoadAnimation(anim(`Idle`, Id))
			New.Priority = Enum.AnimationPriority.Idle
			New.Looped = true
			IdleCache[Id] = New
		end
		if New == Old then return end
		AM.TrackTable.Idle = New
		Old:Stop(0.2)
		if not table.find(Local.Cached(), Old) then task.delay(0.3, function() pcall(function() Old:Destroy() end) end) end
		if Playing then New:Play(0.2) end
	end)
end

function Local.Cached(): { AnimationTrack }
	local L = {}
	for _, T in IdleCache do table.insert(L, T) end
	return L
end

-- (soccer-2.0 final) every slot's clip loads before its first play (a kick's jump to contact needs the Length)
function Local.Preload()
	if Preloaded then return end
	Preloaded = true
	task.spawn(function()
		pcall(function()
			local Config = require(ReplicatedStorage:WaitForChild(`Config`):WaitForChild(`Sports`))
			local List = {}
			for Slot in Config.SoccerAnims do
				local Id = Clips.Id(Slot)
				if Id then table.insert(List, anim(Slot, Id)) end
			end
			ContentProvider:PreloadAsync(List)
		end)
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
	Local.Preload()
	On = true
	RestoreFailed = false
	Local.Override()
	pcall(function()
		AM:StopAllTracks():SetTracks(Pack):PlayTrack(`Idle`, 0.2)
		for _, N in { `Idle`, `Walk` } do local T = AM.TrackTable[N] if T then T.Looped = true end end
	end)
	-- the pack's own Idle track is the Idle clip's cached one
	IdleCache = {}
	IdleFor = AM.Animator
	local IdleId = Clips.Id(`Idle`)
	if IdleId and AM.TrackTable.Idle then IdleCache[IdleId] = AM.TrackTable.Idle end
	IdleSlot = `Idle`
	local Want = Local.WantIdle()
	if Want ~= IdleSlot then Local.SetIdle(Want) end
end

function Local.Restore()
	On = false
	IdleSlot = nil
	Keeper = false
	local Retry = RestoreFailed
	RestoreFailed = false
	Clips.Cancel() -- (soccer-2.0 final, spec §6) a running clip dash ends with the match
	local AC = ac()
	if not AC then RestoreFailed = true return end
	AC.Override(nil)
	local AM = AC.Controller
	local Char = Player.Character
	if not (AM and AM.Animator and Char) then return end
	-- the same choice as Transformation's restorePack: the weapon pack when equipped, else Default
	local Hum = Char:FindFirstChildWhichIsA(`Humanoid`)
	local W = Char:GetAttribute(`Weapon`)
	local Pack = (Hum and Hum:GetAttribute(`Equip`) and W and ReplicatedStorage.Assets.Animations.Weapons:FindFirstChild(W)) or ReplicatedStorage.Assets.Animations.Default
	local Ok, Err = pcall(function() AM:StopAllTracks():SetTracks(Pack.Movement):PlayTrack(`Idle`, 0.15) end)
	-- the soccer idles SetTracks didn't take with it
	local Cur = AM.TrackTable and AM.TrackTable.Idle
	for _, T in IdleCache do if T ~= Cur then pcall(function() T:Stop(0) T:Destroy() end) end end
	IdleCache = {}
	IdleFor = nil
	if not Ok then
		RestoreFailed = true -- (soccer-2.0 final) the next Step tries again
		if not Retry then warn(`[SoccerPack] Restore failed, retrying: {Err}`) end
	end
end

function Local.Step()
	local Want = Local.IsSoccer()
	if Want and not On then Local.Apply()
	elseif not Want and (On or RestoreFailed) then Local.Restore()
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
		RestoreFailed = false -- a new body starts on the default pack
		IdleCache = {}
		IdleFor = nil
		local AC = ac()
		if AC then AC.Override(nil) end -- the next Step turns the pack back on if the match goes on
	end)
end

-- (soccer-2.0) Studio checks
function Shared.StateForTests() return { On = On; Idle = IdleSlot; Keeper = Keeper } end

return Shared
