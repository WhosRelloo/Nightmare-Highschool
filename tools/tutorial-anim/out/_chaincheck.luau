-- tools/tutorial-anim/chaincheck.luau: play each tutorial chain on a temporary R6 dummy in Edit mode, exactly as the
-- game will (each piece in turn, loops entered at Entry and left at Exit), step the Animator at 60 fps and measure every
-- handoff, both the runtime switches between pieces and the blends baked inside them: the peak acceleration of the body's parts across the cut against the clips' own motion inside the
-- steps. A runtime switch passes when its peak stays at or under the clips' own p99 (or under a gentle 45 st/s2): the
-- cut is no jerkier than the motion around it. Baked blends are printed for reference (build.py audits them against
-- their own source clips). Destroys the dummy after.
-- build.py writes out/_chaincheck.luau from this, with the plan pasted in as CHAINS.
local CHAINS = {
	ColdOpen = {
		{ Piece = "ColdOpen1", Length = 3.633, Hold = true, EndOffset = { X = -0.9255, Z = -0.044, Yaw = -72.291 } },
	},
	Drainpipe = {
		{ Piece = "Drainpipe1", Length = 2.933, EndOffset = { X = -0.1705, Z = 0.3113, Yaw = 19.228 } },
		{ Piece = "Drainpipe2_GameCrouch", Length = 2.833, Loop = true, Entry = 0.633, Exit = 0.0, EndOffset = { X = -0.1767, Z = 0.3011, Yaw = 18.681 } },
	},
	BiscuitStirs = {
		{ Piece = "BiscuitStirs1_GameCrouchWalk", Length = 1.333, Loop = true, Entry = 0.0, Exit = 0.467, EndOffset = { X = -0.0123, Z = -0.2034, Yaw = -21.855 } },
		{ Piece = "BiscuitStirs2", Length = 5.6, EndOffset = { X = 0.0314, Z = -0.1836, Yaw = -28.866 } },
		{ Piece = "BiscuitStirs3_GameCrouchWalk", Length = 1.333, Loop = true, Entry = 0.3, Exit = 0.0, EndOffset = { X = 0.0188, Z = -0.1951, Yaw = -25.654 } },
	},
	FenceOver = {
		{ Piece = "FenceOver1_GameCrouchWalk", Length = 1.333, Loop = true, Entry = 0.0, Exit = 0.467, EndOffset = { X = -0.0123, Z = -0.2034, Yaw = -21.855 } },
		{ Piece = "FenceOver2", Length = 2.9, EndOffset = { X = -1.5586, Z = -0.4214, Yaw = -100.683 } },
	},
	ThePlan = {
		{ Piece = "ThePlan1", Length = 8.167, EndOffset = { X = -0.184, Z = -2.1859, Yaw = -39.048 } },
	},
	Getaway = {
		{ Piece = "Getaway1_RunLookBack", Length = 2.233, Loop = true, Entry = 0.0, Exit = 1.933, EndOffset = { X = -0.0883, Z = -0.3516, Yaw = 13.415 } },
		{ Piece = "Getaway2", Length = 8.1, EndOffset = { X = -2.3239, Z = -6.871, Yaw = -24.622 } },
		{ Piece = "Getaway3_LookAroundNervous", Length = 4.467, Loop = true, Entry = 1.8, Exit = 0.0, EndOffset = { X = -2.2942, Z = -6.9044, Yaw = -11.821 } },
	},
	HomeAgain = {
		{ Piece = "HomeAgain1", Length = 2.7, EndOffset = { X = -0.0593, Z = -0.0846, Yaw = -20.127 } },
		{ Piece = "HomeAgain2_GameCrouchWalk", Length = 1.333, Loop = true, Entry = 0.3, Exit = 0.533, EndOffset = { X = -0.0736, Z = -0.094, Yaw = -16.916 } },
		{ Piece = "HomeAgain3", Length = 4.867, EndOffset = { X = -0.5598, Z = 1.8135, Yaw = -10.351 } },
		{ Piece = "HomeAgain4_SleepLoop", Length = 1.7, Loop = true, Entry = 0.167, Exit = 0.033, EndOffset = { X = -0.5602, Z = 1.8135, Yaw = -10.365 } },
		{ Piece = "HomeAgain5", Length = 1.2, EndOffset = { X = -0.5641, Z = 1.8124, Yaw = -10.779 } },
		{ Piece = "HomeAgain6_LieLookAround", Length = 12.5, Loop = true, Entry = 5.467, Exit = 0.0, EndOffset = { X = -0.5582, Z = 1.8075, Yaw = -10.37 } },
	},
	Excuses = {
		{ Piece = "Excuses1_LieLookAround", Length = 12.5, Loop = true, Entry = 0.0, Exit = 4.133, EndOffset = { X = 0.0292, Z = 0.4564, Yaw = -2.141 } },
		{ Piece = "Excuses2", Length = 15.233, EndOffset = { X = 0.1354, Z = -1.9423, Yaw = -8.63 } },
	},
	ParentsWaiting = {
		{ Piece = "ParentsWaiting1_ParentSit", Length = 6.4, Loop = true, Entry = 0.0, Exit = 2.8, EndOffset = { X = -0.0151, Z = -0.5023, Yaw = 0.452 } },
		{ Piece = "ParentsWaiting2", Length = 3.067, EndOffset = { X = -0.0103, Z = -0.5252, Yaw = 0.422 } },
		{ Piece = "ParentsWaiting3_ParentSit", Length = 6.4, Loop = true, Entry = 3.8, Exit = 0.067, EndOffset = { X = -0.0131, Z = -0.5142, Yaw = 0.307 } },
		{ Piece = "ParentsWaiting4", Length = 30.967, EndOffset = { X = -0.0073, Z = -0.5289, Yaw = -0.657 } },
		{ Piece = "ParentsWaiting5_ParentSit", Length = 6.4, Loop = true, Entry = 0.567, Exit = 0.0, EndOffset = { X = -0.0084, Z = -0.5109, Yaw = -0.724 } },
	},
	Breakfast = {
		{ Piece = "Breakfast1_TableIdle", Length = 4.167, Loop = true, Entry = 0.0, Exit = 0.467, EndOffset = { X = -0.0153, Z = -0.2294, Yaw = -0.947 } },
		{ Piece = "Breakfast2", Length = 6.433, EndOffset = { X = -0.0218, Z = -0.2219, Yaw = -0.997 } },
		{ Piece = "Breakfast3_TableIdle", Length = 4.167, Loop = true, Entry = 1.133, Exit = 0.0, EndOffset = { X = -0.0161, Z = -0.2258, Yaw = -0.893 } },
	},
	MomSlidesEnvelope = {
		{ Piece = "MomSlidesEnvelope1_ParentSit", Length = 6.4, Loop = true, Entry = 0.0, Exit = 2.867, EndOffset = { X = -0.0151, Z = -0.5023, Yaw = 0.452 } },
		{ Piece = "MomSlidesEnvelope2", Length = 1.9, EndOffset = { X = -0.0225, Z = -0.4205, Yaw = 0.885 } },
		{ Piece = "MomSlidesEnvelope3_ParentSit", Length = 6.4, Loop = true, Entry = 0.633, Exit = 0.0, EndOffset = { X = -0.023, Z = -0.3996, Yaw = 0.786 } },
	},
	TheBus = {
		{ Piece = "TheBus1_WaitBored", Length = 10.667, Loop = true, Entry = 0.0, Exit = 5.133, EndOffset = { X = -0.0118, Z = 0.0769, Yaw = 1.548 } },
		{ Piece = "TheBus2", Length = 4.0, EndOffset = { X = -0.1218, Z = -1.2967, Yaw = -9.195 } },
	},
}
local ONLY = nil
local BLENDS = {
	ColdOpen = { { piece = "ColdOpen1", t = 2.233, name = "PeekOut -> ClimbThrough" } },
	Drainpipe = { { piece = "Drainpipe1", t = 1.833, name = "WallClimbDown -> HangDrop" }, { piece = "Drainpipe1", t = 2.400, name = "HangDrop -> GameCrouch" } },
	BiscuitStirs = { { piece = "BiscuitStirs2", t = 0.567, name = "GameCrouchWalk -> LookBackNervous" }, { piece = "BiscuitStirs2", t = 4.333, name = "LookBackNervous -> SneakRight" }, { piece = "BiscuitStirs2", t = 5.233, name = "SneakRight -> GameCrouchWalk" } },
	FenceOver = { { piece = "FenceOver2", t = 0.600, name = "GameCrouchWalk -> ClimbThrough" } },
	ThePlan = { { piece = "ThePlan1", t = 0.867, name = "FastStop -> Think" }, { piece = "ThePlan1", t = 3.767, name = "Think -> PointForward" } },
	Getaway = { { piece = "Getaway2", t = 0.367, name = "RunLookBack -> HedgeDive" }, { piece = "Getaway2", t = 1.333, name = "HedgeDive -> GetUpProne" }, { piece = "Getaway2", t = 7.733, name = "GetUpProne -> LookAroundNervous" } },
	HomeAgain = { { piece = "HomeAgain1", t = 2.100, name = "PullUpLedge -> GameCrouchWalk" }, { piece = "HomeAgain3", t = 0.567, name = "GameCrouchWalk -> LieDown" }, { piece = "HomeAgain3", t = 4.300, name = "LieDown -> SleepLoop" }, { piece = "HomeAgain5", t = 0.600, name = "SleepLoop -> LieLookAround" } },
	Excuses = { { piece = "Excuses2", t = 0.633, name = "LieLookAround -> StandUpFromBack" }, { piece = "Excuses2", t = 5.467, name = "StandUpFromBack -> ExcuseAsk" }, { piece = "Excuses2", t = 7.400, name = "ExcuseAsk -> ExcuseShrug" }, { piece = "Excuses2", t = 8.933, name = "ExcuseShrug -> ExcuseShame" } },
	ParentsWaiting = { { piece = "ParentsWaiting2", t = 0.500, name = "ParentSit -> ParentHeadShake" }, { piece = "ParentsWaiting2", t = 2.567, name = "ParentHeadShake -> ParentSit" }, { piece = "ParentsWaiting4", t = 0.300, name = "ParentSit -> ParentTalkSit" }, { piece = "ParentsWaiting4", t = 30.667, name = "ParentTalkSit -> ParentSit" } },
	Breakfast = { { piece = "Breakfast2", t = 0.333, name = "TableIdle -> TableAsk" }, { piece = "Breakfast2", t = 6.100, name = "TableAsk -> TableIdle" } },
	MomSlidesEnvelope = { { piece = "MomSlidesEnvelope2", t = 0.367, name = "ParentSit -> TablePoint" }, { piece = "MomSlidesEnvelope2", t = 1.367, name = "TablePoint -> ParentSit" } },
	TheBus = { { piece = "TheBus2", t = 0.467, name = "WaitBored -> BusArrives" }, { piece = "TheBus2", t = 2.633, name = "BusArrives -> BoardBus" } },
}
local FOLDER = game.ReplicatedStorage.NHCineClips.Tutorial
local DT = 1 / 60

local Players = game:GetService("Players")
local dummy = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R6)
dummy.Name = "_ChainCheck"
dummy:PivotTo(CFrame.new(0, 500, 0))
dummy.HumanoidRootPart.Anchored = true
dummy.Parent = workspace
local hum = dummy:FindFirstChildOfClass("Humanoid")
local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator", hum)
local PARTS = { "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local ENDS = { Torso = Vector3.new(0, 1, 0), Head = Vector3.new(0, 0.5, 0), ["Left Arm"] = Vector3.new(0, -1, 0), ["Right Arm"] = Vector3.new(0, -1, 0), ["Left Leg"] = Vector3.new(0, -1, 0), ["Right Leg"] = Vector3.new(0, -1, 0) }

local tracks = {}
local function track(name)
	if tracks[name] then return tracks[name] end
	local seq = FOLDER:FindFirstChild(name)
	assert(seq, "missing clip " .. name)
	local a = Instance.new("Animation")
	a.AnimationId = seq:GetAttribute("PreviewId")
	local t = animator:LoadAnimation(a)
	t.Priority = Enum.AnimationPriority.Action
	local t0 = os.clock()
	while t.Length == 0 and os.clock() - t0 < 15 do task.wait(0.1) end  -- a freshly registered clip loads a moment later
	assert(t.Length > 0, "clip never loaded: " .. name)
	tracks[name] = t
	return t
end

local samples, marks = {}, {}
local function sample()
	animator:StepAnimations(DT)
	local pts = {}
	for _, p in PARTS do
		local part = dummy[p]
		table.insert(pts, (part.CFrame * CFrame.new(ENDS[p])).Position)
		table.insert(pts, part.Position)
	end
	table.insert(samples, pts)
end
local function run(secs)
	for _ = 1, math.floor(secs / DT + 0.5) do sample() end
end

local report = {}
for chainName, steps in CHAINS do
	if ONLY and chainName ~= ONLY then continue end
	samples, marks = {}, {}
	local prev = nil
	local over = 0
	for k, st in steps do
		local t = track(st.Piece)
		t.Looped = st.Loop == true
		t:Play(0)                                                  -- identical frames: switch instantly, no fade from weight 0
		t.TimePosition = if st.Loop then (st.Entry + over) % st.Length else math.max(0, over)  -- carry the offset from the exact switch point
		if prev then prev:Stop(0) end
		if k > 1 then
			table.insert(marks, { at = #samples, name = "switch " .. steps[k - 1].Piece .. " -> " .. st.Piece })
		end
		for _, b in BLENDS[chainName] or {} do                  -- the blends baked inside this piece
			if b.piece == st.Piece then
				table.insert(marks, { at = #samples + math.floor((b.t - over) / DT + 0.5), name = "baked  " .. b.name })
			end
		end
		if st.Loop then
			run(st.Length)                                         -- a full pass, then on to the exit phase
			if steps[k + 1] then
				local left = (st.Exit - t.TimePosition) % st.Length
				local n = math.ceil(left / DT - 1e-6)
				run(n * DT)
				over = n * DT - left
			end
		else
			-- hand over up to one tick BEFORE the end (a one-shot can't play past its last frame: it would stall there);
			-- the piece's tail is the next loop's own frames, so the loop just starts that much earlier in its cycle
			local n = math.floor((st.Length - over) / DT + 1e-6)
			run(n * DT)
			over = n * DT - (st.Length - over)
		end
		prev = t
	end
	if prev then prev:Stop(0) end
	-- accelerations of every tracked point
	local acc = {}
	for i = 3, #samples do
		local m = 0
		for j = 1, #samples[i] do
			local a = (samples[i][j] - 2 * samples[i - 1][j] + samples[i - 2][j]).Magnitude / (DT * DT)
			if a > m then m = a end
		end
		acc[i] = m
	end
	local near = {}
	for _, mk in marks do
		for i = mk.at - 20, mk.at + 20 do near[i] = true end
	end
	local inside = {}
	for i = 3, #samples do
		if not near[i] and acc[i] then table.insert(inside, acc[i]) end
	end
	table.sort(inside)
	local p99 = inside[math.max(1, math.floor(#inside * 0.99))] or 1
	if p99 <= 0 then
		table.insert(report, chainName .. ": NOT MEASURED (the dummy did not move)")
		continue
	end
	local lines = { string.format("%s: %d frames, the clips' own motion p99 %.0f st/s2", chainName, #samples, p99) }
	for _, mk in marks do
		local peak = 0
		local r = if string.sub(mk.name, 1, 6) == "switch" then 4 else 20
		for i = mk.at - r, mk.at + r do
			if acc[i] and acc[i] > peak then peak = acc[i] end
		end
		local judged = string.sub(mk.name, 1, 6) == "switch"       -- baked blends are audited offline by build.py
		local pass = peak <= p99 or peak <= 45
		table.insert(lines, string.format("  %-58s peak %5.0f (%.2fx) %s", mk.name, peak, peak / p99, if judged then (pass and "ok" or "POP") else "(baked)"))
	end
	table.insert(report, table.concat(lines, "\n"))
	for _, t in tracks do t:Stop(0) end
	animator:StepAnimations(0)
end
dummy:Destroy()
table.sort(report)
return table.concat(report, "\n")
