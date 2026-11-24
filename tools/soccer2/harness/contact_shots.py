"""Pose a copy of the "Soccer Anims" rig at each Contact time of the baked clips and save a side-on screenshot.
usage: python -X utf8 -I tools/soccer2/harness/contact_shots.py   (Edit mode; the copy and the camera are put back)
Writes docs/superpowers/mockups/2026-11-24-soccer-2-0/contact-<clip>.png."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RBXC = r"E:/Rensei/Rensei-Game-Design/Art/Tools/rbxc.py"
PLACE = "placeId: 98950102230473"
OUT = os.path.join(ROOT, "docs", "superpowers", "mockups", "2026-11-24-soccer-2-0")
SHOT = os.path.join(ROOT, "tools", "admin-console", "shot.py")
TMP = os.path.join(HERE, "_contact.lua")
CLIPS = [("Strike Foward Jog_R6", 0.43), ("KickSoccerball_Right", 0.23), ("Soccer Pass_R6", 0.47), ("Chip_R6", 0.53),
         ("Scissor Kick_R6", 0.68), ("Soccer Penalty Kick_R6", 0.73), ("Soccer Spin_R6", 0.23), ("Soccer Spin_R6", 0.60),
         ("Soccer Tackle_R6", 0.53)]
POSE = r'''local KSP = game:GetService("KeyframeSequenceProvider")
local Src = workspace["Soccer Anims"]
local Old = workspace:FindFirstChild("NHContactRig") if Old then Old:Destroy() end
local Rig = Src:Clone() Rig.Name = "NHContactRig"
for _, D in Rig:GetDescendants() do if D:IsA("Folder") and D.Name == "AnimSaves" then D:Destroy() end end
Rig:PivotTo(Src:GetPivot() * CFrame.new(14, 0, 0)) Rig.Parent = workspace
-- Edit mode does not run an Animator, so lerp the two keyframes around the time and set each Motor6D.Transform by hand
local KS = game.ReplicatedStorage.NHSoccerClips[%s]
local Tt = %f
local Ks = {} for _, K in KS:GetChildren() do if K:IsA("Keyframe") then table.insert(Ks, K) end end
table.sort(Ks, function(a, b) return a.Time < b.Time end)
local Lo, Hi = Ks[1], Ks[#Ks]
for _, K in Ks do if K.Time <= Tt then Lo = K end end
for I = #Ks, 1, -1 do if Ks[I].Time >= Tt then Hi = Ks[I] end end
local u = if Hi.Time > Lo.Time then math.clamp((Tt - Lo.Time) / (Hi.Time - Lo.Time), 0, 1) else 0
local T6 = Rig:FindFirstChild("Torso")
local J = { Torso = Rig.HumanoidRootPart.RootJoint, Head = T6.Neck, ["Left Arm"] = T6["Left Shoulder"], ["Right Arm"] = T6["Right Shoulder"], ["Left Leg"] = T6["Left Hip"], ["Right Leg"] = T6["Right Hip"] }
local function pose(K, N) for _, P in K:GetDescendants() do if P:IsA("Pose") and P.Name == N then return P end end end
for N, M in J do
	local A, B = pose(Lo, N), pose(Hi, N)
	if A and B then M.Transform = A.CFrame:Lerp(B.CFrame, u) elseif A or B then M.Transform = (A or B).CFrame end
end
-- a Transform alone does not move the parts in Edit mode (and moving one part drags the whole assembly), so cut the joints,
-- anchor the parts and place each one from its joint: Part0 * C0 * Transform * C1^-1
local HRP = Rig.HumanoidRootPart
local Rows = {}
for N, M in J do table.insert(Rows, { N = N, P0 = M.Part0, P1 = M.Part1, C0 = M.C0, C1 = M.C1, T = M.Transform }) end
for _, M in J do M:Destroy() end
for _, D in Rig:GetDescendants() do if D:IsA("BasePart") then D.Anchored = true end end
local Base = HRP.CFrame
local Place = {}
for _, R in Rows do if R.N == "Torso" then R.P1.CFrame = Base * R.C0 * R.T * R.C1:Inverse() end end
for _, R in Rows do if R.N ~= "Torso" then R.P1.CFrame = R.P0.CFrame * R.C0 * R.T * R.C1:Inverse() end end
local Cam = workspace.CurrentCamera
if workspace:GetAttribute("NHCamBefore") == nil then workspace:SetAttribute("NHCamBefore", Cam.CFrame) end
local P = Rig.HumanoidRootPart.Position
Cam.CFrame = CFrame.lookAt(P + Rig.HumanoidRootPart.CFrame.RightVector * 9 + Vector3.new(0, -0.5, 0), P + Vector3.new(0, -1.5, 0))
return "PASS posed"'''
CLEAN = r'''local R = workspace:FindFirstChild("NHContactRig") if R then R:Destroy() end
local C = workspace:GetAttribute("NHCamBefore") if C then workspace.CurrentCamera.CFrame = C workspace:SetAttribute("NHCamBefore", nil) end
return "PASS cleaned"'''
def run(lua):
    open(TMP, "w", encoding="utf-8").write(lua)
    r = subprocess.run([sys.executable, "-X", "utf8", "-I", RBXC, "luau", PLACE, "Edit", "@" + TMP], capture_output=True, text=True, encoding="utf-8")
    return (r.stdout or r.stderr).strip()
os.makedirs(OUT, exist_ok=True)
try:
    for name, t in CLIPS:
        print(name, t, run(POSE % ('"' + name + '"', t)))
        slug = name.replace(" ", "_") + "-" + str(int(round(t * 100)))
        subprocess.run([sys.executable, "-X", "utf8", "-I", SHOT, os.path.join(OUT, "contact-" + slug + ".png")])
finally:
    print(run(CLEAN))
