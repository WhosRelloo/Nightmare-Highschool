-- camcheck (2.35.0, spec 2026-11-20 §2 / §5): the camera seam check. Client VM, ONE call (execute_luau resets the camera
-- type when a call ends, so the cut is started and watched inside this call). Plays __SeamlessTest through the server
-- (a client Replay; mark it Seen first: bridge.py CineMark $P '"__SeamlessTest"' '"Seen"'), records the camera and the
-- look (grade, bloom, DOF, exposure) every frame after everything else has written them, and checks:
--   * the glide in (In), the handoff from Main's shots into the Walk beat (BeatIn, task 8), the glide out of the beat
--     into Close's shot (BeatOut, task 8 fix round 1) and the blend out (Out): position, angular and FOV acceleration, each within FACTOR x 1.5 of
--     its own phase median, on the phase's frames and the frames either side;
--   * the release: the first frame after Out against a constant-velocity prediction from the two frames before it
--     (0.01 stud, 0.1 deg);
--   * the look: no grade/DOF/exposure step in In/Out beyond 2x the steepest eased step for that frame's dt (a pop).
-- Acceleration uses each sample's real frame time (Studio throttles to 15-40 fps unfocused): the non-uniform second
-- difference a = 2*((x_i - x_{i-1})/dt1 - (x_{i-1} - x_{i-2})/dt0)/(dt0 + dt1). Angular uses the look vector (rad/s^2).
-- WALK = true: the player walks (Humanoid:Move after the control module, every frame) until the cut disables the
-- controls. Make that variant with: sed 's/^local WALK = false/local WALK = true/' camcheck.lua > camcheck_walk.lua
local WALK = false
-- ID: the cut to watch. PHASES: the seamless phases that cut has (a cut with Def.EndHold, like TutorialBus, has "In" only: it never
-- blends out). HOLD: the cut ends held (Def.EndHold): instead of the release check, the camera must stay frozen on the held
-- frame and NHCineHold must be set. TutorialBus variant:
--   sed 's/^local ID = "__SeamlessTest"/local ID = "TutorialBus"/; s/^local PHASES = .*/local PHASES = { "In" }/; s/^local HOLD = false/local HOLD = true/; s/^local TRIGGER = .*/local TRIGGER = "wait"/'
local ID = "__SeamlessTest"
local PHASES = { "In", "BeatIn", "BeatOut", "Out" }
local HOLD = false
-- TRIGGER: "replay" fires a journal Replay from here (mark the cut Seen first); "wait" waits for the caller to start it the way the
-- tutorial does (bridge.py PlayCut $P '"TutorialBus"' false, ~3 s after this starts, with TutorialEnter done): a held cut (HOLD) is
-- never held on a replay (task 10 fix round 1), so the TutorialBus variant uses "wait".
local TRIGGER = "replay"
-- TURN (degrees): before the cut, the gameplay camera is swung this far round the player (the Custom camera keeps it),
-- so the glide has a big turn to make. Variant: sed 's/^local TURN = 0/local TURN = 120/'
local TURN = 0
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local Player = Players.LocalPlayer
local Cam = workspace.CurrentCamera
local Rows = {}
local LastPath = nil
local Name = "CamCheck_" .. tostring(math.random(1e6))
local function fx(N) return Lighting:FindFirstChild(N) or Lighting:FindFirstChild(N .. "Out") end
local function look()
	local CC, B, D = fx("CineGrade"), fx("CineBloom"), fx("CineDOF")
	local T = CC and CC.TintColor or Color3.new(1, 1, 1)
	return {
		contrast = CC and CC.Contrast or 0; saturation = CC and CC.Saturation or 0; brightness = CC and CC.Brightness or 0;
		tint = (1 - T.R) + (1 - T.G) + (1 - T.B); bloom = B and B.Enabled and B.Intensity or 0;
		dof = D and D.Enabled and D.FarIntensity or 0; exposure = Lighting.ExposureCompensation;
		day = (function()
			-- (task 8 fix round 2) the day/night grade (Controllers.World.DayCycle) must run on through a seamless cut
			local G = Lighting:FindFirstChild("NHDayGrade")
			if not G then return { on = false; c = 0; s = 0; b = 0; t = Color3.new(1, 1, 1) } end
			return { on = G.Enabled; c = G.Contrast; s = G.Saturation; b = G.Brightness; t = G.TintColor }
		end)();
	}
end
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local Path = Player:GetAttribute("NHCinePath")
	if Path then LastPath = Path end
	table.insert(Rows, { cf = Cam.CFrame; fov = Cam.FieldOfView; phase = Player:GetAttribute("NHCineSeam") or "Play"; t = os.clock(); look = look() })
end)
local Walking = false
local Holding = false
if WALK then
	local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
	local Root = Player.Character:FindFirstChild("HumanoidRootPart")
	local Dir = (Cam.CFrame.LookVector * Vector3.new(1, 0, 1)).Unit
	Walking, Holding = true, true
	-- a held direction, until the cut takes the controls away: CineActor.Begin eases WalkSpeed down over 0.3 s, then
	-- puts it back and disables the controls in the same step, so the key is let go on the first frame WalkSpeed is
	-- back after having dropped. (This VM's PlayerModule is its own copy, so the game's controls can't be read directly.)
	local WS0 = Hum.WalkSpeed
	local Eased = false
	RunService:BindToRenderStep(Name .. "Walk", Enum.RenderPriority.Input.Value + 1, function()
		if not Holding then return end
		if Hum.WalkSpeed < WS0 - 0.01 then Eased = true end
		if Eased and Hum.WalkSpeed >= WS0 - 0.01 then
			Holding = false
			Hum:Move(Vector3.zero)
			return
		end
		Hum:Move(Dir)
	end)
	task.wait(0.8)
	if Root.AssemblyLinearVelocity.Magnitude < 2 then Dir = -Dir task.wait(0.8) end -- against a wall: the other way
	Walking = Root.AssemblyLinearVelocity.Magnitude > 2 and Holding -- really walking when the cut fires
	if not Walking then Holding = false RunService:UnbindFromRenderStep(Name .. "Walk") end
else
	task.wait(0.5) -- some live frames before the cut (the In edge needs them)
end
if TURN ~= 0 then
	local Focus = Cam.Focus.Position
	Cam.CFrame = CFrame.new(Focus) * CFrame.Angles(0, math.rad(TURN), 0) * CFrame.new(-Focus) * Cam.CFrame
	task.wait(0.6)
end
local SpeedAtFire = Player.Character.HumanoidRootPart.AssemblyLinearVelocity.Magnitude
if TRIGGER == "replay" then game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = ID }) end
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 3) or os.clock() - T0 > 50
task.wait(1.2)
RunService:UnbindFromRenderStep(Name)
if WALK then pcall(function() RunService:UnbindFromRenderStep(Name .. "Walk") end) end

-- one channel's acceleration at sample i (vectors or numbers)
local function second(i, get)
	if i < 3 or i > #Rows then return 0 end
	local a, b, c = Rows[i - 2], Rows[i - 1], Rows[i]
	local dt0, dt1 = math.max(b.t - a.t, 1e-4), math.max(c.t - b.t, 1e-4)
	local v0 = (get(b) - get(a)) / dt0
	local v1 = (get(c) - get(b)) / dt1
	local d = 2 * (v1 - v0) / (dt0 + dt1)
	return if typeof(d) == "Vector3" then d.Magnitude else math.abs(d)
end
-- median floors: a channel that barely moves in a phase (the Out turn when the cut's last shot already looks where the
-- Custom camera does) has a float-noise median; below these accelerations nothing is visible
local CHANNELS = {
	{ "pos", function(r) return r.cf.Position end, 0.05 },   -- studs/s^2
	{ "ang", function(r) return r.cf.LookVector end, 0.05 },  -- rad/s^2 (look vector)
	{ "fov", function(r) return r.fov end, 0.5 },             -- deg/s^2
}
-- an eased glide's peak acceleration over its median. Final runs (fix round 2, 9 runs at 15 fps): In pos 1.29-2.22,
-- ang 1.22-1.61, fov 1.63-1.82; Out pos/fov 1.34-1.76. 2.5 x 1.5 headroom = a 3.75 x median bound.
local FACTOR = 2.5
local Report, Pass = {}, true
local Ratios = {}
for _, Phase in PHASES do
	local Idx = {}
	for i = 3, #Rows do if Rows[i].phase == Phase then table.insert(Idx, i) end end
	if #Idx < 5 then Pass = false table.insert(Report, Phase .. ": not seen") continue end
	local Parts = {}
	for _, Ch in CHANNELS do
		local Key, Get, Floor = Ch[1], Ch[2], Ch[3]
		local A = {}
		for _, i in Idx do table.insert(A, second(i, Get)) end
		local Sorted = table.clone(A)
		table.sort(Sorted)
		local Median = math.max(Sorted[math.floor(#Sorted / 2) + 1], Floor)
		local Max = Sorted[#Sorted]
		-- the frames either side of the phase too: entering and leaving must not jerk
		local Edge = math.max(second(math.max(3, Idx[1]), Get), second(math.min(#Rows, Idx[#Idx] + 1), Get))
		local Ok = Max <= 1.5 * Median * FACTOR and Edge <= 1.5 * Median * FACTOR
		Pass = Pass and Ok
		table.insert(Ratios, string.format("%s.%s %.2f/%.2f", Phase, Key, Max / Median, Edge / Median))
		table.insert(Parts, string.format("%s median %.4g max %.4g edges %.4g %s", Key, Median, Max, Edge, Ok and "ok" or "JERK"))
	end
	table.insert(Report, string.format("%s: %d frames; %s", Phase, #Idx, table.concat(Parts, "; ")))
end
-- the release: the first frame after Out, against the two frames before it carried on at constant velocity
local LastOut
for i = #Rows, 1, -1 do if Rows[i].phase == "Out" then LastOut = i break end end
if HOLD then
	-- a cut that ends held: no glide out. The last second of frames (after NHCineSeam went nil) must be one frozen frame, the
	-- camera still Scriptable and NHCineHold set (the title stays up)
	local Tail = {}
	for i = #Rows, 1, -1 do
		if Rows[i].phase ~= "Play" then break end
		table.insert(Tail, Rows[i])
	end
	local Drift, Ang = 0, 0
	for _, R in Tail do
		Drift = math.max(Drift, (R.cf.Position - Tail[1].cf.Position).Magnitude)
		Ang = math.max(Ang, math.deg(math.acos(math.clamp(R.cf.LookVector:Dot(Tail[1].cf.LookVector), -1, 1))))
	end
	local Held = Player:GetAttribute("NHCineHold") == true
	local Ok = #Tail >= 10 and Drift <= 0.001 and Ang <= 0.01 and Held and Cam.CameraType == Enum.CameraType.Scriptable
	Pass = Pass and Ok
	table.insert(Report, string.format("hold: %d frozen frames, drift %.5f studs, %.4f deg, NHCineHold %s, camera %s %s",
		#Tail, Drift, Ang, tostring(Held), tostring(Cam.CameraType), Ok and "ok" or "NOT HELD"))
elseif LastOut and Rows[LastOut + 1] and LastOut > 1 then
	local P0, A, B = Rows[LastOut - 1], Rows[LastOut], Rows[LastOut + 1]
	local K = math.max(B.t - A.t, 1e-4) / math.max(A.t - P0.t, 1e-4)
	local PredPos = A.cf.Position + (A.cf.Position - P0.cf.Position) * K
	local PredLook = (A.cf.LookVector + (A.cf.LookVector - P0.cf.LookVector) * K).Unit
	local D = (B.cf.Position - PredPos).Magnitude
	local Ang = math.deg(math.acos(math.clamp(B.cf.LookVector:Dot(PredLook), -1, 1)))
	local Ok = D <= 0.01 and Ang <= 0.1
	Pass = Pass and Ok
	table.insert(Report, string.format("release: prediction error %.4f studs, %.4f deg %s", D, Ang, Ok and "ok" or "JUMP"))
else
	Pass = false
	table.insert(Report, "release: not seen")
end
-- the look: grade, bloom, DOF and exposure ease in over the glide and out over the blend. A frame's step may be at most
-- 2x what smootherstep's steepest slope (1.875 / phase length) covers in that frame's real dt (capped at 90%): a pop is
-- a whole swing in one frame; an eased change at 15 fps on a 0.6 s glide is ~20% a frame
do
	local Keys = { "contrast", "saturation", "brightness", "tint", "bloom", "dof", "exposure" }
	local Span = {}
	for _, Phase in PHASES do
		local A, B
		for i = 1, #Rows do if Rows[i].phase == Phase then A = A or Rows[i].t B = Rows[i].t end end
		Span[Phase] = if A then math.max(B - A, 0.1) else nil
	end
	local Bad, Shown = {}, {}
	for _, Key in Keys do
		local Lo, Hi = math.huge, -math.huge
		for _, R in Rows do Lo = math.min(Lo, R.look[Key]) Hi = math.max(Hi, R.look[Key]) end
		local Swing = Hi - Lo
		if Swing < 1e-3 then continue end
		local Worst = 0
		for i = 2, #Rows do
			local Ph = nil
			for _, Name in PHASES do
				if Rows[i].phase == Name or Rows[i - 1].phase == Name then Ph = Name break end
			end
			if Ph and Span[Ph] then
				local Allowed = math.min(0.9, 2 * 1.875 * (Rows[i].t - Rows[i - 1].t) / Span[Ph])
				local Step = math.abs(Rows[i].look[Key] - Rows[i - 1].look[Key]) / Swing
				Worst = math.max(Worst, Step / Allowed)
			end
		end
		table.insert(Shown, string.format("%s %.2f", Key, Worst))
		if Worst > 1 then table.insert(Bad, Key) end
	end
	local Ok = #Bad == 0
	Pass = Pass and Ok
	table.insert(Report, string.format("look: worst step / allowed: %s %s", #Shown > 0 and table.concat(Shown, ", ") or "(no grade)", Ok and "ok" or ("POP " .. table.concat(Bad, ","))))
end
-- (task 8 fix round 2) the day/night grade: never toggled, and no frame-to-frame step bigger than its own drift
-- (DayCycle eases with the hour: far under 0.005 a frame); the night look is contrast 0.1, saturation -0.15, a violet tint
do
	local Worst, Toggles = 0, 0
	for i = 2, #Rows do
		local A, B = Rows[i - 1].look.day, Rows[i].look.day
		if A.on ~= B.on then Toggles += 1 end
		local Step = math.max(math.abs(A.c - B.c), math.abs(A.s - B.s), math.abs(A.b - B.b),
			math.abs(A.t.R - B.t.R), math.abs(A.t.G - B.t.G), math.abs(A.t.B - B.t.B))
		Worst = math.max(Worst, Step)
	end
	local D = Rows[1] and Rows[1].look.day
	local Ok = Toggles == 0 and Worst <= 0.005 and D ~= nil and D.on
	Pass = Pass and Ok
	table.insert(Report, string.format("day grade: on %s (contrast %.2f, saturation %.2f, tint %.2f/%.2f/%.2f), toggles %d, worst step %.4f %s",
		tostring(D and D.on), D and D.c or 0, D and D.s or 0, D and D.t.R or 0, D and D.t.G or 0, D and D.t.B or 0, Toggles, Worst,
		Ok and "ok" or "POP"))
end
local Dts = {}
for i = 2, #Rows do table.insert(Dts, Rows[i].t - Rows[i - 1].t) end
table.sort(Dts)
table.insert(Report, string.format("%s%d frames, median dt %.1f ms; max/median, edge/median: %s",
	(if WALK then string.format("WALK (speed at fire %.1f, walking %s, let go %s); ", SpeedAtFire, tostring(Walking), tostring(not Holding)) else "")
		.. (if TURN ~= 0 then string.format("TURN %d; ", TURN) else ""),
	#Rows, (Dts[math.floor(#Dts / 2) + 1] or 0) * 1000, table.concat(Ratios, ", ")))
local Beat = 0
for _, R in Rows do if R.phase == "Beat" then Beat += 1 end end
table.insert(Report, string.format("path %s; Beat frames %d", tostring(LastPath), Beat))
return (Pass and "CAM OK\n" or "CAM JERK\n") .. table.concat(Report, "\n")
