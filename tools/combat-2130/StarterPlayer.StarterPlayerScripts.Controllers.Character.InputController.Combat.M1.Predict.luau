--[[
	Predict (client, under InputController.Combat.M1): combat concept 12 (2.13.0). Client-predicted swings.

	A ground M1 used to start only when the server's animation reached you, one round trip after the click. Now the
	client starts the same swing the moment you click, guessing which hit of the string the server will play. The
	guess goes out with the press (M1 packet flags: + index * 8):
	  * if the server plays the same hit, it plays its own copy almost invisibly (weight 0.01) and keeps it for timing
	    (hit frame, end lag, cancels). Ours is what everyone sees, since a player's own animations replicate. When the
	    server's copy stops (stunned, feinted, cancelled into an ender), ours stops with it;
	  * if the server plays a different hit, it plays it normally and ours fades out at once;
	  * if the server won't play it (cooldown, busy, buffered for later, the clinch, a running or air swing), it bumps the
	    character's NHPredictRefused attribute and ours fades out at once (a 1-1.5 s timeout covers a lost reply).
	It only predicts when the outcome is near certain: on the ground, not sprinting (running M1), not holding block
	(that click is the clinch; InputController.General.Block keeps NHBlockHeld on the local player), not attacking,
	stunned or busy, not right after the string's last hit (its cooldown),
	and not on the 1 s combo-reset edge. Otherwise the press goes out unpredicted and the old path runs.

	Off switch: ReplicatedStorage attribute NHPredictOff = true.
]]
local Players = game:GetService(`Players`)
local ReplicatedStorage = game:GetService(`ReplicatedStorage`)

local StateManager = require(ReplicatedStorage.Packages.Bind.StateManager)
local WeaponsConfig = require(ReplicatedStorage.Config.Weapons)

local COMBO_RESET = 1 -- the string restarts this long after the last hit landed (Combat.M1: bLua.ComboCounter(..., 1))
local EDGE = 0.15 -- this close to the reset, the server may count either way: don't guess
local AFTER_LAST = 1.6 -- after the string's last hit, M1 waits out its end lag and a 1 s cooldown
local BLOCKERS = { `Attacking`, `Stun`, `ParryStun`, `Ragdoll`, `Paralyzed`, `SkillInUse`, `Slow`, `Freeze` }

local Predict = {}

local Watched: Model? = nil
local TickSeenAt = 0 -- os.clock() when this character's Tick (the last hit frame) changed
local Last = { Index = 0, At = 0 }
local Pending: { Twin: AnimationTrack, Conn: RBXScriptConnection }? = nil

local function Watch(Character: Model)
	if Watched == Character then return end
	Watched = Character
	TickSeenAt = 0 -- an old Tick of unknown age counts as stale (the string starts over)
	Last = { Index = 0, At = 0 }
	Character:GetAttributeChangedSignal(`Tick`):Connect(function()
		if Watched == Character then TickSeenAt = os.clock() end
	end)
	-- the server says it won't play the swing we started (refused, buffered, the clinch, a running or air swing)
	Character:GetAttributeChangedSignal(`NHPredictRefused`):Connect(function()
		if Watched == Character then Predict.Drop(0.12) end
	end)
end

local function Settle(FadeOut: number?)
	local P = Pending
	Pending = nil
	if not P then return end
	if P.Conn then P.Conn:Disconnect() end
	if FadeOut and P.Twin.IsPlaying then P.Twin:Stop(FadeOut) end
end

-- drop the pending predicted swing (the server refused it)
function Predict.Drop(FadeOut: number?)
	Settle(FadeOut or 0.12)
end

-- Starts the predicted swing and returns its index (1..MaxCombo) for the packet, or nil to send the press unpredicted.
function Predict.Try(Character: Model, Humanoid: Humanoid): number?
	if ReplicatedStorage:GetAttribute(`NHPredictOff`) == true then return nil end
	local Player = Players.LocalPlayer
	if Player:GetAttribute(`InMainMenu`) == true or Character:GetAttribute(`WolfForm`) then return nil end
	if Player:GetAttribute(`NHBlockHeld`) == true then return nil end -- a click while blocking is the clinch (General.Block sets this locally)
	if Humanoid:GetAttribute(`Sprint`) or Humanoid.FloorMaterial == Enum.Material.Air then return nil end
	if StateManager.HasState(Character, BLOCKERS) then return nil end
	if Pending then return nil end

	local Weapon = Character:GetAttribute(`Weapon`)
	local Config = Weapon and WeaponsConfig[Weapon]
	local Clips = Config and Config.Animations and Config.Animations.M1
	if not Clips then return nil end
	Watch(Character)

	local Now = os.clock()
	local Max = Config.MaxCombo or 4
	if Last.Index >= Max and Now - Last.At < AFTER_LAST then return nil end
	-- time since the last hit as the server will count it when this press arrives: the server stamps each hit with
	-- synced server time (NHHitAt, Combat.M1), and the press reaches it about half a round trip from now
	local Ping = 0
	pcall(function() Ping = Player:GetNetworkPing() end)
	local HitAt = Character:GetAttribute(`NHHitAt`)
	local Since = if typeof(HitAt) == `number` then workspace:GetServerTimeNow() + Ping / 2 - HitAt else Now - TickSeenAt
	if math.abs(Since - COMBO_RESET) < EDGE then return nil end
	local Combo = Character:GetAttribute(`Combo`)
	local Index = if typeof(Combo) ~= `number` or Since > COMBO_RESET then 1 else Combo + 1
	if Index > Max then Index = 1 end
	local Clip = Clips[Index]
	local Animator = Humanoid:FindFirstChildOfClass(`Animator`)
	if not (Clip and Animator) then return nil end

	local Twin = Animator:LoadAnimation(Clip)
	Twin.Priority = Enum.AnimationPriority.Action3
	Twin:Play(0)
	if Config.AnimationSpeed then Twin:AdjustSpeed(Config.AnimationSpeed) end
	Last = { Index = Index, At = Now }

	local Ids = {}
	for _, A in Clips do if typeof(A) == `Instance` then Ids[A.AnimationId] = true end end
	local Mine = Clip.AnimationId
	local This = { Twin = Twin, Conn = nil :: any }
	Pending = This
	This.Conn = Animator.AnimationPlayed:Connect(function(Server: AnimationTrack)
		if Server == Twin or not (Server.Animation and Ids[Server.Animation.AnimationId]) then return end
		if Pending ~= This then return end
		if Server.Animation.AnimationId == Mine then
			-- the server's copy (weight 0.01): ours lives as long as it does
			Settle(nil)
			Server.Stopped:Once(function() if Twin.IsPlaying then Twin:Stop(0.1) end end)
		else
			Settle(0.08) -- the server played another hit, at full weight
		end
	end)
	-- a refusal comes back as NHPredictRefused (above). This is only a safety net for a lost reply: long enough for a
	-- slow server (Studio's play server runs ~20 fps, and its copy arrived 0.55 s after the click), by which time the
	-- swing has nearly played out anyway.
	task.delay(math.clamp(Ping * 2 + 1, 1, 1.5), function()
		if Pending == This then Settle(0.12) end
	end)
	return Index
end

return Predict
