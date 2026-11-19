local H = game:GetService("HttpService")
local SSS = game.ServerScriptService.Services
local F = require(SSS.Player.Paths).Facts(P)
local Pr = require(SSS.Player.Progression).Get(P)
return H:JSONEncode({ F = F; Paths = Pr.Paths; Tally = Pr.Tally; Attr = P:GetAttribute("PathTop") })
