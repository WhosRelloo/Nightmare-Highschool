-- tools/tutorial-anim/chaincheck.luau: play each tutorial chain on a temporary R6 dummy in Edit mode, exactly as the
-- game will (each piece in turn, loops entered at Entry and left at Exit), step the Animator at 60 fps and measure every
-- handoff, both the runtime switches between pieces and the blends baked inside them: the peak acceleration of the body's parts across the cut against the clips' own motion inside the
-- steps. A runtime switch passes when its peak stays at or under the clips' own p99 (or under a gentle 45 st/s2): the
-- cut is no jerkier than the motion around it. Baked blends are printed for reference (build.py audits them against
-- their own source clips). Destroys the dummy after.
-- build.py writes out/_chaincheck.luau from this, with the plan pasted in as CHAINS.
local CHAINS = __CHAINS__
local ONLY = __ONLY__
local BLENDS = __BLENDS__
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
