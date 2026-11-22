-- tutorialclips (final fix round): the 66 published tutorial player clips (Config.CineClips; the KeyframeSequences in
-- ReplicatedStorage.NHCineClips.Tutorial are the source). Client VM, Play, one call. For each sequence: an id in Config.CineClips, it loads
-- (Length > 0) on the player's Animator, its Length is within 0.05 s of the sequence's and Looped equals the sequence's Loop. Also: a chain
-- piece's Loop in Config.TutorialAnim matches the published track's Looped.
local Players = game:GetService("Players")
local Folder = game.ReplicatedStorage.NHCineClips.Tutorial
local Clips = require(game.ReplicatedStorage.Config.CineClips)
local TA = require(game.ReplicatedStorage.Config.TutorialAnim)
local Animator = Players.LocalPlayer.Character:FindFirstChildWhichIsA("Humanoid", true):FindFirstChildOfClass("Animator")
local PieceLoop = {}
for _, Chain in TA.Chains do for _, P in Chain do PieceLoop[P.Piece] = P.Loop == true end end
local Fails, N, Done = {}, 0, 0
local Results = {}
for _, Seq in Folder:GetChildren() do
	if not Seq:IsA("KeyframeSequence") then continue end
	N += 1
	task.spawn(function()
		local Id = Clips[Seq.Name]
		local Len = 0
		for _, K in Seq:GetKeyframes() do Len = math.max(Len, K.Time) end
		if typeof(Id) ~= "string" or Id == "" then table.insert(Fails, Seq.Name .. ": no id in Config.CineClips") Done += 1 return end
		local A = Instance.new("Animation") A.AnimationId = Id
		local Ok, T = pcall(function() return Animator:LoadAnimation(A) end)
		if not Ok then table.insert(Fails, Seq.Name .. ": LoadAnimation " .. tostring(T)) Done += 1 return end
		local t0 = os.clock()
		while T.Length == 0 and os.clock() - t0 < 12 do task.wait(0.1) end
		if T.Length == 0 then table.insert(Fails, Seq.Name .. ": Length 0 after 12 s (" .. Id .. ")")
		else
			if math.abs(T.Length - Len) > 0.05 then table.insert(Fails, string.format("%s: Length %.3f vs sequence %.3f", Seq.Name, T.Length, Len)) end
			if T.Looped ~= Seq.Loop then table.insert(Fails, string.format("%s: Looped %s vs sequence Loop %s", Seq.Name, tostring(T.Looped), tostring(Seq.Loop))) end
			if PieceLoop[Seq.Name] ~= nil and PieceLoop[Seq.Name] ~= T.Looped then table.insert(Fails, string.format("%s: chain step loop %s vs track Looped %s", Seq.Name, tostring(PieceLoop[Seq.Name]), tostring(T.Looped))) end
		end
		T:Destroy() A:Destroy()
		Done += 1
	end)
end
local t0 = os.clock()
while Done < N and os.clock() - t0 < 60 do task.wait(0.2) end
local function pub(Name) local V = Clips[Name] return (typeof(V) == "string" and V ~= "") and V or "(none: Ctx.Clip would fall to the preview)" end
local Head = (#Fails == 0 and Done == N) and "CLIPS OK" or "CLIPS FAIL"
local Out = Head .. string.format("\n%d sequences, %d checked, %d failures", N, Done, #Fails)
if #Fails > 0 then Out ..= "\n" .. table.concat(Fails, "\n") end
return Out .. "\nCtx.Clip (Config.CineClips first) for TheBus1_WaitBored -> " .. pub("TheBus1_WaitBored") .. " ; FenceOver2 -> " .. pub("FenceOver2")
