-- task 7: (1) CineActor Begin/Release race; (2) a seamless Skip dips to black and hands everything back.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Player = Players.LocalPlayer
local Out = {}
local Ctl = require(Player.PlayerScripts:WaitForChild("PlayerModule")):GetControls()
local function enabled() return Ctl.activeController ~= nil and Ctl.activeController.enabled == true end
local Actor = require(Player.PlayerScripts.Controllers.CineActor)
local Hum = Player.Character:FindFirstChildOfClass("Humanoid")
local Speed0 = Hum.WalkSpeed

-- (1) Release 0.1 s into Begin's 0.3 s ease-out: controls must stay enabled
table.insert(Out, "before: controls " .. tostring(enabled()))
task.spawn(Actor.Begin)
task.wait(0.1)
Actor.Release()
task.wait(0.6)
local Ok1 = enabled() and Hum.WalkSpeed == Speed0
table.insert(Out, string.format("begin/release race: controls %s, walkspeed %s (was %s) %s", tostring(enabled()), tostring(Hum.WalkSpeed), tostring(Speed0), Ok1 and "ok" or "FAIL"))
-- and the normal case still disables
task.spawn(Actor.Begin)
task.wait(0.5)
local Dis = not enabled()
Actor.Release()
task.wait(0.1)
table.insert(Out, string.format("begin alone disables: %s; release re-enables: %s", tostring(Dis), tostring(enabled())))

-- (2) seamless skip at 2.5 s
local PG = Player.PlayerGui
local Before = {}
for _, G in PG:GetChildren() do if G:IsA("LayerCollector") and G.Name ~= "NHCineUI" then Before[G] = G.Enabled end end
local Remote = game.ReplicatedStorage:WaitForChild("NHCine")
local Session
local Conn = Remote.OnClientEvent:Connect(function(M) if typeof(M) == "table" and M.Kind == "Play" then Session = M.Session end end)
Remote:FireServer({ Kind = "Replay"; Id = "__SeamlessTest" })
local T0 = os.clock()
repeat task.wait(0.05) until Session or os.clock() - T0 > 5
task.wait(2.5)
local MidHud = 0
for G in Before do if G.Parent and G.Enabled then MidHud += 1 end end
local Cam = workspace.CurrentCamera
local Veil = PG:FindFirstChild("NHCineUI") and PG.NHCineUI:FindFirstChild("Veil")
local Bars = PG.NHCineUI.Top.Size.Y.Scale
local MaxA, BlackAt, ClearAt = 0, nil, nil
local Name = "SkipCheck"
local TS = os.clock()
RunService:BindToRenderStep(Name, Enum.RenderPriority.Last.Value, function()
	local A = 1 - Veil.BackgroundTransparency
	if A > MaxA then MaxA = A end
	if A >= 0.999 and not BlackAt then BlackAt = os.clock() - TS end
	if BlackAt and A <= 0.001 and not ClearAt then ClearAt = os.clock() - TS end
end)
Remote:FireServer({ Kind = "Skip"; Session = Session })
task.wait(1.5)
RunService:UnbindFromRenderStep(Name)
Conn:Disconnect()
local Restored, Total = 0, 0
for G, Was in Before do if G.Parent then Total += 1 if G.Enabled == Was then Restored += 1 end end end
local Ok2 = MaxA >= 0.999 and ClearAt ~= nil and ClearAt < 0.6 and Cam.CameraType == Enum.CameraType.Custom
	and Player:GetAttribute("NHCineSeam") == nil and enabled() and Restored == Total and Bars == 0
table.insert(Out, string.format("skip: session %s, mid-cut HUD guis still on %d, bars %.2f; veil peak %.3f, black at %.3f s, clear at %s s; camera %s; seam %s; controls %s; HUD restored %d/%d %s",
	tostring(Session), MidHud, Bars, MaxA, BlackAt or -1, ClearAt and string.format("%.3f", ClearAt) or "never", Cam.CameraType.Name,
	tostring(Player:GetAttribute("NHCineSeam")), tostring(enabled()), Restored, Total, Ok2 and "ok" or "FAIL"))
return table.concat(Out, "\n")
