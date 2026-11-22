-- sneakedge (task 11): the held crouch. Part 1 (this call): TutorialSneak running, you stand up FAR from Biscuit (a BeatCrouch Off at
-- the start of the Garden beat): the crouch must come back by itself within ~2 s and "Stay low." must show once. The cut is left
-- running: the caller then runs bridge.py TutorialLeave and sneakafter.lua (the crouch goes, the cut and Biscuit's extra tracks are gone).
-- (fix round 1) TutorialSneak is a first viewing now (Replay = false): TutorialEnter first, start this script in the background, then ~4 s
-- later bridge.py PlayCut $P '"TutorialSneak"' false (and clear the mark afterwards: bridge.py CineMark $P '"TutorialSneak"' nil).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Char = Player.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local Root = Char.HumanoidRootPart
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
Root.CFrame = CFrame.lookAt(Vector3.new(3994, 3, 4104), Vector3.new(4012, 3, 4082))
Root.AssemblyLinearVelocity = Vector3.zero
Player:SetAttribute("NHCinePath", nil)
workspace:WaitForChild("Hometown"):WaitForChild("Garden"):WaitForChild("WFBiscuit")
task.wait(1.5)
local T0 = os.clock()
repeat task.wait(0.1) until Player:GetAttribute("NHCineSeam") == "Beat" or os.clock() - T0 > 40
task.wait(2.0) -- the beat's crouch has landed
local Before = Hum:GetAttribute("Crouch") == true
local Said, DownAt, BackAt, WasDown = false, nil, nil, false
local Conn = RunService.RenderStepped:Connect(function()
	local G = Player.PlayerGui:FindFirstChild("NHCineUI")
	if G then for _, D in G:GetDescendants() do if D:IsA("TextLabel") and D.Text == "Stay low." and D.Visible then Said = true end end end
	if DownAt and Hum:GetAttribute("Crouch") ~= true then WasDown = true end
	if WasDown and Hum:GetAttribute("Crouch") == true and not BackAt then BackAt = os.clock() end
end)
Remote:FireServer({ Kind = "BeatCrouch"; On = false })
DownAt = os.clock()
task.wait(3)
Conn:Disconnect()
local Near = (Root.Position - Vector3.new(4014, 0, 4093)).Magnitude
return string.format("crouch before %s; back after %.2f s (%s); 'Stay low.' shown %s; path %s; %.1f studs from Biscuit; seam %s",
	tostring(Before), BackAt and BackAt - DownAt or -1, tostring(BackAt ~= nil), tostring(Said), tostring(Player:GetAttribute("NHCinePath")), Near, tostring(Player:GetAttribute("NHCineSeam")))
