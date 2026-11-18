-- (2.26.0) The Strikethrough, played live with inputs fed through NHCineTestInput. MODE = "win" (every prompt right)
-- or "miss" (every prompt missed; the tug mashed too slowly). Start the cut with bridge.py PlayCut right after this.
local MODE = "__MODE__"
local RS = game:GetService("ReplicatedStorage")
local P = game.Players.LocalPlayer
local R = RS.NHCine
local Hook = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
Hook.Name = "NHCineTestInput"
Hook.Parent = RS
local Log, Grade, Played = {}, nil, false
local c = R.OnClientEvent:Connect(function(m)
	if m.Kind == "Play" then Played = true table.insert(Log, "Play interactive=" .. tostring(m.Interactive)) end
	if m.Kind == "Grade" then Grade = m.Grade end
end)
local c2 = P:GetAttributeChangedSignal("NHCinePrompt"):Connect(function()
	local K = P:GetAttribute("NHCinePrompt")
	if not K then return end
	table.insert(Log, "prompt " .. tostring(K))
	if MODE == "win" then
		if K == "Direction" then task.wait(0.2) Hook:Fire({ Kind = "Pick"; Id = "Left" }) end
		if K == "Press" then task.wait(0.5) Hook:Fire({ Kind = "Down" }) task.wait(0.05) Hook:Fire({ Kind = "Up" }) end
		if K == "Mash" then for _ = 1, 16 do task.wait(0.1) Hook:Fire({ Kind = "Down" }) Hook:Fire({ Kind = "Up" }) end end
		if K == "Hold" then task.wait(0.1) Hook:Fire({ Kind = "Down" }) task.wait(1.0) Hook:Fire({ Kind = "Up" }) end
	else
		if K == "Mash" then for _ = 1, 3 do task.wait(0.5) Hook:Fire({ Kind = "Down" }) Hook:Fire({ Kind = "Up" }) end end
	end
end)
local t0 = os.clock()
while not Played and os.clock() - t0 < 20 do task.wait(0.1) end
task.wait(2)
while os.clock() - t0 < 90 and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom do task.wait(0.2) end
task.wait(3) -- the grade card
c:Disconnect() c2:Disconnect() Hook:Destroy()
return table.concat(Log, " | ") .. " | grade " .. tostring(Grade) .. " | path " .. tostring(P:GetAttribute("NHCinePath"))
