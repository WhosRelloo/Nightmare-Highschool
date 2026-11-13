# Combat 2.11.0: A5 soft lock-on, B7 delay string, B10 charged heavy, B11 wall splat. Tagged "(combat A5/B7/B10/B11)".
# New modules (q11_new/): InputController.Combat.LockOn (+ .Core), StateController.Misc.General.Charge, ...General."Wall Splat".
UNP = "ReplicatedStorage.Remotes.UnPackets"
KB = "ReplicatedStorage.Packages.Bind.Keybinds.Config"
CM1 = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M1"
CM2 = "StarterPlayer.StarterPlayerScripts.Controllers.Character.InputController.Combat.M2"
AM = "ServerScriptService.Services.Player.ActionManager"
M1 = "ServerScriptService.Services.Player.ActionManager.Combat.M1"
BLOCK = "ServerScriptService.Services.Player.ActionManager.General.Block"
M2F = "ServerStorage.Assets.M2.Fist"
DMG = "ServerStorage.Packages.DamageLogic"

T, N = "\t", "\n"

EDITS = [
# ---------------- A5: lock-on key, aim assist on every swing ----------------
(KB, r"""		Grip = { `B`, `DPadUp` };""",
     r"""		Grip = { `B`, `DPadUp` };
		LockOn = { `MouseButton3` }; -- (combat A5) middle mouse; pads and touch get aim assist on each swing instead (no free button)"""),
(CM1, r"""	local InAir = Humanoid.FloorMaterial == Enum.Material.Air""",
      r"""	pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5) face the target / aim assist
	local InAir = Humanoid.FloorMaterial == Enum.Material.Air"""),
# ---------------- B10: M2 carries press / let-go flags ----------------
(UNP, r"""	M2 = Packet(`M2`, Packet.Boolean8);""",
      r"""	M2 = Packet(`M2`, Packet.NumberU8); -- (combat B10) flags: 1 = aerial, 2 = a new press, 4 = let go (0 = a hold-repeat)"""),
(CM2, T + "if InAir then UnPackets.M2:Fire(true) end" + N,
      T + "-- (combat B10) flags: 1 = aerial, 2 = a new press, 4 = let go (0 = a hold-repeat). Holding charges the Fist heavy." + N
      + T + "pcall(function() require(script.Parent.LockOn.Core).Assist(Character) end) -- (combat A5)" + N
      + T + "local Pressed = false" + N
      + T + "if InAir then UnPackets.M2:Fire(3) Pressed = true end" + N),
(CM2, T + T + "UnPackets.M2:Fire()" + N + T + T + "task.wait(.05)" + N + N + T + "end" + N + "end",
      T + T + "UnPackets.M2:Fire(if Pressed then 0 else 2)" + N + T + T + "Pressed = true" + N + T + T + "task.wait(.05)" + N + N + T + "end" + N
      + T + "UnPackets.M2:Fire(4) -- (combat B10) let go: a charging heavy swings" + N + "end"),
(AM, r"""	UnPackets.M2.OnServerEvent:Connect(function(Player: Player, Aerial: boolean)""",
     r"""	UnPackets.M2.OnServerEvent:Connect(function(Player: Player, Flags: number) -- (combat B10) 1 = aerial, 2 = a new press, 4 = let go
		if typeof(Flags) ~= `number` then return end
		local Aerial = Flags % 2 == 1
		local HeldBy = Player.Character and Manager.new(Player.Character)
		if HeldBy then
			if (Flags // 4) % 2 == 1 then HeldBy.M2Held = false return end -- let go (Assets.M2.Fist charges while held)
			if (Flags // 2) % 2 == 1 then HeldBy.M2Held = true end
			HeldBy.M2LastPacket = os.clock() -- the hold-repeats keep a charge alive even if the let-go packet is lost
		end"""),
# ---------------- B7: delay string ----------------
(BLOCK, r"""		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParry`)""",
        r"""		self.BlockStartedAt = os.clock() -- (combat B7) a delayed 4th hit goes through a guard raised early
		TagService.RemoveAllTagsFromInstance(self.Character, `AddedParry`)"""),
(M1, r"""		if Riposte then self.Character:SetAttribute(`NHRiposteUntil`, nil) end""",
     r"""		if Riposte then self.Character:SetAttribute(`NHRiposteUntil`, nil) end
		-- (combat B7) the delay string: a 4th hit thrown after a pause (0.3 s or more since hit 3 landed, before the
		-- string resets at 1 s) goes through a guard raised early (held 0.25 s or more). A late, reactive block still parries.
		local Delayed = LastCombo and tick() - (self.Character:GetAttribute(`Tick`) or 0) >= 0.3"""),
(M1, T*3 + "if not DamageLogic.Processed(DamageData) then" + N + T*4 + "return " + N + T*3 + "end" + N + N + T*3 + "VowManager.VowAction(self.Character, `M1`, Humanoid)",
     T*3 + "if Delayed then -- (combat B7)" + N
     + T*4 + "local Ok, Early = pcall(function()" + N
     + T*5 + "local Guard = require(script.Parent.Parent).new(Target)" + N
     + T*5 + "return Guard.Action == `Block` and os.clock() - (Guard.BlockStartedAt or os.clock()) >= 0.25" + N
     + T*4 + "end)" + N
     + T*4 + "if Ok and Early then" + N
     + T*5 + "DamageData.IgnoreStates = { Block = true }" + N
     + T*5 + "DamageData.Tag = `DELAY`" + N
     + T*5 + "DamageData.Heavy = true" + N
     + T*4 + "end" + N
     + T*3 + "end" + N + N
     + T*3 + "if not DamageLogic.Processed(DamageData) then" + N + T*4 + "return " + N + T*3 + "end" + N + N + T*3 + "VowManager.VowAction(self.Character, `M1`, Humanoid)"),
# ---------------- B10: the charged heavy ----------------
(M2F, r"""local Packets = require(ReplicatedStorage.Remotes.Packets)""",
      r"""local Packets = require(ReplicatedStorage.Remotes.Packets)

-- (combat B10) the charged heavy: keep M2 held and the wind-up holds there and charges in three steps
local CHARGE_AT = 0.12 -- seconds into the swing where the pose holds
local CHARGE_STEP = 0.4 -- per step
local CHARGE_MAX = 1.2 -- three steps
local function Holding(self): boolean
	return self.M2Held == true and os.clock() - (self.M2LastPacket or 0) < 0.25
end"""),
(M2F, r"""	self:Cooldown(`M2`, EndLag + ENDLAG_COOLDOWNS)
""",
      r"""	self:Cooldown(`M2`, EndLag + ENDLAG_COOLDOWNS)

	-- (combat B10) still holding M2 just into the wind-up: the swing holds there and charges (0.4 s a step, up to three).
	-- Each step adds 15% damage and guard damage; the third breaks a guard outright. A tap swings as before. You can be
	-- counter-hit while charging (the wind-up window stays open).
	local Level = 0
	if Holding(self) then
		task.wait(CHARGE_AT)
		local Raw = Track.Track
		if Raw and Holding(self) then
			local Speed = Raw.Speed
			Raw:AdjustSpeed(0)
			self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + CHARGE_MAX + 0.5)
			StateManager.CreateState(self.Character, `Freeze`, CHARGE_MAX + 0.1)
			local Start = os.clock()
			while Holding(self) and os.clock() - Start < CHARGE_MAX + 0.02 do
				local L = math.min(3, math.floor((os.clock() - Start) / CHARGE_STEP))
				if L > Level then
					Level = L
					Packets.Replicate:Fire(`Misc`, `Charge`, { User = self.Character; Level = L })
				end
				task.wait()
			end
			StateManager.RemoveAllStates(self.Character, `Freeze`)
			Raw:AdjustSpeed(if Speed > 0 then Speed else 1)
			local HitAt = (AnimMarkers.Time(Track, 'Hit') or 0.3) / (if SwingRate > 0 then SwingRate else 1)
			self.Character:SetAttribute(`NHWindupUntil`, workspace:GetServerTimeNow() + math.max(0.05, HitAt - CHARGE_AT))
		end
	end
"""),
(M2F, r"""			Damage = Config.Damage * 1.3;""",
      r"""			Damage = Config.Damage * 1.3 * (1 + 0.15 * Level); -- (combat B10) +15% a charge step"""),
(M2F, r"""			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };""",
      r"""			States = { Stun = .8; };--Ragdoll = LastCombo and 1.5 };

			-- (combat B10) a charged heavy: more guard damage each step; the full charge breaks a guard outright
			Posture = if Level > 0 then 20 + 15 * Level else nil;
			InstantPostureBreak = Level >= 3;
			Tag = if Level >= 3 then `FULL CHARGE` elseif Level > 0 then `CHARGED` else nil;
			Heavy = true;"""),
# ---------------- B11: wall splat ----------------
(DMG, r"""function Shared.Processed(DamageData: DamageData): boolean?""",
      r"""-- (combat B11) a wall splat: a hard horizontal knockback (40+) that drives the target into a wall within its travel pins
-- them there (0.9 s stun, a head snap against the wall), so the attacker can follow up. Client: Misc."Wall Splat".
function Local.WallSplat(DamageData: DamageData, Target: Model)
	local LV = DamageData.LinearVelocity
	if not LV or LV.UpVector or (LV.Velocity or 0) < 40 or DamageData.AirPush or DamageData.AirDownslam then return end
	local Root = Target:FindFirstChild(`HumanoidRootPart`) :: BasePart?
	if not Root then return end
	local Dir = (LV.Unit or DamageData.Character:GetPivot().LookVector) * Vector3.new(1, 0, 1)
	if Dir.Magnitude < 0.1 then return end
	Dir = Dir.Unit
	local Reach = math.min(LV.Velocity * (LV.Duration or 0.3), 14) + 1.5
	local Params = RaycastParams.new()
	Params.FilterType = Enum.RaycastFilterType.Exclude
	Params.FilterDescendantsInstances = { workspace:FindFirstChild(`Live`), workspace:FindFirstChild(`Visuals`) }
	Params.IgnoreWater = true
	local Hit = workspace:Raycast(Root.Position, Dir * Reach, Params)
	if not (Hit and Hit.Instance and Hit.Instance.CanCollide and math.abs(Hit.Normal.Y) < 0.5) then return end
	local Travel = math.max(0, (Hit.Position - Root.Position).Magnitude - 1.2)
	task.delay(math.min(Travel / LV.Velocity, 0.4), function()
		if not Target.Parent or Downed.IsDowned(Target) or not Root.Parent then return end
		LinearVelocity.StopTaggedBodyMovers(Target, `Stun`)
		local At = Hit.Position + Hit.Normal * 1.1
		local Out = Vector3.new(Hit.Normal.X, 0, Hit.Normal.Z)
		local Pos = Vector3.new(At.X, Root.Position.Y, At.Z)
		Target:PivotTo(if Out.Magnitude > 0.1 then CFrame.lookAt(Pos, Pos + Out) else CFrame.new(Pos))
		StateManager.CreateState(Target, `Stun`, 0.9)
		local Snap = ReplicatedStorage.Assets.Animations.Default.Hit:FindFirstChild(`3`)
		if Snap then
			TrackService.StopTaggedTracks(Target, `Stun`, 0)
			local T = TrackService.Play(Snap, Target, `Stun`, 0)
			T:SetPriority(Enum.AnimationPriority.Action4)
		end
		Packets.Replicate:Fire(`Misc`, `Wall Splat`, { User = Target; Attacker = DamageData.Character; Point = Hit.Position; Normal = Hit.Normal })
	end)
end

function Shared.Processed(DamageData: DamageData): boolean?"""),
(DMG, r"""		Shared.KnockBack(DamageData, Target, `Stun`)
""",
      r"""		Shared.KnockBack(DamageData, Target, `Stun`)
		Local.WallSplat(DamageData, Target) -- (combat B11)
"""),
]

# ---- then: the charge step counted with a tolerance (q11b)
# 2.11.0 play-test fix: a 1.5 s hold only reached charge step 2. 1.2 / 0.4 is 2.9999... in floating point, so step 3 only
# counted if a server frame happened to land inside the loop's last 0.02 s. The step is now worked out with a tolerance,
# and again after the loop.
M2F = "ServerStorage.Assets.M2.Fist"
EDITS_FIX = [
(M2F, r"""				local L = math.min(3, math.floor((os.clock() - Start) / CHARGE_STEP))""",
      r"""				local L = math.min(3, math.floor((os.clock() - Start) / CHARGE_STEP + 1e-6))"""),
(M2F, r"""			StateManager.RemoveAllStates(self.Character, `Freeze`)
			Raw:AdjustSpeed(if Speed > 0 then Speed else 1)""",
      r"""			-- the step reached, counted once more after the loop (its last frame can land just past a step)
			local Final = math.min(3, math.floor(math.min(os.clock() - Start, CHARGE_MAX) / CHARGE_STEP + 1e-6))
			if Final > Level then
				Level = Final
				Packets.Replicate:Fire(`Misc`, `Charge`, { User = self.Character; Level = Final })
			end
			StateManager.RemoveAllStates(self.Character, `Freeze`)
			Raw:AdjustSpeed(if Speed > 0 then Speed else 1)"""),
]
