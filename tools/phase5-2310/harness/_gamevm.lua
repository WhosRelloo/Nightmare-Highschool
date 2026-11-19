local S = Instance.new("Script")
S.Source = [==[
local P = game.Players:GetPlayers()[1]
local ok, r = pcall(function()
local SSS = game.ServerScriptService.Services
local Paths = require(SSS.Player.Paths)
local want = {}
for _, L in require(game.ReplicatedStorage.Config.CliqueTalk.Generic).Path.Academic.Any do want[L] = true end
local heard, moved, said = nil, 0, 0
local log = {}
local con = {}
local students = {}
for _, m in workspace:GetDescendants() do
  if m:IsA("Model") and m ~= P.Character and m:FindFirstChildWhichIsA("Humanoid") and m:FindFirstChild("HumanoidRootPart") and m:GetAttribute("NHSayAt") ~= nil then table.insert(students, m) end
end
for _, m in students do
  table.insert(con, m:GetAttributeChangedSignal("NHSay"):Connect(function()
    said += 1 table.insert(log, (m:GetAttribute("NHLookAt") == P and "*" or "") .. tostring(m:GetAttribute("NHSay")))
    local t = m:GetAttribute("NHSay")
    if t and want[t] then heard = t .. " <- " .. m.Name end
  end))
end
local t0 = os.clock()
local i = 0
while os.clock() - t0 < 95 and not heard and #students > 0 do
  i = i % #students + 1
  local m = students[i]
  local r = m:FindFirstChild("HumanoidRootPart")
  if r then P.Character:PivotTo(r.CFrame * CFrame.new(0, 0, -5) * CFrame.Angles(0, math.pi, 0)) moved += 1 end
  task.wait(4)
end
for _, c in con do c:Disconnect() end
return "PathTop " .. tostring(P:GetAttribute("PathTop")) .. " | students " .. #students .. " moved " .. moved .. " lines " .. said .. " | heard: " .. tostring(heard) .. " || " .. table.concat(log, " / ")

end)
script:SetAttribute("Out", if ok then tostring(r) else ("ERR " .. tostring(r)))
]==]
S.Parent = game.ServerScriptService
local t0 = os.clock()
while S:GetAttribute("Out") == nil and os.clock() - t0 < 110 do task.wait(0.25) end
local r = S:GetAttribute("Out")
S:Destroy()
return tostring(r)