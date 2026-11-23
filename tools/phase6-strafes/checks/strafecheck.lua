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
-- the clearer side (no teleport: the server's AntiTeleport pins a client-moved root)
local function room(D)
	local RP = RaycastParams.new() RP.FilterType = Enum.RaycastFilterType.Exclude RP.FilterDescendantsInstances = { C }
	local H = workspace:Raycast(Root.Position, D * 30, RP)
	return if H then H.Distance else 30
end
local SideSign = if room(Root.CFrame.RightVector) >= room(-Root.CFrame.RightVector) then 1 else -1
local Fails, Notes = {}, {}
local function Ok(Cnd, W) if not Cnd then table.insert(Fails, W) end end
local Face = Root.CFrame - Root.Position
local Dir = Vector3.zero
P:SetAttribute("NHStrafeTest", "Lock")
Hum.AutoRotate = false
local Conn2 = RunService.Heartbeat:Connect(function() Hum:Move(Dir, false) end)
-- the ControlModule writes the real input at RenderStepped (Input priority), before AnimationController's PreAnimation:
-- write ours right after it, so the controller sees this move the way it sees a real one
RunService:BindToRenderStep("NHStrafeTestMove", Enum.RenderPriority.Input.Value + 1, function() Hum:Move(Dir, false) end)
local Conn = RunService.PreSimulation:Connect(function()
	Hum:Move(Dir, false) -- (AutoRotate is off: the body keeps its heading, as in lock-on)
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
		if Last and S == LastSide then Dist += (F - Last):Dot(Dir) T += Dt end -- the planted foot's mean velocity along the move (0 = planted)
		Last, LastSide = F, S
	end
	return if T > 0 then math.abs(Dist / T) else 0
end
local Right = Face.RightVector * SideSign
local SideName = if SideSign > 0 then "StrafeRight" else "StrafeLeft"
table.insert(Notes, "testing " .. SideName .. string.format(" (room %.0f studs)", room(Right)))
-- sideways (0.8 s to settle, 1.2 s measured: about 17 studs, inside the 30 of room)
Dir = Right
task.wait(0.8)
local T = tracks()
Ok(T[SideName] and T[SideName].WeightCurrent >= 0.85, SideName .. " weight " .. tostring(T[SideName] and T[SideName].WeightCurrent))
Ok(not T.Walk or T.Walk.WeightCurrent <= 0.15, "Walk weight " .. tostring(T.Walk and T.Walk.WeightCurrent))
local V = Root.AssemblyLinearVelocity
local Speed = Vector3.new(V.X, 0, V.Z).Magnitude
table.insert(Notes, string.format("strafe speed %.2f (WalkSpeed %.2f)", Speed, Hum.WalkSpeed))
Ok(math.abs(Speed - 8.5) < 0.8, "strafe speed " .. Speed)
local Sl = slip(1.2)
for _, Tr in Animator:GetPlayingAnimationTracks() do if Tr.Animation and Tr.Animation.Name == SideName then table.insert(Notes, string.format("%s track speed %.2fx id %s", SideName, Tr.Speed, Tr.Animation.AnimationId)) end end
table.insert(Notes, string.format("legs %.3f", C["Left Leg"].Size.Y))
table.insert(Notes, string.format("strafe stance-foot slip %.2f studs/s", Sl))
Ok(Sl < 0.6, "strafe foot slip " .. Sl)
local Torso = C:FindFirstChild("Torso")
local function flatL(CF) local L = CF.LookVector * Vector3.new(1, 0, 1) return L.Unit end
local Yaw = math.deg(math.acos(math.clamp(flatL(Torso.CFrame):Dot(flatL(Root.CFrame)), -1, 1))) -- yaw only (the clip leans and rolls a little)
table.insert(Notes, string.format("chest off the root's facing %.1f deg", Yaw))
Ok(Yaw < 12, "chest yaw " .. Yaw)
-- forward-right diagonal
Dir = (Right + Face.LookVector).Unit
task.wait(1)
T = tracks()
Ok(T.Walk and T[SideName] and math.abs(T.Walk.WeightCurrent - 0.5) < 0.15 and math.abs(T[SideName].WeightCurrent - 0.5) < 0.15, "diagonal weights " .. tostring(T.Walk and T.Walk.WeightCurrent) .. " / " .. tostring(T[SideName] and T[SideName].WeightCurrent))
-- back
Dir = -Face.LookVector
task.wait(1)
T = tracks()
Ok(T.Walk and T.Walk.Speed < 0, "backpedal speed " .. tostring(T.Walk and T.Walk.Speed))
-- release
Dir = Vector3.zero
P:SetAttribute("NHStrafeTest", nil)
Conn:Disconnect() Conn2:Disconnect() RunService:UnbindFromRenderStep("NHStrafeTestMove")
Hum.AutoRotate = true
task.wait(0.6)
T = tracks()
Ok(not T.StrafeRight and not T.StrafeLeft, "strafes still playing after release")
return (#Fails == 0 and "PASS strafecheck" or ("FAIL strafecheck\n" .. table.concat(Fails, "\n"))) .. "\n" .. table.concat(Notes, "\n")
