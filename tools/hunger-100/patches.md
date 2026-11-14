# Hunger 1.0: edits to existing scripts (NH Combat Test)

New modules (whole files here, installed with `install.py`, checksummed):
- `ReplicatedStorage.Config.Body`
- `ServerScriptService.Services.Features.Body`
- `StarterPlayer.StarterPlayerScripts.Controllers.Gui.HungerVessel`

Backups of everything edited below: `ServerStorage.NH_Backup.Hunger_pre`.

## ReplicatedStorage.Functions.UpdateState
- Type: a `SetBody` action (`body: any`) after `SetHousing`.
- Handler: `if Action.type == \`SetBody\` then PlayerData.Body = Action.body end`, after `SetTraining`.

## ReplicatedStorage.PlayerData
- Type: `Body: { [string]: any }` before `Phone`.
- Default: `Body = {};` after `Training = {};`.

## ServerScriptService.Services.Features.Inventory
- **`Shared.Use`:** after the taste-book milestone, it feeds hunger:
  `pcall(function() require(ServerScriptService.Services.Features.Body).Ate(P, It) end)`.
- **`Shared.KitEat`:** after `Local.Heal(...)`, it feeds hunger:
  `pcall(function() require(ServerScriptService.Services.Features.Body).AteHeal(P, Heal) end)`.
- **`Shared.UseBest`:** at full health, `return Local.UseBestHunger(P, Inv)` replaces `return false, "You're not hurt."`.
- **`Local.UseBestHunger(P, Inv)`** (new, before `Shared.Undo`):
  - below 70 hunger, it eats the cheapest Heal or Buff that brings hunger to about 80 for your race
    (`Config.Body.Gain`), else the most filling one;
  - otherwise it says "You're not hurt or hungry." (or "Nothing here will feed you." for races that don't eat food).

## ServerScriptService.Services.Features.RaceAction
- In `Downed.OnExecuted`, after `Evolution.Feed`, it feeds hunger:
  `if P then pcall(function() require(ServerScriptService.Services.Features.Body).Fed(P, Kind) end) end`.

## ServerScriptService.Services.Player.Progression
- In `Shared.Effects`, after the taste book, a pcall block adds `Body.Effects(Player)` as `Sources.Hunger`.

## ServerScriptService.Services.Studio.TestBridge
- `Commands.Body(name, "State" | "Set", n | "Tick", seconds | "Eat", itemId | "Fed", kind | "Effects" | "Saved")`.

## StarterPlayer.StarterPlayerScripts.Controllers.Gui.SnackWheel
- **`Local.Socket`:** a `HungerChip` pill at the top of each well:
  - "+N" in the race colour (`Config.Body.Gain`);
  - or `<s>+N</s>` in grey when the race can't eat it.
- **`Local.Render`:** the chip fades with the count pill.
