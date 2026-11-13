# Combat audit (fists first): fixes + feel. Every edit is tagged "(combat audit)".
AM = "ServerScriptService.Services.Player.ActionManager"
M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
RUN = "ServerScriptService.Services.Player.ActionManager.Combat.M1.Running M1"
BLOCK = "ServerScriptService.Services.Player.ActionManager.General.Block"
DMG = "ServerStorage.Packages.DamageLogic"
DT = "StarterPlayer.StarterPlayerScripts.Controllers.StateController.Misc.General.Damage Type"
WEAP = "ReplicatedStorage.Config.Weapons"

EDITS = [
# ---- ActionManager: buffer a click that lands during a swing's recovery (players only; NPCs call Shared.M1)
(AM, r"""local TOGGLE_STATES = { Activate = true, Release = true }""",
     r"""local TOGGLE_STATES = { Activate = true, Release = true }
local M1_BUFFER = 0.35 -- (combat audit) a click this close to the end of a swing plays next instead of being dropped"""),
(AM, r"""		local ActionManager = Manager.new(Character)
		ActionManager:Activate(`M1`, Paramaters)
	end)""",
     r"""		local ActionManager = Manager.new(Character)
		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the
		-- next swing starts the moment this one ends (Manager.Activate), if the click was within M1_BUFFER of it
		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial then
			ActionManager.BufferedM1 = os.clock()
		end
	end)"""),
(AM, r"""		if Owns() then
			self.Action = false
			Local.CleanupAirWeld(self.Character)
		end
	end)""",
     r"""		if Owns() then
			self.Action = false
			Local.CleanupAirWeld(self.Character)
			-- (combat audit) play the buffered click
			local Buffered = Action == `M1` and self.BufferedM1
			self.BufferedM1 = nil
			if Buffered and os.clock() - Buffered <= M1_BUFFER then
				local Char = self.Character
				task.defer(function() if Char and Char.Parent and self.Action == false then Shared.M1(Char) end end)
			end
		end
	end)"""),
# ---- M1: the recovery in real seconds (the marker is clip time; fists play at 1.15x), and the end-of-combo cooldown
# never races the end of the swing
(M1, r"""		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) no marker = nil = an endless Attacking state""",
     r"""		local EndLag = AnimMarkers.Time(Track, 'EndLag') or 0.6 -- (audit) no marker = nil = an endless Attacking state
		-- (combat audit) EndLag is clip time, but the swing plays at AnimationSpeed: each fist swing used to hold you ~14%
		-- past its own end (0.52 s instead of 0.45 s on the first), which made the combo feel sticky
		local Rate = (Track.Track and Track.Track.Speed) or 1
		if Rate > 0 then EndLag /= Rate end"""),
(M1, r"""		StateManager.CreateState(self.Character, `Attacking`, EndLag)
		task.wait(EndLag)
		Trails.Disable(self.Character)""",
     r"""		StateManager.CreateState(self.Character, `Attacking`, EndLag)
		task.wait(EndLag)
		-- (combat audit) the last hit's cooldown is set before the swing ends, never after (a buffered click would start a 5th)
		if LastCombo and not self.Cooldowns[script.Name] then self:Cooldown(script.Name, ENDLAG_COOLDOWNS) end
		Trails.Disable(self.Character)"""),
# ---- Running M1: a hit after the attacker's character went away called a method the hitbox doesn't have
(RUN, r"""		if not self.Character then self.HitBox:Disconnect(); self.HitBox = nil end""",
      r"""		if not self.Character then return end -- (combat audit) HitBox has no Disconnect: this line used to error"""),
# ---- Block: the parry-tap thread, and parry spam
(BLOCK, r"""local BLOCK_COOLDOWN = .1""",
        r"""local BLOCK_COOLDOWN = .1
local PARRY_LOCKOUT = .5 -- (combat audit) after a parry window that caught nothing, the next press guards without one"""),
(BLOCK, r"""		local Parry = TrackService.Play(Animations.Parry, self.Character, `Parry`, 0.08)
		Parry:SetPriority(Enum.AnimationPriority.Action4)
		TagService:AddTag(self.Character, `Parry`, .25, true)

		task.wait(.25)
""",
        r"""		-- (combat audit) parry spam: mashing block re-opened a fresh 0.25 s parry window every 0.35 s (~70% of the time
		-- parrying). A window now locks the next one out for PARRY_LOCKOUT after it closes; you still guard at once. A parry
		-- that lands lifts the lock (DamageLogic.Parry).
		local Token = {}
		self.BlockToken = Token
		local Now = os.clock()
		if Now >= (self.ParryLockUntil or 0) then
			self.ParryLockUntil = Now + 0.25 + PARRY_LOCKOUT
			local Parry = TrackService.Play(Animations.Parry, self.Character, `Parry`, 0.08)
			Parry:SetPriority(Enum.AnimationPriority.Action4)
			TagService:AddTag(self.Character, `Parry`, .25, true)

			task.wait(.25)
			-- (combat audit) a parry tap that already let go kept running here and flashed the guard pose (and Slow) over
			-- whatever you did next, an M1 for example
			if self.Action ~= `Block` or self.BlockToken ~= Token then return end
		end
"""),
# ---- DamageLogic: a landed parry lifts the lockout; the hit packet says who hit and how hard (for hit-stop)
(DMG, r"""	ActionManager.CancelCooldown(Target, `Block`)
""",
      r"""	ActionManager.CancelCooldown(Target, `Block`)
	pcall(function() ActionManager.new(Target).ParryLockUntil = nil end) -- (combat audit) a landed parry lifts the parry lockout
"""),
(DMG, r"""		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon })""",
      r"""		Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = CharacterProfile.Weapon; Attacker = Character; Heavy = true }) -- (combat audit)"""),
(DMG, r"""	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon })""",
      r"""	-- (combat audit) Attacker and Heavy drive the hit-stop and camera kick (StateController Damage Type)
	Packets.Replicate:Fire(`Misc`, `Damage Type`, { User = Target; Weapon = Weapon; Attacker = Character; Heavy = DamageData.Stun ~= nil or DamageData.AirDownslam == true })"""),
# ---- client: hit-stop on contact, and a camera kick for the two people in the exchange
(DT, r"""---| Effect |---""",
     r"""local Players = game:GetService(`Players`)

-- (combat audit) hit-stop: the attack and hit-react tracks hold for a few frames on contact (the house style: light 3,
-- heavy 6 at 60 fps). Only Action3/Action4 tracks (swings, hit reacts) pause; walking and idle carry on.
local HOLD = { [Enum.AnimationPriority.Action3] = true; [Enum.AnimationPriority.Action4] = true }
local function HitStop(Model: Model?, Duration: number)
	local Hum = Model and Model:FindFirstChildWhichIsA(`Humanoid`)
	local Animator = Hum and Hum:FindFirstChildOfClass(`Animator`)
	if not Animator then return end
	local Held = {}
	for _, T in Animator:GetPlayingAnimationTracks() do
		if HOLD[T.Priority] and T.Speed > 0 then
			table.insert(Held, { T, T.Speed })
			T:AdjustSpeed(0)
		end
	end
	if #Held == 0 then return end
	task.delay(Duration, function()
		for _, H in Held do
			if H[1].IsPlaying and H[1].Speed == 0 then H[1]:AdjustSpeed(H[2]) end
		end
	end)
end

---| Effect |---"""),
(DT, r"""	local Humanoid = Paramaters.User:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end
""",
     r"""	local Humanoid = Paramaters.User:FindFirstChildWhichIsA(`Humanoid`) :: Humanoid
	if not Humanoid then return end

	-- (combat audit) contact weight: both bodies hold, and the attacker's and the victim's cameras jolt (Camera Shake setting)
	local Heavy = Paramaters.Heavy == true
	local Hold = if Heavy then 0.1 else 0.05
	HitStop(Paramaters.User, Hold)
	if typeof(Paramaters.Attacker) == `Instance` then HitStop(Paramaters.Attacker, Hold) end
	local Me = Players.LocalPlayer and Players.LocalPlayer.Character
	if Me and (Me == Paramaters.Attacker or Me == Paramaters.User) then
		EmitManager.ShakeCamera(if Heavy then 3 else 1.4, 10, 0, if Heavy then 0.3 else 0.16)
	end
"""),
# ---- Katana: the four swings in combo order
(WEAP, r"""			M1 = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].M1:GetChildren();""",
       r"""			M1 = (function() -- (combat audit) in combo order: GetChildren has none, so the swings could come out shuffled
				local L = ReplicatedStorage.Assets.Animations.Weapons[`Katana`].M1:GetChildren()
				table.sort(L, function(A, B)
					local X, Y = tonumber(A.Name), tonumber(B.Name)
					if X and Y then return X < Y end
					return A.Name < B.Name
				end)
				return L
			end)();"""),
]

# ---- then, applied on top: fixes from the first play-test (q8b)
# Combat audit, fixes from the first play-test: a wider click buffer, and the parry pose stops when you let go.
AM = "ServerScriptService.Services.Player.ActionManager"
BLOCK = "ServerScriptService.Services.Player.ActionManager.General.Block"

EDITS_FIX1 = [
(AM, r"""local M1_BUFFER = 0.35 -- (combat audit) a click this close to the end of a swing plays next instead of being dropped""",
     r"""local M1_BUFFER = 0.5 -- (combat audit) a click this close to the end of a swing plays next instead of being dropped (0.35 lost clicks to the server's wait overshooting by a frame)"""),
(BLOCK, r"""	Release = function(self: ActionManager)
""",
        r"""	Release = function(self: ActionManager)
		TrackService.StopTaggedTracks(self.Character, `Parry`, 0.12) -- (combat audit) a parry tap's pose ends with the tap
"""),
(BLOCK, r"""	OnCancel = function(self: ActionManager)
""",
        r"""	OnCancel = function(self: ActionManager)
		TrackService.StopTaggedTracks(self.Character, `Parry`, 0.12) -- (combat audit)
"""),
]

# ---- then: one click = one swing (q8c)
# Combat audit, second play-test: one click = one swing. The client re-sends M1 every 0.05 s while the button is down,
# so a normal 0.1 s click sends 2-3 packets; only a fresh press (a gap since the last packet) may be buffered.
AM = "ServerScriptService.Services.Player.ActionManager"

EDITS_FIX2 = [
(AM, r"""		local ActionManager = Manager.new(Character)
		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the
		-- next swing starts the moment this one ends (Manager.Activate), if the click was within M1_BUFFER of it
		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial then
			ActionManager.BufferedM1 = os.clock()
		end""",
     r"""		local ActionManager = Manager.new(Character)
		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the
		-- next swing starts the moment this one ends (Manager.Activate), if the click was within M1_BUFFER of it.
		-- Only a fresh press counts: the client re-sends M1 every 0.05 s while the button is held, and buffering those
		-- repeats turned one click into two swings.
		local Now = os.clock()
		local Fresh = Now - (ActionManager.LastM1Packet or 0) > 0.09
		ActionManager.LastM1Packet = Now
		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial and Fresh then
			ActionManager.BufferedM1 = Now
		end"""),
]
