-- forms check (server, game VM): put a cape on the CHARACTER only (Appearance.WearCape; the saved look untouched).
-- CAPE = 2 (Vamp Cape) to wear one, 1 to take it off again.
local CAPE = 2
local P = game.Players:GetPlayers()[1]
local App = require(game.ReplicatedStorage.UI.Appearance)
App.WearCape(P.Character, CAPE)
task.wait(0.3)
return "NHCape=" .. tostring(P.Character:FindFirstChild("NHCape"))
