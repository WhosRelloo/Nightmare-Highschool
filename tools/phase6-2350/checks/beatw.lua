-- beatw (2.35.0, task 8): W moves you during a walk-and-talk beat (the controls stay on). Real key input can't come from
-- execute_luau (VirtualInputManager needs RobloxScript), so this is three steps:
--   1. client.py beatw.lua               (STEP = "start": plays __SeamlessTest, returns once NHCineSeam is "Beat")
--   2. Studio MCP user_keyboard_input    keyDown W, wait 1000 ms, keyUp W (Client)
--   3. sed 's/^local STEP = "start"/local STEP = "end"/' beatw.lua > beatw_end.lua; client.py beatw_end.lua
-- Wait for the cut to finish (step 3 does) and ~1.5 s more before the next replay: the server still holds the session
-- until the client's Done.
local STEP = "start"
local Player = game:GetService("Players").LocalPlayer
local Root = Player.Character:WaitForChild("HumanoidRootPart")
if STEP == "start" then
	game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
	local T0 = os.clock()
	repeat task.wait(0.03) until Player:GetAttribute("NHCineSeam") == "Beat" or os.clock() - T0 > 25
	Player:SetAttribute("BeatWP0", Root.Position)
	Player:SetAttribute("BeatWT0", os.clock())
	return string.format("seam %s, path %s", tostring(Player:GetAttribute("NHCineSeam")), tostring(Player:GetAttribute("NHCinePath")))
end
local P0 = Player:GetAttribute("BeatWP0")
local D = (Vector3.new(Root.Position.X, 0, Root.Position.Z) - Vector3.new(P0.X, 0, P0.Z)).Magnitude
local Dt = os.clock() - Player:GetAttribute("BeatWT0")
local Seam, Path = Player:GetAttribute("NHCineSeam"), Player:GetAttribute("NHCinePath")
Player:SetAttribute("BeatWP0", nil)
Player:SetAttribute("BeatWT0", nil)
local T0 = os.clock()
repeat task.wait(0.1) until Player:GetAttribute("NHCineSeam") == nil or os.clock() - T0 > 20
task.wait(1.5)
local Ok = D > 4 and (Seam == "Beat" or Seam == "BeatOut") and typeof(Path) == "string" and Path:find(">Walk", 1, true) ~= nil
return string.format("%s\nW moved %.2f studs in %.2f s since the beat began; seam at the read %s; path %s; final path %s; camera after %s",
	Ok and "BEATW OK" or "BEATW FAIL", D, Dt, tostring(Seam), tostring(Path), tostring(Player:GetAttribute("NHCinePath")),
	workspace.CurrentCamera.CameraType.Name)
