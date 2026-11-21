-- racecheck (2.35.0, task 7): the CineActor Begin/Release race on the GAME's instance. Client VM, one call; start it,
-- then run bridge.py CineRaceTest $P (TestBridge plays __SeamlessTest and ends it 0.1 s later, in the game's VM).
-- Pass: the Release landed inside Begin's 0.3 s ease-out and the game's controls are on afterwards. "Inside": the
-- director sets NHCineSeam = "In" and spawns Begin in the same step, and Finish clears it right before Release, so a
-- clear under 0.25 s after the set is inside the ease. (WalkSpeed can't show it: this VM never sees Begin's eased
-- WalkSpeed at render time; a LocalScript hook on the game's instance did, see the task-7 report.)
-- NEVER require PlayerModule or the game's controllers from here (execute_luau's own VM: a require builds a rogue
-- PlayerModule copy). The controls are read by behaviour: while the game's are enabled, its ControlModule writes the
-- input (zero) to the humanoid every frame at Input priority, so a Move written the frame before is gone.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
local function gameControlsOn(): boolean
	local N = "RaceCheckCtl" .. tostring(math.random(1e6))
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
local WS0 = Hum.WalkSpeed
local Before = gameControlsOn()
local Seen, Cleared, SeenAt, ClearAt = false, false, nil, nil
local N = "RaceCheck"
RunService:BindToRenderStep(N, Enum.RenderPriority.Last.Value, function()
	local Ph = Player:GetAttribute("NHCineSeam")
	if Ph ~= nil and not Seen then Seen = true SeenAt = os.clock() end
	if Seen and Ph == nil and not Cleared then Cleared = true ClearAt = os.clock() end
end)
local T0 = os.clock()
repeat task.wait(0.05) until Cleared or os.clock() - T0 > 30
task.wait(1.5)
RunService:UnbindFromRenderStep(N)
local After = gameControlsOn()
local InEase = SeenAt ~= nil and ClearAt ~= nil and ClearAt - SeenAt < 0.25
local Ok = Seen and InEase and Before and After and Hum.WalkSpeed == WS0
return string.format("%s\ncut seen %s; cleared %.0f ms after it began (inside the ease: %s); controls before %s, after %s; walkspeed now %s",
	Ok and "RACE OK" or "RACE FAIL", tostring(Seen), (SeenAt and ClearAt) and (ClearAt - SeenAt) * 1000 or -1, tostring(InEase), tostring(Before), tostring(After), tostring(Hum.WalkSpeed))
