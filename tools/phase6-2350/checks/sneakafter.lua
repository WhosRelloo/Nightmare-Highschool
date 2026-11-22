-- sneakafter (task 11): after TutorialLeave mid-cut (sneakedge.lua): the cut is over, the crouch is gone, nothing of the cut is left
-- on Biscuit but his sleep loop, and the lamp prop is gone.
local Players = game:GetService("Players")
local Player = Players.LocalPlayer
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
task.wait(2.5)
local Cast = workspace:FindFirstChild("NHHometownCast")
local B = Cast and Cast:FindFirstChild("WFBiscuit")
local A = B and B:FindFirstChildWhichIsA("Animator", true)
local N, Ids = 0, {}
if A then for _, T in A:GetPlayingAnimationTracks() do N += 1 table.insert(Ids, T.Animation.AnimationId) end end
return string.format("seam %s; crouch %s; walk speed %.1f; cast folder %s; Biscuit tracks %d %s; lamp %s; NHBeatNoSprint %s",
	tostring(Player:GetAttribute("NHCineSeam")), tostring(Hum:GetAttribute("Crouch")), Hum.WalkSpeed, tostring(Cast ~= nil), N, table.concat(Ids, ","),
	tostring(workspace:FindFirstChild("NHCineActors") ~= nil), tostring(Player:GetAttribute("NHBeatNoSprint")))
