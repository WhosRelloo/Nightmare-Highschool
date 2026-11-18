local RS = game:GetService("ReplicatedStorage")
local P = game.Players.LocalPlayer
local R = RS.NHCine
local Hook = RS:FindFirstChild("NHCineTestInput") or Instance.new("BindableEvent")
Hook.Name = "NHCineTestInput"
Hook.Parent = RS
local Log, Grade, Sess = {}, nil, nil
local c = R.OnClientEvent:Connect(function(m)
	if m.Kind == "Play" then Sess = m.Session table.insert(Log, "Play interactive=" .. tostring(m.Interactive)) end
	if m.Kind == "Grade" then Grade = m.Grade end
end)
local OutSeg = {}
local c2 = P:GetAttributeChangedSignal("NHCinePrompt"):Connect(function()
	local K = P:GetAttribute("NHCinePrompt")
	if K == "Press" then task.wait(0.6) Hook:Fire({ Kind = "Down" }) end
	if K == "Mash" then for i = 1, 14 do task.wait(0.1) Hook:Fire({ Kind = "Down" }) end end
	table.insert(Log, "prompt " .. tostring(K))
end)
R:FireServer({ Kind = "Replay"; Id = "__QteTest" })
local t0 = os.clock()
while os.clock() - t0 < 25 and workspace.CurrentCamera.CameraType ~= Enum.CameraType.Custom or os.clock() - t0 < 2 do task.wait(0.1) end
c:Disconnect() c2:Disconnect() Hook:Destroy()
return table.concat(Log, " | ") .. " | grade " .. tostring(Grade) .. " | path " .. tostring(P:GetAttribute("NHCinePath"))
