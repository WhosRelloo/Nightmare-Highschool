local RS = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Played, Flags = false, nil
local c = RS.NHCine.OnClientEvent:Connect(function(m) if m.Kind == "Play" then Played = true Flags = m.Flags end end)
local t0 = os.clock()
while not Played and os.clock() - t0 < 20 do task.wait(0.05) end
c:Disconnect()
task.wait(__AT__)
local Cam = workspace.CurrentCamera
local CF, FOV = Cam.CFrame, Cam.FieldOfView
pcall(function() RunService:UnbindFromRenderStep("NHCap") end)
RunService:BindToRenderStep("NHCap", Enum.RenderPriority.Last.Value + 1, function() Cam.CameraType = Enum.CameraType.Scriptable Cam.CFrame, Cam.FieldOfView = CF, FOV end)
local H = game:GetService("HttpService")
return "held; flags " .. H:JSONEncode(Flags or {})
