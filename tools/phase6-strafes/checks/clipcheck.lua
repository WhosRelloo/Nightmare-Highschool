-- clipcheck (phase6-strafes T2, Edit): the 42 NHG_ KeyframeSequences in ServerStorage.NHGestures and NHPublish.Gestures.
-- Config.Gestures is inlined by harness/pure.py. Reads only.  python -X utf8 -I harness/pure.py checks/clipcheck.lua
local function load(name) return loadstring(__SRC[name])() end
local Cfg = load("ReplicatedStorage.Config.Gestures.luau")
local SS = game:GetService("ServerStorage")
local A, B = SS:FindFirstChild("NHGestures"), SS:FindFirstChild("NHPublish") and SS.NHPublish:FindFirstChild("Gestures")
if not (A and B) then return "FAIL folders missing" end
local Fails, N = {}, 0
local function lenOf(KS) local M = 0 for _, K in KS:GetChildren() do if K:IsA("Keyframe") then M = math.max(M, K.Time) end end return M end
local function check(Full, Clip)
	N += 1
	local K1, K2 = A:FindFirstChild(Full), B:FindFirstChild(Full)
	if not (K1 and K2) then table.insert(Fails, Full .. " missing") return end
	if K1.Loop ~= Clip.Loop then table.insert(Fails, Full .. " loop " .. tostring(K1.Loop)) end
	if K1.Priority.Name ~= Clip.Priority then table.insert(Fails, Full .. " priority " .. K1.Priority.Name) end
	if math.abs(lenOf(K1) - Clip.Len) > 0.02 then table.insert(Fails, string.format("%s len %.3f want %.3f", Full, lenOf(K1), Clip.Len)) end
	if Clip.Upper then
		for _, P in K1:GetDescendants() do
			if P:IsA("Pose") and (P.Name == "Left Leg" or P.Name == "Right Leg") then table.insert(Fails, Full .. " has leg poses") break end
			if P:IsA("Pose") and P.Name == "Torso" and P.Weight > 0 then table.insert(Fails, Full .. " torso weight " .. P.Weight) break end
		end
	end
end
for Base, Clip in Cfg.Clips do
	if Clip.Buckets then for _, Bk in Clip.Buckets do check("NHG_" .. Base .. "_" .. Bk, Clip) end
	else check("NHG_" .. Base, Clip) end
end
-- the square-chest strafes: chest yaw <= 1 degree on every frame, and the client copies
local RS = game:GetService("ReplicatedStorage"):FindFirstChild("NHLocoClips")
for _, S in { "NHG_StrafeLeft_Square", "NHG_StrafeRight_Square" } do
	N += 1
	local KS = A:FindFirstChild(S)
	if not (KS and B:FindFirstChild(S) and RS and RS:FindFirstChild(S)) then table.insert(Fails, S .. " missing (server, publish or client copy)") continue end
	if not KS.Loop or KS.Priority ~= Enum.AnimationPriority.Core then table.insert(Fails, S .. " loop/priority") end
	local Worst = 0
	for _, P in KS:GetDescendants() do
		if P:IsA("Pose") and P.Name == "Torso" then
			local V = P.CFrame.RightVector
			Worst = math.max(Worst, math.abs(math.deg(math.atan2(V.Y, V.X))))
		end
	end
	if Worst > 1 then table.insert(Fails, string.format("%s torso yaw %.1f", S, Worst)) end
end
return (#Fails == 0 and "PASS clipcheck " or "FAIL clipcheck\n" .. table.concat(Fails, "\n") .. "\n") .. N .. " pieces checked"
