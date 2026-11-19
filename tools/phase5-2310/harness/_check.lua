local SSS = game.ServerScriptService.Services
local r = require(SSS.Player.Paths).CheckNow(P)
return #r .. " " .. tostring(P:GetAttribute("Path_Combat")) .. " titles " .. table.concat(require(SSS.Social.Reputation).Get(P).Titles, ",")
