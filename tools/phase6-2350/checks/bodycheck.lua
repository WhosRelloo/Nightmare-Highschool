-- Body seam check (Client VM): plays a chain on the local character through CineActor and measures every switch and the
-- re-seat at render rate (acceleration from the real frame times), with chaincheck's ratio test (at or under the chain's own p99, or under 45 st/s2). A duplicated
-- frame in motion (a one-frame freeze) fails it too. The HumanoidRootPart is ANCHORED while it measures (animation
-- continuity only: falls/collisions at the test spot are out of scope); the unanchored gameplay path is not measured here.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Actor = require(Players.LocalPlayer.PlayerScripts.Controllers.CineActor)
local TA = require(game.ReplicatedStorage.Config.TutorialAnim)
local Folder = game.ReplicatedStorage.NHCineClips.Tutorial
local function resolve(Name)
	local Seq = Folder:FindFirstChild(Name)
	if not Seq then return nil end
	return Seq:GetAttribute("PreviewId") or tostring(game:GetService("AnimationClipProvider"):RegisterAnimationClip(Seq))
end
local C = Players.LocalPlayer.Character
local Parts = { "Torso", "Head", "Left Arm", "Right Arm", "Left Leg", "Right Leg" }
local Samples, Marks, Times = {}, {}, {}
local Chain = "TheBus"
local Root = C.HumanoidRootPart
local WasAnchored = Root.Anchored
local Conn = nil
local Reseated = nil
local Started = os.clock()
local Elapsed = 0
local Ok, Err = pcall(function()
	Conn = RunService.RenderStepped:Connect(function()
		local P = {}
		for _, N in Parts do table.insert(P, C[N].Position) table.insert(P, (C[N].CFrame * CFrame.new(0, -1, 0)).Position) end
		table.insert(Samples, P)
		table.insert(Times, os.clock())
	end)
	Root.Anchored = true -- continuity check: falls/collisions at the test spot must not contaminate it
	Actor.Begin()
	Actor.Chain(Chain, resolve, nil, function(Piece) table.insert(Marks, { at = #Samples, name = "switch " .. Piece }) end)
	local Last = TA.Chains[Chain][#TA.Chains[Chain]]
	table.insert(Marks, { at = #Samples, name = "reseat " .. Last.Piece })
	Reseated = Actor.Reseat(Last.Piece, Last.EndOffset, resolve)
	task.wait(0.6)
end)
Elapsed = os.clock() - Started
-- finally: whatever happened above, nothing is left anchored, held or connected
if Conn then Conn:Disconnect() end
pcall(Actor.Release)
Root.Anchored = WasAnchored
if not Ok then return "BODY ERROR (restored: Anchored " .. tostring(Root.Anchored) .. ", released)\n" .. tostring(Err) end

-- acceleration from the real frame times (a non-uniform second difference), so a throttled or jittery frame rate
-- doesn't read as motion: a_i = 2 * ((x_i - x_{i-1}) / dt1 - (x_{i-1} - x_{i-2}) / dt0) / (dt0 + dt1)
local Acc = {}
for i = 3, #Samples do
	local Dt0 = math.max(1e-4, Times[i - 1] - Times[i - 2])
	local Dt1 = math.max(1e-4, Times[i] - Times[i - 1])
	local M = 0
	for j = 1, #Samples[i] do
		local A = (2 * ((Samples[i][j] - Samples[i - 1][j]) / Dt1 - (Samples[i - 1][j] - Samples[i - 2][j]) / Dt0) / (Dt0 + Dt1)).Magnitude
		if A > M then M = A end
	end
	Acc[i] = M
end
local Dts = {}
for i = 2, #Times do table.insert(Dts, Times[i] - Times[i - 1]) end
table.sort(Dts)
local Near, Inside = {}, {}
for _, Mk in Marks do for i = Mk.at - 4, Mk.at + 4 do Near[i] = true end end
for i = 3, #Samples do if not Near[i] then table.insert(Inside, Acc[i]) end end
table.sort(Inside)
local P99 = Inside[math.max(1, math.floor(#Inside * 0.99))] or 1
local Lines, Pass = {}, Reseated == true
table.insert(Lines, "Reseat returned " .. tostring(Reseated))
for _, Mk in Marks do
	local Peak = 0
	for i = Mk.at - 4, Mk.at + 4 do if Acc[i] and Acc[i] > Peak then Peak = Acc[i] end end
	local Ok2 = Peak <= P99 or Peak <= 45
	Pass = Pass and Ok2
	table.insert(Lines, string.format("%s peak %.0f (p99 %.0f) %s", Mk.name, Peak, P99, Ok2 and "ok" or "POP"))
end
-- duplicates in motion: a sample identical to the one before while the body still moves afterwards (a freeze). The
-- chain's last piece ends at rest (settle, then held until the re-seat), so the still tail from its last change before
-- the re-seat mark on is by design and not counted; anything after the mark is judged by the reseat peak.
local function same(a, b)
	for j = 1, #a do if a[j] ~= b[j] then return false end end
	return true
end
local ReseatAt = Marks[#Marks].at
local LastMove = 2
for i = 2, math.min(ReseatAt, #Samples) do if not same(Samples[i], Samples[i - 1]) then LastMove = i end end
local Dup, DupAt = 0, {}
for i = 2, LastMove do
	if same(Samples[i], Samples[i - 1]) then Dup += 1 table.insert(DupAt, i) end
end
local Still = 0
for i = LastMove + 1, math.min(ReseatAt + 4, #Samples) do if same(Samples[i], Samples[i - 1]) then Still += 1 end end
Pass = Pass and Dup == 0
table.insert(Lines, string.format("duplicate frames in motion: %d%s (samples %d, last motion before the re-seat at %d, reseat mark at %d, still samples from there to mark+4: %d)",
	Dup, #DupAt > 0 and (" at " .. table.concat(DupAt, ",")) or "", #Samples, LastMove, ReseatAt, Still))
-- per frame across the re-seat: the fastest part point's step (studs) and the acceleration the check sees
local Seam = {}
for i = math.max(2, ReseatAt - 4), math.min(#Samples, ReseatAt + 4) do
	local V = 0
	for j = 1, #Samples[i] do V = math.max(V, (Samples[i][j] - Samples[i - 1][j]).Magnitude) end
	table.insert(Seam, string.format("%+d:%.4f/%.0f", i - ReseatAt, V, Acc[i] or 0))
end
table.insert(Lines, "across the re-seat (frame: max part step st / accel st/s2): " .. table.concat(Seam, " "))
table.insert(Lines, string.format("render rate %.0f fps (%d samples over the run; frame time median %.1f ms, p95 %.1f ms, max %.1f ms)",
	#Samples / math.max(0.001, Elapsed), #Samples, (Dts[#Dts // 2] or 0) * 1000, (Dts[math.max(1, math.floor(#Dts * 0.95))] or 0) * 1000, (Dts[#Dts] or 0) * 1000))
table.insert(Lines, "unanchored gameplay path: NOT measured by this check (root anchored while measuring)")
return (Pass and "BODY OK\n" or "BODY POP\n") .. table.concat(Lines, "\n")
