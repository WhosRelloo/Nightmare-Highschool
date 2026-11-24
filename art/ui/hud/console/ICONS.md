# Headmaster's Console icons

49 icons, rendered by `admin_console_icons.py` (Blender 5.2, headless) with the console's own materials, world and lights
(it loads them from `admin_console_render.py`): dark iron, warm brass, crimson enamel, ruby, enamel glass.

- **Size:** 64 x 64 design px, rendered at 256 x 256 (4x) on a transparent background. Shown in the card and rail wells
  (about 56-60 px); downscale in Studio with the image's own scaling.
- **Files:** `icons/<Name>.png`. Upload to group 15981569 with the console art; the registry's `Icon` field takes the
  name until an asset id exists (spec §7, §9).
- **Re-render:** `E:/Blender/blender.exe -b --factory-startup -P admin_console_icons.py -- <out dir> [--quick] [--only A,B]`.

## Sections (11)
| Icon | Section | Shape |
|---|---|---|
| `SecInbox` | Inbox | envelope with a ruby wax seal |
| `SecStudent` | Student | head and shoulders, crimson collar |
| `SecServer` | Server | crenellated tower |
| `SecLog` | Log | open ledger with a crimson ribbon |
| `SecCharacter` | Character | hand mirror |
| `SecProgress` | Progress | rank chevrons under a star |
| `SecSchool` | School | handbell |
| `SecStory` | Story | scroll with a seal |
| `SecWorld` | World | globe in a brass ring |
| `SecSpawns` | Spawns | skull with ruby eyes |
| `SecSelf` | Self | spread wing |

## Card families (38)
| Icon | Cards |
|---|---|
| `Warn` | Warn |
| `Mute` | Mute / Unmute |
| `Freeze` | Freeze, Freeze all / Thaw all |
| `Jail` | Jail (detention), Owe / Clear detention |
| `Spectate` | Spectate, Stop spectating, ESP |
| `Bring` | Bring, Bring all |
| `GoTo` | Go to, Go to a place, Ctrl+click teleport |
| `Kick` | Kick |
| `Ban` | Ban (all lengths) |
| `Note` | Note |
| `Announce` | Announce |
| `Lock` | Server lock |
| `Shutdown` | Shutdown |
| `Health` | Health graphs (FPS, memory, ping) |
| `Resolve` | Claim, Resolve (Inbox) |
| `Dismiss` | Dismiss (Inbox) |
| `Heal` | Heal |
| `Revive` | Revive |
| `God` | God mode |
| `Kill` | Kill |
| `Speed` | Speed, Fly |
| `Race` | Race and sub-race, Tier |
| `Height` | Height, Build |
| `Transform` | Transform, Form direction |
| `Yen` | Give Yen |
| `Exp` | EXP, Set level, Stat points, Titles |
| `Gear` | Gear, Spins |
| `Time` | Set time, clock speed, skip to a period, Time presets |
| `Season` | Season |
| `Moon` | Moon, Sky override and Storm |
| `Cutscene` | Play any cutscene, mark Seen / clear |
| `Tutorial` | Tutorial (enter, checkpoints, leave) |
| `Clues` | Case clues and insights, Places found |
| `Wolf` | Wolf pack, Sparring partner |
| `Beast` | Each Beast, Delinquent crew |
| `Teleport` | Staff teleport flock, Noclip |
| `Invisible` | Invisible, "Preview just for me" |
| `Discipline` | Discipline points, Excuse today, Lift suspension, Bell Tower (Heat, Bells, summons, notoriety, hall monitors, Wanted) |

Cards not listed fall back to their section's icon (Name change, Clubs, start a lesson, ring the bell, quests, Clear all
enemies, the inspector).
