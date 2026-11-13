# Armory 2.5.0: install notes

New scripts (byte-identical in NH Combat Test and the Map; checked by checksum on 2026-11-13):
- `ReplicatedStorage.Config.Armory` (ModuleScript): `ReplicatedStorage.Config.Armory.luau`
- `ServerScriptService.Services.Features.Armory` (ModuleScript): `ServerScriptService.Services.Features.Armory.luau`
- `StarterPlayer.StarterPlayerScripts.Controllers.Gui.ArmoryUi` (ModuleScript): `StarterPlayer.StarterPlayerScripts.Controllers.Gui.ArmoryUi.luau`

The booth: `build_placeholder.luau` (the two calls for each place are at its bottom).

Targeted patches (each marked `(armory)`; backups in `ServerStorage.NH_Backup.Armory_pre_20261112`):

| Script | Patch | Places |
|---|---|---|
| `ReplicatedStorage.PlayerData` | type line `Armory: { [string]: any };`; default `Weapon = \`Fist\`;` and `Armory = {};` | both |
| `Services.Player.Data` | Combat Test: after `Profile:Reconcile()`, `pcall(require(ReplicatedStorage.Config.Armory).Migrate, Profile.Data)` (warns on error). Map: the same call in `LoadSlot` before `Profiles[Player] = Data` | both |
| `Services.Managers.EntityLoader` | non-player branch: `clonedData.Weapon = \`Katana\`` right after the `table.clone` of the defaults (NPCs and dummies keep Katana) | both |
| `Services.Features.ClassLocker` | requires `Config.Armory`; `Info` sends `Open = owned`, `Owned`, `Price`, `Locked` and the "Sold at the armory" / "Locked for now." blurbs; `Pick` refuses a class you don't own | Combat Test patched; Map: new (it had none), same source |
| `Controllers.Gui.ClassLocker` | the button reads **At the armory** / **Locked** for a class you don't own | Combat Test patched; Map: new, same source |
| `Cmdr.Commands.Adjust.AdjustWeaponServer` | `Config.Armory.Grant(Profile, Weapon)` before the `UpdateWeapon` | Combat Test (the Map has no Cmdr) |
