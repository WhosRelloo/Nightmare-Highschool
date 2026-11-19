-- open the Permanent Record in the game VM (a LocalScript shares the controllers' require cache) on a given tab / race
local ls = Instance.new("LocalScript")
ls.Name = "RecPreview"
ls.Source = [[
local M = require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.StatsPanel)
local Tab = script:GetAttribute("Tab")
local Race = script:GetAttribute("Race")
if Race and Race ~= "" then M.PreviewRace(Race) end
M.Toggle(true)
task.wait(0.5)
if Tab and Tab ~= "" then M.Open(Tab) end
script:SetAttribute("Done", true)
]]
ls:SetAttribute("Tab", "Honours")
ls:SetAttribute("Race", "")
ls.Parent = game.Players.LocalPlayer.PlayerGui
local t = os.clock()
repeat task.wait(0.2) until ls:GetAttribute("Done") or os.clock() - t > 8
task.wait(1.2)
local out = {}
local G = game.Players.LocalPlayer.PlayerGui:FindFirstChild("NHReportCard")
-- text fit check: every visible TextLabel in the book
local bad = 0
for _, d in G:GetDescendants() do
  if d:IsA("TextLabel") and d.Visible and d.Text ~= "" and not d.TextFits and d.TextTruncate == Enum.TextTruncate.None then bad += 1 table.insert(out, "NOFIT " .. d.Text:sub(1, 40)) end
end
return "open=" .. tostring(G and G.Enabled) .. " nofit=" .. bad .. "\n" .. table.concat(out, "\n", 1, math.min(#out, 8))
