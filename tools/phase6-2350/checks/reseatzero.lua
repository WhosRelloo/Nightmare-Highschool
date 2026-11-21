-- reseatzero (final fix round): CineActor.Reseat with an _End clip that never loads (Length 0) must not move the root. Client VM, one call.
-- Uses a module copy of CineActor (self-contained state) and an id that is not an animation.
local Players = game:GetService("Players")
local Actor = require(Players.LocalPlayer.PlayerScripts.Controllers.CineActor)
local Root = Players.LocalPlayer.Character.HumanoidRootPart
local Before = Root.CFrame
local Moved = Actor.Reseat("Nothing", { X = 3; Z = 3; Yaw = 90 }, function() return "rbxassetid://1" end)
task.wait(0.3)
local D = (Root.Position - Before.Position).Magnitude
local Ok = Moved == false and D < 0.5
return (Ok and "RESEAT0 OK" or "RESEAT0 FAIL") .. string.format("\nReseat returned %s, root moved %.2f studs (want false, < 0.5)", tostring(Moved), D)
