-- replayrefused (task 11 fix round 1, ruling I4): TutorialSneak and TutorialBus have Replay = false, so a journal Replay of either is
-- refused even once seen. Client VM, one call. Mark both Seen first (bridge.py CineMark $P '"TutorialSneak"' '"Seen"', same for
-- TutorialBus), clear them after. Fires a Replay for each and sees no Play message and no cut state for 2 s each.
local Player = game:GetService("Players").LocalPlayer
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Out, Pass = {}, true
for _, Id in { "TutorialSneak", "TutorialBus" } do
	local Got = false
	local Conn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" then Got = true end end)
	Remote:FireServer({ Kind = "Replay"; Id = Id })
	task.wait(2)
	Conn:Disconnect()
	local Ok = not Got and Player:GetAttribute("NHCineSeam") == nil
	Pass = Pass and Ok
	table.insert(Out, string.format("%s replay: Play message %s, seam %s %s", Id, tostring(Got), tostring(Player:GetAttribute("NHCineSeam")), Ok and "ok" or "FAIL"))
end
return (Pass and "REPLAY REFUSED OK\n" or "REPLAY ACCEPTED FAIL\n") .. table.concat(Out, "\n")
