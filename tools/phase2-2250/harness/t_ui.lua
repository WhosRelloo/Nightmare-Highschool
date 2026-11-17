local UI = require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.CineUI)
local KIND = "__KIND__"
UI.Show({ Skippable = false })
local P = { kind = KIND; beat = 0.6; dur = 5; on = {}; options = { { id = "a"; text = "Nobody answered." }, { id = "b"; text = "Who's Mira Holt?" } }; default = "a" }
UI.PromptShow(P, { Reduced = false; Touch = false; OnTap = function() end; OnPick = function() end })
task.wait(0.4)
local Layer
for _, G in game.Players.LocalPlayer.PlayerGui:GetChildren() do
	if G.Name == "NHCineUI" and G:FindFirstChild("Prompt") then Layer = G.Prompt end
end
local parts = {}
if Layer then for _, c in Layer:GetChildren() do table.insert(parts, c.Name) end end
return "prompt layer " .. tostring(Layer ~= nil) .. " parts: " .. table.concat(parts, ",")
