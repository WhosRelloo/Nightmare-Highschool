-- camcheck (2.35.0, spec 2026-11-20 §2 / §5): the camera seam check. Client VM, ONE call (execute_luau resets the camera
-- type when a call ends, so the cut is started and watched inside this call). Plays __SeamlessTest through the server
-- (a client Replay; mark it Seen first: bridge.py CineMark $P '"__SeamlessTest"' '"Seen"'), records the camera every
-- frame after everything else has written it, and checks the glide in, the blend out and the release frame.
-- Acceleration uses each sample's real frame time (Studio throttles to 15-40 fps unfocused): the non-uniform second
-- difference a = 2*((x_i - x_{i-1})/dt1 - (x_{i-1} - x_{i-2})/dt0)/(dt0 + dt1), in studs/s^2.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Cam = workspace.CurrentCamera
local Rows = {}
local Name = "CamCheck_" .. tostring(math.random(1e6))
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	table.insert(Rows, { cf = Cam.CFrame; fov = Cam.FieldOfView; phase = Player:GetAttribute("NHCineSeam") or "Play"; t = os.clock() })
end)
task.wait(0.5) -- some live frames before the cut (the In edge needs them)
game.ReplicatedStorage:WaitForChild("NHCine"):FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 3) or os.clock() - T0 > 20
task.wait(1.2)
RunService:UnbindFromRenderStep(Name)
local function acc(i)
	if i < 3 or i > #Rows then return 0 end
	local a, b, c = Rows[i - 2], Rows[i - 1], Rows[i]
	local dt0, dt1 = math.max(b.t - a.t, 1e-4), math.max(c.t - b.t, 1e-4)
	local v0 = (b.cf.Position - a.cf.Position) / dt0
	local v1 = (c.cf.Position - b.cf.Position) / dt1
	return (2 * (v1 - v0) / (dt0 + dt1)).Magnitude
end
local FACTOR = 2.5 -- an eased glide's peak acceleration over its median: measured 1.55-2.44 (In) and 1.44 (Out) over 3 runs (task-7 report); the brief guessed 4 for smootherstep
local Report, Pass = {}, true
local Ratios = {}
for _, Phase in { "In", "Out" } do
	local Idx = {}
	for i = 3, #Rows do if Rows[i].phase == Phase then table.insert(Idx, i) end end
	if #Idx < 5 then Pass = false table.insert(Report, Phase .. ": not seen") continue end
	local A = {}
	for _, i in Idx do table.insert(A, acc(i)) end
	local Sorted = table.clone(A)
	table.sort(Sorted)
	local Median = math.max(Sorted[math.floor(#Sorted / 2) + 1], 1e-3)
	local Max = Sorted[#Sorted]
	-- the frames either side of the phase too: entering and leaving the glide must not jerk
	local Edge = math.max(acc(math.max(3, Idx[1])), acc(math.min(#Rows, Idx[#Idx] + 1)))
	local Ok = Max <= 1.5 * Median * FACTOR and Edge <= 1.5 * Median * FACTOR
	Pass = Pass and Ok
	table.insert(Ratios, string.format("%s max/median %.2f", Phase, Max / Median))
	table.insert(Report, string.format("%s: %d frames, median %.3f, max %.3f, edges %.3f %s", Phase, #Idx, Median, Max, Edge, Ok and "ok" or "JERK"))
end
-- the release: the first "Play" frame after "Out" equals the last "Out" frame (the Custom camera), allowing for that
-- frame's own motion
local LastOut
for i = #Rows, 1, -1 do if Rows[i].phase == "Out" then LastOut = i break end end
if LastOut and Rows[LastOut + 1] then
	local A, B = Rows[LastOut].cf, Rows[LastOut + 1].cf
	local D = (A.Position - B.Position).Magnitude
	local Ang = math.deg(math.acos(math.clamp(A.LookVector:Dot(B.LookVector), -1, 1)))
	-- the frame's own motion: what the previous frame moved (position and turn), at this frame's dt
	local P0 = Rows[LastOut - 1]
	local dtPrev = math.max(Rows[LastOut].t - P0.t, 1e-4)
	local dtThis = math.max(Rows[LastOut + 1].t - Rows[LastOut].t, 1e-4)
	local Move = (A.Position - P0.cf.Position).Magnitude * dtThis / dtPrev
	local Turn = math.deg(math.acos(math.clamp(A.LookVector:Dot(P0.cf.LookVector), -1, 1))) * dtThis / dtPrev
	local Ok = D <= 0.01 + Move * 2 and Ang <= 0.1 + Turn * 2
	Pass = Pass and Ok
	table.insert(Report, string.format("release: %.4f studs, %.3f deg (own motion %.4f studs, %.3f deg) %s", D, Ang, Move, Turn, Ok and "ok" or "JUMP"))
elseif Pass then
	Pass = false
	table.insert(Report, "release: not seen")
end
local Dts = {}
for i = 2, #Rows do table.insert(Dts, Rows[i].t - Rows[i - 1].t) end
table.sort(Dts)
table.insert(Report, string.format("%d frames, median dt %.1f ms; %s", #Rows, (Dts[math.floor(#Dts / 2) + 1] or 0) * 1000, table.concat(Ratios, ", ")))
return (Pass and "CAM OK\n" or "CAM JERK\n") .. table.concat(Report, "\n")
