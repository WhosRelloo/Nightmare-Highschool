local KSP = game:GetService("KeyframeSequenceProvider")
local rig = workspace["Cape stuff"].R6
local T = rig.Torso
local M = { Root = rig.HumanoidRootPart.RootJoint, Neck = T.Neck, RightShoulder = T["Right Shoulder"], LeftShoulder = T["Left Shoulder"], RightHip = T["Right Hip"], LeftHip = T["Left Hip"] }
local PART = { Root = "Torso", Neck = "Head", RightShoulder = "Right Arm", LeftShoulder = "Left Arm", RightHip = "Right Leg", LeftHip = "Left Leg" }
local ORDER = { "Root", "Neck", "RightShoulder", "LeftShoulder", "RightHip", "LeftHip" }
local function rot(cf) return cf - cf.Position end
local function eul(cf) local x, y, z = cf:ToEulerAnglesXYZ() return string.format("%.1f,%.1f,%.1f", math.deg(x), math.deg(y), math.deg(z)) end
local A = game.ReplicatedStorage.Assets.Animations
local clips = {
	Idle = A.Weapons.Fist.Movement.Idle, M1_1 = A.Weapons.Fist.M1["1"], M1_2 = A.Weapons.Fist.M1["2"], M1_3 = A.Weapons.Fist.M1["3"], M1_4 = A.Weapons.Fist.M1["4"],
	M2 = A.Weapons.Fist.M2, Block = A.Weapons.Fist.Block, RunningM1 = A.Weapons.Fist.RunningM1, Hit1 = A.Default.Hit["1"], Knockback = A.Default.Knockback,
}
local out = {}
for name, anim in clips do
	local ok, ks = pcall(function() return KSP:GetKeyframeSequenceAsync(anim.AnimationId) end)
	if not ok then table.insert(out, "@" .. name .. " FAILED " .. tostring(ks)) continue end
	local kfs = ks:GetKeyframes()
	table.sort(kfs, function(a, b) return a.Time < b.Time end)
	table.insert(out, string.format("@%s %s loop=%s", name, anim.AnimationId, tostring(ks.Loop)))
	for _, kf in kfs do
		local parts = { string.format("%.4f", kf.Time) }
		local names = {}
		if kf.Name ~= "Keyframe" and kf.Name ~= "" then table.insert(names, kf.Name) end
		for _, m in kf:GetChildren() do if m:IsA("KeyframeMarker") then table.insert(names, "M:" .. m.Name) end end
		local styles = {}
		for _, j in ORDER do
			local p = kf:FindFirstChild(PART[j], true)
			if p and p:IsA("Pose") and p.Weight > 0 then
				local m = M[j]
				local c0, c1 = m.C0, m.C1
				if j == "Root" then
					local tc = c0 * p.CFrame * c1:Inverse()
					table.insert(parts, string.format("Root=%.3f,%.3f,%.3f|%s", tc.Position.X, tc.Position.Y, tc.Position.Z, eul(rot(tc))))
				else
					local r = rot(c0) * rot(p.CFrame) * rot(c1):Inverse()
					table.insert(parts, j .. "=" .. eul(r))
					local o = p.CFrame.Position
					if o.Magnitude > 0.0005 then table.insert(parts, string.format("%s_o=%.3f,%.3f,%.3f", j, o.X, o.Y, o.Z)) end
				end
				styles[p.EasingStyle.Name .. "/" .. p.EasingDirection.Name] = true
			end
		end
		local st = {} for s in styles do table.insert(st, s) end
		table.insert(out, table.concat(parts, ";") .. (#names > 0 and ("  #" .. table.concat(names, ",")) or "") .. "  ~" .. table.concat(st, ","))
	end
end
return table.concat(out, "\n")
