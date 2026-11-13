# Fist moveset (concepts 6, 8, 9): string enders, the clinch, riposte. Every edit is tagged "(fist moveset)".
# New modules (installed separately): ActionManager.Combat.Ender, ActionManager.Combat.Clinch (q10_new/).
AM = "ServerScriptService.Services.Player.ActionManager"
M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
DMG = "ServerStorage.Packages.DamageLogic"
DT = "StarterPlayer.StarterPlayerScripts.Controllers.StateController.Misc.General.Damage Type"

EDITS = [
# ---------------- ActionManager: routing ----------------
(AM, r"""local M1_BUFFER = 0.5""",
     r"""local ENDER_WINDOW = 0.8 -- (fist moveset) M2 this soon after hit 2 or 3 lands is a string ender
local M1_BUFFER = 0.5"""),
(AM, r"""		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the""",
     r"""		-- (fist moveset) M1 while holding block is the clinch (Combat.Clinch): a grab that goes through a guard
		if ActionManager.Action == `Block` and not Paramaters.Aerial and Local.IsFist(Character) then
			ActionManager:Activate(`Clinch`)
			return
		end
		-- (combat audit) a click during a swing used to be dropped (tapping in rhythm lost hits); now it's remembered and the"""),
(AM, r"""		local ActionManager = Manager.new(Character)
		ActionManager:Activate(`M2`, Paramaters)
	end)""",
     r"""		local ActionManager = Manager.new(Character)
		-- (fist moveset) right after hit 2 or 3 of the string, M2 is a string ender instead of the plain heavy
		if not Paramaters.Aerial and Local.TryEnder(ActionManager, Character, Humanoid) then return end
		ActionManager:Activate(`M2`, Paramaters)
	end)"""),
(AM, r"""function Local.CleanupAirWeld(Character: Model)""",
     r"""-- (fist moveset) the string enders and the clinch are the fist class's (equipped)
function Local.IsFist(Character: Model): boolean
	local Ok, Fist = pcall(function() return require(script.Skills.GrabCore).IsFist(Character) end)
	return Ok and Fist == true
end

-- (fist moveset) concept 6: M2 within ENDER_WINDOW of hit 2 or 3 landing ends the string with a special:
--   after hit 2, the launcher (the Uppercut); after hit 3, the body blow; holding back after any hit, the shove (Combat.Ender).
-- It cancels the swing's recovery once that swing's hit frame has passed. Returns true if an ender started.
function Local.TryEnder(AM, Character: Model, Humanoid: Humanoid): boolean
	if not Local.IsFist(Character) then return false end
	if next(AM.Cooldowns[`M2`] or {}) then return false end
	local Combo = Character:GetAttribute(`Combo`) or 0
	local LastHit = Character:GetAttribute(`Tick`) or 0 -- tick() of the last swing's hit frame (Combat.M1)
	if Combo < 1 or tick() - LastHit > ENDER_WINDOW then return false end
	local Root = Humanoid.RootPart
	local Move = Humanoid.MoveDirection
	local Back = Root ~= nil and Move.Magnitude > 0.1 and Move.Unit:Dot(-Root.CFrame.LookVector) > 0.5
	local Kind = if Back then `Shove` elseif Combo == 2 then `Launcher` elseif Combo == 3 then `BodyBlow` else nil
	if not Kind then return false end
	if Kind == `Launcher` and next(AM.Cooldowns[`Uppercut`] or {}) then return false end
	if AM.Action == `M1` then
		local Wu = Character:GetAttribute(`NHWindupUntil`)
		if typeof(Wu) == `number` and workspace:GetServerTimeNow() < Wu then return false end -- the next swing is winding up
		AM:Cancel(`M1`)
	elseif AM.Action then
		return false
	end
	Character:SetAttribute(`Combo`, 0) -- the string is over; the next M1 starts a new one
	if Kind == `Launcher` then
		if AM:Activate(`Uppercut`) then AM:Cooldown(`M2`, 2.5) return true end
		return false
	end
	return AM:Activate(`Ender`, Kind) == true
end

function Local.CleanupAirWeld(Character: Model)"""),
# ---------------- M1: riposte ----------------
(M1, r"""		local LastCombo = NewCombo == Config.MaxCombo :: boolean""",
     r"""		local LastCombo = NewCombo == Config.MaxCombo :: boolean
		-- (fist moveset) concept 9: the first swing after a parry you landed is a riposte (DamageLogic.Parry sets the window)
		local RiposteUntil = self.Character:GetAttribute(`NHRiposteUntil`)
		local Riposte = typeof(RiposteUntil) == `number` and workspace:GetServerTimeNow() < RiposteUntil
		if Riposte then self.Character:SetAttribute(`NHRiposteUntil`, nil) end"""),
(M1, r"""				Damage = if isFinisher then Config.Damage * 1.5 else Config.Damage;""",
     r"""				Damage = (if isFinisher then Config.Damage * 1.5 else Config.Damage) * (if Riposte then 1.5 else 1); -- (fist moveset) riposte x1.5"""),
(M1, r"""				Stun = if isFinisher then 2 elseif LastCombo then 1.5 else nil;""",
     r"""				Stun = if isFinisher then 2 elseif LastCombo then 1.5 elseif Riposte then 1 else nil; -- (fist moveset) a riposte staggers"""),
(M1, r"""				AirDownslam = isFinisher;""",
     r"""				AirDownslam = isFinisher;
				Tag = if Riposte then `RIPOSTE` else nil; -- (fist moveset) the readout"""),
# ---------------- DamageLogic ----------------
(DMG, r"""	if table.find(Tags, `AutoParry`) or  table.find(Tags, `Parry`) then""",
      r"""	if (table.find(Tags, `AutoParry`) or table.find(Tags, `Parry`)) and not DamageData.IgnoreStates.Parry then -- (fist moveset) a grab goes through a parry"""),
(DMG, r"""	StateManager.CreateState(Target, `ParryStun`, .4)""",
      r"""	StateManager.CreateState(Target, `ParryStun`, .4)
	Target:SetAttribute(`NHRiposteUntil`, workspace:GetServerTimeNow() + 0.9) -- (fist moveset) the parrier's next M1 is a riposte"""),
(DMG, r"""function Local.HitReact(Attacker: Model, Target: Model, Count: number): Animation
	local Fallback = HitReacts[((Count - 1) % #HitReacts) + 1]""",
      r"""function Local.HitReact(Attacker: Model, Target: Model, Count: number, React: string?): Animation
	local Fallback = HitReacts[((Count - 1) % #HitReacts) + 1]
	-- (fist moveset) a move can ask for its own reaction (the body blow and the clinch double them over: clip 1)
	local Forced = React and ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(React)
	if Forced then return Forced end"""),
(DMG, r"""Local.HitReact(Character, Target, HitCount)""",
      r"""Local.HitReact(Character, Target, HitCount, DamageData.React)"""),
(DMG, r"""Heavy = true; Counter = Counter; Damage = DamageData.Damage })""",
      r"""Heavy = true; Counter = Counter; Damage = DamageData.Damage; Tag = DamageData.Tag })"""),
(DMG, r"""Heavy = DamageData.Stun ~= nil or DamageData.AirDownslam == true;
		Counter = Counter; Damage = DamageData.Damage })""",
      r"""Heavy = DamageData.Heavy == true or DamageData.Stun ~= nil or DamageData.AirDownslam == true;
		Counter = Counter; Damage = DamageData.Damage; Tag = DamageData.Tag })"""),
# ---------------- client: the move names on the readout ----------------
(DT, r"""local function ShowCombo(Counter: boolean)""",
     r"""local function ShowCombo(Tag: string?) -- (fist moveset) COUNTER, RIPOSTE or a move's name over the count"""),
(DT, r"""	if Readout.N < 2 and not Counter then return end -- one hit isn't a combo: nothing on screen""",
     r"""	if Readout.N < 2 and not Tag then return end -- one hit isn't a combo: nothing on screen"""),
(DT, r"""	G.Root.Counter.Visible = Counter or (G.Root.Counter.Visible and Now - (Readout.CounterAt or 0) < 0.8)
	if Counter then Readout.CounterAt = Now end""",
     r"""	if Tag then
		G.Root.Counter.Text = Tag
		G.Root.Counter.TextColor3 = if Tag == `COUNTER` or Tag == `RIPOSTE` then CRIMSON else require(ReplicatedStorage.UI.Components).Theme.Colors.Gold
	end
	G.Root.Counter.Visible = Tag ~= nil or (G.Root.Counter.Visible and Now - (Readout.CounterAt or 0) < 0.8)
	if Tag then Readout.CounterAt = Now end"""),
(DT, r"""	if Setting(`ComboCounter`, true) then ShowCombo(Counter) end""",
     r"""	local Tag = if Counter then `COUNTER` elseif typeof(Paramaters.Tag) == `string` then Paramaters.Tag else nil
	if Setting(`ComboCounter`, true) then ShowCombo(Tag) end"""),
(DT, r"""DamageNumber(Paramaters.User, Paramaters.Damage, Heavy, Counter) end""",
     r"""DamageNumber(Paramaters.User, Paramaters.Damage, Heavy, Counter or Tag == `RIPOSTE`) end"""),
]

# ---- then: one click = one swing, by a press flag on the M1 packet (q10b)
# One click = one swing, for real: the M1 packet carries a flags byte (1 = aerial, 2 = a new press). Hold-repeats arrive
# ~0.1 s apart once the network batches them, so the 2.8.0 timing rule (a gap > 0.09 s = a new press) let one click
# queue a second swing. Only a flagged press is buffered now.
UNP = "ReplicatedStorage.Remotes.UnPackets"
CM1 = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1"
AM = "ServerScriptService.Services.Player.ActionManager"

T = "\t"
N = "\n"

EDITS_FIX1 = [
(UNP, r"""	M1 = Packet(`M1`, Packet.Boolean8);""",
      r"""	M1 = Packet(`M1`, Packet.NumberU8); -- (combat audit) flags: 1 = aerial, 2 = a new press (0 = a hold-repeat)"""),
(CM1, T + "-- Only allow aerial M1 if in air but NOT in air combat" + N,
      T + "-- (combat audit) the packet is a flags byte: 1 = aerial, 2 = a new press (the server buffers only presses;" + N
      + T + "-- the hold-repeats below send 0)" + N
      + T + "local Pressed = false" + N
      + T + "-- Only allow aerial M1 if in air but NOT in air combat" + N),
(CM1, T + T + "UnPackets.M1:Fire(true) " + N,
      T + T + "UnPackets.M1:Fire(3)" + N + T + T + "Pressed = true" + N),
(CM1, r"""		UnPackets.M1:Fire()
		task.wait(.05)""",
      r"""		UnPackets.M1:Fire(if Pressed then 0 else 2)
		Pressed = true
		task.wait(.05)"""),
(AM, r"""	UnPackets.M1.OnServerEvent:Connect(function(Player: Player, Aerial: boolean) """,
     r"""	UnPackets.M1.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat audit) 1 = aerial, 2 = a new press
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		local Press = (Flags // 2) % 2 == 1"""),
(AM, r"""		local Now = os.clock()
		local Fresh = Now - (ActionManager.LastM1Packet or 0) > 0.09
		ActionManager.LastM1Packet = Now
		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial and Fresh then
			ActionManager.BufferedM1 = Now
		end""",
     r"""		-- Only a new press counts (the client flags it): the client re-sends M1 every 0.05 s while the button is held, and
		-- buffering those repeats turned one click into two swings. (A timing guess, gap > 0.09 s, wasn't enough: the
		-- network batches the repeats ~0.1 s apart.)
		if not ActionManager:Activate(`M1`, Paramaters) and ActionManager.Action == `M1` and not Paramaters.Aerial and Press then
			ActionManager.BufferedM1 = os.clock()
		end"""),
]

# ---- then: the shove after hit 1 instead of hold-back (q10c)
# Fist moveset, play-test fix: "hold back + M2" was unreliable (the character turns to walk away, so the shove swung at
# nothing). The string itself picks the ender now: M2 after hit 1 = shove, after 2 = launcher, after 3 = body blow.
AM = "ServerScriptService.Services.Player.ActionManager"
EDITS_FIX2 = [
(AM, r"""--   after hit 2, the launcher (the Uppercut); after hit 3, the body blow; holding back after any hit, the shove (Combat.Ender).""",
     r"""--   after hit 1, the shove; after hit 2, the launcher (the Uppercut); after hit 3, the body blow (Combat.Ender).
--   (Holding back for the shove was tried first: the character turns to walk away, so it swung at nothing.)"""),
(AM, r"""	local Root = Humanoid.RootPart
	local Move = Humanoid.MoveDirection
	local Back = Root ~= nil and Move.Magnitude > 0.1 and Move.Unit:Dot(-Root.CFrame.LookVector) > 0.5
	local Kind = if Back then `Shove` elseif Combo == 2 then `Launcher` elseif Combo == 3 then `BodyBlow` else nil""",
     r"""	local Kind = if Combo == 1 then `Shove` elseif Combo == 2 then `Launcher` elseif Combo == 3 then `BodyBlow` else nil"""),
]
