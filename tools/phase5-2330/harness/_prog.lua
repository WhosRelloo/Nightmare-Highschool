local SSS = game.ServerScriptService.Services
local Pr = require(SSS.Player.Progression).Get(P)
local t = {} for k, v in Pr.Paths do table.insert(t, k .. "=" .. v) end
return "Level " .. Pr.Level .. " Exp " .. Pr.Exp .. " paths " .. table.concat(t, ",")
