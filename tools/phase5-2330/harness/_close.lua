local ls = Instance.new("LocalScript")
ls.Source = [[require(game.Players.LocalPlayer.PlayerScripts.Controllers.Gui.StatsPanel).Toggle(false) script:SetAttribute("Done", true)]]
ls.Parent = game.Players.LocalPlayer.PlayerGui
task.wait(1)
return "closed"
