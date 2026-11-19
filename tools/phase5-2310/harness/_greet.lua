local SSS = game.ServerScriptService.Services
local Paths = require(SSS.Player.Paths)
local B = game.ServerStorage.NHTestBridge
B:Invoke("SetTime", "12:30") -- (next day: lunch, students about; restore.py puts discipline back)
task.wait(2)
local Pr = require(SSS.Player.Progression).Get(P) Pr.Paths = {} require(SSS.Player.Data).UpdateState(P, { type = "SetProgress"; progress = Pr })
local F = Paths.Facts(P)
F.Subjects = { History = 4; Mathematics = 4; Chemistry = 4; English = 2 } F.BestStreak = 10 F.BestCard = 4
Paths.FactsOverride[P] = F
Paths.CheckNow(P)
local want = {}
for _, L in require(game.ReplicatedStorage.Config.CliqueTalk.Generic).Path.Academic.Any do want[L] = true end
local heard, seen = nil, 0
local t0 = os.clock()
while os.clock() - t0 < 100 and not heard do
  -- stand next to the nearest student each few seconds
  local best, bd
  for _, m in workspace.Live:GetChildren() do
    local r = m:FindFirstChild("HumanoidRootPart")
    if r and m ~= P.Character and m:GetAttribute("RosterId") then
      local d = (r.Position - P.Character.HumanoidRootPart.Position).Magnitude
      if not bd or d < bd then best, bd = m, d end
    end
  end
  if best and (os.clock() - t0) % 12 < 0.6 then P.Character:PivotTo(best.HumanoidRootPart.CFrame * CFrame.new(0, 0, -5) * CFrame.Angles(0, math.pi, 0)) seen += 1 end
  for _, d in workspace:GetDescendants() do
    if d:IsA("TextLabel") and want[d.Text] then heard = d.Text .. " <- " .. d:GetFullName() break end
  end
  task.wait(0.5)
end
Paths.FactsOverride[P] = nil
return "PathTop " .. tostring(P:GetAttribute("PathTop")) .. " | moved " .. seen .. " | heard: " .. tostring(heard)
