-- approachcheck (2.35.0, task 14): every placed animation starts with an on-foot approach. Client VM, ONE call; the cut is started from
-- outside as the tutorial does (first viewing, not a replay):
--   MODE "sneak": start this in the background, then ~3 s later   bridge.py PlayCut $P '"TutorialSneak"' false
--   MODE "bus":   TutorialEnter, start this in the background, then ~3 s later   bridge.py PlayCut $P '"TutorialBus"' false
--                 (BUS_OFFSET puts the player that far off the Stand mark first: a short walk, a long one from the side)
-- It samples the root EVERY frame (real per-sample frame times: Studio throttles when it isn't focused) and reports:
--   * SLIDES: the root moving more than 0.5 studs/s for 3+ frames (and 0.15 s) with NO walk / run / crouch-walk track playing, outside a
--     dip (black veil). Zero required. (A single isolated frame jump is not a slide: it is a placement, listed under JUMPS)
--   * SPINS: yaw rate above 90 degrees/s for 3+ frames while the root speed is near 0 (under 0.5 studs/s), outside a dip. Zero required.
--   * IDLE GAPS: from the stop to the first chain piece's track, in frames (negative = the piece started that many frames BEFORE the
--     stop, the intended blend lead); and the frames stopped with NO chain piece playing (a dead idle). Zero dead-idle frames wanted.
--   * JUMPS: isolated one-frame root moves over 0.8 studs, each with the veil state (the fence dip is under black; the re-seat is a
--     pose-to-identical-pose switch and listed as such). (fix round 1, M5) a jump outside black that isn't the re-seat (an _End track
--     starting on that frame or the one either side) is a FAIL.
--   * (fix round 1) WALK ON THE SPOT: frames where a walk-cycle track (the game's Walk / Sprint / CrouchWalk, or a chain piece made of
--     one: *Walk*) is ADVANCING at a SEEN weight over 0.5 (its weight less what higher-priority tracks cover), while the root's flat
--     speed is under 0.5 studs/s, outside black. A run of up to 2 frames is a blend; anything beyond is a FAIL.
--   * (fix round 2) CADENCE: the seen walk cycle's playback speed against root speed / its stride speed (CrouchWalk 7, Walk 10, Sprint 24),
--     within 25 % while the root moves (> 0.5 studs/s): a leg cycle out of step with the ground is a skate. <= 2 frames out. Hard for the
--     chain's own walk cycle and for the game's locomotion on steady frames; the game's start/stop transients are listed as info.
--   * (fix round 1) SEAM SPEED (sneak): the root's speed (5-frame average, fix round 3) in the first 0.2 s after the beat -> approach seam must not
--     drop under 70 % of its speed just before it.
--   * (fix round 1) SETTLE: the heading left 0.6 s after the stop against the mark's heading (residual, <= 15 degrees) and the size of
--     the settle turn from the stop to then (<= 20 degrees; a bigger error keeps steering instead of turning on the spot).
--   * the mark: distance and heading error where the approach stopped; the fence's CLEARANCE: the smallest gap in Z between any body
--     part of the character and the gate/fence's near face from the start of the approach to FenceOver2's first frame.
local MODE = "sneak"
local BUS_YAW = 10 -- (fix round 2) bus mode with BUS_OFFSET zero: on the mark, turned this many degrees off its heading
local BUS_OFFSET = Vector3.new(0, 0, 4) -- bus mode: where the player is put, relative to the Stand mark (x along the kerb, z behind it): 4 = a short walk, (6, 0, 8) = a long one from the side
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Char = Player.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local Root = Char.HumanoidRootPart
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Animator = Hum:FindFirstChildOfClass("Animator")
local Names = {}
local Clips = require(game.ReplicatedStorage.Config.CineClips)
for K, V in Clips do if typeof(V) == "string" and V ~= "" then Names[(V:gsub("rbxassetid://", ""))] = K end end
local Tut = game.ReplicatedStorage.NHCineClips:FindFirstChild("Tutorial")
if Tut then for _, S in Tut:GetChildren() do local P = S:GetAttribute("PreviewId") if P then Names[tostring(P)] = Names[tostring(P)] or S.Name end end end
local Loco = {}
for _, A in game.ReplicatedStorage.Assets.Animations.Default.Movement:GetChildren() do
	if A:IsA("Animation") then Loco[(A.AnimationId:gsub("rbxassetid://", ""))] = A.Name end
end
local WALKING = { Walk = true, Sprint = true, FastSprint = true, CrouchWalk = true }
local CHAIN = MODE == "sneak" and { "FenceOver1_GameCrouchWalk", "FenceOver2" } or { "TheBus1_WaitBored", "TheBus2" }
local CHAINSET = {}
for _, N in CHAIN do CHAINSET[N] = true end
local Fence = {}
local Marks, Goal
local MarkYaw, VaultPos -- (fix round 1) the approach mark's heading (settle rows) and, sneak, the vault mark itself (seam row)
local function yawOfCF(C) local L = C.LookVector return math.deg(math.atan2(-L.X, -L.Z)) end
if MODE == "sneak" then
	Marks = workspace:WaitForChild("NHCineSets"):WaitForChild("Garden")
	local FZ = Marks:WaitForChild("FenceZone", 15)
	if not FZ then return "APPROACH FAIL\nprecondition: the Garden set isn't streamed to this client (the player is far from Wickfield). Run harness/stream_set.lua with SET = \"Garden\" first (harness/run_cut.sh does it)" end
	Goal = FZ.Position
	-- TutorialSneak's Vault: FenceZone + VAULT_BACK (0.6) along its +Z, turned APPROACH_YAW (40) left
	local Zone = Marks.FenceZone.CFrame
	VaultPos = Zone.Position + Zone.Rotation:VectorToWorldSpace(Vector3.new(0, 0, 0.6))
	MarkYaw = yawOfCF(Zone * CFrame.Angles(0, math.rad(40), 0))
	for _, N in { "WFPicketFence", "WFPicketGate" } do
		for _, D in workspace.Hometown.Garden:WaitForChild(N):GetDescendants() do
			if D:IsA("BasePart") and D.CanCollide and D.Size.Y > 0.5 then table.insert(Fence, D) end
		end
	end
	Root.CFrame = CFrame.lookAt(Marks.Start.Position + Vector3.new(0, 3, 0), Goal + Vector3.new(0, 3, 0))
else
	Marks = workspace:WaitForChild("NHCineSets"):WaitForChild("BusStop")
	local ST = Marks:WaitForChild("Stand", 15)
	if not ST then return "APPROACH FAIL\nprecondition: the BusStop set isn't streamed to this client. Run harness/stream_set.lua with SET = \"BusStop\" first (harness/run_cut.sh does it)" end
	Goal = ST.Position
	MarkYaw = yawOfCF(Marks.Stand.CFrame)
	-- off the mark: BUS_START studs back and to the side (behind the kerb, facing the stop)
	if BUS_OFFSET.Magnitude < 0.01 then
		-- (fix round 2) ON the mark, turned BUS_YAW off its heading: no walk at all (NearSkip), the heading turns in the blend
		Root.CFrame = CFrame.new(Goal + Vector3.new(0, 3, 0)) * Marks.Stand.CFrame.Rotation * CFrame.Angles(0, math.rad(BUS_YAW), 0)
	else
		Root.CFrame = CFrame.lookAt(Goal + BUS_OFFSET + Vector3.new(0, 3, 0), Goal + Vector3.new(0, 3, 0))
	end
end
Root.AssemblyLinearVelocity = Vector3.zero
Player:SetAttribute("NHCinePath", nil)
task.wait(1.5)

local Rows, Name = {}, "ApproachCheck_" .. math.random(1e6)
local Last
local LastTp = setmetatable({}, { __mode = "k" })
local function clearance()
	local Best, Who = math.huge, nil
	for _, P in Char:GetChildren() do
		if P:IsA("BasePart") and P.Name ~= "HumanoidRootPart" then
			local R, H = P.CFrame, P.Size / 2
			local function ext(I) return math.abs(R:VectorToWorldSpace(Vector3.xAxis)[I]) * H.X + math.abs(R:VectorToWorldSpace(Vector3.yAxis)[I]) * H.Y + math.abs(R:VectorToWorldSpace(Vector3.zAxis)[I]) * H.Z end
			local MinZ, X0, X1, Y0, Y1 = P.Position.Z - ext("Z"), P.Position.X - ext("X"), P.Position.X + ext("X"), P.Position.Y - ext("Y"), P.Position.Y + ext("Y")
			for _, F in Fence do
				local Fx, Fy, Fz = F.Size.X / 2, F.Size.Y / 2, F.Size.Z / 2
				if X1 > F.Position.X - Fx and X0 < F.Position.X + Fx and Y1 > F.Position.Y - Fy and Y0 < F.Position.Y + Fy then
					local G = MinZ - (F.Position.Z + Fz)
					if G < Best then Best, Who = G, P.Name end
				end
			end
		end
	end
	return Best, Who
end
local function sample()
	local Now = os.clock()
	local Ui = Player.PlayerGui:FindFirstChild("NHCineUI")
	local Veil = Ui and Ui:FindFirstChild("Veil", true)
	local Tracks = {}
	local Walk, ChainOn, ChainW = false, {}, {}
	local Cyc, CycWho, EndOn = 0, nil, false
	local CadW, CadWho, CadSpeed = 0, nil, 0
	-- (fix round 1) a track is only SEEN if no higher-priority track at full weight covers it (Core is the lowest priority)
	local function rank(T) return if T.Priority == Enum.AnimationPriority.Core then -1 else T.Priority.Value end
	local Playing = Animator and Animator:GetPlayingAnimationTracks() or {}
	local function seen(T) -- its weight less what the strongest higher-priority track covers
		local Top = 0
		for _, O in Playing do if O ~= T and rank(O) > rank(T) then Top = math.max(Top, O.WeightCurrent) end end
		return T.WeightCurrent * (1 - math.min(1, Top))
	end
	if Animator then
		for _, T in Playing do
			local Id = T.Animation and (T.Animation.AnimationId:gsub("rbxassetid://", "")) or ""
			local L = Loco[Id]
			if L and WALKING[L] and T.WeightCurrent > 0.05 then Walk = true end
			local N = Names[Id]
			if N and CHAINSET[N] then ChainOn[N] = true ChainW[N] = T.WeightCurrent end
			if N and N:match("_End$") then EndOn = true end
			-- (fix round 1) a walk cycle that is advancing (its time moved since the last frame)
			local Tp = T.TimePosition
			local Was = LastTp[T]
			LastTp[T] = Tp
			if ((L and WALKING[L]) or (N and N:match("Walk"))) and Was and math.abs(Tp - Was) > 1e-3 and seen(T) > Cyc then
				Cyc, CycWho = seen(T), L or N
			end
			-- (fix round 2) cadence: the most-seen walk-cycle track (advancing or not) and its playback speed
			if ((L and WALKING[L]) or (N and N:match("Walk"))) and seen(T) > CadW then
				CadW, CadWho, CadSpeed = seen(T), L or N, T.Speed
			end
			table.insert(Tracks, L or N or Id)
		end
	end
	local Look = Root.CFrame.LookVector
	local Row = { t = Now; dt = Last and (Now - Last.t) or 0; pos = Root.Position; yaw = math.deg(math.atan2(-Look.X, -Look.Z));
		seam = Player:GetAttribute("NHCineSeam"); path = Player:GetAttribute("NHCinePath"); veil = Veil and Veil.BackgroundTransparency or 1;
		walk = Walk; chain = ChainOn; cw = ChainW; cyc = Cyc; cycWho = CycWho; endOn = EndOn; cadW = CadW; cadWho = CadWho; cadSpeed = CadSpeed; appr = Player:GetAttribute("NHApproach") == true;
		vel = Vector3.new(Root.AssemblyLinearVelocity.X, 0, Root.AssemblyLinearVelocity.Z).Magnitude; ws = Hum.WalkSpeed; crouch = Hum:GetAttribute("Crouch") == true; tracks = Tracks;
		clear = if MODE == "sneak" then (clearance()) else nil; clearWho = if MODE == "sneak" then select(2, clearance()) else nil }
	Last = Row
	table.insert(Rows, Row)
end
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, sample)
-- sneak: walk (crouched) to the fence until the Fence segment takes over, as sneakcheck does
local Began = false
local FenceAt = nil
RunService:BindToRenderStep(Name .. "Walk", Enum.RenderPriority.Input.Value + 1, function()
	local Ph = Player:GetAttribute("NHCineSeam")
	if Ph ~= nil then Began = true end
	local Path = Player:GetAttribute("NHCinePath") or ""
	-- (fix round 1) like a player holding W: the walk carries on through the beat -> fence seam until CineActor.Approach takes over
	-- (NHApproach), never longer than 1 s past the seam (so it can't fight the approach)
	if Path:match("Fence$") then FenceAt = FenceAt or os.clock() end
	if MODE ~= "sneak" or not Began or Player:GetAttribute("NHApproach") or (FenceAt and os.clock() - FenceAt > 1) then return end
	if not FenceAt and not (Ph == "In" or Ph == "Beat" or Ph == "BeatIn") then return end
	local D = (Goal - Root.Position) * Vector3.new(1, 0, 1)
	if D.Magnitude > 0.5 then Hum:Move(D.Unit, false) end
end)
local T0, Started = os.clock(), false
local FirstSeam
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true FirstSeam = FirstSeam or os.clock() end
until (Started and MODE == "sneak" and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 6)
	or (Started and MODE == "bus" and os.clock() - FirstSeam > 24) or os.clock() - T0 > 90
task.wait(0.5)
RunService:UnbindFromRenderStep(Name)
RunService:UnbindFromRenderStep(Name .. "Walk")
Hum:Move(Vector3.zero)

local Rep, Pass = {}, true
local function add(S) table.insert(Rep, S) end
local function check(Ok, S) Pass = Pass and Ok add(S .. (Ok and " ok" or " FAIL")) end
local function black(R) return R.veil < 0.5 end
local function flat(V) return Vector3.new(V.X, 0, V.Z) end
-- per-frame speed, yaw rate
for I = 2, #Rows do
	local A, B = Rows[I - 1], Rows[I]
	local Dt = math.max(B.t - A.t, 1e-3)
	B.d = (flat(B.pos) - flat(A.pos)).Magnitude
	B.v = B.d / Dt
	local Dy = (B.yaw - A.yaw + 540) % 360 - 180
	B.w = math.abs(Dy) / Dt
	B.dy = Dy
end
Rows[1].d, Rows[1].v, Rows[1].w, Rows[1].dy = 0, 0, 0, 0
-- only the cut's own frames (after the first seam phase)
local S0
for I, R in Rows do if R.seam ~= nil then S0 = I break end end
S0 = S0 or 1
-- the approach is judged from the segment that makes it: the Fence segment (sneak), the whole cut (bus)
local A0 = S0
if MODE == "sneak" then
	for I, R in Rows do if R.path and R.path:match("Fence$") and R.seam ~= nil then A0 = I break end end
end
-- jumps: an isolated frame over 0.8 studs with calm frames either side
local Jumps, IsJump, BadJumps = {}, {}, {}
for I = S0 + 1, #Rows - 1 do
	local R = Rows[I]
	if R.d > 0.8 and Rows[I - 1].v < R.v * 0.5 and Rows[I + 1].v < R.v * 0.5 then
		IsJump[I] = true
		-- (fix round 1, M5) the re-seat: an _End track starts on this frame or the one either side
		local Reseat = false
		for J = math.max(2, I - 1), math.min(#Rows, I + 1) do if Rows[J].endOn and not Rows[J - 1].endOn then Reseat = true end end
		local Hidden = black(R) or black(Rows[I - 1])
		if not Hidden and not Reseat then table.insert(BadJumps, I) end
		table.insert(Jumps, string.format("%.2f studs at %.2f s (veil transparency %.2f, walk track %s%s)", R.d, R.t - Rows[S0].t, math.max(R.veil, Rows[I - 1].veil), tostring(R.walk),
			Reseat and ", the re-seat" or (Hidden and ", under black" or ", ON SCREEN")))
	end
end
-- slides: runs of frames with v > 0.5, no walking track, not black, not a jump, lasting 3+ frames and 0.15 s
local Slides, Run = {}, {}
local function flush()
	if #Run >= 3 and Rows[Run[#Run]].t - Rows[Run[1]].t >= 0.15 then
		local Peak = 0
		for _, I in Run do Peak = math.max(Peak, Rows[I].v) end
		table.insert(Slides, string.format("%d frames from %.2f s, peak %.2f studs/s", #Run, Rows[Run[1]].t - Rows[S0].t, Peak))
	end
	Run = {}
end
for I = S0, #Rows do
	local R = Rows[I]
	if R.v > 0.5 and not R.walk and not IsJump[I] and not black(R) and R.seam ~= nil then table.insert(Run, I) else flush() end
end
flush()
-- spins: yaw rate over 90 deg/s, root speed under 0.5, 3+ frames, not black, not a jump
local Spins, RunS = {}, {}
local function flushS()
	if #RunS >= 3 then
		local Peak = 0
		for _, I in RunS do Peak = math.max(Peak, Rows[I].w) end
		table.insert(Spins, string.format("%d frames from %.2f s, peak %.0f deg/s", #RunS, Rows[RunS[1]].t - Rows[S0].t, Peak))
	end
	RunS = {}
end
for I = S0, #Rows do
	local R = Rows[I]
	if R.w > 90 and R.v < 0.5 and not IsJump[I] and not black(R) and R.seam ~= nil then table.insert(RunS, I) else flushS() end
end
flushS()
local PeakW, PeakWAt = 0, 0
for I = S0, #Rows do if Rows[I].v < 0.5 and not IsJump[I] and not black(Rows[I]) and Rows[I].w > PeakW then PeakW = Rows[I].w PeakWAt = Rows[I].t - Rows[S0].t end end
do -- every stopped frame turning faster than 90 deg/s, even a single one (a spin needs 3 in a row; these are listed so a one-frame twitch is seen)
	local L = {}
	for I = S0, #Rows do
		local R = Rows[I]
		if R.w > 90 and R.v < 0.5 and not IsJump[I] and not black(R) and R.seam ~= nil and #L < 8 then
			table.insert(L, string.format("%.2f s: %.1f deg in %.0f ms (%.0f deg/s)", R.t - Rows[S0].t, R.dy, (R.t - Rows[I - 1].t) * 1000, R.w))
		end
	end
	add("stopped frames over 90 deg/s: " .. (#L > 0 and table.concat(L, "; ") or "none"))
end
check(#Slides == 0, string.format("SLIDES (moving over 0.5 studs/s with no walk/run/crouch-walk track, outside a dip): %d%s", #Slides, #Slides > 0 and (" -> " .. table.concat(Slides, "; ")) or ""))
check(#Spins == 0, string.format("SPINS (over 90 deg/s while stopped, 3+ frames, outside a dip): %d%s; peak stopped yaw rate %.0f deg/s at %.2f s", #Spins, #Spins > 0 and (" -> " .. table.concat(Spins, "; ")) or "", PeakW, PeakWAt))
add("JUMPS: " .. (#Jumps > 0 and table.concat(Jumps, " | ") or "none"))
check(#BadJumps == 0, string.format("JUMPS on screen (not under black, not the re-seat): %d", #BadJumps))
do -- (fix round 1) walk on the spot: an advancing walk cycle at weight > 0.5 with the root still; up to 2 frames a run is a blend
	local Runs, Cur, Excess, Secs = {}, {}, 0, 0
	local function flushW()
		if #Cur > 2 then
			Excess += #Cur - 2
			local Dur = Rows[Cur[#Cur]].t - Rows[Cur[1]].t + (Rows[Cur[1]].dt or 0)
			Secs += Dur
			table.insert(Runs, string.format("%d frames (%.2f s) from %.2f s, %s", #Cur, Dur, Rows[Cur[1]].t - Rows[S0].t, tostring(Rows[Cur[1]].cycWho)))
		end
		Cur = {}
	end
	for I = S0, #Rows do
		local R = Rows[I]
		if R.cyc > 0.5 and R.v < 0.5 and not black(R) and R.seam ~= nil and not IsJump[I] then table.insert(Cur, I) else flushW() end
	end
	flushW()
	check(Excess == 0, string.format("WALK ON THE SPOT (an advancing walk cycle at weight > 0.5, root under 0.5 studs/s, beyond 2 blend frames): %d frames, %.2f s%s",
		Excess, Secs, #Runs > 0 and (" -> " .. table.concat(Runs, "; ")) or ""))
end
do -- (fix round 2) CADENCE: the seen walk cycle's playback speed against the root's speed over the clip's own stride speed (CrouchWalk
	-- and the *GameCrouchWalk pieces 7 studs/s at speed 1, Walk 10, Sprint 24: the game's own scales), within 25 %, while the root moves
	-- over 0.5 studs/s, outside black. A leg cycle out of step with the ground is a skate.
	-- HARD (<= 2 frames out): a chain piece's walk cycle (ours: FenceOver1) on every frame, and the game's own locomotion on STEADY frames
	-- (root acceleration <= 15 studs/s^2). On the game's locomotion this proves CineActor's cadence hook ran (it writes speed = root speed /
	-- these same stride constants); it does NOT prove the constants match each clip's real stride (that needs a foot-contact measure). INFO: the game's own Walk/CrouchWalk on the start/stop transients (the ramp from a standing start,
	-- the last stud's ease-out), where the game's own AnimationController blends a start or a stop exactly as it does in normal play.
	local STRIDE = { CrouchWalk = 7, Walk = 10, Sprint = 24, FastSprint = 30 }
	-- (2026-11-22, the strafes build) when Config.Locomotion exists the game's walk cycles follow its stride-matched rule
	-- (Functions.Locomotion.Rate: ground speed / (Stride * leg / 2), clamped to [CadenceMin, CadenceMax]). The chain's *GameCrouchWalk
	-- pieces are the same CrouchWalk clip baked in, so they follow the CrouchWalk rule too (one clip, one cadence)
	local LocoCfg = game.ReplicatedStorage:FindFirstChild("Config") and game.ReplicatedStorage.Config:FindFirstChild("Locomotion")
	LocoCfg = LocoCfg and require(LocoCfg) or nil -- pure config: a VM copy is fine
	local LegLen = Char:FindFirstChild("Left Leg") and Char["Left Leg"].Size.Y or 2
	local function want(Name: string, V: number): number
		local Key = if STRIDE[Name] then Name elseif Name:match("CrouchWalk") then "CrouchWalk" else "Walk"
		if LocoCfg and LocoCfg.Stride and LocoCfg.Stride[Key] then
			return math.clamp(V / (LocoCfg.Stride[Key] * math.max(LegLen, 0.1) / 2), LocoCfg.CadenceMin, LocoCfg.CadenceMax)
		end
		return V / STRIDE[Key]
	end
	add("cadence rule: " .. (LocoCfg and string.format("Config.Locomotion stride-matched (CrouchWalk %.1f, Walk %.1f per 2-stud leg; leg %.2f)", LocoCfg.Stride.CrouchWalk, LocoCfg.Stride.Walk, LegLen) or "the game's old scales (CrouchWalk 7, Walk 10)"))
	local Bad, N, Worst, WorstAt, WorstWho = 0, 0, 0, 0, nil
	local TBad, TN, TWorst = 0, 0, 0
	local OutL = {}
	for I = math.max(S0, 2), #Rows do
		local R = Rows[I]
		if R.cadWho and R.cadW > 0.5 and R.vel > 0.5 and not black(R) and R.seam ~= nil then
			local Want = want(tostring(R.cadWho), R.vel)
			local Err = math.abs(R.cadSpeed - Want) / math.max(Want, 1e-3)
			local Acc = math.abs(R.vel - Rows[I - 1].vel) / math.max(R.t - Rows[I - 1].t, 1e-3)
			local Ours = STRIDE[R.cadWho] == nil
			if Ours or Acc <= 15 then
				N += 1
				if Err > 0.25 then
					Bad += 1
					if #OutL < 8 then table.insert(OutL, string.format("%.2f s %s %.2f vs %.2f%s", R.t - Rows[S0].t, tostring(R.cadWho), R.cadSpeed, Want, R.appr and " (approach)" or "")) end
				end
				if Err > Worst then Worst, WorstAt, WorstWho = Err, R.t - Rows[S0].t, string.format("%s speed %.2f vs %.2f", tostring(R.cadWho), R.cadSpeed, Want) end
			else
				TN += 1
				if Err > 0.25 then TBad += 1 end
				TWorst = math.max(TWorst, Err)
			end
		end
	end
	check(Bad <= 2, string.format("CADENCE (walk-cycle speed vs root speed / stride, within 25 %%: the chain's walk cycle always, the game's own on steady frames): %d of %d frames out (<= 2); worst %.0f %% at %.2f s (%s)",
		Bad, N, Worst * 100, WorstAt, tostring(WorstWho)) .. (#OutL > 0 and (" -> " .. table.concat(OutL, "; ")) or ""))
	add(string.format("cadence on the start/stop transients (info: the game's own locomotion, accel > 15 studs/s^2): %d of %d frames out of 25 %%, worst %.0f %%", TBad, TN, TWorst * 100))
end
-- the approach: first moving frame in the cut, the stop (the last frame of the approach's walk), the first chain piece
local Move0, Stop0, P1, P2
for I = A0, #Rows do
	local R = Rows[I]
	if not Move0 and R.v > 1 and R.walk then Move0 = I end
	if not P1 and R.chain[CHAIN[1]] then P1 = I end
	if not P2 and R.chain[CHAIN[2]] then P2 = I end
end
local OnMark = MODE == "bus" and BUS_OFFSET.Magnitude < 0.01
if OnMark and P1 then
	-- (fix round 2) on the mark there's no walk: the "stop" is where the first piece starts; any frame that moves is reported below
	Move0 = Move0 or P1
	local Moved = 0
	for I = S0, #Rows do if Rows[I].v > 0.5 and not IsJump[I] and not black(Rows[I]) and Rows[I].walk then Moved += 1 end end
	check(Moved <= 2, string.format("ON THE MARK: %d walking frames (want none: NearSkip, no walk)", Moved))
end
if P1 and not OnMark then
	-- the stop: the first frame after the walk started where the root is still (under 0.5 studs/s for 2 frames) at or after the piece began, minus nothing
	for I = math.max(2, Move0 or A0), #Rows - 1 do
		if Rows[I].v < 0.5 and Rows[I + 1].v < 0.5 and Rows[I - 1].v >= 0.5 then Stop0 = I break end
	end
end
if Move0 and P1 then
	local StopI = Stop0 or P1
	local Lead = StopI - P1 -- frames the piece began BEFORE the stop
	local Dead = 0
	for I = StopI, P1 - 1 do if Rows[I] and not (next(Rows[I].chain)) then Dead += 1 end end
	-- frames between the stop and the piece with the root still and no chain piece (a dead idle): none when the piece began before it
	local Dt = (Rows[StopI].t - Rows[P1].t)
	add(string.format("approach: walking from %.2f s (frame %d), stop at frame %d (%.2f s), first chain piece at frame %d (%.2f s): the piece began %d frames (%.2f s) BEFORE the stop", Rows[Move0].t - Rows[S0].t, Move0, StopI, Rows[StopI].t - Rows[S0].t, P1, Rows[P1].t - Rows[S0].t, Lead, Dt))
	check(Dead == 0, string.format("IDLE GAP: %d frames stopped with no chain piece playing (want 0); the piece started %d frames before the stop", Dead, Lead))
	-- (fix round 1) a first piece that is NOT a walk cycle covers the legs: started long before the stop, the root walks on under a still
	-- pose. Its fade-in (0.3 s) plus a little: <= 0.45 s before the stop. (A walk-cycle first piece is paced by the walk: no limit.)
	if CHAIN[1]:match("Walk") then
		add(string.format("LEAD: %.2f s (the first piece is a walk cycle paced by the walk: no limit)", Dt))
	else
		check(Dt <= 0.45, string.format("LEAD: the first piece began %.2f s before the stop (<= 0.45: its fade-in, not a still pose over a walk)", Dt))
	end
	local Wmax = 0
	for I = P1, math.min(#Rows, P1 + 90) do Wmax = math.max(Wmax, Rows[I].cw[CHAIN[1]] or 0) end
	-- the arrival: where the root stopped against the mark, and the body's heading
	local SettledI = StopI
	for I = StopI, #Rows do SettledI = I if Rows[I].t - Rows[StopI].t >= 0.6 then break end end
	local Settled = Rows[SettledI]
	local Err = (flat(Settled.pos) - flat(Goal)).Magnitude
	add(string.format("start (%.2f, %.2f) stop (%.2f, %.2f) mark (%.2f, %.2f)", Rows[Move0].pos.X, Rows[Move0].pos.Z, Rows[StopI].pos.X, Rows[StopI].pos.Z, Goal.X, Goal.Z))
	add(string.format("arrival: %.2f studs from the mark 0.6 s after the stop; first piece weight reached %.2f", Err, Wmax))
	add(string.format("heading at the stop %.1f, 0.6 s on %.1f (the mark's heading + %s)", Rows[StopI].yaw, Settled.yaw, MODE == "sneak" and "40 degrees left of the fence" or "facing the road"))
	-- (fix round 1) the settle: the residual heading against the mark and the size of the turn after the stop (stopping short of any jump)
	local SetI = StopI
	for I = StopI + 1, SettledI do if IsJump[I] then break end SetI = I end
	local Resid = (Rows[SetI].yaw - MarkYaw + 540) % 360 - 180
	local Turn = (Rows[SetI].yaw - Rows[StopI].yaw + 540) % 360 - 180
	-- (fix round 3) on the mark (NearSkip) the turn may be up to 45: the one settle allowed past TurnMax, instead of an out-and-back
	local TurnCap = if OnMark then 45 else 20
	check(math.abs(Resid) <= 15 and math.abs(Turn) <= TurnCap, string.format("SETTLE: residual heading %.1f deg against the mark (<= 15), settle turn %.1f deg after the stop (<= %d)", Resid, Turn, TurnCap))
	-- (fix round 1) the beat -> approach seam (sneak): no drop under 70 % of the speed just before it
	if MODE == "sneak" and A0 > S0 + 5 then
		-- speed over 5 frames (fix round 3; it was 3): a render frame with no physics step reads near 0 and the next one double, and that
		-- beat runs 2 frames long (measured 3.1 / 9.4 / 3.6 / 10.7 studs/s with WalkSpeed a steady 6.3): sampling, not motion
		local function v3(I)
			local A, B = math.max(1, I - 2), math.min(#Rows, I + 2)
			return (flat(Rows[B].pos) - flat(Rows[A].pos)).Magnitude / math.max(Rows[B].t - Rows[A].t, 1e-3)
		end
		local Pre = {}
		for I = A0 - 4, A0 - 2 do table.insert(Pre, v3(I)) end
		table.sort(Pre)
		local PreV = Pre[2]
		-- the seam: its first 0.2 s (the old stutter bottomed out 0.08-0.13 s in; later dips are the walk's own slow-down for the turn at the
		-- lead-in corner, listed below as info)
		local MinV, MinAt = math.huge, A0
		local CornerV, CornerAt = math.huge, A0
		for I = A0, #Rows - 1 do
			local R = Rows[I]
			if (flat(R.pos) - flat(VaultPos)).Magnitude < 1.2 or I >= StopI then break end
			if not IsJump[I] and not IsJump[I + 1] then
				if R.t - Rows[A0].t <= 0.2 then
					if v3(I) < MinV then MinV, MinAt = v3(I), I end
				elseif v3(I) < CornerV then CornerV, CornerAt = v3(I), I end
			end
		end
		if CornerV < math.huge then add(string.format("after the seam (info): lowest %.2f studs/s at %.2f s (the turn at the lead-in corner slows the pace: TurnPace)", CornerV, Rows[CornerAt].t - Rows[A0].t)) end
		if MinV == math.huge then MinV = PreV end
		local L = {}
		for I = A0 - 3, math.min(#Rows, A0 + 14) do table.insert(L, string.format("%.1f/%.1f", Rows[I].v, Rows[I].ws)) end
		add("seam frames (speed/WalkSpeed, from 3 before the seam): " .. table.concat(L, " "))
		local MinWs = math.huge
		for I = A0, #Rows do if Rows[I].t - Rows[A0].t > 0.2 then break end MinWs = math.min(MinWs, Rows[I].ws) end
		add(string.format("seam: the WalkSpeed asked for in the first 0.2 s, lowest %.2f (%.0f %% of the speed before the seam)", MinWs, PreV > 0 and 100 * MinWs / PreV or 0))
		check(PreV < 1 or MinV >= 0.7 * PreV, string.format("SEAM SPEED (5-frame average): %.2f studs/s before the beat -> approach seam, lowest %.2f (%.0f %%) in its first 0.2 s, at %.2f s (>= 70 %%)",
			PreV, MinV, PreV > 0 and 100 * MinV / PreV or 0, Rows[MinAt].t - Rows[A0].t))
	elseif MODE == "sneak" then
		add("SEAM SPEED: not measured (the seam came too soon after the cut began)")
	else
		add("SEAM SPEED: n/a (bus: you stand through the glide, no beat before the walk)")
	end
	if MODE == "sneak" then
		-- three windows: while walking up (to the stop), the FenceOver1 crouch walk (stop to FenceOver2's first frame), and the climb's first 0.5 s
		local function window(From, To)
			local Min, At, Who = math.huge, nil, nil
			for I = From, To do if Rows[I].clear and Rows[I].clear < Min then Min, At, Who = Rows[I].clear, I, Rows[I].clearWho end end
			return Min, At, Who
		end
		local StopI = Stop0 or P1
		local M1, A1, W1 = window(Move0, StopI)
		local M2, A2, W2 = window(StopI, (P2 or #Rows) - 1)
		local P3 = P2 or #Rows
		local E3 = P3
		while E3 < #Rows and Rows[E3 + 1].t - Rows[P3].t < 0.5 and not IsJump[E3 + 1] do E3 += 1 end
		local M3, A3, W3 = window(P3, E3)
		add(string.format("fence clearance (gap in Z between a body part and the fence's near face; negative = inside it): walking up %.2f (%s), FenceOver1 until the climb %.2f (%s), first 0.5 s of FenceOver2 %.2f (%s)", M1, tostring(W1), M2, tostring(W2), M3, tostring(W3)))
		add(string.format("root z at the stop %.2f (the fence's near face z %.2f)", Rows[StopI].pos.Z, (function() local Z = -math.huge for _, F in Fence do Z = math.max(Z, F.Position.Z + F.Size.Z / 2) end return Z end)()))
		local Min = math.min(M1, M2)
		check(Min > 0.1, "the body clears the gate and pickets until the climb begins (walking up and FenceOver1)")
	end
else
	check(false, string.format("approach: no walking frame (%s) or no first chain piece (%s) found", tostring(Move0), tostring(P1)))
end
if P2 then add(string.format("second chain piece at %.2f s from the cut's first phase", Rows[P2].t - Rows[S0].t)) end
local Tl = {}
local Prev
for I = S0, #Rows do
	local R = Rows[I]
	local Key = (R.walk and "walk" or "-") .. "/" .. (next(R.chain) and (next(R.chain)) or "-")
	if Key ~= Prev then table.insert(Tl, string.format("%s@%.2f", Key, R.t - Rows[S0].t)) Prev = Key end
end
add("timeline: " .. table.concat(Tl, " "))
do
	local Seen = {}
	for I = S0, #Rows do for _, N in Rows[I].tracks do Seen[N] = (Seen[N] or 0) + 1 end end
	local L = {}
	for N, C in Seen do table.insert(L, N .. " " .. C) end
	table.sort(L)
	add("tracks seen during the cut: " .. table.concat(L, ", "))
end
add(string.format("%d frames, median frame %.0f ms", #Rows, (function() local L = {} for I = 2, #Rows do table.insert(L, Rows[I].dt * 1000) end table.sort(L) return L[math.ceil(#L / 2)] or 0 end)()))
return (Pass and "APPROACH OK\n" or "APPROACH FAIL\n") .. table.concat(Rep, "\n")
