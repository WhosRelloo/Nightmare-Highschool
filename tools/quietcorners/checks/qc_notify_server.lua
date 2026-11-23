local P = game.Players:GetPlayers()[1]
require(game.ServerScriptService.Services.Features.Notifications).Notify(P, { Title = "Clue found"; Text = "The server path"; Kind = "Info"; Duration = 8 })
task.wait(1)
local Found = false
-- client GUIs don't replicate: the client half reads PlayerGui.Notifications (qc_slips); here, just prove no error
return "sent"
