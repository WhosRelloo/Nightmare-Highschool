"""Seam check: each part's position (HRP space) at the end of one clip vs the start of the next, on stage rig R1.
usage: python seam.py   (pairs below)"""
import sys, json
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from dump import run

M1 = "ReplicatedStorage.Assets.Animations.Weapons.Fist."
PAIRS = [  # (label, srcA, tA, srcB, tB)
    ("M1.1@0.45 -> Shove@0", M1 + "M1.1", 0.45, "ks:ServerStorage.NH_FistAnims.FistShove", 0.0),
    ("Shove@end -> Idle@0", "ks:ServerStorage.NH_FistAnims.FistShove", 9, M1 + "Movement.Idle", 0.0),
    ("M1.3@0.40 -> BodyBlow@0", M1 + "M1.3", 0.40, "ks:ServerStorage.NH_FistAnims.FistBodyBlow", 0.0),
    ("BodyBlow@end -> Idle@0", "ks:ServerStorage.NH_FistAnims.FistBodyBlow", 9, M1 + "Movement.Idle", 0.0),
    ("Block@0 -> Clinch@0", M1 + "Block", 0.0, "ks:ServerStorage.NH_FistAnims.FistClinch", 0.0),
    ("Clinch@end -> Idle@0", "ks:ServerStorage.NH_FistAnims.FistClinch", 9, M1 + "Movement.Idle", 0.0),
    ("Idle@0 -> ClinchVictim@0", M1 + "Movement.Idle", 0.0, "ks:ServerStorage.NH_FistAnims.FistClinchVictim", 0.0),
    ("ClinchVictim@end -> Idle@0", "ks:ServerStorage.NH_FistAnims.FistClinchVictim", 9, M1 + "Movement.Idle", 0.0),
]
lua = """
local r = workspace.NHAnimStage.R1
local an = r.Humanoid.Animator
local function idOf(src)
	local path = src:sub(1, 3) == "ks:" and src:sub(4) or src
	local i = game
	for seg in string.gmatch(path, "[^%.]+") do i = i:FindFirstChild(seg) or game:GetService(seg) end
	if src:sub(1, 3) == "ks:" then return i:GetAttribute("PreviewId") end
	return i.AnimationId
end
local function sample(src, t)
	for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) tr:Destroy() end
	for _, m in r:GetDescendants() do if m:IsA("Motor6D") then m.Transform = CFrame.identity end end
	local a = Instance.new("Animation") a.AnimationId = idOf(src)
	local tr = an:LoadAnimation(a)
	tr:Play(0) tr:AdjustSpeed(0)
	local w = 0 while tr.Length == 0 and w < 40 do task.wait(0.05) w += 1 end
	tr.TimePosition = math.min(t, tr.Length - 1e-3)
	an:StepAnimations(0)
	local hrp = r.HumanoidRootPart
	local o = {}
	for _, n in {"Torso", "Head", "Right Arm", "Left Arm", "Right Leg", "Left Leg"} do
		local cf = hrp.CFrame:ToObjectSpace(r[n].CFrame)
		local rx, ry, rz = cf:ToOrientation()
		o[n] = {cf.Position, Vector3.new(rx, ry, rz)}
	end
	tr:Stop(0) tr:Destroy()
	return o
end
local out = {}
for _, p in PAIRS do
	local a, b = sample(p[2], p[3]), sample(p[4], p[5])
	local worst, wn, rot = 0, "", 0
	for n, va in a do
		local d = (va[1] - b[n][1]).Magnitude
		if d > worst then worst, wn = d, n end
		local cfa = CFrame.fromOrientation(va[2].X, va[2].Y, va[2].Z)
		local cfb = CFrame.fromOrientation(b[n][2].X, b[n][2].Y, b[n][2].Z)
		local _, ang = (cfa:Inverse() * cfb):ToAxisAngle()
		rot = math.max(rot, math.deg(math.abs(ang)))
	end
	table.insert(out, string.format("%-28s pos %.3f (%s)  rot %.1f deg", p[1], worst, wn, rot))
end
return table.concat(out, "\\n")
"""
pairs = "local PAIRS = {" + ",".join("{%s,%s,%s,%s,%s}" % (json.dumps(l), json.dumps(a), ta, json.dumps(b), tb)
                                     for l, a, ta, b, tb in PAIRS) + "}\n"
o, e = run("Edit", pairs + lua)
try:
    o = json.loads(o)
except Exception:
    pass
print(o, e[:300])
