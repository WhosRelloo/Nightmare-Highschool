-- bake_soccer_clips (soccer-2.0 Task 2, Edit): copies the 24 FIER soccer clips from Workspace."Soccer Anims".AnimSaves
-- into ReplicatedStorage.NHSoccerClips with the baked travel removed, Contact markers, the right-foot mirror and loop
-- flags, and writes ReplicatedStorage.Config.SoccerClips (lengths, contacts, travel paths, strides). It only reads the
-- sources. Re-runnable: it rebuilds the folder and the module each time.
-- usage: python -X utf8 -I tools/admin-console/run_check.py Edit tools/soccer2/bake/bake_soccer_clips.lua
-- Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §1.
local RS = game:GetService("ReplicatedStorage")
local Rig = workspace:FindFirstChild("Soccer Anims")
local Src = Rig and Rig:FindFirstChild("AnimSaves")
if not Src then return 'FAIL no Workspace."Soccer Anims".AnimSaves' end
local Root, Torso = Rig:FindFirstChild("HumanoidRootPart"), Rig:FindFirstChild("Torso")
local RJ = Root and Root:FindFirstChild("RootJoint")
if not (RJ and Torso) then return "FAIL the rig has no RootJoint / Torso" end
local C0r = RJ.C0 - RJ.C0.Position

local NAMES = { "Chip_R6", "Fallen Idle_R6", "Goalkeeper CatchIdle_R6", "Goalkeeper Catch_R6", "Goalkeeper Diving SaveLeft_R6",
	"Goalkeeper Diving SaveRigh_R6", "Goalkeeper Idle_R6", "Goalkeeper StepLeft_R6", "Goalkeeper StepRight_R6", "Jog Backward_R6",
	"Jog Forward_R6", "Kick Soccerball_R6", "Offensive Idle_R6", "Scissor Kick_R6", "Soccer Idle_R6", "Soccer Pass_R6",
	"Soccer Penalty Kick_R6", "Soccer Spin_R6", "Soccer Tackle_R6", "Soccer Tackled2_R6", "Soccer Tackled_R6", "Soccer Trip_R6",
	"Stall Soccerball_R6", "Strike Foward Jog_R6" }
local MIRROR_FROM, MIRROR_TO = "Kick Soccerball_R6", "KickSoccerball_Right"
local CONTACT = { ["Strike Foward Jog_R6"] = { 0.43 }, ["Kick Soccerball_R6"] = { 0.23 }, [MIRROR_TO] = { 0.23 },
	["Soccer Pass_R6"] = { 0.47 }, ["Chip_R6"] = { 0.53 }, ["Scissor Kick_R6"] = { 0.68 }, ["Soccer Penalty Kick_R6"] = { 0.73 },
	["Soccer Spin_R6"] = { 0.23, 0.60 }, ["Soccer Tackle_R6"] = { 0.53 } }
local LOOPMODE = { ["Jog Forward_R6"] = true, ["Goalkeeper CatchIdle_R6"] = true }
local PATHMODE = { ["Chip_R6"] = true, ["Soccer Penalty Kick_R6"] = true, ["Soccer Spin_R6"] = true, ["Soccer Tackled_R6"] = true,
	["Soccer Trip_R6"] = true, ["Goalkeeper Diving SaveLeft_R6"] = true, ["Goalkeeper Diving SaveRigh_R6"] = true,
	["Goalkeeper StepLeft_R6"] = true, ["Goalkeeper StepRight_R6"] = true }
local LOOPS = { ["Soccer Idle_R6"] = true, ["Offensive Idle_R6"] = true, ["Goalkeeper Idle_R6"] = true, ["Goalkeeper CatchIdle_R6"] = true,
	["Goalkeeper StepLeft_R6"] = true, ["Goalkeeper StepRight_R6"] = true, ["Jog Forward_R6"] = true, ["Jog Backward_R6"] = true,
	["Fallen Idle_R6"] = true }

local JOINT = { Torso = RJ; Head = Torso:FindFirstChild("Neck"); ["Left Arm"] = Torso:FindFirstChild("Left Shoulder");
	["Right Arm"] = Torso:FindFirstChild("Right Shoulder"); ["Left Leg"] = Torso:FindFirstChild("Left Hip"); ["Right Leg"] = Torso:FindFirstChild("Right Hip") }
for N, J in JOINT do if not J then return "FAIL the rig has no joint for " .. N end end
local SWAP = { ["Left Arm"] = "Right Arm", ["Right Arm"] = "Left Arm", ["Left Leg"] = "Right Leg", ["Right Leg"] = "Left Leg" }

local function keys(KS) local L = {} for _, K in KS:GetChildren() do if K:IsA("Keyframe") then table.insert(L, K) end end table.sort(L, function(a, b) return a.Time < b.Time end) return L end
local function pose(K, Name) for _, P in K:GetDescendants() do if P:IsA("Pose") and P.Name == Name then return P end end return nil end
local function length(KS) local L = keys(KS) return if #L > 0 then L[#L].Time else 0 end
local function r3(v) return math.floor(v * 1000 + 0.5) / 1000 end
-- HRP-space position of a Torso pose: the RootJoint Transform turned by C0's rotation (+X right, +Y up, -Z forward)
local function hrp(P) return C0r:VectorToWorldSpace(P.CFrame.Position) end
local function setHrp(P, V) P.CFrame = CFrame.new(C0r:VectorToObjectSpace(V)) * (P.CFrame - P.CFrame.Position) end
-- linear sample of { {t, x, z} } rows
local function at(Rows, t)
	if t <= Rows[1][1] then return Rows[1][2], Rows[1][3] end
	for I = 2, #Rows do
		local B = Rows[I]
		if t <= B[1] then local A = Rows[I - 1] local u = (t - A[1]) / math.max(B[1] - A[1], 1e-6) return A[2] + (B[2] - A[2]) * u, A[3] + (B[3] - A[3]) * u end
	end
	return Rows[#Rows][2], Rows[#Rows][3]
end

-- §1.1: remove the baked travel in place; returns the removed offsets { {t, dx, dz}, ... } at the Torso keys
local function strip(KS, Mode)
	local L = keys(KS)
	local First, Last
	for _, K in L do local P = pose(K, "Torso") if P then First = First or { T = K.Time; V = hrp(P) } Last = { T = K.Time; V = hrp(P) } end end
	if not First then return nil end
	local Span = math.max(Last.T - First.T, 1e-6)
	local Raw = {}
	for _, K in L do
		local P = pose(K, "Torso")
		if P then
			local V = hrp(P)
			local dx, dz
			if Mode == "Loop" then
				local u = (K.Time - First.T) / Span
				dx, dz = (Last.V.X - First.V.X) * u, (Last.V.Z - First.V.Z) * u
			else
				dx, dz = V.X - First.V.X, V.Z - First.V.Z
			end
			table.insert(Raw, { K.Time, dx, dz })
			setHrp(P, Vector3.new(V.X - dx, V.Y, V.Z - dz))
		end
	end
	return Raw
end
local function resample(Raw, Len)
	local Out = {}
	for I = 0, math.max(1, math.floor(Len * 30 + 0.5)) do
		local t = math.min(I / 30, Len)
		local x, z = at(Raw, t)
		table.insert(Out, { r3(t), r3(x), r3(z) })
	end
	return Out
end

-- §1.3: the mirror (M * T * M with M = X scaled by -1, then solved for the opposite joint)
local function reflect(C)
	local x, y, z, r00, r01, r02, r10, r11, r12, r20, r21, r22 = C:GetComponents()
	return CFrame.new(-x, y, z, r00, -r01, -r02, -r10, r11, r12, -r20, r21, r22)
end
local function mirror(KS)
	for _, K in keys(KS) do
		local Todo = {}
		for _, P in K:GetDescendants() do
			if P:IsA("Pose") and JOINT[P.Name] then
				local To = SWAP[P.Name] or P.Name
				local A, B = JOINT[P.Name], JOINT[To]
				table.insert(Todo, { P = P; To = To; CF = B.C0:Inverse() * reflect(A.C0 * P.CFrame * A.C1:Inverse()) * B.C1 })
			end
		end
		for _, It in Todo do It.P.Name = It.To It.P.CFrame = It.CF end
	end
end

-- §1.2: a Contact marker on the keyframe at t (an empty keyframe is added when none is within half a frame)
local function addMarker(KS, t)
	local Best, Dist = nil, math.huge
	for _, K in keys(KS) do local d = math.abs(K.Time - t) if d < Dist then Best, Dist = K, d end end
	if not Best or Dist > 1 / 60 then Best = Instance.new("Keyframe") Best.Time = t Best.Parent = KS end
	local M = Instance.new("KeyframeMarker") M.Name = "Contact" M.Value = tostring(t)
	Best:AddMarker(M)
end

-- §1.4: 2 x the largest fore-aft foot spread / length (the strafe baker's rule), feet in Torso space
local function spread(KS)
	local LH, RH = JOINT["Left Leg"], JOINT["Right Leg"]
	local Best = 0
	for _, K in keys(KS) do
		local L, R = pose(K, "Left Leg"), pose(K, "Right Leg")
		if L and R then
			local Lf = (LH.C0 * L.CFrame * LH.C1:Inverse()) * Vector3.new(0, -1, 0)
			local Rf = (RH.C0 * R.CFrame * RH.C1:Inverse()) * Vector3.new(0, -1, 0)
			Best = math.max(Best, math.abs(Lf.Z - Rf.Z))
		end
	end
	return 2 * Best / math.max(length(KS), 1e-6)
end

local Missing = {}
for _, N in NAMES do local S = Src:FindFirstChild(N) if not (S and S:IsA("KeyframeSequence")) then table.insert(Missing, N) end end
if #Missing > 0 then return "FAIL missing source clips: " .. table.concat(Missing, ", ") end

local Out = Instance.new("Folder")
Out.Name = "NHSoccerClips"
local Data = {}
local function bake(Source, Name)
	local KS = Source:Clone()
	KS.Name = Name
	local Len = length(KS)
	local E = { Length = r3(Len); Loop = LOOPS[Name] == true }
	if Name == MIRROR_TO then mirror(KS) end
	local Mode = if LOOPMODE[Name] then "Loop" elseif PATHMODE[Name] then "Path" else nil
	if Mode then
		local Raw = strip(KS, Mode)
		if Raw and Mode == "Path" then E.Path = resample(Raw, Len) end
		if Raw and Mode == "Loop" then E.Ramp = { r3(Raw[#Raw][2]), r3(Raw[#Raw][3]) } end
	end
	local C = CONTACT[Name]
	if C then
		E.ContactAt = C[1]
		if #C > 1 then E.Contacts = C end
		for _, t in C do addMarker(KS, t) end
	end
	KS.Loop = E.Loop
	KS.Parent = Out
	Data[Name] = E
end
for _, N in NAMES do bake(Src[N], N) end
bake(Src[MIRROR_FROM], MIRROR_TO)

-- Diving SaveRigh's own travel is baked forward: its path is Diving SaveLeft's, mirrored, on its own clock
local DL, DR = Data["Goalkeeper Diving SaveLeft_R6"], Data["Goalkeeper Diving SaveRigh_R6"]
local Scale = DL.Length / math.max(DR.Length, 1e-6)
local P = {}
for I = 0, math.floor(DR.Length * 30 + 0.5) do
	local t = math.min(I / 30, DR.Length)
	local x, z = at(DL.Path, t * Scale)
	table.insert(P, { r3(t), r3(-x), r3(z) })
end
DR.Path = P

local function sideSpeed(E) local L = E.Path[#E.Path] return math.sqrt(L[2] * L[2] + L[3] * L[3]) / math.max(E.Length, 1e-6) end
local Jog = Data["Jog Forward_R6"]
local Stride = {
	SoccerJog = r3(math.sqrt(Jog.Ramp[1] ^ 2 + Jog.Ramp[2] ^ 2) / math.max(Jog.Length, 1e-6));
	SoccerJogBack = r3(spread(Out["Jog Backward_R6"]));
	KeeperStep = r3((sideSpeed(Data["Goalkeeper StepLeft_R6"]) + sideSpeed(Data["Goalkeeper StepRight_R6"])) / 2);
}

-- Config.SoccerClips (generated)
local function f(v) return tostring(r3(v)) end
local Lines = {
	"-- GENERATED by tools/soccer2/bake/bake_soccer_clips.lua (soccer-2.0). Do not edit by hand: change the bake and re-run it.",
	"-- Clips[name] = { Length, Loop, ContactAt?, Contacts?, Path?, Ramp? }. Path rows { t, x, z } (HRP space, studs, 30 fps)",
	"-- are the travel the bake removed; Ramp is a loop clip's removed travel per cycle. Stride: ground speed at 1x on",
	"-- 2-stud legs (the Config.Locomotion.Stride unit). Spec: docs/superpowers/specs/2026-11-24-soccer-2-0-design.md §1.",
	"return {",
	"\tClips = {",
}
local Sorted = {}
for N in Data do table.insert(Sorted, N) end
table.sort(Sorted)
for _, N in Sorted do
	local E = Data[N]
	local Parts = { "Length = " .. f(E.Length), "Loop = " .. tostring(E.Loop) }
	if E.ContactAt then table.insert(Parts, "ContactAt = " .. f(E.ContactAt)) end
	if E.Contacts then local C = {} for _, t in E.Contacts do table.insert(C, f(t)) end table.insert(Parts, "Contacts = { " .. table.concat(C, ", ") .. " }") end
	if E.Ramp then table.insert(Parts, "Ramp = { " .. f(E.Ramp[1]) .. ", " .. f(E.Ramp[2]) .. " }") end
	if E.Path then local Rows = {} for _, Rw in E.Path do table.insert(Rows, "{" .. f(Rw[1]) .. "," .. f(Rw[2]) .. "," .. f(Rw[3]) .. "}") end table.insert(Parts, "Path = { " .. table.concat(Rows, ", ") .. " }") end
	table.insert(Lines, string.format("\t\t[%q] = { %s };", N, table.concat(Parts, "; ")))
end
table.insert(Lines, "\t};")
table.insert(Lines, string.format("\tStride = { SoccerJog = %s; SoccerJogBack = %s; KeeperStep = %s };", f(Stride.SoccerJog), f(Stride.SoccerJogBack), f(Stride.KeeperStep)))
table.insert(Lines, "}")

local Old = RS:FindFirstChild("NHSoccerClips")
if Old then Old:Destroy() end
Out.Parent = RS
local Mod = RS.Config:FindFirstChild("SoccerClips")
if not Mod then Mod = Instance.new("ModuleScript") Mod.Name = "SoccerClips" Mod.Parent = RS.Config end
Mod.Source = table.concat(Lines, "\n") .. "\n"
return string.format("PASS baked %d clips; SoccerJog %s, SoccerJogBack %s, KeeperStep %s (Jog Forward spread rule %s); Config.SoccerClips %d bytes",
	#Out:GetChildren(), f(Stride.SoccerJog), f(Stride.SoccerJogBack), f(Stride.KeeperStep), f(spread(Out["Jog Forward_R6"])), #Mod.Source)
