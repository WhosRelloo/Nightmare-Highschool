-- buscheck (2.35.0, task 10): the Bus cut end to end, from the client VM, ONE call (the cut is started and watched inside it).
-- Mark it Seen first (bridge.py CineMark $P '"TutorialBus"' '"Seen"'), TutorialEnter, and stand the player on Stand.
-- Samples every frame and checks:
--   * the cast: the bus is the player's own copy (NHHometownCast), the shared source never moves, the copy comes in from
--     BusStart, stops on BusStop and leaves to BusAway; the copy has exactly one Animator;
--   * the clips: the group-owned ids LOAD in Play (Length > 0); at most 2 bus tracks playing at any frame (the one fading
--     out and the new one); none is left playing when the cut ends;
--   * the player's chain: TheBus1_WaitBored loops, TheBus2 starts near 16.15 s (the step on's shot at 15.8 s), and the
--     character is out of sight (LocalTransparencyModifier) from ~19.75 s until the hold is released;
--   * the end: NHCineHold set, the title card up (text, rendered text height >= 20 px), the camera frozen;
--   * the release: TutorialLeave (done by the caller after this returns) must put everything back.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Clips = require(game.ReplicatedStorage.Config.CineClips)
local Tutorial = game.ReplicatedStorage.NHCineClips:FindFirstChild("Tutorial")
local Rows = {}
local Name = "BusCheck_" .. math.random(1e6)
local Source = workspace.Hometown.BlackBus:FindFirstChild("WFBlackBus")
local SourceStart = Source:GetPivot().Position
local function previewId(N)
	local S = Tutorial and Tutorial:FindFirstChild(N)
	return S and tostring(S:GetAttribute("PreviewId")) or nil
end
local Ids = { TheBus1_WaitBored = previewId("TheBus1_WaitBored"); TheBus2 = previewId("TheBus2") }
local function chainTracks()
	local C = Player.Character
	local A = C and C:FindFirstChildWhichIsA("Animator", true)
	local L = {}
	if A then
		for _, T in A:GetPlayingAnimationTracks() do
			local Id = T.Animation and T.Animation.AnimationId or ""
			for N, P in Ids do
				if P and (Id == P or Id == "rbxassetid://" .. P) then L[N] = true end
			end
		end
	end
	return L
end
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local Cast = workspace:FindFirstChild("NHHometownCast")
	local Bus = Cast and Cast:FindFirstChild("WFBlackBus")
	local Playing, Animators = 0, 0
	if Bus then
		for _, D in Bus:GetDescendants() do
			if D:IsA("Animator") then
				Animators += 1
				for _ in D:GetPlayingAnimationTracks() do Playing += 1 end
			end
		end
	end
	local Char = Player.Character
	local Head = Char and Char:FindFirstChild("Head")
	local UI = Player.PlayerGui:FindFirstChild("NHCineUI")
	local Title = UI and UI:FindFirstChild("Title", true)
	local Card = UI and UI:FindFirstChild("Card")
	table.insert(Rows, {
		t = os.clock(); seam = Player:GetAttribute("NHCineSeam"); hold = Player:GetAttribute("NHCineHold") == true;
		bus = Bus and Bus:GetPivot().Position; playing = Playing; animators = Animators;
		ltm = Head and Head.LocalTransparencyModifier or 0; chain = chainTracks();
		card = Card and Card.GroupTransparency or 1; cardText = Title and Title.Text or ""; cardSize = Title and Title.TextBounds.Y or 0;
		cam = workspace.CurrentCamera.CFrame; src = Source:GetPivot().Position;
	})
end)
-- the clips load in Play: LoadAnimation on a throwaway copy of the rig
local Loads = {}
do
	local M = Source:Clone()
	M.Parent = workspace
	local An = M:FindFirstChildWhichIsA("Animator", true)
	for _, N in { "BusBrakeStop", "BusDoorsOpen", "BusDoorsClose", "BusDriverTurn", "BusEngineIdle", "BusPullAway", "BusWipersSweep" } do
		local A = Instance.new("Animation")
		A.AnimationId = Clips[N]
		local Ok, T = pcall(function() return An:LoadAnimation(A) end)
		local Len = Ok and T.Length or 0
		for _ = 1, 20 do
			if Len > 0 then break end
			task.wait(0.1)
			Len = Ok and T.Length or 0
		end
		table.insert(Loads, string.format("%s %s", N, Len > 0 and string.format("%.3fs", Len) or "FAILED"))
		if Ok then T:Destroy() end
		A:Destroy()
	end
	M:Destroy()
end
task.wait(0.5)
game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "TutorialBus" })
local W0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - W0 > 3) or os.clock() - W0 > 45
task.wait(1.0)
RunService:UnbindFromRenderStep(Name)
local Report, Pass = { "clips in Play: " .. table.concat(Loads, ", ") }, true
for _, L in Loads do if L:find("FAILED") then Pass = false end end
local Start = nil
for _, R in Rows do if R.seam ~= nil then Start = R.t break end end
if not Start then return "BUS FAIL\nthe cut never started\n" .. table.concat(Report, "\n") end
local function at(Fn) for _, R in Rows do if Fn(R) then return R.t - Start end end return nil end
local Walk = at(function(R) return R.chain.TheBus1_WaitBored end)
local Two = at(function(R) return R.chain.TheBus2 end)
local Hid = at(function(R) return R.ltm >= 0.99 end)
local Hold = at(function(R) return R.hold end)
local Stop = workspace.NHCineSets.BusStop.BusStop.Position
local Away = workspace.NHCineSets.BusStop.BusAway.Position
local Frames, MaxTracks, MaxAnimators, SourceMoved = 0, 0, 0, 0
for _, R in Rows do
	if R.bus then Frames += 1 end
	MaxTracks = math.max(MaxTracks, R.playing)
	MaxAnimators = math.max(MaxAnimators, R.animators)
	SourceMoved = math.max(SourceMoved, (R.src - SourceStart).Magnitude)
end
-- the bus's settle: the first time it is within 0.05 stud of the stop's X and stays there
local Stopped = nil
for _, R in Rows do
	if R.bus then
		if math.abs(R.bus.X - Stop.X) < 0.05 then Stopped = Stopped or (R.t - Start) else Stopped = nil end
		if R.t - Start > 12 then break end
	end
end
local EndBus = nil
for i = #Rows, 1, -1 do if Rows[i].bus then EndBus = Rows[i].bus break end end
local EndRow = Rows[#Rows]
local TitleRow = nil
for i = #Rows, 1, -1 do if Rows[i].cardText ~= "" and Rows[i].card < 0.1 then TitleRow = Rows[i] break end end
local Tail = {}
for i = #Rows, 1, -1 do
	if Rows[i].seam ~= nil then break end
	table.insert(Tail, Rows[i])
end
local Drift = 0
for _, R in Tail do Drift = math.max(Drift, (R.cam.Position - Tail[1].cam.Position).Magnitude) end
local function chk(Label, Ok, Detail)
	Pass = Pass and Ok
	table.insert(Report, string.format("%s %s: %s", Ok and "ok  " or "FAIL", Label, Detail))
end
local function f(N, Fmt) return N and string.format(Fmt or "%.2f", N) or "?" end
chk("own copy", Frames > 100 and SourceMoved < 0.01, string.format("copy sampled %d frames, shared source moved %.3f studs", Frames, SourceMoved))
chk("one Animator", MaxAnimators == 1, "animators on the copy " .. MaxAnimators)
chk("bus arrives and stops", Stopped ~= nil and Stopped > 4 and Stopped < 9, "settled on BusStop's X at " .. f(Stopped) .. " s")
chk("bus leaves", EndBus ~= nil and EndBus.X < Stop.X - 80, string.format("final X %.1f (stop %.1f, away %.1f)", EndBus and EndBus.X or 0, Stop.X, Away.X))
chk("tracks (at most 2 at a time)", MaxTracks <= 2 and MaxTracks >= 1, "max playing bus tracks " .. MaxTracks)
chk("bus tracks gone at the end", EndRow.playing == 0, "playing at the end " .. EndRow.playing)
chk("chain", Walk ~= nil and Two ~= nil and Two > 14.5 and Two < 18, string.format("TheBus1 loop from %s s, TheBus2 from %s s", f(Walk), f(Two)))
chk("you are out of sight after the doors close", Hid ~= nil and Hid > 19 and Hid < 21, "character hidden from " .. f(Hid) .. " s")
chk("hold", Hold ~= nil and EndRow.hold and #Tail >= 10 and Drift < 0.001, string.format("NHCineHold from %s s, %d held frames, camera drift %.5f", f(Hold), #Tail, Drift))
chk("title", TitleRow ~= nil and TitleRow.cardText == "NIGHTMARE HIGHSCHOOL" and TitleRow.cardSize >= 20, string.format("card '%s' size %s", TitleRow and TitleRow.cardText or "none", TitleRow and tostring(TitleRow.cardSize) or "?"))
chk("still out of sight at the end (the caller releases)", EndRow.ltm >= 0.99, "LocalTransparencyModifier " .. EndRow.ltm)
return (Pass and "BUS OK\n" or "BUS FAIL\n") .. table.concat(Report, "\n")
