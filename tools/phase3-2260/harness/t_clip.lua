local RS = game:GetService("ReplicatedStorage")
local R = RS.NHCine
local found, fxSeen = nil, false
local sess
local c = R.OnClientEvent:Connect(function(m) if m.Kind == "Play" then sess = m.Session end end)
R:FireServer({ Kind = "Replay"; Id = "__QteTest" })
local t0 = os.clock()
while os.clock() - t0 < 2.5 do
	task.wait(0.05)
	local A = workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineActor_Self")
	local An = A and A:FindFirstChildOfClass("Humanoid") and A.Humanoid:FindFirstChildOfClass("Animator")
	if An then for _, T in An:GetPlayingAnimationTracks() do if T.Animation.AnimationId:find("99575689929104") then found = T.Animation.AnimationId end end end
	if workspace:FindFirstChild("NHCineActors") and workspace.NHCineActors:FindFirstChild("CineFx", true) then fxSeen = true end
end
R:FireServer({ Kind = "Skip"; Session = sess })
c:Disconnect()
return "clip " .. tostring(found) .. " | fx " .. tostring(fxSeen)
