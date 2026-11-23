-- checkpoint_clear.lua (Server VM): clear the tutorial checkpoint (a cut that ran sets one: TutorialSneak:Garden, TutorialBus:Main, ...)
local S = Instance.new("Script")
S.Source = [[ require(game.ServerScriptService.Services.Player.Progression).SetCheckpoint(game.Players:GetPlayers()[1], nil) ]]
S.Parent = game.ServerScriptService
task.wait(1)
S:Destroy()
return "checkpoint cleared"
