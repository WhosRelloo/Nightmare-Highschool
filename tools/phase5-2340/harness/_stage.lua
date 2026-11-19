local B = game.ServerStorage.NHTestBridge
B:Invoke("SetTime", "12:00")
local P = game.Players:GetPlayers()[1]
local pl = Instance.new("Part") pl.Name = "_TestStage" pl.Anchored = true pl.Size = Vector3.new(30, 1, 30) pl.Position = Vector3.new(0, 600, 0) pl.Color = Color3.fromRGB(60, 56, 62) pl.Parent = workspace
local lp = Instance.new("Part") lp.Name = "_TestLight" lp.Anchored = true lp.Transparency = 1 lp.CanCollide = false lp.Position = Vector3.new(4, 608, -8) lp.Parent = workspace
local l = Instance.new("PointLight") l.Range = 30 l.Brightness = 3 l.Parent = lp
P.Character:PivotTo(CFrame.new(0, 604, 0))
task.wait(1)
P.Character.HumanoidRootPart.Anchored = true
return tostring(P.Character:GetPivot().Position)
