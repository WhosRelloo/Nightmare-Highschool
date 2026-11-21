-- sneakcheck (2.35.0, task 11; fix round 1): TutorialSneak end to end from the client VM, ONE call (the cut is watched here).
-- The cut is a FIRST VIEWING (TutorialSneak has Replay = false: a journal replay is refused), started from outside the way the
-- tutorial does: with TutorialEnter done and the cut NOT marked Seen, start this script in the background, then ~3 s later
--   bridge.py PlayCut $P '"TutorialSneak"' false        (modes sneak and fail: not skippable)
--   bridge.py PlayCut $P '"TutorialSneak"' true         (mode skipfence: skippable, so the Skip below is accepted)
-- MODE "sneak": crouch-walk Start -> FenceZone (never within 8 studs of Biscuit); MODE "fail": walk toward Biscuit, stand up
-- (BeatCrouch Off) within 7 studs, wait out Hide, then on to the fence; MODE "skipfence": as sneak, but 0.6 s into the Fence segment
-- (before FenceOver2 stands you) send a Skip: you must not be left crouched. Samples every frame and reports:
--   * path (Garden>Fence, or Garden>Hide>Garden>Fence)
--   * Biscuit (ruling I3): the player's cast copy exists BEFORE the cut, and has a clip playing on every frame before the cut, during it,
--     in its Out phase and after it (0 frames of N with none, per bucket)
--   * the crouch: held through the Garden beat; the walk speed on the Garden beat (4.9 = 0.7 x the crouch speed 7), the same on the
--     second Garden pass after a soft fail (I1)
--   * the lamp: on at the wuff and back to 1 (off) after the sigh (M1)
--   * the fence (C1): the torso faces the fence as FenceOver2 starts; the dip's root jump happens under a black veil; you end on the far
--     side of the fence plane, at least 1 stud clear of it, facing away from the house, standing
--   * the end: NHCineSeam back to nil, controls handed back; the timeline and the Fence segment's own length (for FENCE_DUR)
local MODE = "sneak"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Char = Player.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local Root = Char.HumanoidRootPart
local StartPos = Vector3.new(3994, 3, 4104)
Root.CFrame = CFrame.lookAt(StartPos, Vector3.new(4012, 3, 4081))
Root.AssemblyLinearVelocity = Vector3.zero
Player:SetAttribute("NHCinePath", nil)
local Marks = workspace:WaitForChild("NHCineSets"):WaitForChild("Garden")
local Fence, BiscuitMark = Marks:WaitForChild("FenceZone").Position, Marks:WaitForChild("Biscuit").Position
local Garden = workspace:WaitForChild("Hometown"):WaitForChild("Garden")
Garden:WaitForChild("WFBiscuit")
-- the fence plane: the far face of the fence and the gate (their collidable parts' smallest Z)
local FarFace = math.huge
for _, N in { "WFPicketFence", "WFPicketGate" } do
	local M = Garden:WaitForChild(N)
	for _, D in M:GetDescendants() do
		if D:IsA("BasePart") and D.CanCollide and D.Size.Y > 0.5 then FarFace = math.min(FarFace, D.Position.Z - D.Size.Z / 2) end
	end
end
local Clips = require(game.ReplicatedStorage.Config.CineClips)
local Names = {}
for K, V in Clips do if typeof(V) == "string" then Names[(V:gsub("rbxassetid://", ""))] = K end end
local Tut = game.ReplicatedStorage.NHCineClips:FindFirstChild("Tutorial")
if Tut then for _, S in Tut:GetChildren() do local P = S:GetAttribute("PreviewId") if P then Names[tostring(P)] = S.Name end end end
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Session
local PlayConn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" and M.Id == "TutorialSneak" then Session = M.Session end end)

Root.CFrame = CFrame.lookAt(Marks.Start.Position + Vector3.new(0, 3, 0), Fence + Vector3.new(0, 3, 0))
Root.AssemblyLinearVelocity = Vector3.zero
task.wait(1.5)
local Rows, Name = {}, "SneakCheck_" .. math.random(1e6)
local FailAt, Stood, Returned = nil, false, false
local function biscuit()
	local C = workspace:FindFirstChild("NHHometownCast")
	local B = C and C:FindFirstChild("WFBiscuit")
	local A = B and B:FindFirstChildWhichIsA("Animator", true)
	local L = {}
	if A then for _, T in A:GetPlayingAnimationTracks() do
		local Id = T.Animation and (T.Animation.AnimationId:gsub("rbxassetid://", "")) or ""
		table.insert(L, (Names[Id] or Id) .. (T.Length > 0 and "" or "(len0)"))
	end end
	return B ~= nil, A ~= nil, L
end
local Began, SkipAt = false, nil
RunService:BindToRenderStep(Name .. "Walk", Enum.RenderPriority.Input.Value + 1, function()
	local Ph = Player:GetAttribute("NHCineSeam")
	if Ph ~= nil then Began = true end
	local Path = Player:GetAttribute("NHCinePath") or ""
	if MODE == "skipfence" and Path:match("Fence$") and Ph ~= nil and not SkipAt then
		SkipAt = os.clock()
		task.delay(0.6, function() Remote:FireServer({ Kind = "Skip"; Session = Session }) end)
	end
	if not Began or not (Ph == "In" or Ph == "Beat" or Ph == "BeatIn") then return end
	local Goal = Fence
	if MODE == "fail" and not Returned then
		if Path == "Garden" then
			Goal = BiscuitMark
			if (Root.Position - BiscuitMark).Magnitude < 7 and not Stood then
				Stood = true
				FailAt = os.clock()
				Remote:FireServer({ Kind = "BeatCrouch"; On = false }) -- stand up, deliberately, near him
			end
		elseif Path:match("Hide") then Returned = true end
	end
	local D = (Goal - Root.Position) * Vector3.new(1, 0, 1)
	if D.Magnitude > 0.5 and not Path:match("Fence$") then Hum:Move(D.Unit, false) end
end)
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local Has, Anim, L = biscuit()
	local Lamp = workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineProp_BedroomLight")
	local Ui = Player.PlayerGui:FindFirstChild("NHCineUI")
	local Veil = Ui and Ui:FindFirstChild("Veil", true)
	local Torso = Char:FindFirstChild("Torso")
	table.insert(Rows, { t = os.clock(); seam = Player:GetAttribute("NHCineSeam"); path = Player:GetAttribute("NHCinePath"); crouch = Hum:GetAttribute("Crouch") == true;
		ws = Hum.WalkSpeed; pos = Root.Position; rl = Root.CFrame.LookVector; head = Char.Head.Position; tl = Torso and Torso.CFrame.LookVector or Root.CFrame.LookVector;
		has = Has; anim = Anim; clips = L; lamp = Lamp and Lamp.Transparency or nil; veil = Veil and Veil.BackgroundTransparency or 1;
		dist = (Root.Position - BiscuitMark).Magnitude; cam = workspace.CurrentCamera.CFrame.Position; look = workspace.CurrentCamera.CFrame.LookVector; vel = Root.AssemblyLinearVelocity.Magnitude })
end)
-- wait for the caller to start the cut; sampling has run since here (the BEFORE bucket)
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 6) or os.clock() - T0 > 90
task.wait(1.5)
RunService:UnbindFromRenderStep(Name)
RunService:UnbindFromRenderStep(Name .. "Walk")
PlayConn:Disconnect()
Hum:Move(Vector3.zero)

local Rep = {}
local function add(S) table.insert(Rep, S) end
local LastPath, Frames = nil, 0
local FirstSeam, LastSeam
for _, R in Rows do
	if R.path then LastPath = R.path end
	if R.seam then FirstSeam = FirstSeam or R.t LastSeam = R.t end
end
-- buckets (I3): before the cut starts, during it (every phase but Out), its Out phase, after it
local B = { before = { n = 0, cast = 0, noclip = 0 }, during = { n = 0, cast = 0, noclip = 0 }, out = { n = 0, cast = 0, noclip = 0 }, after = { n = 0, cast = 0, noclip = 0 } }
local Seen, MinDist = {}, math.huge
local CrouchBeat, CrouchHeld = 0, 0
local LampMin, LampMax, LampOnAt, LampOffAfter = 1, 0, nil, false
local Ws1, Ws2 = {}, {}
for I, R in Rows do
	local K
	if not FirstSeam or R.t < FirstSeam then K = "before" elseif R.seam == "Out" then K = "out" elseif R.seam then K = "during" else K = "after" end
	local X = B[K]
	X.n += 1
	if R.has then X.cast += 1 if #R.clips == 0 then X.noclip += 1 end end
	if K == "during" then
		Frames += 1
		MinDist = math.min(MinDist, R.dist)
		for _, N in R.clips do Seen[N] = (Seen[N] or 0) + 1 end
	end
	if R.seam == "Beat" and R.path == "Garden" and (not FailAt or R.t < FailAt) and R.t > (FirstSeam or 0) + 1.5 then
		CrouchBeat += 1 if R.crouch then CrouchHeld += 1 end
		if R.vel > 1 and R.t > (FirstSeam or 0) + 2.5 then table.insert(Ws1, R.ws) end
	end
	if R.seam == "Beat" and R.path == "Garden>Hide>Garden" and R.vel > 1 then table.insert(Ws2, R.ws) end
	if R.lamp then
		LampMin = math.min(LampMin, R.lamp) LampMax = math.max(LampMax, R.lamp)
		if R.lamp <= 0.05 and not LampOnAt then LampOnAt = I end
		if LampOnAt and R.lamp >= 0.99 then LampOffAfter = true end
	end
end
local function median(L) table.sort(L) return L[math.ceil(#L / 2)] end
local Pass = true
local function check(Ok, S) Pass = Pass and Ok add(S .. (Ok and " ok" or " FAIL")) end
local WantPath = if MODE == "fail" then "Garden>Hide>Garden>Fence" else "Garden>Fence"
check(LastPath == WantPath, "path " .. tostring(LastPath) .. " (want " .. WantPath .. ")")
for _, K in { "before", "during", "out", "after" } do
	local X = B[K]
	-- the cast copy is there on EVERY frame of every bucket (Hometown casts him when NHTutorial is set, before the cut) and has a
	-- clip playing on every one of them (an Out phase can be a frame or two; a run with none is not a failure)
	check((X.n == 0 and K == "out") or (X.n > 0 and X.cast == X.n and X.noclip == 0), string.format("Biscuit %s the cut: cast copy on %d of %d frames, %d of them with NO clip playing", K, X.cast, X.n, X.noclip))
end
local L = {}
for N, C in Seen do table.insert(L, N .. " " .. C) end
table.sort(L)
add("clips seen during the cut: " .. table.concat(L, ", "))
if MODE ~= "skipfence" then
	check((MODE == "fail" and CrouchBeat == 0) or (CrouchBeat > 0 and CrouchHeld >= CrouchBeat * 0.95), string.format("crouch held %d of %d Garden-beat frames (before any stand-up)", CrouchHeld, CrouchBeat))
	local W1 = median(Ws1)
	check(W1 ~= nil and math.abs(W1 - 4.9) < 0.4, string.format("walk speed on the Garden beat %s (want 4.9 = 0.7 x crouch speed 7), %d moving frames", tostring(W1), #Ws1))
	if MODE == "fail" then
		local W2 = median(Ws2)
		check(W2 ~= nil and W1 ~= nil and math.abs(W2 - W1) < 0.4, string.format("walk speed on the second Garden pass %s (want the first pass's %s), %d moving frames", tostring(W2), tostring(W1), #Ws2))
	end
end
if MODE == "sneak" then
	check(MinDist > 8, string.format("closest approach to Biscuit %.2f studs", MinDist))
	check(LampMax == 0 or LampMax == 1 and LampMin == 1, string.format("lamp stayed off (min %.2f max %.2f)", LampMin, LampMax))
elseif MODE == "fail" then
	check(LampMin == 0 and LampMax == 1, string.format("lamp went on and off again (min %.2f max %.2f)", LampMin, LampMax))
	check(LampOnAt ~= nil and LampOffAfter, string.format("lamp back to transparency 1 after it was 0 (on at row %s, off afterwards %s)", tostring(LampOnAt), tostring(LampOffAfter)))
	check(Stood, "stood up near him")
end
local Last = Rows[#Rows]
if MODE == "skipfence" then
	-- I2: the skip landed before FenceOver2 stood you; you must not be left crouched
	local Crouched = false
	for _, R in Rows do if R.path and R.path:match("Fence$") and R.seam and R.crouch then Crouched = true break end end
	check(SkipAt ~= nil and Crouched, "the skip was sent while you were still crouched in the Fence segment")
	check(not Last.crouch, string.format("after the skip: crouch %s (want false)", tostring(Last.crouch)))
	check(Last.seam == nil and Last.ws > 12, string.format("after the skip: seam %s, walk speed %.1f (want nil, > 12)", tostring(Last.seam), Last.ws))
	add(string.format("cut lived %.1f s, %d frames", (LastSeam or 0) - (FirstSeam or 0), #Rows))
	return (Pass and "SNEAK OK\n" or "SNEAK FAIL\n") .. table.concat(Rep, "\n")
end
-- the fence (C1)
do
	local Fi, F0
	for I = 2, #Rows do
		if Rows[I].path and Rows[I].path:match("Fence$") and Rows[I].seam then F0 = F0 or I end
		if Rows[I].path and Rows[I].path:match("Fence$") and Rows[I - 1].crouch and not Rows[I].crouch then Fi = I break end
	end
	if Fi then
		-- the stand-up under the chain's pose: head-vs-root step there
		local W, RY = 0, 0
		for I = Fi - 2, Fi + 3 do
			local A, Bz = Rows[I - 1], Rows[I]
			W = math.max(W, ((Bz.head - Bz.pos) - (A.head - A.pos)).Magnitude)
			RY = math.max(RY, math.abs(Bz.pos.Y - A.pos.Y))
		end
		add(string.format("fence: crouch dropped at frame %d; head-vs-root step there %.3f, root Y step %.3f", Fi, W, RY))
		-- the body faces the fence as FenceOver2 starts: torso heading (0 = facing -Z, positive = left) within 15 degrees
		local T = Rows[Fi].tl
		local Heading = math.deg(math.atan2(-T.X, -T.Z))
		check(math.abs(Heading) < 15, string.format("the torso faces the fence as FenceOver2 starts: heading %.1f degrees (want within 15 of 0)", Heading))
	else check(false, "fence: crouch never dropped in the Fence segment") end
	-- the dip: the root jumps (more than 2 studs in a frame) under a black veil
	local Jumps = {}
	for I = 2, #Rows do
		local D = (Rows[I].pos - Rows[I - 1].pos) * Vector3.new(1, 0, 1)
		if Rows[I].path and Rows[I].path:match("Fence$") and D.Magnitude > 2 then table.insert(Jumps, { I = I, D = D.Magnitude, veil = math.min(Rows[I].veil, Rows[I - 1].veil) }) end
	end
	local Dip = Jumps[1]
	check(Dip ~= nil and Dip.veil <= 0.05, string.format("the dip's root jump (%s studs) happens under a black veil (veil transparency %s)", Dip and string.format("%.2f", Dip.D) or "none", Dip and string.format("%.2f", Dip.veil) or "-"))
	-- the end: the far side of the fence plane, at least 1 stud clear, facing away from the house, standing
	local End = Last.pos
	check(End.Z <= FarFace - 1, string.format("ends on the far side: root z %.2f, the fence's far face z %.2f (%.2f studs clear, want >= 1)", End.Z, FarFace, FarFace - End.Z))
	check(Last.rl.Z < -0.8, string.format("faces away from the house: look z %.2f (want < -0.8)", Last.rl.Z))
	check(not Last.crouch, "standing at the end")
	local P0
	for _, R in Rows do if R.path and R.path:match("Fence$") and not P0 then P0 = R.pos end end
	add(string.format("fence: root at the segment start (%.2f, %.2f, %.2f), at the end (%.2f, %.2f, %.2f); fence far face z %.2f", P0.X, P0.Y, P0.Z, End.X, End.Y, End.Z, FarFace))
	-- the Fence segment's own length (for FENCE_DUR): from its first frame to the last root jump, and to the end of the cut
	local LastJump
	for I = 2, #Rows do
		if Rows[I].path and Rows[I].path:match("Fence$") and (Rows[I].pos - Rows[I - 1].pos).Magnitude > 0.5 then LastJump = Rows[I].t end
	end
	if F0 and LastJump then add(string.format("fence segment: %.2f s to the re-seat, %.2f s to the end of the cut", LastJump - Rows[F0].t, (LastSeam or 0) - Rows[F0].t)) end
end
do -- the timeline: seam phase changes and root jumps (the dip, the re-seat), seconds from the first phase
	local T, Prev, Out = FirstSeam or 0, nil, {}
	for I, R in Rows do
		if R.seam ~= Prev then table.insert(Out, string.format("%s@%.2f", tostring(R.seam), R.t - T)) Prev = R.seam end
		if I > 1 and (R.pos - Rows[I - 1].pos).Magnitude > 0.5 then table.insert(Out, string.format("rootjump %.2f@%.2f veil %.2f", (R.pos - Rows[I - 1].pos).Magnitude, R.t - T, R.veil)) end
	end
	add("timeline: " .. table.concat(Out, " "))
end
check(Last.seam == nil and Last.ws > 5, string.format("handed back: seam %s, walk speed %.1f, crouch %s", tostring(Last.seam), Last.ws, tostring(Last.crouch)))
add(string.format("cut lived %.1f s, %d frames; Biscuit buckets before %d during %d out %d after %d", (LastSeam or 0) - (FirstSeam or 0), #Rows, B.before.n, B.during.n, B.out.n, B.after.n))
return (Pass and "SNEAK OK\n" or "SNEAK FAIL\n") .. table.concat(Rep, "\n")
