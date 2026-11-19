local ls = Instance.new("LocalScript")
ls.Source = [[
local M = require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.StatsPanel)
M.Open(script:GetAttribute("Tab"))
script:SetAttribute("Done", true)
]]
ls:SetAttribute("Tab", "Entries")
ls.Parent = game.Players.LocalPlayer.PlayerGui
task.wait(1.5)
local G = game.Players.LocalPlayer.PlayerGui:FindFirstChild("NHReportCard")
local bad = {}
for _, d in G:GetDescendants() do
  if d:IsA("TextLabel") and d.Text ~= "" and not d.TextFits then table.insert(bad, d.Text:sub(1, 50)) end
end
return "notfit " .. #bad .. ": " .. table.concat(bad, " | ", 1, math.min(#bad, 10))
