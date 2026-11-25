-- soccer_play_polish (Soccer 2.0 polish, Client, Play, during a solo match from soccer_match_start.lua):
-- (2) a body cleared on stream-out drops its cached tracks and connections (and a returning body gets just one set),
-- (4) a second Seek on one track retires the first, (3) a clip that never loads falls back to the plain 1.1 dash.
-- Prints PASS soccer_play_polish or FAIL <why>. Restores every hook.
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local P = Players.LocalPlayer
local Ctl = P.PlayerScripts:WaitForChild("Controllers")
local Soccer = require(Ctl.Gui.Soccer)
if not (Soccer.ConnsForTests and Soccer.PlayForTests) then return "FAIL soccer_play_polish: Controllers.Gui.Soccer has no ConnsForTests/PlayForTests (polish not installed)" end
local Clips = require(Ctl.Gui.Soccer.Clips)
if not Clips.TestId then return "FAIL soccer_play_polish: Soccer.Clips has no TestId (polish not installed)" end
local T = require(RS.Config.Sports).Soccer
local Char = P.Character
local Root = Char.HumanoidRootPart
local Fails = {}
local Dummy = nil
local function flat(V) return Vector3.new(V.X, 0, V.Z) end
local function cleanup()
	Clips.TestId("Dribble", nil)
	if Dummy then pcall(function() Dummy:Destroy() end) end
end
local ok, Err = pcall(function()
	-- (2) stream-out clean-up on a dummy body
	Char.Archivable = true
	Dummy = Char:Clone()
	Dummy.Name = "PolishDummy"
	Dummy:PivotTo(Root.CFrame * CFrame.new(12, 0, 0))
	Dummy.Parent = workspace
	task.wait(0.3)
	local Tr = Soccer.PlayForTests(Dummy, "Pass")
	if not Tr then table.insert(Fails, "(2) no Pass track on the dummy") return end
	local N1 = Soccer.ConnsForTests(Dummy)
	if N1 < 1 then table.insert(Fails, "(2) the body holds no connections after a Play: " .. N1) end
	if next(Soccer.TracksForTests(Dummy)) == nil then table.insert(Fails, "(2) no cached track after a Play") end
	Dummy.Parent = nil
	task.wait(0.2)
	if next(Soccer.TracksForTests(Dummy)) ~= nil then table.insert(Fails, "(2) cached tracks survive the stream-out") end
	if Soccer.ConnsForTests(Dummy) ~= 0 then table.insert(Fails, "(2) connections after the stream-out: " .. Soccer.ConnsForTests(Dummy)) end
	if Tr.IsPlaying then table.insert(Fails, "(2) the old track still plays") end
	-- it comes back: one new set of connections, not a second one on top of an old one
	Dummy.Parent = workspace
	task.wait(0.2)
	Soccer.PlayForTests(Dummy, "Pass")
	local N2 = Soccer.ConnsForTests(Dummy)
	if N2 ~= N1 then table.insert(Fails, string.format("(2) a returning body holds %d connections (first time %d)", N2, N1)) end
	Dummy:Destroy()
	task.wait(0.2)
	if Soccer.ConnsForTests(Dummy) ~= 0 then table.insert(Fails, "(2) connections after Destroy: " .. Soccer.ConnsForTests(Dummy)) end
	Dummy = nil

	-- (4) a newer Seek on one track retires the older one: a stand-in track records its TimePosition writes
	local Store = { Length = 0; IsPlaying = true; Speed = 1; TimePosition = 0 }
	local Writes = {}
	local Fake = setmetatable({}, {
		__index = Store;
		__newindex = function(_, K, V) if K == "TimePosition" then table.insert(Writes, V) end Store[K] = V end;
	})
	Clips.Seek(Fake, 1, 1)
	task.wait(0.1)
	Clips.Seek(Fake, 2, 1)
	task.wait(0.1)
	Store.Length = 5
	task.wait(0.2)
	if #Writes ~= 1 then table.insert(Fails, "(4) " .. #Writes .. " TimePosition writes from two Seeks (want 1)") end
	if Writes[1] and Writes[1] < 2 then table.insert(Fails, string.format("(4) the surviving write is %.2f (want >= 2, the second Seek's)", Writes[1])) end

	-- (3) a clip that never loads: DashPath falls back to the plain dash (the dribble's 1.1 distance).
	-- The bogus track is cached under the slot on the local body, so it is dropped and destroyed afterwards.
	local Tracks = Soccer.TracksForTests(Char)
	local function dropDribble()
		for K, Old in Tracks do if K:sub(1, 7) == "Dribble" then pcall(function() Old:Stop(0) Old:Destroy() end) Tracks[K] = nil end end
	end
	dropDribble()
	Clips.TestId("Dribble", "rbxassetid://1")
	local Centre = workspace.Sports.Pitch:GetBoundingBox().Position
	local D = flat(Centre - Root.Position)
	D = if D.Magnitude > 1 then D.Unit else flat(Root.CFrame.LookVector).Unit
	Root.CFrame = CFrame.lookAt(Root.Position, Root.Position + D)
	task.wait(0.3)
	local From = Root.Position
	Soccer.FxForTests("S_Dribble", { Player = P; Dir = D })
	task.wait(1 + T.Dribble.Time + 0.7)
	local Want = T.Dribble.Dash * 0.5   -- the 1.1 dribble distance (Gui.Soccer S_Dribble)
	local Got = flat(Root.Position - From).Magnitude
	if Got < Want * 0.8 then table.insert(Fails, string.format("(3) the never-loaded dribble moved %.2f of %.2f studs (want >= 80%%)", Got, Want)) end
	-- put everything back: the hook, and the bogus track the body cached
	Clips.TestId("Dribble", nil)
	dropDribble()
	local Id = Clips.Id("Dribble")
	if not Id or Id == "rbxassetid://1" then table.insert(Fails, "(3) after the restore Dribble resolves to " .. tostring(Id)) return end
	local Fresh = Soccer.PlayForTests(Char, "Dribble")
	if not Fresh then table.insert(Fails, "(3) no fresh Dribble track after the restore") return end
	local L0 = os.clock()
	while Fresh.Length <= 0 and os.clock() - L0 < 3 do RunService.Heartbeat:Wait() end
	if Fresh.Length <= 0 then table.insert(Fails, "(3) the fresh Dribble track never reached Length > 0") end
	Fresh:Stop(0)
	dropDribble()
end)
cleanup()
if not ok then return "FAIL soccer_play_polish: " .. tostring(Err) end
if #Fails > 0 then return "FAIL soccer_play_polish\n" .. table.concat(Fails, "\n") end
return "PASS soccer_play_polish"
