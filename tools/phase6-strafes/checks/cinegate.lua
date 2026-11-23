-- cinegate (phase6-strafes T5 round B, Client, Play): no strafe while a cut or an approach owns the character.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local C = P.Character
local Hum = C:FindFirstChildOfClass("Humanoid")
local Root = C:FindFirstChild("HumanoidRootPart")
local Animator = Hum:FindFirstChildOfClass("Animator")
local Fails = {}
local Face = Root.CFrame - Root.Position
P:SetAttribute("NHStrafeTest", "Lock")
Hum.AutoRotate = false
local Dir = Vector3.zero
local Conn = RunService.PreSimulation:Connect(function() Root.CFrame = CFrame.new(Root.Position) * Face Hum:Move(Dir, false) end)
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
	Dir = Face.RightVector
	task.wait(0.8)
	if strafeW() > 0.05 then table.insert(Fails, B[2] .. ": strafe weight " .. strafeW()) end
	Dir = Vector3.zero
	B[1]:SetAttribute(B[2], nil)
	task.wait(0.3)
end
-- and with nothing set it does strafe (the check itself works)
Dir = Face.RightVector
task.wait(1)
local Free = strafeW()
Dir = Vector3.zero
Conn:Disconnect()
P:SetAttribute("NHStrafeTest", nil)
Hum.AutoRotate = true
if Free < 0.5 then table.insert(Fails, "control: no strafe without a blocker (" .. Free .. ")") end
return #Fails == 0 and "PASS cinegate" or ("FAIL cinegate\n" .. table.concat(Fails, "\n"))
