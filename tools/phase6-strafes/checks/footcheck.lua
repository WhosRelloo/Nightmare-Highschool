-- footcheck (phase6-strafes T5 round B, Client, Play): the stride-matched walk. Walks forward 3 s at the live walk speed
-- and measures the planted foot's slip against the ground speed (owner-visual V2: the 2.4x cap leaves some slide).
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
local Dir = Root.CFrame.RightVector * SideSign -- along the hallway; AutoRotate turns the body into it
local Conn2 = RunService.Heartbeat:Connect(function() Hum:Move(Dir, false) end)
-- the ControlModule writes the real input at RenderStepped (Input priority), before AnimationController's PreAnimation:
-- write ours right after it, so the controller sees this move the way it sees a real one
RunService:BindToRenderStep("NHStrafeTestMove", Enum.RenderPriority.Input.Value + 1, function() Hum:Move(Dir, false) end)
local Conn = RunService.PreSimulation:Connect(function() Hum:Move(Dir, false) end)
task.wait(0.8)
local Dist, T, Last, LastSide, Ground, N, Rate = 0, 0, nil, nil, 0, 0, 0
local T0 = os.clock()
while os.clock() - T0 < 1.4 do
	local Dt = RunService.Heartbeat:Wait()
	local L, R = C["Left Leg"], C["Right Leg"]
	local Lp = (L.CFrame * CFrame.new(0, -L.Size.Y / 2, 0)).Position
	local Rp = (R.CFrame * CFrame.new(0, -R.Size.Y / 2, 0)).Position
	local F, S = if Lp.Y < Rp.Y then Lp else Rp, if Lp.Y < Rp.Y then "L" else "R"
	if Last and S == LastSide then Dist += (F - Last):Dot(Dir) T += Dt end -- signed, along the move
	Last, LastSide = F, S
	local V = Root.AssemblyLinearVelocity
	Ground += Vector3.new(V.X, 0, V.Z).Magnitude N += 1
	for _, Tr in Animator:GetPlayingAnimationTracks() do if Tr.Animation and Tr.Animation.Name == "Walk" then Rate = Tr.Speed end end
end
Conn:Disconnect() Conn2:Disconnect() RunService:UnbindFromRenderStep("NHStrafeTestMove")
Hum:Move(Vector3.zero)
local G = Ground / math.max(N, 1)
local Slip = if T > 0 then math.abs(Dist / T) else 0
local Ratio = Slip / math.max(G, 0.01)
local Line = string.format("walk ground %.2f st/s, Walk track %.2fx, stance-foot slip %.2f st/s (%.0f %% of the ground speed), legs %.2f", G, Rate, Slip, Ratio * 100, C["Left Leg"].Size.Y)
return (if Ratio <= 0.3 then "PASS footcheck\n" else "FAIL footcheck (slip over 30 %)\n") .. Line
