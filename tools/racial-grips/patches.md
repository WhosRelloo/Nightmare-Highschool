# 2.6.0 racial grips: Studio edits (NH Combat Test)

Backups: `ServerStorage.NH_Backup.RacialGrips_pre220` (Downed, Features.RaceAction, Misc.RaceAction, RaceActionFx,
Config.Downed, TouchControls).

## New
- `ReplicatedStorage.Config.RaceGrips`: `luau/Config.RaceGrips.luau` (race -> Kind, clips, offsets, beats, colours,
  sound/texture ids, fallbacks).
- `StarterPlayerScripts.Controllers.World.RaceActionFx.RaceGripFx`: `luau/Controllers.World.RaceGripFx.luau` (client
  VFX, sound, camera; a child module so the controller loader doesn't start it on its own).
- `ServerStorage.NH_GripAnims`: the 11 KeyframeSequences for the owner to publish, plus `Builder` (a Studio-only
  tool that rebuilds them from `out/*.pack.luau`).

## Features.Downed
- `StartGrip(Gripper, Override)`: `Override.Offset` (CFrame). With it, the victim is made massless, `Ragdoll` group,
  server-owned, `PlatformStand`, pivoted to `Root.CFrame * Offset` (offset scaled by `Gripper:GetScale()`), and held by
  a `GripWeld` (Part0 gripper root, Part1 victim root, C0 = Offset). Without it, the old `GripVictimOffset` placement.
- `Record.Weld`, `Record.Saved` on the grip record.
- `Local.EndGrip(Gripper, Finished?)`: a finished racial grip freezes the victim clip on its last (lying) frame and
  destroys it 1.5 s later; the weld is removed, mass/collisions restored, `PlatformStand` off; an interrupted grip sets
  the living body down where it is (`PlaceAt`) and gives a player back network ownership.
- `FinishGrip` calls `EndGrip(Gripper, true)`.
- `GrippedBy` is set on the target before `GripEndsAt` on the gripper (Features.RaceAction looks the victim up on it).

## ActionManager.Misc.RaceAction
- `BY_RACE` = `Config.RaceGrips.ByRace` (Werewolf -> `Maul`, Human -> `Stake`).
- `clipId(Id, ClipName)`: the published id, else in Studio a temporary id from
  `KeyframeSequenceProvider:RegisterKeyframeSequence(ServerStorage.NH_GripAnims[ClipName])`.
- `overrideFor(Kind)`: gripper + victim + `Offset` when both clips resolve, else the old single clip
  (`Config.RaceGrips.Fallback`).
- The unholy-only check reads `Kinds[Kind].UnholyOnly` (Priest only; Humans now stake any body).

## Features.RaceAction
- `HEAL` / `FEED` gain `Maul` (0.35 / 30) and `Stake` (0.2 / 0).
- The channel Fx carries `Victim` (the model whose `GrippedBy` is the gripper), `Sub` (the gripper's `SubRace`) and
  `VictimRace`.

## Controllers.World.RaceActionFx
- Requires `RaceGripFx`, `Init(Fx)`; a Kind it handles goes to `RaceGripFx.Play` (finish events ignored).
- The old fallback colours are no longer blood: EatBody grave dust (96, 104, 80), BloodDrain pale rose (244, 214, 222).

## Controllers.Gui.TouchControls
- `RACE_ACTION`: Human `STAKE`, Werewolf `MAUL`.
