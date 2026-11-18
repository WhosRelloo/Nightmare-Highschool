-- replay the prologue; PRESS = true answers on the beat, false lets it pass; returns the path taken
local PRESS = __PRESS__
local RS = game:GetService("ReplicatedStorage")
local P = game.Players.LocalPlayer
local R = RS.NHCine
local Hook = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
Hook.Name = "NHCineTestInput"
Hook.Parent = RS
local sess, path, opened
local c = R.OnClientEvent:Connect(function(m) if m.Kind == "Play" then sess = m.Session end end)
local c2 = P:GetAttributeChangedSignal("NHCinePrompt"):Connect(function()
	if P:GetAttribute("NHCinePrompt") == "Press" then
		opened = os.clock()
		if PRESS then task.wait(0.55) Hook:Fire({ Kind = "Down" }) end
	end
end)
R:FireServer({ Kind = "Replay"; Id = "Prologue" })
local t0 = os.clock()
while os.clock() - t0 < 30 do
	task.wait(0.1)
	local p = P:GetAttribute("NHCinePath")
	if p and p:find("Holt") then path = p break end
end
R:FireServer({ Kind = "Skip"; Session = sess })
task.wait(1.2)
c:Disconnect() c2:Disconnect() Hook:Destroy()
return "path " .. tostring(path) .. " | prompt opened at " .. string.format("%.1f", (opened or t0) - t0) .. " s | cam after skip " .. tostring(workspace.CurrentCamera.CameraType)
