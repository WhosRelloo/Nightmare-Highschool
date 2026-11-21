-- buscheck (2.35.0, task 10): the Bus cut end to end, from the client VM, ONE call (the cut is started and watched inside it).
-- TutorialEnter, stand the player on Stand, run this in the background, and 3 s later start the cut as the tutorial does
-- (bridge.py PlayCut $P '"TutorialBus"' false: not a replay, so the cut ends held). It waits up to 40 s for the cut.
-- Samples every frame and checks:
--   * the cast: the bus is the player's own copy (NHHometownCast), the shared source never moves, the copy comes in from
--     BusStart, stops on BusStop and leaves to BusAway; the copy has exactly one Animator;
--   * the clips: the group-owned ids LOAD in Play (Length > 0); at most 2 bus tracks playing at any frame (the one fading
--     out and the new one); none is left playing when the cut ends;
--   * the player's chain: TheBus1_WaitBored loops, TheBus2 starts near 16.15 s (the step on's shot at 15.8 s), and the
--     character is out of sight (LocalTransparencyModifier) from ~19.75 s until the hold is released;
--   * the alignment, MEASURED while the bus is parked (bones and marks, not the mesh): the DoorA/DoorB bone midpoint against
--     Stand (X) and the Stand..Board span (Z), and the lowest wheel point against the road (a raycast under each wheel);
--   * the hold (fix round 1): the bus tracks still playing on every held frame (the frozen title frame keeps its pose);
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
local Marks = workspace.NHCineSets.BusStop
local Align = nil -- measured once, while the bus is parked on its mark
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
-- the alignment samples run on Heartbeat (the Animator's Motor6D poses are applied by then); the bus is a rigid Motor6D rig, so
-- the joint parts (DoorA, DoorB, Wheel*) and the mesh pieces are read straight from their world positions, with EngineIdle (the
-- base loop) and the cut's clips playing:
--   Align: once, while the bus is parked on its mark (doors still shut): the DoorA/DoorB joint midpoint, the lowest wheel point
--   Leaves: once the DoorsOpen swing is complete (the DoorA joint turned > 80 deg): the world AABB of both door leaves and
--           their glass against the boarding line, a corridor 1.6 studs wide from Stand to Board
local function aabb(Part)
	local C, S = Part.CFrame, Part.Size
	local Lo, Hi = Vector3.one * math.huge, Vector3.one * -math.huge
	for _, X in { -1, 1 } do for _, Y in { -1, 1 } do for _, Z in { -1, 1 } do
		local P = (C * CFrame.new(X * S.X / 2, Y * S.Y / 2, Z * S.Z / 2)).Position
		Lo, Hi = Lo:Min(P), Hi:Max(P)
	end end end
	return Lo, Hi
end
local Leaves = nil
local AlignConn = RunService.Heartbeat:Connect(function()
	local Cast = workspace:FindFirstChild("NHHometownCast")
	local Bus = Cast and Cast:FindFirstChild("WFBlackBus")
	if not Bus then return end
	local function joint(N) local P = Bus:FindFirstChild(N) return P and P:IsA("BasePart") and P or nil end
	if not Align and math.abs(Bus:GetPivot().Position.X - Marks.BusStop.Position.X) < 0.05 then
		local A, B = joint("DoorA"), joint("DoorB")
		if A and B then
			local RP = RaycastParams.new()
			RP.FilterType = Enum.RaycastFilterType.Exclude
			RP.FilterDescendantsInstances = { Bus, Source, Cast, Player.Character }
			local Worst, Lowest, RoadAt = 0, math.huge, 0
			for _, W in { "WheelFL", "WheelFR", "WheelRL", "WheelRR" } do
				local Piece = Bus:FindFirstChild("WFBlackBus_" .. W)
				if Piece then
					local Low = Piece.Position.Y - Piece.Size.Y / 2
					local Hit = workspace:Raycast(Piece.Position + Vector3.new(0, 6, 0), Vector3.new(0, -30, 0), RP)
					if Hit then
						Worst = math.max(Worst, math.abs(Low - Hit.Position.Y))
						if Low < Lowest then Lowest, RoadAt = Low, Hit.Position.Y end
					end
				end
			end
			Align = { mid = (A.Position + B.Position) / 2; wheelWorst = Worst; lowest = Lowest; road = RoadAt }
		end
	end
	local Motor = nil
	for _, D in Bus:GetDescendants() do if D:IsA("Motor6D") and D.Name == "DoorA" then Motor = D end end
	if Align and Motor and math.abs(Bus:GetPivot().Position.X - Marks.BusStop.Position.X) < 0.05 then
		local _, Rad = Motor.Transform:ToAxisAngle()
		if math.deg(math.abs(Rad)) > 80 then
			local Stand, Board = Marks.Stand.Position, Marks.Board.Position
			local CLo = Vector3.new(Stand.X - 0.8, Stand.Y, Board.Z)
			local CHi = Vector3.new(Stand.X + 0.8, Stand.Y + 5.5, Stand.Z)
			local Sep, Who = math.huge, ""
			for _, N in { "WFBlackBus_DoorA", "WFBlackBus_DoorA_Glass", "WFBlackBus_DoorB", "WFBlackBus_DoorB_Glass" } do
				local P = Bus:FindFirstChild(N)
				if P then
					local Lo, Hi = aabb(P)
					-- separating gap from the corridor box (positive = clear, <= 0 = the leaf is in the way)
					local Gap = math.max(Lo.X - CHi.X, CLo.X - Hi.X, Lo.Y - CHi.Y, CLo.Y - Hi.Y, Lo.Z - CHi.Z, CLo.Z - Hi.Z)
					if Gap < Sep then Sep, Who = Gap, N end
				end
			end
			-- the worst (smallest) gap over every frame the leaves are open past 80 deg, bus parked
			if not Leaves or Sep < Leaves.clear then Leaves = { clear = Sep; who = Who; angle = math.max(Leaves and Leaves.angle or 0, math.deg(math.abs(Rad))) } end
		end
	end
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
		-- the asset's own loop flag (read before anything sets it), and that it DRIVES the Motor6D rig: some joint's Transform
		-- leaves identity while it plays
		local Flag = Ok and T.Looped
		local Moved = 0
		if Ok and Len > 0 then
			T.Priority = Enum.AnimationPriority.Action
			T:Play(0)
			local T1 = os.clock()
			while os.clock() - T1 < math.min(Len, 1.6) do
				for _, D in M:GetDescendants() do
					if D:IsA("Motor6D") then
						local X = D.Transform
						local _, Rad = X:ToAxisAngle()
						Moved = math.max(Moved, X.Position.Magnitude, math.abs(Rad))
					end
				end
				RunService.Heartbeat:Wait()
			end
			T:Stop(0)
		end
		local Want = (N == "BusEngineIdle" or N == "BusWipersSweep")
		table.insert(Loads, string.format("%s %s loop %s%s drives rig %s", N, Len > 0 and string.format("%.3fs", Len) or "FAILED", tostring(Flag), Flag == Want and "" or " WRONG", Moved > 1e-3 and "yes" or "NO"))
		if Flag ~= Want or Moved <= 1e-3 then table.insert(Loads, "FAILED " .. N .. " (loop flag or no motion)") end
		if Ok then T:Destroy() end
		A:Destroy()
	end
	M:Destroy()
end
task.wait(0.5)
local W0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - W0 > 3) or os.clock() - W0 > 70
task.wait(1.0)
RunService:UnbindFromRenderStep(Name)
AlignConn:Disconnect()
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
chk("tracks (at most 3 at a time)", MaxTracks <= 3 and MaxTracks >= 1, "max playing bus tracks (base loop + current + the one fading out) " .. MaxTracks)
chk("chain", Walk ~= nil and Two ~= nil and Two > 14.5 and Two < 18, string.format("TheBus1 loop from %s s, TheBus2 from %s s", f(Walk), f(Two)))
chk("you are out of sight after the doors close", Hid ~= nil and Hid > 19 and Hid < 21, "character hidden from " .. f(Hid) .. " s")
chk("hold", Hold ~= nil and EndRow.hold and #Tail >= 10 and Drift < 0.001, string.format("NHCineHold from %s s, %d held frames, camera drift %.5f", f(Hold), #Tail, Drift))
do
	local Stand, Board = Marks.Stand.Position, Marks.Board.Position
	local M = Align and Align.mid
	local DX = M and (M.X - Stand.X) or math.huge
	local Within = M and M.Z <= Stand.Z + 0.3 and M.Z >= Board.Z - 0.3
	chk("doorway (bones vs marks)", M ~= nil and math.abs(DX) <= 0.5 and Within == true,
		M and string.format("DoorA/DoorB midpoint (%.2f, %.2f, %.2f): dX to Stand %.2f, Z %.2f between Stand %.2f and Board %.2f", M.X, M.Y, M.Z, DX, M.Z, Stand.Z, Board.Z) or "no sample")
	chk("door leaves clear the boarding line (DoorsOpen done)", Leaves ~= nil and Leaves.clear >= 0,
		Leaves and string.format("door joint turned %.0f deg; nearest leaf piece %s is %.2f studs from the 1.6-wide Stand-Board corridor (worst frame)", Leaves.angle, Leaves.who, Leaves.clear) or "DoorsOpen never completed")
	chk("wheels on the road", Align ~= nil and Align.wheelWorst <= 0.25,
		Align and string.format("lowest wheel point %.2f, road %.2f, worst wheel to road %.2f studs", Align.lowest, Align.road, Align.wheelWorst) or "no sample")
end
local HeldPlaying, HeldRows = math.huge, 0
for _, R in Rows do
	if R.hold then HeldRows += 1 HeldPlaying = math.min(HeldPlaying, R.playing) end
end
local NoClip = 0
for _, R in Rows do if R.bus and R.playing == 0 then NoClip += 1 end end
chk("a clip plays on every frame the copy exists (the base loop)", NoClip <= 1, NoClip .. " frames with the copy and no playing track")
chk("bus tracks stay up through the hold", HeldRows >= 10 and HeldPlaying >= 1, string.format("%d held frames, fewest playing bus tracks %s", HeldRows, tostring(HeldPlaying)))
chk("title", TitleRow ~= nil and TitleRow.cardText == "NIGHTMARE HIGHSCHOOL" and TitleRow.cardSize >= 20, string.format("card '%s' size %s", TitleRow and TitleRow.cardText or "none", TitleRow and tostring(TitleRow.cardSize) or "?"))
chk("still out of sight at the end (the caller releases)", EndRow.ltm >= 0.99, "LocalTransparencyModifier " .. EndRow.ltm)
return (Pass and "BUS OK\n" or "BUS FAIL\n") .. table.concat(Report, "\n")
