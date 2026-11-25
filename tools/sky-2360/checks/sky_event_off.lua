local Lineage = require(game.ReplicatedStorage.Lineage)
if _G.NHSkyOpenEvent then Lineage.MoonEvent = _G.NHSkyOpenEvent _G.NHSkyOpenEvent = nil end
require(game.ServerScriptService.Services.Features.MoonPhases).Tick()
return "PASS event restored: " .. tostring(workspace:GetAttribute("NHMoonEventTonight"))
