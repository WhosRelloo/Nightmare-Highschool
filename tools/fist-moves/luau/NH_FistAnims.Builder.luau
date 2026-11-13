-- NH fist moves (2.12.0), Studio-only tool: builds the fist move KeyframeSequences from tools/fist-moves (pack.py format)
-- into ServerStorage.NH_FistAnims for the owner to publish. Nothing in the game requires this module.
-- Same as NH_GripAnims.Builder, except a marker named Hit or EndLag also names its keyframe: the game reads those with
-- GetTimeOfKeyframe / KeyframeReached (ServerStorage.Packages.AnimMarkers).
local M = {}
local ROOT = "HumanoidRootPart"
local NAME = { T = "Torso", H = "Head", LA = "Left Arm", RA = "Right Arm", LL = "Left Leg", RL = "Right Leg" }
local PARENT = { Torso = ROOT, Head = "Torso", ["Left Arm"] = "Torso", ["Right Arm"] = "Torso", ["Left Leg"] = "Torso", ["Right Leg"] = "Torso" }
local NAMED = { Hit = true, EndLag = true }

function M.BuildPacked(name, DATA, MARKERS, priority)
	local seq = Instance.new("KeyframeSequence")
	seq.Name = name
	seq.Loop = false
	seq.Priority = Enum.AnimationPriority[priority or "Action4"]
	local idx = 0
	for line in string.gmatch(DATA, "[^\n]+") do
		idx += 1
		local t, rest = string.match(line, "^(%-?%d+)|?(.*)$")
		local kf = Instance.new("Keyframe")
		kf.Time = tonumber(t) / 1000
		local poses = {}
		local function ensure(part)
			local p = poses[part]
			if p then return p end
			p = Instance.new("Pose")
			p.Name = part
			p.Weight = 0
			p.EasingStyle = Enum.PoseEasingStyle.Linear
			poses[part] = p
			local par = PARENT[part]
			p.Parent = if par then ensure(par) else kf
			return p
		end
		ensure(ROOT)
		for code, vals in string.gmatch(rest, "(%a+):([^;]+)") do
			local n = {}
			for v in string.gmatch(vals, "[^,]+") do table.insert(n, tonumber(v) / 1000) end
			local m = math.sqrt(n[1] ^ 2 + n[2] ^ 2 + n[3] ^ 2 + n[4] ^ 2)
			local p = ensure(NAME[code])
			p.Weight = 1
			p.CFrame = CFrame.new(n[5] or 0, n[6] or 0, n[7] or 0, n[1] / m, n[2] / m, n[3] / m, n[4] / m)
		end
		for _, mk in (MARKERS and MARKERS[idx]) or {} do
			local k = Instance.new("KeyframeMarker")
			k.Name = mk[1]
			k.Value = mk[2] or ""
			k.Parent = kf
			if NAMED[mk[1]] then kf.Name = mk[1] end
		end
		kf.Parent = seq
	end
	local old = script.Parent:FindFirstChild(name)
	if old then old:Destroy() end
	seq.Parent = script.Parent
	local ok, id = pcall(function() return game:GetService("KeyframeSequenceProvider"):RegisterKeyframeSequence(seq) end)
	seq:SetAttribute("PreviewId", ok and tostring(id) or nil)
	local kfs = seq:GetKeyframes()
	local named = {}
	for _, k in kfs do if k.Name ~= "Keyframe" then table.insert(named, string.format("%s@%.3f", k.Name, k.Time)) end end
	return string.format("built %s: %d keys, %.2f s, %s, preview %s", name, #kfs, kfs[#kfs].Time, table.concat(named, " "), tostring(ok and id or id))
end
return M
