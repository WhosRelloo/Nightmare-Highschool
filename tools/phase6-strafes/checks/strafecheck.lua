-- strafecheck (phase6-strafes T5 round B, Client, Play): the directional walk.
-- Forces the lock-on mode with the Studio-only Player attribute NHStrafeTest = "Lock" (AnimationController reads it as
-- Locked), holds the body facing its start heading (AutoRotate off, as LockOn does), and drives Humanoid:Move each
-- PreSimulation (after the ControlModule's RenderStepped write). Measures weights, the speed cap and the foot slip.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local C = P.Character
local Hum = C and C:FindFirstChildOfClass("Humanoid")
local Root = C and C:FindFirstChild("HumanoidRootPart")
if not (Hum and Root) then return "FAIL no character" end
local Animator = Hum:FindFirstChildOfClass("Animator")
local Fails, Notes = {}, {}
local function Ok(Cnd, W) if not Cnd then table.insert(Fails, W) end end
local Face = Root.CFrame - Root.Position
local Dir = Vector3.zero
P:SetAttribute("NHStrafeTest", "Lock")
Hum.AutoRotate = false
local Conn = RunService.PreSimulation:Connect(function()
	Root.CFrame = CFrame.new(Root.Position) * Face
	Hum:Move(Dir, false)
end)
local function tracks()
	local T = {}
	for _, Tr in Animator:GetPlayingAnimationTracks() do
		local N = Tr.Animation and Tr.Animation.Name
		if N == "Walk" or N == "StrafeLeft" or N == "StrafeRight" then T[N] = Tr end
	end
	return T
end
local function lowFoot()
	local L, R = C:FindFirstChild("Left Leg"), C:FindFirstChild("Right Leg")
	local Lp = (L.CFrame * CFrame.new(0, -L.Size.Y / 2, 0)).Position
	local Rp = (R.CFrame * CFrame.new(0, -R.Size.Y / 2, 0)).Position
	return if Lp.Y < Rp.Y then Lp else Rp, if Lp.Y < Rp.Y then "L" else "R"
end
local function slip(Seconds)
	local Dist, T, Last, LastSide = 0, 0, nil, nil
	local T0 = os.clock()
	while os.clock() - T0 < Seconds do
		local Dt = RunService.Heartbeat:Wait()
		local F, S = lowFoot()
		if Last and S == LastSide then Dist += (Vector3.new(F.X, 0, F.Z) - Vector3.new(Last.X, 0, Last.Z)).Magnitude T += Dt end
		Last, LastSide = F, S
	end
	return if T > 0 then Dist / T else 0
end
local Right = Face.RightVector
-- right
Dir = Right
task.wait(1.2)
local T = tracks()
Ok(T.StrafeRight and T.StrafeRight.WeightCurrent >= 0.85, "StrafeRight weight " .. tostring(T.StrafeRight and T.StrafeRight.WeightCurrent))
Ok(not T.Walk or T.Walk.WeightCurrent <= 0.15, "Walk weight " .. tostring(T.Walk and T.Walk.WeightCurrent))
local V = Root.AssemblyLinearVelocity
local Speed = Vector3.new(V.X, 0, V.Z).Magnitude
table.insert(Notes, string.format("strafe speed %.2f (WalkSpeed %.2f)", Speed, Hum.WalkSpeed))
Ok(math.abs(Speed - 8.5) < 0.8, "strafe speed " .. Speed)
local Sl = slip(2)
table.insert(Notes, string.format("strafe stance-foot slip %.2f studs/s", Sl))
Ok(Sl < 0.9, "strafe foot slip " .. Sl)
local Torso = C:FindFirstChild("Torso")
local Yaw = math.deg(math.acos(math.clamp(Torso.CFrame.LookVector:Dot(Root.CFrame.LookVector), -1, 1)))
table.insert(Notes, string.format("chest off the root's facing %.1f deg", Yaw))
Ok(Yaw < 12, "chest yaw " .. Yaw)
-- forward-right diagonal
Dir = (Right + Face.LookVector).Unit
task.wait(1)
T = tracks()
Ok(T.Walk and T.StrafeRight and math.abs(T.Walk.WeightCurrent - 0.5) < 0.15 and math.abs(T.StrafeRight.WeightCurrent - 0.5) < 0.15, "diagonal weights")
-- back
Dir = -Face.LookVector
task.wait(1)
T = tracks()
Ok(T.Walk and T.Walk.Speed < 0, "backpedal speed " .. tostring(T.Walk and T.Walk.Speed))
-- release
Dir = Vector3.zero
P:SetAttribute("NHStrafeTest", nil)
Conn:Disconnect()
Hum.AutoRotate = true
task.wait(0.6)
T = tracks()
Ok(not T.StrafeRight and not T.StrafeLeft, "strafes still playing after release")
return (#Fails == 0 and "PASS strafecheck" or ("FAIL strafecheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
