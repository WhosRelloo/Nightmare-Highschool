-- reducecheck (2.35.0, task 7 fix round 1, spec §2.1/§2.2): with Reduce Motion, a seamless cut's glide in and blend out
-- are 0.2 s fades through black: in the In and Out phases the camera only changes across a frame the veil fully covers.
-- Client VM, one call. Sets NHReducedMotion on this player (client side) for the run and puts it back.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Cam = workspace.CurrentCamera
local Was = Player:GetAttribute("NHReducedMotion")
Player:SetAttribute("NHReducedMotion", true)
local Rows = {}
local Name = "ReduceCheck"
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local G = Player.PlayerGui:FindFirstChild("NHCineUI")
	local V = G and G.Enabled and G:FindFirstChild("Veil")
	table.insert(Rows, { cf = Cam.CFrame; fov = Cam.FieldOfView; veil = V and (1 - V.BackgroundTransparency) or 0;
		phase = Player:GetAttribute("NHCineSeam") or "Play"; t = os.clock() })
end)
task.wait(0.3)
game.ReplicatedStorage.NHCine:FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
local T0 = os.clock()
local Started = false
repeat
	task.wait(0.1)
	if Player:GetAttribute("NHCineSeam") ~= nil then Started = true end
until (Started and Player:GetAttribute("NHCineSeam") == nil and os.clock() - T0 > 3) or os.clock() - T0 > 20
task.wait(0.8)
RunService:UnbindFromRenderStep(Name)
Player:SetAttribute("NHReducedMotion", Was)
local Report, Pass = {}, true
for _, Phase in { "In", "Out" } do
	local Moves, Hidden, Peak, First, Last = 0, 0, 0, nil, nil
	for i = 2, #Rows do
		local R, P = Rows[i], Rows[i - 1]
		if R.phase == Phase or P.phase == Phase then
			First = First or P.t
			Last = R.t
			Peak = math.max(Peak, R.veil)
			local Moved = (R.cf.Position - P.cf.Position).Magnitude > 0.01
				or math.deg(math.acos(math.clamp(R.cf.LookVector:Dot(P.cf.LookVector), -1, 1))) > 0.1
				or math.abs(R.fov - P.fov) > 0.05
			if Moved then
				-- a change is only allowed onto (or off) a fully black frame
				if R.veil >= 0.99 or P.veil >= 0.99 then Hidden += 1 else Moves += 1 end
			end
		end
	end
	local Ok = First ~= nil and Moves == 0 and Hidden >= 1 and Peak >= 0.99
	Pass = Pass and Ok
	table.insert(Report, string.format("%s: visible camera changes %d, changes at black %d, veil peak %.2f, phase span %.2f s %s",
		Phase, Moves, Hidden, Peak, First and (Last - First) or -1, Ok and "ok" or "FAIL"))
end
table.insert(Report, string.format("%d frames (no require here: a require from this VM builds rogue module copies)", #Rows))
return (Pass and "REDUCE OK\n" or "REDUCE FAIL\n") .. table.concat(Report, "\n")
