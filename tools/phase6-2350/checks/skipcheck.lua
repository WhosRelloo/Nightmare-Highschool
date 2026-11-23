-- skipcheck (2.35.0, task 7): (1) a seamless cut takes the game's controls and a skip gives them back; (2) a seamless Skip dips to black and hands
-- everything back. Client VM, one call.
-- NEVER require PlayerModule or the game's controllers from here: execute_luau runs in its own Luau VM, so a require
-- builds a second, rogue PlayerModule (its ControlModule then writes zero input every frame and its CameraModule runs)
-- for the rest of the session. The GAME's controls are read by behaviour (gameControlsOn): while enabled, its
-- ControlModule writes the player's input (zero) to the humanoid every frame at Input priority, so a Move written the
-- frame before is gone; while disabled, nothing does and the Move stays.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Out = {}
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")

local function gameControlsOn(): boolean
	local N = "SkipCheckCtl" .. tostring(math.random(1e6))
	local Step, Result = 0, nil
	RunService:BindToRenderStep(N, Enum.RenderPriority.Input.Value + 1, function()
		Step += 1
		if Step == 1 then Hum:Move(Vector3.new(0, 0, -1))
		elseif Step == 2 then Result = Hum.MoveDirection.Magnitude < 0.5 Hum:Move(Vector3.zero) end
	end)
	repeat RunService.RenderStepped:Wait() until Result ~= nil
	RunService:UnbindFromRenderStep(N)
	return Result
end

local function playAndSession(): string?
	local Session
	local Conn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" then Session = M.Session end end)
	Remote:FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
	local T0 = os.clock()
	repeat task.wait() until Session or os.clock() - T0 > 5
	Conn:Disconnect()
	return Session
end

-- (2026-11-22) precondition: the replay below is refused unless __SeamlessTest is marked Seen, and then no cut plays at all: every row
-- would read "controls on mid-cut" / "HUD still on" for a cut that never started. Say so instead (harness/round_start.sh marks it)
do
	local Probe = playAndSession()
	if not Probe then
		return "SKIPCHECK FAIL (precondition): the __SeamlessTest replay was refused, no cut played. Mark it first: python -X utf8 -I bridge.py CineMark $P '\"__SeamlessTest\"' '\"Seen\"' (harness/round_start.sh does it)"
	end
	Remote:FireServer({ Kind = "Skip"; Session = Probe })
	local T0 = os.clock()
	repeat task.wait(0.05) until Player:GetAttribute("NHCineSeam") == nil or os.clock() - T0 > 3
	task.wait(1.5)
end

-- (1) the game's controls: a seamless cut takes them, a skip gives them back. (The Begin/Release race itself:
-- racecheck.lua + race_server.lua, which can end a cut inside Begin's 0.3 s ease; a client round trip can't.)
do
	local S2 = playAndSession()
	local T1 = os.clock()
	repeat task.wait(0.05) until Player:GetAttribute("NHCineSeam") == "Cut" or os.clock() - T1 > 5
	local During = gameControlsOn()
	Remote:FireServer({ Kind = "Skip"; Session = S2 })
	task.wait(1.5)
	local AfterSkip = gameControlsOn()
	table.insert(Out, string.format("1 control: mid-cut controls %s (want false), after skip %s %s", tostring(During), tostring(AfterSkip), (S2 ~= nil and not During and AfterSkip) and "ok" or "FAIL"))
	task.wait(1.5)
end

-- (2) seamless skip at 2.5 s
local PG = Player.PlayerGui
local Before = {}
for _, G in PG:GetChildren() do if G:IsA("LayerCollector") and G.Name ~= "NHCineUI" then Before[G] = G.Enabled end end
local Session = playAndSession()
task.wait(2.5)
local MidHud = {}
for G in Before do if G.Parent and G.Enabled then table.insert(MidHud, G.Name) end end
local Cam = workspace.CurrentCamera
local Veil = PG:FindFirstChild("NHCineUI") and PG.NHCineUI:FindFirstChild("Veil")
local Bars = PG.NHCineUI.Top.Size.Y.Scale
local MaxA, BlackAt, ClearAt = 0, nil, nil
local Name = "SkipCheck"
local TS = os.clock()
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local A = 1 - Veil.BackgroundTransparency
	if A > MaxA then MaxA = A end
	if A >= 0.999 and not BlackAt then BlackAt = os.clock() - TS end
	if BlackAt and A <= 0.001 and not ClearAt then ClearAt = os.clock() - TS end
end)
Remote:FireServer({ Kind = "Skip"; Session = Session })
task.wait(1.5)
RunService:UnbindFromRenderStep(Name)
local Restored, Total = 0, 0
for G, Was in Before do if G.Parent then Total += 1 if G.Enabled == Was then Restored += 1 end end end
local Ctl2 = gameControlsOn()
local Ok2 = MaxA >= 0.999 and ClearAt ~= nil and ClearAt < 0.6 and Cam.CameraType == Enum.CameraType.Custom
	and Player:GetAttribute("NHCineSeam") == nil and Ctl2 and Restored == Total and Bars == 0
table.insert(Out, string.format("2 skip: mid-cut HUD still on [%s], bars %.2f; veil peak %.3f, black at %.3f s, clear at %s s; camera %s; seam %s; game controls %s; HUD restored %d/%d %s",
	table.concat(MidHud, ","), Bars, MaxA, BlackAt or -1, ClearAt and string.format("%.3f", ClearAt) or "never", Cam.CameraType.Name,
	tostring(Player:GetAttribute("NHCineSeam")), tostring(Ctl2), Restored, Total, Ok2 and "ok" or "FAIL"))
return table.concat(Out, "\n")
