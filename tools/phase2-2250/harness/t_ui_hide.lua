local UI = require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.CineUI)
UI.PromptHide(nil) UI.Hide(0.01)
task.wait(0.2)
for _, G in game.Players.LocalPlayer.PlayerGui:GetChildren() do if G.Name == "NHCineUI" and not G.Enabled then end end
return "hidden"
