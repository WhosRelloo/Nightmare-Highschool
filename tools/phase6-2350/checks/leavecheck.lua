-- leavecheck (2.35.0, task 9, spec §4.3): Tutorial.Leave ends the player's running seamless cine session (the safety net for an
-- open-ended beat). Client VM; the server's TutorialLeave is fired from outside part-way through the beat. Run:
--   bridge.py TutorialEnter $P ; bridge.py CineMark $P '"<CUT>"' '"Seen"'
--   (start this client script in the background), wait ~6 s, then bridge.py TutorialLeave $P
-- CUT is __BeatHoldTest (a 14 s crouching Hold beat) by default; replace the CUT line for __SeamlessTest (4 s Walk beat: leave at ~10 s).
-- Confirms: NHTutorial set before and cleared after; the leave hit mid-beat; the client got { Kind = "End", How = "Skipped" }
-- (the skip-style dip, not a hang); the cut's seam state clears; the game's controls come back; the crouch is released.
-- NEVER require game modules from here (execute_luau's own VM builds rogue copies).
local CUT = "__BeatHoldTest"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Out, Pass = {}, true
local function check(Ok, Text) Pass = Pass and Ok table.insert(Out, (Ok and "ok   " or "FAIL ") .. Text) end

local function gameControlsOn(): boolean
	local N = "LeaveCheckCtl" .. tostring(math.random(1e6))
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

check(Player:GetAttribute("NHTutorial") == true, "0 NHTutorial set before the cut")
local EndHow, Session
local Conn = Remote.OnClientEvent:Connect(function(M)
	if typeof(M) ~= "table" then return end
	if M.Kind == "Play" then Session = M.Session elseif M.Kind == "End" and M.Session == Session then EndHow = M.How end
end)
Remote:FireServer({ Kind = "Replay"; Id = CUT })
local T0 = os.clock()
repeat task.wait(0.05) until Session or os.clock() - T0 > 5
check(Session ~= nil, "1 cut started")
-- wait for the leave (NHTutorial cleared by the server), noting where the cut was when it landed
local Last, SeamBefore, CrouchSeen = nil, nil, false
repeat
	task.wait(0.05)
	local Raw = Player:GetAttribute("NHCineSeam")
	if Raw ~= nil and Player:GetAttribute("NHTutorial") == true then SeamBefore = Raw end -- the last seam while still in Wickfield
	if Hum:GetAttribute("Crouch") == true and Player:GetAttribute("NHTutorial") == true then CrouchSeen = true end
	local Now = tostring(Raw)
	if Now ~= Last then Last = Now table.insert(Out, string.format("     t=%.1f seam=%s", os.clock() - T0, Now)) end
until Player:GetAttribute("NHTutorial") ~= true or os.clock() - T0 > 40
local SeamAtLeave = SeamBefore -- (the seam attribute clears in the same frame as NHTutorial, so the last sample before it)
table.insert(Out, string.format("     last seam before leave=%s, crouched during beat=%s (t=%.1fs)", tostring(SeamBefore), tostring(CrouchSeen), os.clock() - T0))
check(Player:GetAttribute("NHTutorial") == nil, "2 NHTutorial cleared")
check(SeamAtLeave == "Beat" or SeamAtLeave == "BeatIn", "3 the leave landed mid-beat (seam " .. tostring(SeamAtLeave) .. ")")
check(CUT ~= "__BeatHoldTest" or CrouchSeen, "3b the beat had crouched the player before the leave (for __BeatHoldTest)")
local T1 = os.clock()
repeat task.wait(0.05) until (EndHow ~= nil and Player:GetAttribute("NHCineSeam") == nil) or os.clock() - T1 > 6
check(EndHow == "Skipped", "4 client got End How=" .. tostring(EndHow) .. " (want Skipped)")
check(Player:GetAttribute("NHCineSeam") == nil, "5 seam state cleared (" .. tostring(Player:GetAttribute("NHCineSeam")) .. ")")
task.wait(1.5)
check(gameControlsOn(), "6 game controls back")
check(Hum:GetAttribute("Crouch") ~= true, "7 crouch released")
check(Player:GetAttribute("NHBeatNoSprint") ~= true, "8 no-sprint cleared")
Conn:Disconnect()
return (Pass and "PASS" or "FAIL") .. "\n" .. table.concat(Out, "\n")
