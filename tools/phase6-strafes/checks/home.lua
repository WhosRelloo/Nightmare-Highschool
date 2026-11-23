local P = game.Players:GetPlayers()[1]
local R = P.Character.HumanoidRootPart
R.CFrame = CFrame.new(122, 5, 51) -- the main hallway, facing -Z: strafes run along its length
task.wait(1)
return tostring(R.Position) .. " owner " .. tostring(R:GetNetworkOwner())
