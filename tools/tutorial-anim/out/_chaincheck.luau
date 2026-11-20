-- tools/tutorial-anim/chaincheck.luau: play each tutorial chain on a temporary R6 dummy in Edit mode, exactly as the
-- game will (each piece in turn, loops entered at Entry and left at Exit), step the Animator at 60 fps and measure every
-- handoff, both the runtime switches between pieces and the blends baked inside them: the peak acceleration of the body's parts across the cut against the clips' own motion inside the
-- steps. A runtime switch passes when its peak stays at or under the clips' own p99 (or under a gentle 45 st/s2): the
-- cut is no jerkier than the motion around it. Baked blends are printed for reference (build.py audits them against
-- their own source clips). Destroys the dummy after.
-- build.py writes out/_chaincheck.luau from this, with the plan pasted in as CHAINS.
local CHAINS = {
	ColdOpen = {
		{ Piece = "ColdOpen1", Length = 3.633, Hold = true },
	},
	Drainpipe = {
		{ Piece = "Drainpipe1", Length = 2.867 },
		{ Piece = "Drainpipe2_SneakLoop", Length = 1.667, Loop = true, Entry = 1.433, Exit = 0.0 },
	},
	BiscuitStirs = {
		{ Piece = "BiscuitStirs1_SneakLoop", Length = 1.667, Loop = true, Entry = 0.0, Exit = 0.433 },
		{ Piece = "BiscuitStirs2", Length = 5.7 },
		{ Piece = "BiscuitStirs3_SneakLoop", Length = 1.667, Loop = true, Entry = 0.567, Exit = 0.0 },
	},
	FenceOver = {
		{ Piece = "FenceOver1_SneakLoop", Length = 1.667, Loop = true, Entry = 0.0, Exit = 0.667 },
		{ Piece = "FenceOver2", Length = 2.967 },
	},
	ThePlan = {
		{ Piece = "ThePlan1", Length = 8.167 },
	},
	Getaway = {
		{ Piece = "Getaway1_RunLookBack", Length = 2.233, Loop = true, Entry = 0.0, Exit = 1.933 },
		{ Piece = "Getaway2", Length = 8.1 },
		{ Piece = "Getaway3_LookAroundNervous", Length = 4.467, Loop = true, Entry = 1.8, Exit = 0.0 },
	},
	HomeAgain = {
		{ Piece = "HomeAgain1", Length = 2.7 },
		{ Piece = "HomeAgain2_SneakLoop", Length = 1.667, Loop = true, Entry = 0.3, Exit = 0.533 },
		{ Piece = "HomeAgain3", Length = 4.9 },
		{ Piece = "HomeAgain4_SleepLoop", Length = 1.7, Loop = true, Entry = 0.167, Exit = 0.033 },
		{ Piece = "HomeAgain5", Length = 1.2 },
		{ Piece = "HomeAgain6_LieLookAround", Length = 12.5, Loop = true, Entry = 5.467, Exit = 0.0 },
	},
	Excuses = {
		{ Piece = "Excuses1_LieLookAround", Length = 12.5, Loop = true, Entry = 0.0, Exit = 4.133 },
		{ Piece = "Excuses2", Length = 15.233 },
	},
	ParentsWaiting = {
		{ Piece = "ParentsWaiting1_ParentSit", Length = 6.4, Loop = true, Entry = 0.0, Exit = 2.8 },
		{ Piece = "ParentsWaiting2", Length = 3.067 },
		{ Piece = "ParentsWaiting3_ParentSit", Length = 6.4, Loop = true, Entry = 3.8, Exit = 0.067 },
		{ Piece = "ParentsWaiting4", Length = 30.967 },
		{ Piece = "ParentsWaiting5_ParentSit", Length = 6.4, Loop = true, Entry = 0.567, Exit = 0.0 },
	},
	Breakfast = {
		{ Piece = "Breakfast1_TableIdle", Length = 4.167, Loop = true, Entry = 0.0, Exit = 0.467 },
		{ Piece = "Breakfast2", Length = 6.433 },
		{ Piece = "Breakfast3_TableIdle", Length = 4.167, Loop = true, Entry = 1.133, Exit = 0.0 },
	},
	MomSlidesEnvelope = {
		{ Piece = "MomSlidesEnvelope1_ParentSit", Length = 6.4, Loop = true, Entry = 0.0, Exit = 2.867 },
		{ Piece = "MomSlidesEnvelope2", Length = 1.9 },
		{ Piece = "MomSlidesEnvelope3_ParentSit", Length = 6.4, Loop = true, Entry = 0.633, Exit = 0.0 },
	},
	TheBus = {
		{ Piece = "TheBus1_WaitBored", Length = 10.667, Loop = true, Entry = 0.0, Exit = 5.133 },
		{ Piece = "TheBus2", Length = 4.0 },
	},
}
local ONLY = nil
local BLENDS = {
	ColdOpen = { { piece = "ColdOpen1", t = 2.233, name = "PeekOut -> ClimbThrough" } },
	Drainpipe = { { piece = "Drainpipe1", t = 1.833, name = "WallClimbDown -> HangDrop" }, { piece = "Drainpipe1", t = 2.400, name = "HangDrop -> SneakLoop" } },
	BiscuitStirs = { { piece = "BiscuitStirs2", t = 0.500, name = "SneakLoop -> LookBackNervous" }, { piece = "BiscuitStirs2", t = 4.267, name = "LookBackNervous -> SneakRight" }, { piece = "BiscuitStirs2", t = 5.267, name = "SneakRight -> SneakLoop" } },
	FenceOver = { { piece = "FenceOver2", t = 0.600, name = "SneakLoop -> ClimbThrough" } },
	ThePlan = { { piece = "ThePlan1", t = 0.867, name = "FastStop -> Think" }, { piece = "ThePlan1", t = 3.767, name = "Think -> PointForward" } },
	Getaway = { { piece = "Getaway2", t = 0.367, name = "RunLookBack -> HedgeDive" }, { piece = "Getaway2", t = 1.333, name = "HedgeDive -> GetUpProne" }, { piece = "Getaway2", t = 7.733, name = "GetUpProne -> LookAroundNervous" } },
	HomeAgain = { { piece = "HomeAgain1", t = 2.100, name = "PullUpLedge -> SneakLoop" }, { piece = "HomeAgain3", t = 0.433, name = "SneakLoop -> LieDown" }, { piece = "HomeAgain3", t = 4.333, name = "LieDown -> SleepLoop" }, { piece = "HomeAgain5", t = 0.600, name = "SleepLoop -> LieLookAround" } },
	Excuses = { { piece = "Excuses2", t = 0.633, name = "LieLookAround -> StandUpFromBack" }, { piece = "Excuses2", t = 5.467, name = "StandUpFromBack -> ExcuseAsk" }, { piece = "Excuses2", t = 7.400, name = "ExcuseAsk -> ExcuseShrug" }, { piece = "Excuses2", t = 8.933, name = "ExcuseShrug -> ExcuseShame" } },
	ParentsWaiting = { { piece = "ParentsWaiting2", t = 0.500, name = "ParentSit -> ParentHeadShake" }, { piece = "ParentsWaiting2", t = 2.567, name = "ParentHeadShake -> ParentSit" }, { piece = "ParentsWaiting4", t = 0.300, name = "ParentSit -> ParentTalkSit" }, { piece = "ParentsWaiting4", t = 30.667, name = "ParentTalkSit -> ParentSit" } },
	Breakfast = { { piece = "Breakfast2", t = 0.333, name = "TableIdle -> TableAsk" }, { piece = "Breakfast2", t = 6.100, name = "TableAsk -> TableIdle" } },
	MomSlidesEnvelope = { { piece = "MomSlidesEnvelope2", t = 0.367, name = "ParentSit -> TablePoint" }, { piece = "MomSlidesEnvelope2", t = 1.367, name = "TablePoint -> ParentSit" } },
	TheBus = { { piece = "TheBus2", t = 0.467, name = "WaitBored -> BusArrives" }, { piece = "TheBus2", t = 2.633, name = "BusArrives -> BoardBus" } },
}
local FOLDER = game.ServerStorage.NHTutorialAnims
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
