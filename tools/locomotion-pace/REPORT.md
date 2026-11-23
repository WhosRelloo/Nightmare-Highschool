# locomotion-pace: report (2026-11-23)

Owner: "fix the running speed and animation. It's too fast. Make sure NPC's follow the same animation rules as players too."
Owner picks: sprint "22 then 30", walk "10 everywhere". Reference: `docs/Movement.md` § Speeds and gaits.

## What's here
- `pre/`: the 15 scripts as fetched from NH Combat Test before the change (also in Studio at
  `ServerStorage.NH_Backup.LocomotionPace_pre_20261123`).
- `live/`: the 15 scripts as installed.
- `install_inplace.py`: sets `.Source` on the existing instances (keeps class, children and attributes). It refuses
  everything if a live script no longer matches `pre/` or a new source doesn't parse.

| Script | Change |
|---|---|
| `ReplicatedStorage.Config.Locomotion` | `Speeds` (Walk 10, Sprint 22, FastSprint 30, FastAfter 2, Attacking 7), `Gaits` (WalkMax 12, SprintMax 26) |
| `ReplicatedStorage.Functions.Locomotion` | `Gait(Set, Ground, Cfg)` |
| `Controllers.Character.AnimationController` | the clip by `Loco.Gait` (was > 40 / > 20) |
| `Services.AI.AI.Animate` (Script) | `Loco.Gait` + `Loco.Rate` on its own legs; no jump or fall clip while sprinting; the `Land` one-shot |
| `Services.Features.Schedules` | students: `Loco.Gait` + `Loco.Rate` (was Speed > 10, `WALK_PACE` / `RUN_PACE`) |
| `Services.Managers.StateManager` | every reset hands back `Speeds.Walk` (was 14.4); Attacking `Speeds.Attacking` (was 10) |
| `Services.Player.ActionManager.Movement.Sprint` | `Speeds.Sprint` / `FastSprint` / `FastAfter` / `Walk` (was 25 / 40.5 / 2 / 12) |
| `Services.Player.Evolution`, `Services.World.Cine` | fallback `Speeds.Walk` (was 14.4) |
| `Services.Player.Crouch` | fallback `Speeds.Walk` (was 12) |
| `Config.Downed` | `CarryWalkSpeed` 8 (was 12) |
| `Config.NPC` | `PatrolSpeed` 10 (was 12) |
| `Services.Features.CombatSpeed` | trained-legs bonus from `Raw >= Speeds.Sprint` (was 24) |
| `Controllers.World.ContactFeel`, `Controllers.CineBeat` | comments; CineBeat's `WALK` reads `Speeds.Walk` (was 12) |
| `StarterPlayer.CharacterWalkSpeed` (property) | 10 (was 16) |

## Checks (Play, slot 2, fresh snapshot, restored)
CineState / Seen / Origin: nil / nil / nil before and after. Console: no errors from these scripts (only the existing
sound-permission errors).

**Player**, measured on the client (a probe LocalScript; 0.86-height body, 1.615-stud legs), driven by `MoveTo`:

| WalkSpeed | Ground | Clip | Rate | Stride-matched |
|---|---|---|---|---|
| 10 | 10.0 | Walk | 2.06–2.10 | 2.10 |
| 22 | 22.0 | Sprint | 2.02 | 2.02 |
| 30 | 30.0 | FastSprint | 2.06 | 2.06 |
| 10 (back) | 10.0 | Walk | 2.10 | 2.10 |
| 7 | 7.0 | Walk | 1.47 | 1.47 |

Before, at 14.4 / 25 / 40.5, this body hit the 2.4× cap on the walk and the fast sprint (the feet slid) and ran the
sprint at 2.29×. A stun during the run reset the walk to 10 (8 under the combat tag's 0.8), not 14.4.

**AI NPCs** (`Workspace.Live`, 1.8-stud legs), on the server where they play:

| NPC | Speed | Clip | Rate | Stride-matched |
|---|---|---|---|---|
| Hall Monitor | 7 | Walk | 1.32 | 1.32 |
| Delinquent / Brute | 8 | Walk | 1.50 | 1.51 |
| Mr. Hale | 6 | Walk | 1.12 | 1.13 |
| Delinquent (forced) | 22 | Sprint | 1.81 | 1.81 |
| Delinquent (forced) | 30 | FastSprint | 1.84 | 1.85 |

**Schedule students** (2.03-stud legs): stroll 6 → Walk 1.02 (1.00); forced flee at 13 → Sprint 1.00 (was the walk clip
at about 2.4×).

## Open
- **A fresh spawn at 10 isn't checked in Play yet.** The template Humanoids held 14.4 and overrode
  `CharacterWalkSpeed`: `StarterPlayer.StarterCharacter.Humanoid` (players spawned at 14.4 until the first sprint or state
  reset) and `ServerScriptService.Services.AI.AI.Rig.Humanoid`. Both are set to 10 in Edit (2026-11-23, after the round).
  The Studio MCP's start/stop was stuck ("Start play hasn't finished yet") for the rest of the session.
- **Owner eye:** whether the new pace looks right in motion, above all on short bodies, which step at about 2× to keep
  their feet planted.
- **Not saved:** the place needs the owner's word to save.
