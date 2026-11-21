-- sneakcheck (2.35.0, task 11): TutorialSneak end to end from the client VM, ONE call (the cut is started and watched here).
-- Needs TutorialEnter and the cut marked Seen (bridge.py CineMark $P '"TutorialSneak"' '"Seen"'). MODE "sneak": crouch-walk
-- Start -> FenceZone (never within 8 studs of Biscuit); MODE "fail": walk toward Biscuit, stand up (BeatCrouch Off) within 7
-- studs, wait out Hide, then on to the fence. Samples every frame and reports:
--   * path (Garden>Fence, or Garden>Hide>Garden>Fence); the Fence checkpoint is read by the caller (bridge.py Origin $P)
--   * Biscuit: the player's cast copy exists; frames with the copy present and NO clip playing (must be 0 while the cut lives);
--     the clips seen by name; the lamp (BedroomLight) on/off
--   * the crouch: Humanoid attribute Crouch through the Garden beat; the stand-up as FenceOver2 starts (root/head jump)
--   * the end: NHCineSeam back to nil, controls handed back
local MODE = "sneak"
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Char = Player.Character
local Hum = Char:FindFirstChildOfClass("Humanoid")
local Root = Char.HumanoidRootPart
-- (StreamingEnabled: the marks only exist on the client near them) go to the Garden's Start first, then wait for them
local StartPos = Vector3.new(3994, 3, 4104)
Root.CFrame = CFrame.lookAt(StartPos, Vector3.new(4012, 3, 4081))
Root.AssemblyLinearVelocity = Vector3.zero
Player:SetAttribute("NHCinePath", nil) -- a previous run's path
local Marks = workspace:WaitForChild("NHCineSets"):WaitForChild("Garden")
local Fence, BiscuitMark = Marks:WaitForChild("FenceZone").Position, Marks:WaitForChild("Biscuit").Position
workspace:WaitForChild("Hometown"):WaitForChild("Garden"):WaitForChild("WFBiscuit")
local Clips = require(game.ReplicatedStorage.Config.CineClips)
local Names = {}
for K, V in Clips do if typeof(V) == "string" then Names[(V:gsub("rbxassetid://", ""))] = K end end
local Tut = game.ReplicatedStorage.NHCineClips:FindFirstChild("Tutorial")
if Tut then for _, S in Tut:GetChildren() do local P = S:GetAttribute("PreviewId") if P then Names[tostring(P)] = S.Name end end end
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")

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
local PREWALK, Began = 0.4, false -- walking already as the cut starts (seconds of walking first; 0 = from standing still)
local Armed = PREWALK > 0
RunService:BindToRenderStep(Name .. "Walk", Enum.RenderPriority.Input.Value + 1, function()
	local Ph = Player:GetAttribute("NHCineSeam")
	if Ph ~= nil then Began = true end
	if Began and not (Ph == "In" or Ph == "Beat" or Ph == "BeatIn") then return end
	if not Began and not Armed then return end
	local Path = Player:GetAttribute("NHCinePath") or ""
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
	if D.Magnitude > 0.5 then Hum:Move(D.Unit, false) end
end)
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local Has, Anim, L = biscuit()
	local Lamp = workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineProp_BedroomLight")
	table.insert(Rows, { t = os.clock(); seam = Player:GetAttribute("NHCineSeam"); path = Player:GetAttribute("NHCinePath"); crouch = Hum:GetAttribute("Crouch") == true;
		ws = Hum.WalkSpeed; pos = Root.Position; head = Char.Head.Position; has = Has; anim = Anim; clips = L; lamp = Lamp and Lamp.Transparency or nil;
		dist = (Root.Position - BiscuitMark).Magnitude; cam = workspace.CurrentCamera.CFrame.Position; look = workspace.CurrentCamera.CFrame.LookVector; vel = Root.AssemblyLinearVelocity.Magnitude })
end)
Armed = true
task.wait(PREWALK)
Remote:FireServer({ Kind = "Replay"; Id = "TutorialSneak" })
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 3) or os.clock() - T0 > 70
task.wait(1.0)
RunService:UnbindFromRenderStep(Name)
RunService:UnbindFromRenderStep(Name .. "Walk")
Hum:Move(Vector3.zero)

local Rep = {}
local function add(S) table.insert(Rep, S) end
local LastPath, SeenCast, NoClip, Frames, Seen, MinDist = nil, 0, 0, 0, {}, math.huge
local CrouchBeat, CrouchHeld = 0, 0
local LampMin, LampMax = 1, 0
local FirstSeam, LastSeam
for _, R in Rows do
	if R.path then LastPath = R.path end
	if R.seam then FirstSeam = FirstSeam or R.t LastSeam = R.t end
	if R.seam and R.seam ~= "Out" then
		Frames += 1
		MinDist = math.min(MinDist, R.dist)
		if R.has then SeenCast += 1 if #R.clips == 0 then NoClip += 1 end end
		for _, N in R.clips do Seen[N] = (Seen[N] or 0) + 1 end
	end
	if R.seam == "Beat" and R.path == "Garden" and (not FailAt or R.t < FailAt) and R.t > (FirstSeam or 0) + 1.5 then
		CrouchBeat += 1 if R.crouch then CrouchHeld += 1 end
	end
	if R.lamp then LampMin = math.min(LampMin, R.lamp) LampMax = math.max(LampMax, R.lamp) end
end
local Pass = true
local function check(Ok, S) Pass = Pass and Ok add(S .. (Ok and " ok" or " FAIL")) end
local WantPath = if MODE == "fail" then "Garden>Hide>Garden>Fence" else "Garden>Fence"
check(LastPath == WantPath, "path " .. tostring(LastPath) .. " (want " .. WantPath .. ")")
check(SeenCast > 0 and NoClip == 0, string.format("Biscuit: cast copy on %d frames, %d of them with NO clip playing", SeenCast, NoClip))
local L = {}
for N, C in Seen do table.insert(L, N .. " " .. C) end
table.sort(L)
add("clips seen: " .. table.concat(L, ", "))
check((MODE == "fail" and CrouchBeat == 0) or (CrouchBeat > 0 and CrouchHeld >= CrouchBeat * 0.95), string.format("crouch held %d of %d Garden-beat frames (before any stand-up)", CrouchHeld, CrouchBeat))
if MODE == "sneak" then
	check(MinDist > 8, string.format("closest approach to Biscuit %.2f studs", MinDist))
	check(LampMax == 0 or LampMax == 1 and LampMin == 1, string.format("lamp stayed off (min %.2f max %.2f)", LampMin, LampMax))
else
	check(LampMin == 0 and LampMax == 1, string.format("lamp went on and off again (min %.2f max %.2f)", LampMin, LampMax))
	check(Stood, "stood up near him")
end
-- the stand-up under the fence chain: the largest frame-to-frame move of the head (relative to the root) in the Fence segment
local Worst, At = 0, 0
for I = 2, #Rows do
	if Rows[I].path and Rows[I].path:match("Fence$") and Rows[I].seam then
		local A, B = Rows[I - 1], Rows[I]
		local D = ((B.head - B.pos) - (A.head - A.pos)).Magnitude
		if D > Worst then Worst, At = D, I end
	end
end
do
	local Fi
	for I = 2, #Rows do
		if Rows[I].path and Rows[I].path:match("Fence$") and Rows[I - 1].crouch and not Rows[I].crouch then Fi = I break end
	end
	if Fi then
		local W, RY = 0, 0
		for I = Fi - 2, Fi + 3 do
			local A, B = Rows[I - 1], Rows[I]
			W = math.max(W, ((B.head - B.pos) - (A.head - A.pos)).Magnitude)
			RY = math.max(RY, math.abs(B.pos.Y - A.pos.Y))
		end
		add(string.format("fence: crouch dropped at frame %d; head-vs-root step there %.3f, root Y step %.3f", Fi, W, RY))
	else add("fence: crouch never dropped in the Fence segment") end
	local P0
	for _, R in Rows do if R.path and R.path:match("Fence$") and not P0 then P0 = R.pos end end
	local P1 = Rows[#Rows].pos
	add(string.format("fence: root at the segment start (%.2f, %.2f, %.2f), at the end (%.2f, %.2f, %.2f); fence plane z 4080", P0.X, P0.Y, P0.Z, P1.X, P1.Y, P1.Z))
end
add(string.format("fence: worst head-vs-root step %.3f studs (frame %d of %d)", Worst, At, #Rows))
do -- the timeline: seam phase changes and root jumps (the re-seat), seconds from the first phase
	local T, Prev, Out = FirstSeam or 0, nil, {}
	for I, R in Rows do
		if R.seam ~= Prev then table.insert(Out, string.format("%s@%.2f", tostring(R.seam), R.t - T)) Prev = R.seam end
		if I > 1 and (R.pos - Rows[I - 1].pos).Magnitude > 0.5 then table.insert(Out, string.format("rootjump %.2f@%.2f", (R.pos - Rows[I - 1].pos).Magnitude, R.t - T)) end
	end
	add("timeline: " .. table.concat(Out, " "))
end
do -- the worst camera accelerations (real frame times) with the phase and the player's speed: what the camera check's JERK rows are
	local A = {}
	for I = 3, #Rows do
		local a, b, c = Rows[I - 2], Rows[I - 1], Rows[I]
		local d0, d1 = math.max(b.t - a.t, 1e-4), math.max(c.t - b.t, 1e-4)
		local acc = (2 * ((c.cam - b.cam) / d1 - (b.cam - a.cam) / d0) / (d0 + d1)).Magnitude
		table.insert(A, { acc = acc, I = I })
	end
	table.sort(A, function(x, y) return x.acc > y.acc end)
	local Out = {}
	for K = 1, 6 do
		local E = A[K]
		if E then local R = Rows[E.I] table.insert(Out, string.format("%.0f %s@%.2f speed %.1f->%.1f ws %.1f", E.acc, tostring(R.seam), R.t - (FirstSeam or 0), Rows[E.I - 1].vel, R.vel, R.ws)) end
	end
	add("worst camera accel: " .. table.concat(Out, " | "))
end
do
	local A = {}
	for I = 3, #Rows do
		local a, b, c = Rows[I - 2], Rows[I - 1], Rows[I]
		local d0, d1 = math.max(b.t - a.t, 1e-4), math.max(c.t - b.t, 1e-4)
		local acc = (2 * ((c.look - b.look) / d1 - (b.look - a.look) / d0) / (d0 + d1)).Magnitude
		table.insert(A, { acc = acc, I = I })
	end
	table.sort(A, function(x, y) return x.acc > y.acc end)
	local Out = {}
	for K = 1, 4 do
		local E = A[K]
		if E then local R = Rows[E.I] table.insert(Out, string.format("%.0f %s %s@%.2f dt %.0fms", E.acc, tostring(R.seam), tostring(R.path), R.t - (FirstSeam or 0), (R.t - Rows[E.I - 1].t) * 1000)) end
	end
	add("worst camera look accel: " .. table.concat(Out, " | "))
end
do
	local Out, Next = {}, 0
	for _, R in Rows do
		local T = R.t - (FirstSeam or 0)
		if T >= 3 and T >= Next then
			Next = T + 0.5
			table.insert(Out, string.format("%.1f %s crouch %s ws %.1f vel %.1f root (%.2f, %.2f)", T, tostring(R.seam), tostring(R.crouch), R.ws, R.vel, R.pos.X, R.pos.Z))
		end
	end
	add("root by second: " .. table.concat(Out, " | "))
end
local Last = Rows[#Rows]
check(Last.seam == nil and Last.ws > 5, string.format("handed back: seam %s, walk speed %.1f, crouch %s", tostring(Last.seam), Last.ws, tostring(Last.crouch)))
add(string.format("cut lived %.1f s, %d frames, fence zone distance at the end %.2f", (LastSeam or 0) - (FirstSeam or 0), #Rows, (Last.pos - Fence).Magnitude * 1))
return (Pass and "SNEAK OK\n" or "SNEAK FAIL\n") .. table.concat(Rep, "\n")
