-- cinegate (phase6-strafes T5 round B, Client, Play): no strafe while a cut or an approach owns the character.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local C = P.Character
local Hum = C:FindFirstChildOfClass("Humanoid")
local Root = C:FindFirstChild("HumanoidRootPart")
local Animator = Hum:FindFirstChildOfClass("Animator")
-- the clearer side (no teleport: the server's AntiTeleport pins a client-moved root)
local function room(D)
	local RP = RaycastParams.new() RP.FilterType = Enum.RaycastFilterType.Exclude RP.FilterDescendantsInstances = { C }
	local H = workspace:Raycast(Root.Position, D * 30, RP)
	return if H then H.Distance else 30
end
local SideSign = if room(Root.CFrame.RightVector) >= room(-Root.CFrame.RightVector) then 1 else -1
local Fails = {}
local Face = Root.CFrame - Root.Position
P:SetAttribute("NHStrafeTest", "Lock")
Hum.AutoRotate = false
local Dir = Vector3.zero
local Conn2 = RunService.Heartbeat:Connect(function() Hum:Move(Dir, false) end)
-- the ControlModule writes the real input at RenderStepped (Input priority), before AnimationController's PreAnimation:
-- write ours right after it, so the controller sees this move the way it sees a real one
RunService:BindToRenderStep("NHStrafeTestMove", Enum.RenderPriority.Input.Value + 1, function() Hum:Move(Dir, false) end)
local Conn = RunService.PreSimulation:Connect(function() Hum:Move(Dir, false) end)
local function strafeW()
	local W = 0
	for _, Tr in Animator:GetPlayingAnimationTracks() do
		local N = Tr.Animation and Tr.Animation.Name
		if N == "StrafeLeft" or N == "StrafeRight" then W = math.max(W, Tr.WeightCurrent) end
	end
	return W
end
for _, B in { { P, "NHApproach", true }, { P, "NHCineSeam", "In" }, { P, "NHCineHold", true }, { C, "NHInCine", true } } do
	B[1]:SetAttribute(B[2], B[3])
	Dir = Face.RightVector * SideSign
	task.wait(0.8)
	if strafeW() > 0.05 then table.insert(Fails, B[2] .. ": strafe weight " .. strafeW()) end
	Dir = Vector3.zero
	B[1]:SetAttribute(B[2], nil)
	task.wait(0.3)
end
-- and with nothing set it does strafe (the check itself works)
Dir = Face.RightVector * SideSign
task.wait(1)
local Free = strafeW()
Dir = Vector3.zero
Conn:Disconnect() Conn2:Disconnect() RunService:UnbindFromRenderStep("NHStrafeTestMove")
P:SetAttribute("NHStrafeTest", nil)
Hum.AutoRotate = true
if Free < 0.5 then table.insert(Fails, "control: no strafe without a blocker (" .. Free .. ")") end
return #Fails == 0 and "PASS cinegate" or ("FAIL cinegate\n" .. table.concat(Fails, "\n"))
