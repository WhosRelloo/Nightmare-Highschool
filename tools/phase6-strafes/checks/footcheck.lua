-- footcheck (phase6-strafes T5 round B, Client, Play): the stride-matched walk. Walks forward 3 s at the live walk speed
-- and measures the planted foot's slip against the ground speed (owner-visual V2: the 2.4x cap leaves some slide).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local C = P.Character
local Hum = C:FindFirstChildOfClass("Humanoid")
local Root = C:FindFirstChild("HumanoidRootPart")
local Animator = Hum:FindFirstChildOfClass("Animator")
local Dir = (Root.CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
local Conn = RunService.PreSimulation:Connect(function() Hum:Move(Dir, false) end)
task.wait(0.8)
local Dist, T, Last, LastSide, Ground, N, Rate = 0, 0, nil, nil, 0, 0, 0
local T0 = os.clock()
while os.clock() - T0 < 3 do
	local Dt = RunService.Heartbeat:Wait()
	local L, R = C["Left Leg"], C["Right Leg"]
	local Lp = (L.CFrame * CFrame.new(0, -L.Size.Y / 2, 0)).Position
	local Rp = (R.CFrame * CFrame.new(0, -R.Size.Y / 2, 0)).Position
	local F, S = if Lp.Y < Rp.Y then Lp else Rp, if Lp.Y < Rp.Y then "L" else "R"
	if Last and S == LastSide then Dist += (Vector3.new(F.X, 0, F.Z) - Vector3.new(Last.X, 0, Last.Z)).Magnitude T += Dt end
	Last, LastSide = F, S
	local V = Root.AssemblyLinearVelocity
	Ground += Vector3.new(V.X, 0, V.Z).Magnitude N += 1
	for _, Tr in Animator:GetPlayingAnimationTracks() do if Tr.Animation and Tr.Animation.Name == "Walk" then Rate = Tr.Speed end end
end
Conn:Disconnect()
Hum:Move(Vector3.zero)
local G = Ground / math.max(N, 1)
local Slip = if T > 0 then Dist / T else 0
local Ratio = Slip / math.max(G, 0.01)
local Line = string.format("walk ground %.2f st/s, Walk track %.2fx, stance-foot slip %.2f st/s (%.0f %% of the ground speed), legs %.2f", G, Rate, Slip, Ratio * 100, C["Left Leg"].Size.Y)
return (if Ratio <= 0.3 then "PASS footcheck\n" else "FAIL footcheck (slip over 30 %)\n") .. Line
