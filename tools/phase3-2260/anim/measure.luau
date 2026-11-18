--!nonstrict
-- Measure the installed clips on a standard R6 rig (2-stud legs): planted-foot skate (sole within 0.12 of the floor),
-- floor penetration, and pops (the lowest corner, compared with the same corner a frame earlier, so a roll is not a slide)
-- (largest one-frame jump of a sole or the torso, studs per frame at 60 fps).
local Folder = game.ReplicatedStorage.NHCineClips.Animations
local VERBOSE = __VERBOSE__
local out = {}
local M = game.ServerScriptService.Services.AI.AI.Rig:Clone()
for _, d in ipairs(M:GetDescendants()) do if d:IsA("Script") or d:IsA("LocalScript") then d:Destroy() end end
M:PivotTo(CFrame.new(0, 103, 0))
M.Parent = workspace
M:ScaleTo(M:GetScale() * (2 / M["Left Leg"].Size.Y))
M.HumanoidRootPart.Anchored = true
local An = M.Humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", M.Humanoid)
local Root, RJ, Torso = M.HumanoidRootPart, M.HumanoidRootPart.RootJoint, M.Torso
local Hips = { ["Left Leg"] = Torso:FindFirstChild("Left Hip"), ["Right Leg"] = Torso:FindFirstChild("Right Hip") }
local function soles()
	local T = Root.CFrame * RJ.C0 * RJ.Transform * RJ.C1:Inverse()
	local res = { torso = T.Position }
	for legName, H in pairs(Hips) do
		local cf, s = T * H.C0 * H.Transform * H.C1:Inverse(), M[legName].Size / 2
		local lo, at, all = math.huge, nil, {}
		for _, x in ipairs({ -1, 1 }) do for _, z in ipairs({ -1, 1 }) do local p = (cf * CFrame.new(x * s.X, -s.Y, z * s.Z)).Position table.insert(all, p) if p.Y < lo then lo, at = p.Y, #all end end end
		res[legName] = { h = lo - Root.Position.Y; p = all[at]; i = at; all = all }
	end
	return res
end
local Floor = soles()["Left Leg"].h
for _, Seq in ipairs(Folder:GetChildren()) do
	if Seq:IsA("KeyframeSequence") then
		local A = Instance.new("Animation") A.AnimationId = Seq:GetAttribute("PreviewId") or ""
		local Tr = An:LoadAnimation(A) Tr:Play(0) Tr:AdjustSpeed(0)
		local t0 = os.clock() while Tr.Length <= 0 and os.clock() - t0 < 3 do task.wait() end
		local prev, skates, deepest, pop, popAt, tpop, tpopAt = nil, {}, 0, 0, 0, 0, 0
		for f = 0, math.floor(Tr.Length * 60) do
			Tr.TimePosition = math.min(f / 60, Tr.Length - 0.001) An:StepAnimations(0)
			local S = soles()
			local speeds = {}
			for _, legName in ipairs({ "Left Leg", "Right Leg" }) do
				local s = S[legName]
				deepest = math.min(deepest, s.h - Floor)
				if prev then
					local j = (s.p - prev[legName].all[s.i]).Magnitude
					if j > pop then pop, popAt = j, f / 60 end
					-- the contact: of the corners within 0.01 of the lowest, the stillest (a foot pivoting on a pinned corner is planted)
					local sp = math.huge
					for ci, c in ipairs(s.all) do
						if c.Y - Root.Position.Y - s.h < 0.01 then sp = math.min(sp, ((c - prev[legName].all[ci]) * Vector3.new(1, 0, 1)).Magnitude * 60) end
					end
					if VERBOSE and s.h - Floor < -0.02 then table.insert(out, string.format("  %s f%d %s h %.3f corner %d (was %d, prev h %.3f) speed %.2f", Seq.Name, f, legName, s.h - Floor, s.i, prev[legName].i, prev[legName].h - Floor, sp)) end
					if s.h - Floor < 0.12 then table.insert(speeds, sp) end
				end
			end
			if prev then local j = (S.torso - prev.torso).Magnitude if j > tpop then tpop, tpopAt = j, f / 60 end end
			if #speeds > 0 then local m = math.min(table.unpack(speeds)) table.insert(skates, m) if VERBOSE and m > 0.6 then table.insert(out, string.format("  %s f%d skate %.2f", Seq.Name, f, m)) end end
			prev = S
		end
		Tr:Stop(0) for _, j in ipairs(M:GetDescendants()) do if j:IsA("Motor6D") then j.Transform = CFrame.identity end end
		-- the house physics audit's rule: per second, the mean skate of the slower grounded foot must stay under 0.4
		local buckets, worstBucket = {}, 0
		for k, v in ipairs(skates) do local b = math.floor((k - 1) / 60) buckets[b] = (buckets[b] or 0) + v / 60 end
		for _, v in pairs(buckets) do worstBucket = math.max(worstBucket, v) end
		local mean, worst, over = 0, 0, 0
		for _, s in ipairs(skates) do mean += s worst = math.max(worst, s) if s > 0.6 then over += 1 end end
		mean = if #skates > 0 then mean / #skates else 0
		table.insert(out, string.format("%-14s %s audit %.2f | planted %3d | skate mean %.2f, worst %.2f st/s, over 0.6: %d | deepest %.2f | sole pop %.2f at %.2f | torso pop %.2f at %.2f", Seq.Name, worstBucket < 0.4 and deepest > -0.15 and "PASS" or "FAIL", worstBucket, #skates, mean, worst, over, deepest, pop, popAt, tpop, tpopAt))
	end
end
M:Destroy()
return table.concat(out, "\n")
