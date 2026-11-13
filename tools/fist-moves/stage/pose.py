"""Pose the stage's 6 rigs at times of a clip (anim id, or a KeyframeSequence path's PreviewId) and aim the camera.
usage: python pose.py <animId|ks:Path> t1 t2 ... [--view side|front|34] [--speed s]"""
import sys, json
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from dump import run
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opts = dict(a[2:].split("=") for a in sys.argv[1:] if a.startswith("--") and "=" in a)
src, times = args[0], [float(t) for t in args[1:]]
view = opts.get("view", "side")
lua = f"""
local F = workspace.NHAnimStage
local ORIGIN = Vector3.new(3000, 500, 3000)
local src = {json.dumps(src)}
local id = src
if src:sub(1, 3) == "ks:" then
	local i = game
	for seg in string.gmatch(src:sub(4), "[^%.]+") do i = i:FindFirstChild(seg) end
	id = i:GetAttribute("PreviewId")
end
local times = {{{",".join(str(t) for t in times)}}}
local yaw = {{ side = -90, front = 180, ["34"] = -130 }}
local y = math.rad(yaw["{view}"] or -90)
for n = 1, 6 do
	local r = F["R" .. n]
	local an = r.Humanoid.Animator
	for _, tr in an:GetPlayingAnimationTracks() do tr:Stop(0) tr:Destroy() end
	for _, m in r:GetDescendants() do if m:IsA("Motor6D") then m.Transform = CFrame.identity end end
	r:PivotTo(CFrame.new(ORIGIN + Vector3.new((n - 3.5) * 7, 0, 0)) * CFrame.Angles(0, y, 0))
	local t = times[n]
	if t then
		local a = Instance.new("Animation") a.AnimationId = id
		local tr = an:LoadAnimation(a)
		tr:Play(0) tr:AdjustSpeed(0)
		local w = 0 while tr.Length == 0 and w < 30 do task.wait(0.05) w += 1 end
		tr.TimePosition = math.min(t, tr.Length)
		an:StepAnimations(0)
	end
end
local cam = workspace.CurrentCamera
cam.CameraType = Enum.CameraType.Scriptable
cam.FieldOfView = 40
cam.CFrame = CFrame.lookAt(ORIGIN + Vector3.new(0, 2.5, 62), ORIGIN + Vector3.new(0, 0.8, 0))
return "posed " .. #times .. " at {view}"
"""
o, e = run("Edit", lua)
print(o.strip(), e[:200])
