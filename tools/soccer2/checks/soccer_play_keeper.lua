-- soccer_play_keeper (soccer-2.0 final-review finding 4, Client, Play, during a solo match from soccer_match_start.lua):
-- the keeper's pack in their zone (KeeperIdle, the KeeperStep strafes and stride), the fade at the box edge, and the
-- catch (Catch, then CatchIdle).
-- How SoccerPack decides it: Gui.Sports State().Keeper and .InZone (the server's Hud: Keeper = the keeper pad,
-- InZone = the root inside the team's SportKeeperZone part, Soccer.luau inBox). A solo match has no keeper pad, so the
-- check stands in for the server: State() reports Keeper = true and InZone by the same inBox test on the root, and
-- HasBall() is true while it catches. The player walks in and out (no teleport: the server's AntiTeleport pins a
-- client-moved root), with Humanoid:Move written after the ControlModule and the Studio lock-on stand-in
-- (NHStrafeTest = "Lock", AutoRotate off), as tools/phase6-strafes/checks/strafecheck.lua does.
-- Restores State/HasBall, the attribute, AutoRotate and the player's spot (walks back).
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local Sports = require(Ctl.Gui.Sports)
local Soccer = require(Ctl.Gui.Soccer)
local Pack = require(Ctl.Character.SoccerPack)
local AC = require(Ctl.Character.AnimationController)
local Clips = require(Ctl.Gui.Soccer.Clips)
local Loco = require(RS.Functions.Locomotion)
local LocoCfg = require(RS.Config.Locomotion)
local Char = P.Character
local Hum = Char and Char:FindFirstChildOfClass("Humanoid")
local Root = Char and Char:FindFirstChild("HumanoidRootPart")
if not (Hum and Root) then return "FAIL soccer_play_keeper: no character" end
if not Pack.StateForTests().On then return "FAIL soccer_play_keeper: the soccer pack isn't on (InSport=" .. tostring(P:GetAttribute("InSport")) .. ")" end
local Team = P:GetAttribute("SportTeam")
local Zone = nil
for _, D in workspace.Sports:GetDescendants() do
	if D:IsA("BasePart") and D:GetAttribute("SportKeeperZone") ~= nil and D:GetAttribute("SportKeeperZone") == Team then Zone = D break end
end
if not Zone then return "FAIL soccer_play_keeper: no SportKeeperZone for team " .. tostring(Team) end
-- the server's test (Services.Sports.Soccer inBox, margin 0)
local function inBox(Part, Pos)
	local L = Part.CFrame:PointToObjectSpace(Pos)
	return math.abs(L.X) <= Part.Size.X / 2 and math.abs(L.Y) <= Part.Size.Y / 2 and math.abs(L.Z) <= Part.Size.Z / 2
end
local function flat(V) return Vector3.new(V.X, 0, V.Z) end
local function id(T) return T and T.Animation and T.Animation.AnimationId end

local Fails = {}
local OrigState, OrigHasBall = Sports.State, Sports.HasBall
local HoldBall = false
Sports.State = function()
	local S, At = OrigState()
	if type(S) ~= "table" then return S, At end
	local C = table.clone(S)
	C.Keeper = true
	C.InZone = inBox(Zone, Root.Position)
	return C, At
end
Sports.HasBall = function() return HoldBall or OrigHasBall() end
local Start = Root.Position
local StartAuto = Hum.AutoRotate
local Dir = Vector3.zero
local function drive() if Dir.Magnitude > 0 then Hum:Move(Dir, false) end end
RunService:BindToRenderStep("NHSoccerKeeperTestMove", Enum.RenderPriority.Input.Value + 1, drive)
local Conn = RunService.PreSimulation:Connect(drive)
local function walkTo(Pos, Within, Timeout)
	local T0 = os.clock()
	while os.clock() - T0 < Timeout do
		local D = flat(Pos - Root.Position)
		if D.Magnitude <= Within then break end
		Dir = D.Unit
		RunService.Heartbeat:Wait()
	end
	Dir = Vector3.zero
	return flat(Pos - Root.Position).Magnitude <= Within
end
local function restore()
	Dir = Vector3.zero
	P:SetAttribute("NHStrafeTest", nil)
	Hum.AutoRotate = StartAuto
	HoldBall = false
	walkTo(Start, 2, 20)
	pcall(function() RunService:UnbindFromRenderStep("NHSoccerKeeperTestMove") end)
	Conn:Disconnect()
	Hum:Move(Vector3.zero, false)
	Sports.State, Sports.HasBall = OrigState, OrigHasBall
end
local function finish()
	restore()
	if #Fails > 0 then return "FAIL soccer_play_keeper\n" .. table.concat(Fails, "\n") end
	return "PASS soccer_play_keeper"
end

-- 1. into the box: the keeper's idle, strafes and stride
local Centre = Zone.Position
if not walkTo(Centre, 2, 25) then table.insert(Fails, "couldn't walk to the keeper zone's centre") return finish() end
if not inBox(Zone, Root.Position) then table.insert(Fails, "at the zone's centre but the root isn't inside the box (Y?)") return finish() end
task.wait(1.0) -- SoccerPack polls at 4 Hz
if not Pack.StateForTests().Keeper then table.insert(Fails, "SoccerPack didn't take the keeper state in the zone") end
local TT = AC.Controller.TrackTable
if id(TT.Idle) ~= (Clips.Id("KeeperIdle")) then table.insert(Fails, "the zone idle is " .. tostring(id(TT.Idle)) .. ", want KeeperIdle") end
local Dirs = AC.DirectionalForTests()
if id(Dirs.Left) ~= (Clips.Id("KeeperStepLeft")) then table.insert(Fails, "the left strafe is " .. tostring(id(Dirs.Left)) .. ", want KeeperStepLeft") end
if id(Dirs.Right) ~= (Clips.Id("KeeperStepRight")) then table.insert(Fails, "the right strafe is " .. tostring(id(Dirs.Right)) .. ", want KeeperStepRight") end
local Data = Clips.Data()
local Leg = Char["Left Leg"].Size.Y
local Want = Loco.Rate(8, Data.Stride.KeeperStep, Leg, LocoCfg)
for _, G in { "StrafeLeft", "StrafeRight" } do
	local Got = AC.Rate(8, G)
	if math.abs(Got - Want) > Want * 0.05 then table.insert(Fails, string.format("%s rate %.3f, want KeeperStep's %.3f", G, Got, Want)) end
end

-- 2. the catch, then the hold (standing still, holding the ball)
HoldBall = true
Soccer.FxForTests("S_Pickup", { Player = P }) -- the server's pickup Fx: Local.Catch for the keeper in the zone
task.wait(0.1)
local function track(Slot) return Soccer.TracksForTests(Char)[Slot] end
local Catch = track("KeeperCatch")
if not (Catch and Catch.IsPlaying) then
	table.insert(Fails, "the catch: KeeperCatch isn't playing")
else
	local C0 = os.clock()
	while Catch.IsPlaying and os.clock() - C0 < Catch.Length + 1 do RunService.Heartbeat:Wait() end
	task.wait(0.15)
	local Hold = track("KeeperCatchIdle")
	if not (Hold and Hold.IsPlaying) then table.insert(Fails, "after the catch: KeeperCatchIdle isn't playing") end
end
HoldBall = false
task.wait(0.4)
local Hold = track("KeeperCatchIdle")
if Hold and Hold.IsPlaying then table.insert(Fails, "the catch hold goes on without the ball") end

-- 3. out of the box sideways (strafing): the keeper's directional tracks fade, never stop above 0.5 weight in a frame
local Out = flat(workspace.Sports.Pitch:GetBoundingBox().Position - Zone.Position)
Out = if Out.Magnitude > 0.1 then Out.Unit else flat(Root.CFrame.RightVector).Unit
Hum.AutoRotate = false
Root.CFrame = CFrame.lookAt(Root.Position, Root.Position + Vector3.new(Out.Z, 0, -Out.X)) -- the way out is on the right
P:SetAttribute("NHStrafeTest", "Lock")
task.wait(0.1)
Dir = Out
local Old = AC.DirectionalForTests()
local OldL, OldR, OldB = Old.Left, Old.Right, Old.Back
local Prev = {}
local MaxW, Swapped, Pops = 0, false, {}
local S0 = os.clock()
while os.clock() - S0 < 8 do
	for _, T in { OldL, OldR, OldB } do if T then Prev[T] = T.WeightCurrent MaxW = math.max(MaxW, if T.IsPlaying then T.WeightCurrent else 0) end end
	RunService.Heartbeat:Wait()
	local Now = AC.DirectionalForTests()
	if Now.Left ~= OldL or Now.Right ~= OldR then
		Swapped = true
		RunService.Heartbeat:Wait() -- one frame after the swap
		for _, T in { OldL, OldR, OldB } do
			if T and (Prev[T] or 0) > 0.5 then
				local W = 0
				pcall(function() W = T.WeightCurrent end)
				if W < 0.1 then table.insert(Pops, string.format("%s %.2f -> %.2f", tostring(T.Animation and T.Animation.Name), Prev[T], W)) end
			end
		end
		break
	end
end
Dir = Vector3.zero
P:SetAttribute("NHStrafeTest", nil)
Hum.AutoRotate = StartAuto
if MaxW <= 0.5 then table.insert(Fails, string.format("the keeper strafe never played above 0.5 weight before the edge (max %.2f)", MaxW)) end
if not Swapped then table.insert(Fails, "leaving the zone didn't swap the directional tracks") end
for _, Pp in Pops do table.insert(Fails, "a directional track popped at the box edge: " .. Pp) end
task.wait(0.8)
if Pack.StateForTests().Keeper then table.insert(Fails, "SoccerPack still in the keeper state outside the zone") end
local WantIdle = if Char:GetAttribute("HasSportBall") then "IdleBall" else "Idle"
if id(AC.Controller.TrackTable.Idle) ~= (Clips.Id(WantIdle)) then table.insert(Fails, "outside the zone the idle is " .. tostring(id(AC.Controller.TrackTable.Idle)) .. ", want " .. WantIdle) end
return finish()
