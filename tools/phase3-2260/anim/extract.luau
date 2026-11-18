-- Measure cutscene source clips by forward kinematics on their own rigs. Edit mode, read only.
local SOURCES = {
	{ Name = "GhoulEmerge"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Emerge end };
	{ Name = "GhoulGrab"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Grab end };
	{ Name = "GhoulAttack1"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Attack1 end };
	{ Name = "GhoulStun1"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Stun1 end };
	{ Name = "GhoulDeath"; Rig = "R15"; Seq = function() return game.ServerStorage.NHBeasts.Clips.GraveGhoul.Death end };
	{ Name = "StalkerReach"; Rig = "R15S"; Seq = function() return game.ServerStorage.NHBeasts.Clips.NightStalker.Reach end };
	{ Name = "FistClinch"; Rig = "R6"; Id = "rbxassetid://105787080820844" };
	{ Name = "FistClinchVictim"; Rig = "R6"; Id = "rbxassetid://127085112840973" };
	{ Name = "FistM2"; Rig = "R6"; Id = "rbxassetid://80262616372750" };
	{ Name = "FistBodyBlow"; Rig = "R6"; Id = "rbxassetid://115837677569118" };
	{ Name = "Uptilt"; Rig = "R6"; Id = "rbxassetid://102341195576821" };
	{ Name = "Knockback"; Rig = "R6"; Id = "rbxassetid://138802633910747" };
}
local H = game:GetService("HttpService")
local KSP = game:GetService("KeyframeSequenceProvider")
local RIGS = { R15 = game.ServerStorage.NHBeasts.GraveGhoul; R15S = game.ServerStorage.NHBeasts.NightStalker; R6 = game.ServerScriptService.Services.AI.AI.Rig }

-- joints by Part1 name: Motor6D (C0 / C1) or AnimationConstraint (its attachments' CFrames), the same FK either way
local function motors(rig)
	local L = {}
	for _, D in rig:GetDescendants() do
		if D:IsA("Motor6D") and D.Part0 and D.Part1 then
			L[D.Part1.Name] = { Part0 = D.Part0; Part1 = D.Part1; C0 = D.C0; C1 = D.C1 }
		elseif D:IsA("AnimationConstraint") and D.Attachment0 and D.Attachment1 then
			local A0, A1 = D.Attachment0, D.Attachment1
			L[A1.Parent.Name] = { Part0 = A0.Parent; Part1 = A1.Parent; C0 = A0.CFrame; C1 = A1.CFrame }
		end
	end
	return L
end

-- every Pose in a keyframe, by part name (the Pose's Name is its Part1); missing poses keep the previous key's
local function posesOf(kf, last)
	local P = table.clone(last or {})
	-- a Pose with Weight 0 is a hierarchy placeholder ("not keyed here"), not an identity pose: keep the previous key's
	for _, D in kf:GetDescendants() do if D:IsA("Pose") and D.Weight > 0 then P[D.Name] = D.CFrame end end
	return P
end

local function fk(rig, M, Poses)
	local Root = rig:FindFirstChild("HumanoidRootPart")
	local W = { [Root.Name] = CFrame.identity }
	local function world(Part)
		if W[Part.Name] then return W[Part.Name] end
		local Mo = M[Part.Name]
		if not Mo then W[Part.Name] = Root.CFrame:ToObjectSpace(Part.CFrame) return W[Part.Name] end
		local P0 = world(Mo.Part0)
		W[Part.Name] = P0 * Mo.C0 * (Poses[Part.Name] or CFrame.identity) * Mo.C1:Inverse()
		return W[Part.Name]
	end
	for Name in M do world(rig:FindFirstChild(Name, true)) end
	return W
end

-- the animation tool applies `rotation` as CFrame.Angles does (XYZ), so measure in the same order
local function euler(cf)
	local x, y, z = cf:ToEulerAnglesXYZ()
	return { pitch = math.deg(x); yaw = math.deg(y); roll = math.deg(z) }
end

local function aim(TorsoCF, A, B)
	local d = TorsoCF:VectorToObjectSpace((B - A).Unit)
	return { x = d.X; y = d.Y; z = -d.Z } -- the tool's forward is the torso's look (-Z)
end

local function measure(rigKind, seq)
	local rig = RIGS[rigKind]
	local M = motors(rig)
	local R6 = rigKind == "R6"
	local kfs = seq:GetKeyframes()
	table.sort(kfs, function(a, b) return a.Time < b.Time end)
	local keys, last = {}, nil
	-- a baked clip (over 40 keys) keeps every second key: the converter thins to key poses anyway, and the bridge caps output
	local Step = if #kfs > 40 then 2 else 1
	for I, kf in kfs do
		last = posesOf(kf, last)
		if Step > 1 and I % Step == 0 and I ~= #kfs then continue end
		local W = fk(rig, M, last)
		local Torso = W[if R6 then "Torso" else "UpperTorso"]
		local Head = W.Head
		local function at(part, off) return (W[part] * CFrame.new(off)).Position end
		local aims
		if R6 then
			aims = {
				LeftShoulder = aim(Torso, at("Left Arm", Vector3.new(0, 1, 0)), at("Left Arm", Vector3.new(0, -1, 0)));
				RightShoulder = aim(Torso, at("Right Arm", Vector3.new(0, 1, 0)), at("Right Arm", Vector3.new(0, -1, 0)));
				LeftHip = aim(Torso, at("Left Leg", Vector3.new(0, 1, 0)), at("Left Leg", Vector3.new(0, -1, 0)));
				RightHip = aim(Torso, at("Right Leg", Vector3.new(0, 1, 0)), at("Right Leg", Vector3.new(0, -1, 0)));
			}
		else
			aims = {
				LeftShoulder = aim(Torso, W.LeftUpperArm.Position, W.LeftHand.Position);
				RightShoulder = aim(Torso, W.RightUpperArm.Position, W.RightHand.Position);
				LeftHip = aim(Torso, W.LeftUpperLeg.Position, W.LeftFoot.Position);
				RightHip = aim(Torso, W.RightUpperLeg.Position, W.RightFoot.Position);
			}
		end
		local function front(part)
			local d = Torso:VectorToObjectSpace(W[part].LookVector)
			return { x = d.X; y = d.Y; z = -d.Z }
		end
		local fronts = if R6 then { LeftShoulder = front("Left Arm"); RightShoulder = front("Right Arm"); LeftHip = front("Left Leg"); RightHip = front("Right Leg") }
			else { LeftShoulder = front("LeftUpperArm"); RightShoulder = front("RightUpperArm"); LeftHip = front("LeftUpperLeg"); RightHip = front("RightUpperLeg") }
		local lowest = math.huge
		for _, part in (if R6 then { "Left Leg", "Right Leg" } else { "LeftFoot", "RightFoot" }) do
			lowest = math.min(lowest, (W[part] * CFrame.new(0, if R6 then -1 else -0.2, 0)).Position.Y)
		end
		table.insert(keys, { t = kf.Time; root = { x = Torso.Position.X; y = Torso.Position.Y; z = Torso.Position.Z };
			torso = euler(Torso - Torso.Position); neck = euler((Torso:ToObjectSpace(Head)) - (Torso:ToObjectSpace(Head)).Position);
			aims = aims; fronts = fronts; footY = lowest })
	end
	return { rig = rigKind; length = kfs[#kfs].Time; keys = keys }
end

local ONLY = "__ONLY__"
local Out = {}
for _, S in SOURCES do
	if ONLY ~= "" and S.Name ~= ONLY then continue end
	local ok, seq = pcall(function() return if S.Seq then S.Seq() else KSP:GetKeyframeSequenceAsync(S.Id) end)
	if ok and seq then
		local ok2, m = pcall(measure, S.Rig, seq)
		Out[S.Name] = if ok2 then m else { error = tostring(m) }
	else
		Out[S.Name] = { error = "could not load " .. tostring(S.Id or "seq") }
	end
end
local function round(v)
	if typeof(v) == "number" then return math.floor(v * 100 + 0.5) / 100 end
	if typeof(v) == "table" then local T = {} for K, X in v do T[K] = round(X) end return T end
	return v
end
return H:JSONEncode(round(Out))
