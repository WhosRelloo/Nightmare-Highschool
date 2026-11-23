-- origin.lua (Server VM): the tutorial checkpoint state (Progression Origin); "[]" / "{}" = none. Record it before and after a round
local S = Instance.new("Script")
S.Source = [[
local H = game:GetService("HttpService")
local P = require(game.ServerScriptService.Services.Player.Progression).Get(game.Players:GetPlayers()[1])
script:SetAttribute("J", H:JSONEncode(P and P.Origin or "none"))
]]
S.Parent = game.ServerScriptService
task.wait(1)
local J = S:GetAttribute("J")
S:Destroy()
return J
