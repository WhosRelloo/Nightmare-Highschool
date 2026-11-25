-- soccer_clips_edit (soccer-2.0 Task 2, Edit): the baked clips and Config.SoccerClips match the spec (§1).
-- usage: python -X utf8 -I tools/admin-console/run_check.py Edit tools/soccer2/checks/soccer_clips_edit.lua
local RS = game:GetService("ReplicatedStorage")
local F = RS:FindFirstChild("NHSoccerClips")
local Mod = RS.Config:FindFirstChild("SoccerClips")
if not (F and Mod) then return "FAIL not baked (NHSoccerClips " .. tostring(F ~= nil) .. ", Config.SoccerClips " .. tostring(Mod ~= nil) .. ")" end
local D = loadstring(Mod.Source)()
local Fails = {}
local Rig = workspace["Soccer Anims"]
local RJ = Rig.HumanoidRootPart.RootJoint
local C0r = RJ.C0 - RJ.C0.Position
local function keys(KS) local L = {} for _, K in KS:GetChildren() do if K:IsA("Keyframe") then table.insert(L, K) end end table.sort(L, function(a, b) return a.Time < b.Time end) return L end
local function pose(K, Name) for _, P in K:GetDescendants() do if P:IsA("Pose") and P.Name == Name then return P end end return nil end
-- 25 clips, each with data
local N = 0
for _, KS in F:GetChildren() do
	if KS:IsA("KeyframeSequence") then
		N += 1
		if not D.Clips[KS.Name] then table.insert(Fails, "no data for " .. KS.Name) end
	end
end
if N ~= 25 then table.insert(Fails, "clips " .. N .. ", want 25") end
-- Path clips: every Torso key within 0.1 stud (X/Z) of the first; Loop clips: the last key back on the first
local PATH = { "Chip_R6", "Soccer Penalty Kick_R6", "Soccer Spin_R6", "Soccer Tackled_R6", "Soccer Trip_R6",
	"Goalkeeper Diving SaveLeft_R6", "Goalkeeper Diving SaveRigh_R6", "Goalkeeper StepLeft_R6", "Goalkeeper StepRight_R6" }
local LOOPMODE = { "Jog Forward_R6", "Goalkeeper CatchIdle_R6" }
local function flat(KS)
	local L = {}
	for _, K in keys(KS) do local P = pose(K, "Torso") if P then local V = C0r:VectorToWorldSpace(P.CFrame.Position) table.insert(L, Vector2.new(V.X, V.Z)) end end
	return L
end
for _, Name in PATH do
	local KS = F:FindFirstChild(Name)
	if not KS then table.insert(Fails, "missing " .. Name) continue end
	local L = flat(KS)
	local Worst = 0
	for _, V in L do Worst = math.max(Worst, (V - L[1]).Magnitude) end
	if Worst >= 0.1 then table.insert(Fails, string.format("%s drifts %.2f", Name, Worst)) end
	if not (D.Clips[Name] and D.Clips[Name].Path) then table.insert(Fails, Name .. " has no Path") end
end
for _, Name in LOOPMODE do
	local KS = F:FindFirstChild(Name)
	if not KS then table.insert(Fails, "missing " .. Name) continue end
	local L = flat(KS)
	if (L[#L] - L[1]).Magnitude >= 0.05 then table.insert(Fails, string.format("%s still travels %.2f per cycle", Name, (L[#L] - L[1]).Magnitude)) end
end
-- the right dive goes right
local DR = D.Clips["Goalkeeper Diving SaveRigh_R6"]
if DR and DR.Path then local Last = DR.Path[#DR.Path] if Last[2] <= 1 then table.insert(Fails, "the right dive's path ends at x " .. Last[2]) end end
-- contact markers within a frame
local CONTACT = { ["Strike Foward Jog_R6"] = { 0.43 }, ["Kick Soccerball_R6"] = { 0.23 }, ["KickSoccerball_Right"] = { 0.23 },
	["Soccer Pass_R6"] = { 0.47 }, ["Chip_R6"] = { 0.53 }, ["Scissor Kick_R6"] = { 0.68 }, ["Soccer Penalty Kick_R6"] = { 0.73 },
	["Soccer Spin_R6"] = { 0.23, 0.60 }, ["Soccer Tackle_R6"] = { 0.53 } }
for Name, Times in CONTACT do
	local KS = F:FindFirstChild(Name)
	local Got = {}
	if KS then for _, K in keys(KS) do for _, M in K:GetMarkers() do if M.Name == "Contact" then table.insert(Got, K.Time) end end end end
	for _, t in Times do
		local Ok = false
		for _, g in Got do if math.abs(g - t) <= 1 / 30 then Ok = true end end
		if not Ok then table.insert(Fails, string.format("%s: no Contact marker at %.2f", Name, t)) end
	end
	if D.Clips[Name] and math.abs((D.Clips[Name].ContactAt or -1) - Times[1]) > 1e-3 then table.insert(Fails, Name .. " ContactAt in the data") end
end
-- the mirror kicks with the right leg (the source with the left)
local function legWork(KS, Leg, a, b)
	local Sum, Prev = 0, nil
	for _, K in keys(KS) do
		if K.Time >= a and K.Time <= b then
			local P = pose(K, Leg)
			if P then
				if Prev then local _, Ang = (Prev:Inverse() * P.CFrame):ToAxisAngle() Sum += math.abs(Ang) end
				Prev = P.CFrame
			end
		end
	end
	return Sum
end
local Src, Mir = F:FindFirstChild("Kick Soccerball_R6"), F:FindFirstChild("KickSoccerball_Right")
if Src and Mir then
	if not (legWork(Src, "Left Leg", 0.08, 0.38) > legWork(Src, "Right Leg", 0.08, 0.38)) then table.insert(Fails, "the source kick isn't left-footed (check the table)") end
	if not (legWork(Mir, "Right Leg", 0.08, 0.38) > legWork(Mir, "Left Leg", 0.08, 0.38)) then table.insert(Fails, "the mirror doesn't kick with the right leg") end
else
	table.insert(Fails, "no kick or mirror to compare")
end
-- loop flags
local LOOPS = { ["Soccer Idle_R6"] = true, ["Offensive Idle_R6"] = true, ["Goalkeeper Idle_R6"] = true, ["Goalkeeper CatchIdle_R6"] = true,
	["Goalkeeper StepLeft_R6"] = true, ["Goalkeeper StepRight_R6"] = true, ["Jog Forward_R6"] = true, ["Jog Backward_R6"] = true, ["Fallen Idle_R6"] = true }
for _, KS in F:GetChildren() do
	if KS:IsA("KeyframeSequence") and KS.Loop ~= (LOOPS[KS.Name] == true) then table.insert(Fails, KS.Name .. " Loop " .. tostring(KS.Loop)) end
end
-- the sources are untouched
for _, KS in workspace["Soccer Anims"].AnimSaves:GetChildren() do if KS:IsA("KeyframeSequence") and KS.Loop then table.insert(Fails, "source " .. KS.Name .. " was changed (Loop)") end end
-- strides
for _, K in { "SoccerJog", "SoccerJogBack", "KeeperStep" } do
	local V = D.Stride and D.Stride[K]
	if not (V and V >= 3 and V <= 9) then table.insert(Fails, "stride " .. K .. " = " .. tostring(V)) end
end
if #Fails > 0 then return "FAIL soccer_clips_edit\n" .. table.concat(Fails, "\n") end
return string.format("PASS soccer_clips_edit (25 clips; SoccerJog %s, SoccerJogBack %s, KeeperStep %s)", tostring(D.Stride.SoccerJog), tostring(D.Stride.SoccerJogBack), tostring(D.Stride.KeeperStep))
