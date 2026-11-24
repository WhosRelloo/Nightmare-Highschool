-- soccer_demo (soccer-2.0 Task 6, Client, Play, during a solo match): about 9 s of jog, charge, kick, dribble, backpedal
-- and dive through the real handlers, while it dumps every rig part per frame into _G.NHSoccerDump (JSON in the audit
-- format: parts "H:<Part>" rows [cx, cy, cz, tipx, tipy, tipz, lowest, 0, 0, 0] with z up and the floor at 0; cam rows).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Http = game:GetService("HttpService")
local P = Players.LocalPlayer
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local Soccer = require(Ctl.Gui.Soccer)
local Char = P.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local Root = Char.HumanoidRootPart
local Centre = workspace.Sports.Pitch:GetBoundingBox().Position
local D = Vector3.new(Centre.X - Root.Position.X, 0, Centre.Z - Root.Position.Z)
D = if D.Magnitude > 1 then D.Unit else Vector3.new(Root.CFrame.LookVector.X, 0, Root.CFrame.LookVector.Z).Unit
local RP = RaycastParams.new() RP.FilterType = Enum.RaycastFilterType.Exclude RP.FilterDescendantsInstances = { Char }
local Hit = workspace:Raycast(Root.Position, Vector3.new(0, -20, 0), RP)
local Floor = if Hit then Hit.Position.Y else Root.Position.Y - 3
local PARTS = { "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local Rows, Cam = {}, {}
for _, N in PARTS do Rows["H:" .. N] = {} Rows["V:" .. N] = {} end
local function r(v) return math.floor(v * 1000 + 0.5) / 1000 end
local function lowest(Pt)
	local Lo = math.huge
	for _, X in { -0.5, 0.5 } do for _, Y in { -0.5, 0.5 } do for _, Z in { -0.5, 0.5 } do
		Lo = math.min(Lo, (Pt.CFrame * (Pt.Size * Vector3.new(X, Y, Z))).Y)
	end end end
	return Lo - Floor
end
local Rec = RunService.Heartbeat:Connect(function()
	for _, N in PARTS do
		local Pt = Char:FindFirstChild(N)
		if Pt then
			local C = Pt.Position
			local Tip = if N == "Torso" or N == "Head" then Pt.CFrame * Vector3.new(0, Pt.Size.Y / 2, 0) else Pt.CFrame * Vector3.new(0, -Pt.Size.Y / 2, 0)
			local Row = { r(C.X), r(C.Z), r(C.Y - Floor), r(Tip.X), r(Tip.Z), r(Tip.Y - Floor), r(lowest(Pt)), 0, 0, 0 }
			table.insert(Rows["H:" .. N], Row)
			table.insert(Rows["V:" .. N], Row)
		end
	end
	local CF = workspace.CurrentCamera.CFrame
	table.insert(Cam, { "C", r(CF.X), r(CF.Z), r(CF.Y), 1, 0, 0, 0 })
end)
local Move = Vector3.zero
RunService:BindToRenderStep("NHSoccerDemo", Enum.RenderPriority.Input.Value + 1, function() Hum:Move(Move) end)
local function face(Look) Root.CFrame = CFrame.lookAt(Root.Position, Root.Position + Look) end
face(D)
task.wait(0.5)                                   -- idle (Soccer Idle)
Move = D task.wait(1.8)                          -- jog (Jog Forward, stride-matched)
Move = Vector3.zero task.wait(0.4)
Soccer.FxForTests("S_Charge", { Player = P }) task.wait(0.7)   -- the creeping wind-up
Soccer.FxForTests("S_Kick", { Player = P; Kind = "Shot"; Power = 0.8 }) task.wait(0.9)
Soccer.FxForTests("S_Dribble", { Player = P; Dir = D }) task.wait(1.3)
P:SetAttribute("NHStrafeTest", "Lock") Hum.AutoRotate = false
Move = -D task.wait(1.6)                         -- backpedal (Jog Backward in the strafe blend)
Move = Vector3.zero P:SetAttribute("NHStrafeTest", nil) Hum.AutoRotate = true task.wait(0.3)
face(Vector3.new(D.Z, 0, -D.X))
Soccer.FxForTests("S_Dive", { Player = P; Dir = D }) task.wait(1.6)
RunService:UnbindFromRenderStep("NHSoccerDemo")
Rec:Disconnect()
_G.NHSoccerDump = Http:JSONEncode({ parts = Rows; cam = Cam })
return "PASS soccer_demo " .. #Cam .. " frames, " .. #_G.NHSoccerDump .. " bytes"
