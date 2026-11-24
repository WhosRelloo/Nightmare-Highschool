# Headmaster's Console icons

49 icons, rendered by `admin_console_icons.py` (Blender 5.2, headless) with the console's own materials, world and lights
(it loads them from `admin_console_render.py`): dark iron, warm brass, crimson enamel, ruby, enamel glass.

- **Size:** 64 x 64 design px, rendered at 256 x 256 (4x) on a transparent background. Shown in the card and rail wells
  (about 56-60 px); downscale in Studio with the image's own scaling.
- **Files:** `icons/<Name>.png`. Uploaded by the owner to group 15981569 (2026-11-23); the ids are below and in
  `icons/icon_ids.json` (name -> id) for the registry's `Icon` field (spec §7, §9).
- **SecStory** came back from Roblox's text filter named `########`; it's the one id in that upload not matched by
  name, and its thumbnail was still pending moderation when the ids were read.
- **Re-render:** `E:/Blender/blender.exe -b --factory-startup -P admin_console_icons.py -- <out dir> [--quick] [--only A,B]`.

## Sections (11)
| Icon | Asset id | Section | Shape |
|---|---|---|---|
| `SecInbox` | 95035139369207 | Inbox | envelope with a ruby wax seal |
| `SecStudent` | 115306112083184 | Student | head and shoulders, crimson collar |
| `SecServer` | 92795627635687 | Server | crenellated tower |
| `SecLog` | 115218002147460 | Log | open ledger with a crimson ribbon |
| `SecCharacter` | 72993194183747 | Character | hand mirror |
| `SecProgress` | 93296547567079 | Progress | rank chevrons under a star |
| `SecSchool` | 115579607387909 | School | handbell |
| `SecStory` | 95010997491386 | Story | scroll with a seal |
| `SecWorld` | 138024999177884 | World | globe in a brass ring |
| `SecSpawns` | 87056821825876 | Spawns | skull with ruby eyes |
| `SecSelf` | 94734540524253 | Self | spread wing |

## Card families (38)
| Icon | Asset id | Cards |
|---|---|---|
| `Warn` | 77485447807777 | Warn |
| `Mute` | 90143520775357 | Mute / Unmute |
| `Freeze` | 131097727643904 | Freeze, Freeze all / Thaw all |
| `Jail` | 133918737992261 | Jail (detention), Owe / Clear detention |
| `Spectate` | 104190161758038 | Spectate, Stop spectating, ESP |
| `Bring` | 79287268573816 | Bring, Bring all |
| `GoTo` | 111475072999017 | Go to, Go to a place, Ctrl+click teleport |
| `Kick` | 135635025217179 | Kick |
| `Ban` | 127382052675224 | Ban (all lengths) |
| `Note` | 140641574037318 | Note |
| `Announce` | 94988139909965 | Announce |
| `Lock` | 91891196400925 | Server lock |
| `Shutdown` | 107963521689040 | Shutdown |
| `Health` | 127282998954478 | Health graphs (FPS, memory, ping) |
| `Resolve` | 124529766373542 | Claim, Resolve (Inbox) |
| `Dismiss` | 95835375715991 | Dismiss (Inbox) |
| `Heal` | 91323313032733 | Heal |
| `Revive` | 127057893991963 | Revive |
| `God` | 79259629304369 | God mode |
| `Kill` | 139180791709719 | Kill |
| `Speed` | 104165011075607 | Speed, Fly |
| `Race` | 90132712022108 | Race and sub-race, Tier |
| `Height` | 74824922408597 | Height, Build |
| `Transform` | 71171496660227 | Transform, Form direction |
| `Yen` | 88678668054857 | Give Yen |
| `Exp` | 114592008444465 | EXP, Set level, Stat points, Titles |
| `Gear` | 115892810789128 | Gear, Spins |
| `Time` | 106222595405962 | Set time, clock speed, skip to a period, Time presets |
| `Season` | 105858687937395 | Season |
| `Moon` | 110126809361473 | Moon, Sky override and Storm |
| `Cutscene` | 122249876131186 | Play any cutscene, mark Seen / clear |
| `Tutorial` | 131698612815057 | Tutorial (enter, checkpoints, leave) |
| `Clues` | 108215265810454 | Case clues and insights, Places found |
| `Wolf` | 134468429837408 | Wolf pack, Sparring partner |
| `Beast` | 132090400116155 | Each Beast, Delinquent crew |
| `Teleport` | 132139114405901 | Staff teleport flock, Noclip |
| `Invisible` | 86781183011373 | Invisible, "Preview just for me" |
| `Discipline` | 82459696704686 | Discipline points, Excuse today, Lift suspension, Bell Tower (Heat, Bells, summons, notoriety, hall monitors, Wanted) |

Cards not listed fall back to their section's icon (Name change, Clubs, start a lesson, ring the bell, quests, Clear all
enemies, the inspector).
