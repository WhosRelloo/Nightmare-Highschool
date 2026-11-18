--!nonstrict
-- Foot-lock bake (2.26.0). Run in Edit after the out/*.lua builders.
-- The non-bending R6 leg is rigid, so a planted foot can stay put only if the hip-to-contact distance stays fixed.
-- For each clip in ReplicatedStorage.NHCineClips.Animations this samples the built clip at 60 fps on a standard
-- R6 rig (2-stud legs), finds where each foot touches the floor, pins that contact point in the world, and solves:
--   * the root height, so a pinned leg exactly reaches its contact (with two pinned legs the higher need wins and the
--     other foot hovers over its pin, never sliding);
--   * each pinned leg's swing (the shortest rotation onto the pin, so its twist is kept);
--   * no sole below the floor on the free leg.
-- Pins ease out over 5 frames. The clip is rebuilt as 60 fps Linear keys with the same markers, loop and priority.
-- Set ONLY = { Name = true } to bake some clips.
local ONLY = __ONLY__
local DEBUG = __DEBUG__
local dbg = {}
local FPS, PLANT_H, MIN_FRAMES, EASE_OUT, ITER, REACH = 60, 0.15, 3, 5, 4, 0.97
local MAXDY, STEP, STEP_LIFT = 0.3, 8, 0.3
-- clips whose source moves a planted foot (a slide the rigid leg cannot hold): those feet step instead
local STEPS = { StrikeTug = true }
-- clips where the body falls over a planted foot: the hip swings around the foot instead of being held up
local FALL = {} -- tried on StrikeShatter (2026-11-17): the swing-out release popped the root 2 studs; off

local Folder = game.ReplicatedStorage.NHCineClips.Animations
local M = game.ServerScriptService.Services.AI.AI.Rig:Clone()
for _, d in ipairs(M:GetDescendants()) do if d:IsA("Script") or d:IsA("LocalScript") then d:Destroy() end end
M:PivotTo(CFrame.new(0, 300, 0))
M.Parent = workspace
M:ScaleTo(M:GetScale() * (2 / M["Left Leg"].Size.Y))
M.HumanoidRootPart.Anchored = true
local An = M.Humanoid:FindFirstChildOfClass("Animator") or Instance.new("Animator", M.Humanoid)
local Torso = M.Torso
local RJ = M.HumanoidRootPart.RootJoint
local Motors = {}
for _, m in ipairs(M:GetDescendants()) do if m:IsA("Motor6D") and m.Part1 then Motors[m.Part1.Name] = m end end
local LEGS = { "Left Leg", "Right Leg" }
local Hip = { ["Left Leg"] = Motors["Left Leg"], ["Right Leg"] = Motors["Right Leg"] }
local PARENT = { Torso = "HumanoidRootPart" }
for name, m in pairs(Motors) do if name ~= "Torso" then PARENT[name] = m.Part0.Name end end

local function corners(legName)
	local s = M[legName].Size / 2
	local c = {}
	for _, x in ipairs({ -1, 1 }) do for _, z in ipairs({ -1, 1 }) do table.insert(c, Vector3.new(x * s.X, -s.Y, z * s.Z)) end end
	return c
end
local CORNERS = { ["Left Leg"] = corners("Left Leg"), ["Right Leg"] = corners("Right Leg") }

-- world (root = identity) frames from transforms
local function torsoCF(rjT) return RJ.C0 * rjT * RJ.C1:Inverse() end
local function legCF(tor, legName, hT) local H = Hip[legName] return tor * H.C0 * hT * H.C1:Inverse() end
local function lowest(cf, legName)
	local lo, li = math.huge, 1
	for i, c in ipairs(CORNERS[legName]) do local y = (cf * c).Y if y < lo then lo, li = y, i end end
	return lo, li
end
local function rotBetween(a, b)
	a, b = a.Unit, b.Unit
	local ax = a:Cross(b)
	if ax.Magnitude < 1e-7 then return CFrame.identity end
	return CFrame.fromAxisAngle(ax.Unit, math.acos(math.clamp(a:Dot(b), -1, 1)))
end
-- the hip transform that puts the leg's local point `lp` on world point `target` (only the swing changes)
local function aimLeg(tor, legName, hT, lp, target)
	local H = Hip[legName]
	local cf = legCF(tor, legName, hT)
	local J = (tor * H.C0).Position
	local R = cf.Rotation
	local v = R * (lp - H.C1.Position)
	local Rn = rotBetween(v, target - J) * R
	local newLeg = CFrame.new(J - Rn * H.C1.Position) * Rn
	local t = (tor * H.C0):Inverse() * newLeg * H.C1
	return t.Rotation
end

local restFloor = lowest(legCF(torsoCF(CFrame.identity), "Left Leg", CFrame.identity), "Left Leg")
local report = { string.format("rig leg %s; floor %.2f below root", tostring(M["Left Leg"].Size), restFloor) }

for _, Seq in ipairs(Folder:GetChildren()) do
	if not Seq:IsA("KeyframeSequence") or (ONLY and not ONLY[Seq.Name]) then continue end
	local A = Instance.new("Animation")
	A.AnimationId = Seq:GetAttribute("PreviewId") or ""
	local Tr = An:LoadAnimation(A)
	Tr:Play(0) Tr:AdjustSpeed(0)
	local t0 = os.clock()
	while Tr.Length <= 0 and os.clock() - t0 < 3 do task.wait() end
	local length = Tr.Length
	-- sample times: the 60 fps grid plus marker and named-key times
	local extra = {}
	for _, kf in ipairs(Seq:GetKeyframes()) do
		local marks = kf:GetMarkers()
		if #marks > 0 or kf.Name ~= "Keyframe" then table.insert(extra, { t = kf.Time, kf = kf }) end
	end
	local times = {}
	for f = 0, math.floor(length * FPS + 1e-6) do table.insert(times, f / FPS) end
	if times[#times] < length - 1e-4 then table.insert(times, length) end
	for _, e in ipairs(extra) do
		local dup = false
		for _, t in ipairs(times) do if math.abs(t - e.t) < 1e-4 then dup = true break end end
		if not dup then table.insert(times, e.t) end
	end
	table.sort(times)
	local S = {}
	for i, t in ipairs(times) do
		Tr.TimePosition = math.min(t, length - 1e-3)
		An:StepAnimations(0)
		local fr = {}
		for name, m in pairs(Motors) do fr[name] = m.Transform end
		S[i] = fr
	end
	Tr:Stop(0)
	for _, m in pairs(Motors) do m.Transform = CFrame.identity end

	local pins, maxDy, lastIter = 0, 0, false
	local stepping = STEPS[Seq.Name]
	local function solve(S)
	-- 1. pins: runs of frames with the sole within PLANT_H of the floor
	local pinAt = { ["Left Leg"] = {}, ["Right Leg"] = {} } -- frame -> { lp, W, w, ease }
	pins = 0
	for _, legName in ipairs(LEGS) do
		local i = 1
		while i <= #S do
			local lo = lowest(legCF(torsoCF(S[i].Torso), legName, S[i][legName]), legName)
			if lo - restFloor < PLANT_H then
				local j = i
				while j + 1 <= #S and lowest(legCF(torsoCF(S[j + 1].Torso), legName, S[j + 1][legName]), legName) - restFloor < PLANT_H do j += 1 end
				if j - i + 1 >= MIN_FRAMES then
					-- the contact point: the corner lowest where the foot comes down, pinned there, on the floor
					local cf = legCF(torsoCF(S[i].Torso), legName, S[i][legName])
					local _, ci = lowest(cf, legName)
					local lp = CORNERS[legName][ci]
					local function contact(k)
						local W = legCF(torsoCF(S[k].Torso), legName, S[k][legName]) * lp
						return Vector3.new(W.X, restFloor, W.Z)
					end
					-- the root shift this pin alone would need at frame k; past MAXDY (or out of reach) the source
					-- means the foot to move, so it steps: lifts, travels and plants again
					local function need(k, W)
						local H = Hip[legName]
						local L = (lp - H.C1.Position).Magnitude
						local J = (torsoCF(S[k].Torso) * H.C0).Position
						local hz = ((W - J) * Vector3.new(1, 0, 1)).Magnitude
						if hz > REACH * L then return math.huge end
						return W.Y + math.sqrt(L * L - hz * hz) - J.Y
					end
					local k, W = i, contact(i)
					pins += 1
					local id = pins
					while k <= j do
						if stepping and k > i and math.abs(need(k, W)) > MAXDY and j - k + 1 > STEP then
							local W2 = contact(k + STEP)
							for q = 0, STEP - 1 do pinAt[legName][k + q] = { lp = lp, from = W, to = W2, s = (q + 1) / (STEP + 1), step = true } end
							k += STEP
							W = W2
							pins += 1
							id = pins
						else
							pinAt[legName][k] = { lp = lp, W = W, w = 1, id = id }
							k += 1
						end
					end
					for q = 1, EASE_OUT do
						if j + q <= #S and not pinAt[legName][j + q] then pinAt[legName][j + q] = { lp = lp, W = W, w = 1 - q / (EASE_OUT + 1), ease = true } end
					end
				end
				i = j + 1
			else
				i += 1
			end
		end
	end

	-- 2. solve each frame
	local out, prevLeg, heldDy, heldShift = {}, {}, {}, {}
	for i, fr in ipairs(S) do
		local tor = torsoCF(fr.Torso)
		-- a planted foot is never left behind: if the hip runs out of reach of its pin, the root is held back
		for _ = 1, 2 do
			for _, legName in ipairs(LEGS) do
				local p = pinAt[legName][i]
				if p and not p.ease and not p.step then
					local H = Hip[legName]
					local L = (p.lp - H.C1.Position).Magnitude
					local J = (tor * H.C0).Position
					local d = (p.W - J) * Vector3.new(1, 0, 1)
					local maxH = REACH * math.sqrt(math.max(L * L - 0.05, 0))
					if d.Magnitude > maxH then tor = CFrame.new(d.Unit * (d.Magnitude - maxH)) * tor end
				end
			end
		end
		-- a falling body (FALL clips) keeps its height and swings back around the planted foot, like a felled tree:
		-- the hip stays one leg length from the pin; the release eases that swing out again
		if FALL[Seq.Name] then
			for _, legName in ipairs(LEGS) do
				local p = pinAt[legName][i]
				local H = Hip[legName]
				if p and not p.ease and not p.step then
					local L = (p.lp - H.C1.Position).Magnitude
					local J = (tor * H.C0).Position
					local v = J.Y - p.W.Y
					local d = (J - p.W) * Vector3.new(1, 0, 1)
					local hzNeed = math.sqrt(math.max(L * L - math.max(v, 0) ^ 2, 0))
					local shift = Vector3.zero
					if d.Magnitude < hzNeed then
						local dir = if d.Magnitude > 1e-3 then d.Unit else -(tor.LookVector * Vector3.new(1, 0, 1)).Unit
						shift = dir * (hzNeed - d.Magnitude)
					end
					heldShift[legName] = shift
					tor = CFrame.new(shift) * tor
				elseif p and p.ease and heldShift[legName] then
					tor = CFrame.new(heldShift[legName] * p.w) * tor
				elseif not p then
					heldShift[legName] = nil
				end
			end
		end
		local dy = -math.huge
		for _, legName in ipairs(LEGS) do
			local p = pinAt[legName][i]
			local H = Hip[legName]
			local J = (tor * H.C0).Position
			if p and not p.ease and not p.step then
				local L = (p.lp - H.C1.Position).Magnitude
				local d = (p.W - J) * Vector3.new(1, 0, 1)
				local horiz = math.min(d.Magnitude, L - 1e-3)
				dy = math.max(dy, p.W.Y + math.sqrt(L * L - horiz * horiz) - J.Y)
			end
		end
		-- a released pin lets the root back down over its ease frames (from the height it last held), not in one frame
		for _, legName in ipairs(LEGS) do
			local p = pinAt[legName][i]
			if p and p.ease and heldDy[legName] then
				local nd = heldDy[legName] * p.w
				dy = if dy == -math.huge then nd else math.max(dy, nd)
			end
		end
		-- a free leg never goes below the floor: the root rises for it, and a pinned foot then hovers over its pin
		-- (its xz held) rather than the free foot scraping along the floor
		if dy == -math.huge then dy = 0 end
		for _, legName in ipairs(LEGS) do
			local p = pinAt[legName][i]
			if not p or p.ease or p.step then
				local lo = lowest(legCF(tor, legName, fr[legName]), legName)
				if lo + dy < restFloor then dy = restFloor - lo end
			end
		end
		local tor2 = CFrame.new(0, dy, 0) * tor
		local nf = table.clone(fr)
		nf.Torso = RJ.C0:Inverse() * tor2 * RJ.C1
		for _, legName in ipairs(LEGS) do
			local p = pinAt[legName][i]
			local H = Hip[legName]
			local J = (tor2 * H.C0).Position
			local target
			if p and p.step then
				-- a step: the foot travels from pin to pin on a low arc
				local s = p.s
				local e = s * s * (3 - 2 * s)
				target = p.from:Lerp(p.to, e) + Vector3.new(0, STEP_LIFT * math.sin(math.pi * s), 0)
				nf[legName] = aimLeg(tor2, legName, fr[legName], p.lp, target)
				p = nil
			elseif p then
				local L = (p.lp - H.C1.Position).Magnitude
				local d = (p.W - J) * Vector3.new(1, 0, 1)
				local horiz = math.min(d.Magnitude, L - 1e-3)
				-- the pin, or the point over it the leg reaches when the other leg sets the height
				local Wy = math.max(p.W.Y, J.Y - math.sqrt(L * L - horiz * horiz))
				target = Vector3.new(p.W.X, Wy, p.W.Z)
				local locked = aimLeg(tor2, legName, fr[legName], p.lp, target)
				local pl = prevLeg[legName]
				if not p.ease and pl and pl.id == p.id then
					-- while pinned, carry the leg on from its last frame by the smallest swing (no twist on the floor)
					local R0 = pl.cf.Rotation
					local Rn = rotBetween(R0 * (p.lp - H.C1.Position), target - J) * R0
					locked = ((tor2 * H.C0):Inverse() * (CFrame.new(J - Rn * H.C1.Position) * Rn) * H.C1).Rotation
				end
				nf[legName] = if p.ease then fr[legName]:Lerp(locked, p.w) else locked
			end
			for _ = 1, 3 do
				local cf = legCF(tor2, legName, nf[legName])
				local lo, ci = lowest(cf, legName)
				if lo >= restFloor - 2e-3 then break end
				if p and not p.ease then
					-- roll the pinned leg about the hip-to-pin line (the hip and the pin stay put): of the rolls that keep
					-- every corner on or above the floor, take the one nearest the previous frame's leg, so it never flips
					local axis = (target - J).Unit
					local prevCF = prevLeg[legName] and prevLeg[legName].id == p.id and prevLeg[legName].cf or cf
					local best, bestCost, bestLo, bestCf = nil, math.huge, -math.huge, cf
					for a = -60, 60 do
						local r = CFrame.new(J) * CFrame.fromAxisAngle(axis, math.rad(a)) * CFrame.new(-J)
						local c = r * cf
						local l2 = lowest(c, legName)
						local _, ang = (prevCF.Rotation:Inverse() * c.Rotation):ToAxisAngle()
						if l2 >= restFloor - 2e-3 then
							if math.abs(ang) < bestCost then best, bestCost, bestCf = a, math.abs(ang), c end
						elseif not best and l2 > bestLo then
							bestLo, bestCf = l2, c
						end
					end
					nf[legName] = ((tor2 * H.C0):Inverse() * bestCf * H.C1).Rotation
					break
				end
				-- a free (or easing) leg: swing the lowest corner up to the floor, keeping the leg's length
				local lp = CORNERS[legName][ci]
				local P = cf * lp
				local L = (lp - H.C1.Position).Magnitude
				local h = J.Y - restFloor
				if h >= L then break end
				local dxz = (P - J) * Vector3.new(1, 0, 1)
				if dxz.Magnitude < 0.05 then dxz = (cf.LookVector * Vector3.new(1, 0, 1)) end
				nf[legName] = aimLeg(tor2, legName, nf[legName], lp, Vector3.new(J.X, restFloor + 1e-3, J.Z) + dxz.Unit * math.sqrt(L * L - h * h))
			end
		end
		for _, legName in ipairs(LEGS) do
			local p = pinAt[legName][i]
			prevLeg[legName] = { id = p and not p.ease and p.id, cf = legCF(tor2, legName, nf[legName]) }
			if p and not p.ease and not p.step then heldDy[legName] = dy elseif not p then heldDy[legName] = nil end
		end
		maxDy = math.max(maxDy, math.abs(dy))
		out[i] = nf
		if DEBUG and lastIter and DEBUG[Seq.Name] and i >= DEBUG[Seq.Name][1] and i <= DEBUG[Seq.Name][2] then
			local bits = {}
			for _, legName in ipairs(LEGS) do
				local p = pinAt[legName][i]
				local lo = lowest(legCF(tor2, legName, nf[legName]), legName)
				local J = (tor2 * Hip[legName].C0).Position
				table.insert(bits, string.format("%s %s h %.3f%s", legName:sub(1, 1), p and (p.step and "step" or p.ease and "ease" or ("pin" .. tostring(p.id))) or "free", lo - restFloor, p and p.W and string.format(" hz %.2f", ((p.W - J) * Vector3.new(1, 0, 1)).Magnitude) or ""))
			end
			table.insert(dbg, string.format("f%d dy %.2f | %s", i - 1, dy, table.concat(bits, " | ")))
		end
	end
	return out
	end
	-- iterate: a foot the new root height brings down to the floor gets its own pin on the next pass
	local out = S
	local iters = if FALL[Seq.Name] then 1 else ITER
	for it = 1, iters do lastIter = it == iters out = solve(out) end

	-- 3. rebuild the sequence
	local new = Instance.new("KeyframeSequence")
	new.Name, new.Loop, new.Priority = Seq.Name, Seq.Loop, Seq.Priority
	for k, v in pairs(Seq:GetAttributes()) do new:SetAttribute(k, v) end
	for i, t in ipairs(times) do
		local kf = Instance.new("Keyframe")
		kf.Time = t
		local poses = {}
		local function ensure(part)
			if poses[part] then return poses[part] end
			local p = Instance.new("Pose")
			p.Name = part
			p.EasingStyle = Enum.PoseEasingStyle.Linear
			p.Weight = if part == "HumanoidRootPart" then 0 else 1
			poses[part] = p
			local par = PARENT[part]
			p.Parent = if par then ensure(par) else kf
			return p
		end
		for name, cf in pairs(out[i]) do ensure(name).CFrame = cf end
		for _, e in ipairs(extra) do
			if math.abs(e.t - t) < 1e-4 then
				kf.Name = e.kf.Name
				for _, mk in ipairs(e.kf:GetMarkers()) do mk:Clone().Parent = kf end
			end
		end
		kf.Parent = new
	end
	Seq:Destroy()
	new.Parent = Folder
	local ok, id = pcall(function() return game:GetService("AnimationClipProvider"):RegisterAnimationClip(new) end)
	new:SetAttribute("PreviewId", ok and tostring(id) or nil)
	table.insert(report, string.format("%-14s %d keys, %d pins, max root shift %.2f", new.Name, #times, pins, maxDy))
end
M:Destroy()
return table.concat(report, "\n") .. "\n" .. table.concat(dbg, "\n")
