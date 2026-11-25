-- the server's moon event as on a real crimson night: Lineage.MoonEvent returns Crimson, MoonPhases ticks it out
local Lineage = require(game.ReplicatedStorage.Lineage)
_G.NHSkyOpenEvent = _G.NHSkyOpenEvent or Lineage.MoonEvent
Lineage.MoonEvent = function() return "Crimson" end
require(game.ServerScriptService.Services.Features.MoonPhases).Tick()
task.wait(1)
return "PASS event set: " .. tostring(workspace:GetAttribute("NHMoonEventTonight"))
