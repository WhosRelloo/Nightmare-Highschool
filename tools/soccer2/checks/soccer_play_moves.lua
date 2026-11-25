-- soccer_play_moves (soccer-2.0 Task 4, Client, Play, during a solo match from soccer_match_start.lua): the charge,
-- kick, dribble, dive and fall clips through the real Fx handler (Controllers.Gui.Soccer FxForTests).
-- Final-review round: A (a one-shot lets go once the player moves after the move; standing still it plays out),
-- B (the Tackle starts at ContactAt - 0.35), C (the Kick charge's creep moves). Moves the player with Humanoid:Move
-- written after the ControlModule (as tools/phase6-strafes/checks/strafecheck.lua does).
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local Soccer = require(Ctl.Gui.Soccer)
if not Soccer.FxForTests then return "FAIL Controllers.Gui.Soccer has no FxForTests (Task 4 not installed)" end
local Clips = require(Ctl.Gui.Soccer.Clips)
local Anim = require(RS.Functions.SoccerAnim)
local T = require(RS.Config.Sports).Soccer
local Char = P.Character
local Root = Char.HumanoidRootPart
local Fails = {}
local function Near(G, W, What, Tol) if math.abs(G - W) > Tol then table.insert(Fails, string.format("%s: got %.3f want %.3f", What, G, W)) end end
local function track(Slot) return Soccer.TracksForTests(Char)[Slot] end
local function stopAll() for _, Tr in Soccer.TracksForTests(Char) do if Tr.IsPlaying then Tr:Stop(0) end end end
local function flat(V) return Vector3.new(V.X, 0, V.Z) end
local Centre = workspace.Sports.Pitch:GetBoundingBox().Position
local function toCentre() local D = flat(Centre - Root.Position) return if D.Magnitude > 1 then D.Unit else flat(Root.CFrame.LookVector).Unit end
local function face(Look) Root.CFrame = CFrame.lookAt(Root.Position, Root.Position + Look) end
local Hum = Char:FindFirstChildOfClass("Humanoid")
local MoveDir = Vector3.zero
RunService:BindToRenderStep("NHSoccerMovesTestMove", Enum.RenderPriority.Input.Value + 1, function() if MoveDir.Magnitude > 0 then Hum:Move(MoveDir, false) end end)
local MoveConn = RunService.PreSimulation:Connect(function() if MoveDir.Magnitude > 0 then Hum:Move(MoveDir, false) end end)
local function cleanup() MoveDir = Vector3.zero pcall(function() RunService:UnbindFromRenderStep("NHSoccerMovesTestMove") end) MoveConn:Disconnect() Hum:Move(Vector3.zero, false) end
-- 1. the charge creeps, then the kick lands Lead before contact
local Kick = Clips.Clip("Kick")
if not Kick then cleanup() return "FAIL no clip data for Kick" end
local HoldAt, Creep = Anim.Hold(Kick, 0.05, Anim.KickMargin, T.Kick.MaxHold)
Soccer.FxForTests("S_Charge", { Player = P })
task.wait(0.05)
local Tr = track("Kick")
if not (Tr and Tr.IsPlaying) then
	table.insert(Fails, "charge: no Kick track playing")
else
	local T0 = os.clock()
	while Tr.TimePosition < HoldAt and os.clock() - T0 < 1 do RunService.Heartbeat:Wait() end
	task.wait(0.1)
	Near(Tr.Speed, Creep, "charge creep speed", 1e-3)
	-- C: the creep moves: at least 0.05 s of clip over 0.8 s
	local A0 = Tr.TimePosition
	task.wait(0.8)
	local Rise = Tr.TimePosition - A0
	if not (Tr.IsPlaying and Rise >= 0.05) then table.insert(Fails, string.format("C: the charge rose %.3f s of clip over 0.8 s (want >= 0.05, playing %s)", Rise, tostring(Tr.IsPlaying))) end
	if Tr.TimePosition > Anim.StartAt(Kick, 0.05) + 1e-3 then table.insert(Fails, "the charge crept past the kick point") end
end
Soccer.FxForTests("S_Kick", { Player = P; Kind = "Shot"; Power = 0.5 })
Tr = track("Kick")
if Tr then Near(Tr.TimePosition, Anim.StartAt(Kick, 0.05), "kick start", 0.02) Near(Tr.Speed, 1, "kick speed", 1e-3) end
-- A: standing still, the kick plays to its end
if Tr then
	local Most, K0 = Tr.TimePosition, os.clock()
	while Tr.IsPlaying and os.clock() - K0 < 1.5 do Most = math.max(Most, Tr.TimePosition) RunService.Heartbeat:Wait() end
	if Most < Tr.Length - 0.06 then table.insert(Fails, string.format("A: standing still, the kick stopped at %.3f of %.3f", Most, Tr.Length)) end
end
task.wait(0.2)
stopAll()
-- 2. the dribble: 11 studs (1.1), the Spin clip through its window at the fitted rate
local Spin = Clips.Clip("Dribble")
local D = toCentre() face(D) task.wait(0.2)
local From = Root.Position
Soccer.FxForTests("S_Dribble", { Player = P; Dir = D })
task.wait(0.05)
local Rate, Time = Anim.Fit(Spin, T.Dribble.Time, 2)
Tr = track("Dribble")
if not Tr then table.insert(Fails, "dribble: no track") else Near(Tr.Speed, Rate, "dribble rate", 1e-3) end
task.wait(Time + 0.4)
Near(flat(Root.Position - From).Magnitude, T.Dribble.Dash * 0.5, "dribble distance", T.Dribble.Dash * 0.05)
if Tr and Tr.IsPlaying then Near(Tr.Speed, 1, "dribble back to 1x", 1e-3) end
stopAll()
-- 3. the dive: the slot by side, 17 studs (1.1)
D = toCentre() face(Vector3.new(D.Z, 0, -D.X)) task.wait(0.2) -- the centre is now on the right
From = Root.Position
Soccer.FxForTests("S_Dive", { Player = P; Dir = D })
task.wait(0.05)
local DR = track("KeeperDiveRight")
if not (DR and DR.IsPlaying) then table.insert(Fails, "dive: KeeperDiveRight isn't playing") end
local _, DT = Anim.Fit(Clips.Clip("KeeperDiveRight"), T.Keeper.DiveTime, 2)
task.wait(DT + 0.4)
local Want = T.Keeper.DiveDash * T.Keeper.DiveTime
Near(flat(Root.Position - From).Magnitude, Want, "dive distance", Want * 0.1)
-- A: the dive's move is over: walking lets the clip go (stopped or fading) within 0.5 s
if DR and DR.IsPlaying then
	MoveDir = flat(Root.CFrame.LookVector).Unit
	local M0, Let = os.clock(), false
	while os.clock() - M0 < 0.5 do
		RunService.Heartbeat:Wait()
		if not DR.IsPlaying or DR.WeightTarget < 0.5 then Let = true break end
	end
	MoveDir = Vector3.zero
	if not Let then table.insert(Fails, "A: the dive clip still holds the body 0.5 s into a walk") end
else
	table.insert(Fails, "A: the dive clip ended before the walk (nothing to let go)")
end
task.wait(0.3)
stopAll()
-- B: the Tackle starts at ContactAt - 0.35
local TC = Clips.Clip("Tackle")
face(toCentre()) task.wait(0.2)
Soccer.FxForTests("S_Tackle", { Player = P; Dir = flat(Root.CFrame.LookVector).Unit })
local TT = track("Tackle")
if not (TT and TT.IsPlaying) then table.insert(Fails, "B: no Tackle track playing")
else
	if TT.TimePosition < 0.15 then table.insert(Fails, string.format("B: the Tackle starts at %.3f (want >= 0.15)", TT.TimePosition)) end
	if TC and TC.ContactAt then Near(TT.TimePosition, TC.ContactAt - 0.35, "B: tackle start", 0.03) end
end
task.wait(0.8)
stopAll()
-- 4. a fall follows the stun (a client-side stand-in for the server's SportStun)
Char:SetAttribute("SportStun", workspace:GetServerTimeNow() + 1.2)
Soccer.FxForTests("S_Ankles", { Player = P; Kind = "Dribble" })
task.wait(0.1)
local Trip = track("Trip")
if not (Trip and Trip.IsPlaying) then table.insert(Fails, "ankles: Trip isn't playing") end
task.wait(2.2)
for K, Tr2 in Soccer.TracksForTests(Char) do if Tr2.IsPlaying then table.insert(Fails, "still playing after the stun: " .. K) end end
Char:SetAttribute("SportStun", nil)
stopAll()
cleanup()
if #Fails > 0 then return "FAIL soccer_play_moves\n" .. table.concat(Fails, "\n") end
return "PASS soccer_play_moves"
