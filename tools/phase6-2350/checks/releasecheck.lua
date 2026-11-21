-- Release-mid-chain check (Client VM, Play): the Skip path. Starts a chain through CineActor, calls Release part-way
-- through, and confirms no chain track keeps playing, Chain returned, and the controls are enabled again.
local Players = game:GetService("Players")
local Actor = require(Players.LocalPlayer.PlayerScripts.Controllers.CineActor)
local Folder = game.ReplicatedStorage.NHCineClips.Tutorial
local function resolve(Name)
	local Seq = Folder:FindFirstChild(Name)
	if not Seq then return nil end
	return Seq:GetAttribute("PreviewId") or tostring(game:GetService("AnimationClipProvider"):RegisterAnimationClip(Seq))
end
local C = Players.LocalPlayer.Character
local Animator = C.Humanoid.Animator
local Root = C.HumanoidRootPart
local WasAnchored = Root.Anchored
local Ids = {}
for _, Seq in Folder:GetChildren() do Ids[Seq:GetAttribute("PreviewId") or ""] = Seq.Name end
local function chainPlaying()
	local L = {}
	for _, T in Animator:GetPlayingAnimationTracks() do
		local N = T.Animation and Ids[T.Animation.AnimationId]
		if N then table.insert(L, N) end
	end
	return L
end
local Lines, Pass = {}, true
local Ok, Err = pcall(function()
	Root.Anchored = true
	for _, Case in { { "TheBus", 2.0 }, { "TheBus", 17.0 }, { "TheBus", 25.0 }, { "Drainpipe", 1.0 } } do -- in the loop, in the last piece, held at its end, in a one-shot
		local Chain, After = Case[1], Case[2]
		Actor.Begin()
		local Done = false
		task.spawn(function() Actor.Chain(Chain, resolve) Done = true end)
		task.wait(After)
		local Before = chainPlaying()
		Actor.Release()
		local T0 = os.clock()
		while not Done and os.clock() - T0 < 2 do task.wait() end
		task.wait(0.4) -- past any fade
		local Left = chainPlaying()
		local Ctl = require(Players.LocalPlayer.PlayerScripts:WaitForChild("PlayerModule")):GetControls()
		local Enabled = Ctl.activeController ~= nil and Ctl.activeController.enabled
		local CaseOk = Done and #Left == 0 and Enabled
		Pass = Pass and CaseOk
		table.insert(Lines, string.format("%s release at %.1f s: playing before {%s}; Chain returned %s (%.2f s); chain tracks still playing after 0.4 s: %d {%s}; controls enabled %s -> %s",
			Chain, After, table.concat(Before, ","), tostring(Done), os.clock() - T0, #Left, table.concat(Left, ","), tostring(Enabled), CaseOk and "ok" or "FAIL"))
	end
end)
pcall(Actor.Release)
Root.Anchored = WasAnchored
if not Ok then return "RELEASE ERROR\n" .. tostring(Err) end
return (Pass and "RELEASE OK\n" or "RELEASE FAIL\n") .. table.concat(Lines, "\n")
