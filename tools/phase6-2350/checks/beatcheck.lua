-- beatcheck (2.35.0, task 8 fix round 1, spec §3 / §4.3): a walk-and-talk beat's movement limits and its timeout hold.
-- Client VM, ONE call. Needs an NHTutorial player (bridge.py TutorialEnter $P) and the cut marked seen (bridge.py
-- CineMark $P '"__BeatHoldTest"' '"Seen"'). Plays __BeatHoldTest (Open shot, a 14 s Hold beat with crouch = true and
-- sprint = false, Close shot; its Config Length is 6 s, so Length + TimeoutPad = 11 s) and samples every frame:
--   * the server's crouch (Humanoid attribute Crouch) holds through the beat and is gone within 1 s of its end;
--   * NHBeatNoSprint is set through the beat and cleared after it;
--   * the cut outlives Length + TimeoutPad from Began and still ends through its blend out (Out seen: Done, not Timeout);
--   * the path is Open>Hold>Close;
--   * the walk speed after the cut is the one before it (crouch's 7 doesn't stick through the Close shot's Begin).
-- (W moving you during a beat needs real key input, which this VM can't send: see beatw.lua.)
-- NEVER require game modules from here (execute_luau's own VM builds rogue copies).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
local PAD, LENGTH = 5, 6
local Rows = {}
local Name = "BeatCheck"
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	table.insert(Rows, { t = os.clock(); seam = Player:GetAttribute("NHCineSeam"); crouch = Hum:GetAttribute("Crouch") == true;
		nosprint = Player:GetAttribute("NHBeatNoSprint") == true; path = Player:GetAttribute("NHCinePath"); ws = Hum.WalkSpeed })
end)
game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "__BeatHoldTest" })
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 3) or os.clock() - T0 > 45
task.wait(1.5)
RunService:UnbindFromRenderStep(Name)

local First, BeatA, BeatB, OutSeen, LastSeam, LastPath = nil, nil, nil, false, nil, nil
for _, R in Rows do
	if R.seam and not First then First = R.t end
	if R.seam == "BeatIn" or R.seam == "Beat" then BeatA = BeatA or R.t BeatB = R.t end
	if R.seam == "Out" then OutSeen = true end
	if R.seam then LastSeam = R.t end
	if R.path then LastPath = R.path end
end
local Report, Pass = {}, true
local function check(Ok, Text) Pass = Pass and Ok table.insert(Report, Text .. (if Ok then " ok" else " FAIL")) end
if not (First and BeatA and BeatB) then
	return "BEAT FAIL\nthe beat was not seen (" .. #Rows .. " frames)"
end
-- crouch: through the Beat phase (after 0.5 s for the round trip), and released within 1 s of the beat's end
local In, Held, NoSprintIn, After, AfterCrouch, AfterNoSprint = 0, 0, 0, 0, 0, 0
for _, R in Rows do
	if R.t >= BeatA + 0.5 and R.t <= BeatB then
		In += 1
		if R.crouch then Held += 1 end
		if R.nosprint then NoSprintIn += 1 end
	elseif R.t > BeatB + 1 then
		After += 1
		if R.crouch then AfterCrouch += 1 end
		if R.nosprint then AfterNoSprint += 1 end
	end
end
check(In > 0 and Held == In, string.format("crouch held %d of %d beat frames", Held, In))
check(After > 0 and AfterCrouch == 0, string.format("crouch after the beat: %d of %d frames", AfterCrouch, After))
check(In > 0 and NoSprintIn == In and AfterNoSprint == 0, string.format("NHBeatNoSprint: beat %d/%d, after %d/%d", NoSprintIn, In, AfterNoSprint, After))
local Life = LastSeam - First
check(Life > LENGTH + PAD + 2 and OutSeen, string.format("cut lived %.1f s (Length + TimeoutPad = %d s), beat %.1f s, blend out seen %s",
	Life, LENGTH + PAD, BeatB - BeatA, tostring(OutSeen)))
check(LastPath == "Open>Hold>Close", "path " .. tostring(LastPath))
local InWs = (function() for _, R in Rows do if R.t >= BeatA + 0.5 then return R.ws end end return -1 end)()
check(math.abs(Rows[#Rows].ws - Rows[1].ws) < 0.01, string.format("walk speed: before %.1f, in the beat %.1f, after %.1f", Rows[1].ws, InWs, Rows[#Rows].ws))
return (if Pass then "BEAT OK\n" else "BEAT FAIL\n") .. table.concat(Report, "\n")
