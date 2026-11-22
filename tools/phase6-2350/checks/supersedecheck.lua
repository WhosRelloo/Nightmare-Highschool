-- supersedecheck (2.35.0, task 7 fix round 1, finding 5): a cut that starts during a seamless cut's 0.8 s blend-out
-- keeps its HUD fade, its NHCineSeam phase and its "Cine" lease (the old Finish must not hand them back over it).
-- Client VM, one call. The server holds the session until the client's Done (sent after the blend), so on "Out" this
-- sends Done itself and replays at once: the new Play lands mid-blend.
-- NEVER require game modules from here (execute_luau's own VM builds rogue copies).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local PG = Player.PlayerGui
local Cam = workspace.CurrentCamera
local Sessions = {}
local Conn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" then table.insert(Sessions, { Id = M.Session; At = os.clock() }) end end)
local Before = {}
for _, G in PG:GetChildren() do if G:IsA("LayerCollector") and G.Name ~= "NHCineUI" and G.Enabled then Before[G] = true end end
local function hudOn(): number
	local N = 0
	for G in Before do if G.Parent and G.Enabled and G.Name ~= "NHPhone" and G.Name ~= "ClassWaypoint" then N += 1 end end
	return N
end
Remote:FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
local T0 = os.clock()
repeat task.wait() until Player:GetAttribute("NHCineSeam") == "Out" or os.clock() - T0 > 35
local OutAt = os.clock()
Remote:FireServer({ Kind = "Done"; Session = Sessions[1] and Sessions[1].Id })
Remote:FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
repeat task.wait() until #Sessions >= 2 or os.clock() - OutAt > 3
local SecondAt = Sessions[2] and Sessions[2].At - OutAt
-- the old blend ends ~0.8 s after Out (+ the HUD's 0.4 s); then look at the new cut
task.wait(2.0)
local Mid = { seam = Player:GetAttribute("NHCineSeam"); cam = Cam.CameraType.Name; hud = hudOn() }
-- let the new cut play out
local T1 = os.clock()
repeat task.wait(0.1) until Player:GetAttribute("NHCineSeam") == nil and os.clock() - T1 > 1 or os.clock() - T1 > 30
task.wait(1.0)
Conn:Disconnect()
local End = { seam = Player:GetAttribute("NHCineSeam"); cam = Cam.CameraType.Name; hud = hudOn() }
local Total = 0
for G in Before do if G.Parent and G.Name ~= "NHPhone" and G.Name ~= "ClassWaypoint" then Total += 1 end end
local Ok = SecondAt ~= nil and SecondAt < 0.8 and Mid.seam == "Cut" and Mid.cam == "Scriptable" and Mid.hud == 0
	and End.seam == nil and End.cam == "Custom" and End.hud == Total
return string.format("%s\nsecond cut's Play %.0f ms after Out (inside the 0.8 s blend: %s)\n2 s later: seam %s, camera %s, HUD guis on %d (want Cut, Scriptable, 0)\nafter it: seam %s, camera %s, HUD guis on %d of %d",
	Ok and "SUPERSEDE OK" or "SUPERSEDE FAIL", (SecondAt or -1) * 1000, tostring(SecondAt ~= nil and SecondAt < 0.8),
	tostring(Mid.seam), Mid.cam, Mid.hud, tostring(End.seam), End.cam, End.hud, Total)
