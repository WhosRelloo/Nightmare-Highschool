local SS = game:GetService("SerializationService")
local HS = game:GetService("HttpService")
local items = {
  game.ServerStorage.NHRaceCosmetics,
  game.ServerScriptService.NHLineage,
  game.ServerScriptService.Services.Player.RaceCosmetics,
  game.ServerScriptService.Services.Features.NightSight,
  game.StarterPlayer.StarterPlayerScripts.Controllers.Character.TailSway,
  game.StarterPlayer.StarterPlayerScripts.Controllers.Character.NightSight,
  game.StarterPlayer.StarterPlayerScripts.Controllers.Gui.Bloodline,
}
local buf = SS:SerializeInstancesAsync(items)
local j = HS:JSONEncode(buf)
return j
