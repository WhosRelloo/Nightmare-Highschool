# 07. Technical Architecture Plan

## 1. Conventions to follow (from the code as it is)
- **Modules:**
  - services are ModuleScripts with `Shared` and `Local` tables;
  - a service's start-up code lives in `OnStart`;
  - config goes in `ReplicatedStorage.Config.<X>`, with a `Sanitize` function for anything saved.
- **Saving:** only through `Data.UpdateState(P, {type = "Set<Block>"; ...})`. **One owner per block.** New blocks need a `PlayerData` default, a `Set` action in `Functions.UpdateState`, and a `Sanitize` for old saves.
- **Remotes:** feature folders `ReplicatedStorage.NH<Feature>`, made at runtime, each with its own rate limit; `Packets` for the hot paths. Keep new remotes few: one folder per new service at most.
- **Rewards:**
  - EXP only through `Progression.Award`;
  - buffs only through `Progression.Effects`;
  - Yen through `UpdateYen`;
  - titles through `Reputation.AwardTitle`.
- **Camera:** only through `CameraLease`.
- **UI:** `UI.Components` (the kit), `Kit.AutoScale`, the Theme. Every new screen follows the UI rule: unique, on theme, PBR, animated.
- **Testing:** `Services.Studio.TestBridge` commands, slot 4 "Testy", real input for feel tests.

## 2. Existing modules to extend

| Module | Extension |
|---|---|
| `School.SchoolClock` | `IsNight()`, `Phase()` (dusk / night / deep), `Term()`, `Week()`. Systems move onto `PeriodChanged`. |
| `Features.Schedules`, `AI.StudentBrain` | Rostered students, per-student timetables, teacher, custodian and Headmaster roles, abstract simulation far from players, memory backed by Relationships |
| `School.Activities` | The Bench mode (a game-module variant `Bench = true`), Lab Partners, exams, class-level unlocks |
| `School.Attendance`, `Config.Classes` | Elective periods, a per-student timetable lookup |
| `School.HallMonitor`, `Config.Discipline` | Night duty, the curfew rule, teacher witnesses |
| `Social.Reputation` | The NPC list grows to the cast and roster; a `Rival` flag; the entry cap |
| `Social.Superlatives`, `CliqueEvents` | Weekly competitions, the Pecking Order |
| `Player.Progression` | The Paths evaluator, Honours, Legacy marks, extra fields on the Record sheet |
| `Quests.Quests`, `Config.Quests` | A `Kill` objective, a `Decision` objective (choice → `Quests.Decisions`), a `Cinematic` field on stages, an `Enrol` objective, Chapters 2-5 |
| `Quests.Investigation`, `Config.Cases` | New cases, shared party evidence, role-split clues |
| `Features.Phone` | The Midnight Broadcast station, Bestiary, Today card, Archive bookmarks |
| `Features.Homes` | The trophy wall, decor slots |
| `Features.Beasts` | Traces, a kill tally, the Bestiary state |
| `Social.Dialogue` | `ctx.PathTier`, `ctx.Skill`, `ctx.Decided`, Persuade choices; the talk shot moves onto Cine/CameraLease |

## 3. New modules

| Module | Purpose |
|---|---|
| `Services.World.Incidents` | The incident bus (`Emit`, `On`) plus the scene director (`Config.Scenes`) |
| `Services.Social.Rumours` | Rumour facts, spreading, mutation, outputs |
| `Services.World.Broadcast` | Content items, sent to the Gazette, Night FM station and PA |
| `Services.World.Crisis` | Blackout, Lockdown and Bell events (rare, opt-in) |
| `Services.World.Cine` + `Controllers.Cine` | The cinematic framework (see 04) |
| `Services.School.Bench` (inside Activities) + `Controllers.Gui.Bench` | The shared bench engine: viewport, tools, intents |
| `ServerStorage.Activities.<Subject>Bench` | One per subject or elective |
| `Services.Social.Archive` + `Gui.Archive` | The School Archive and Yearbook, with changing records |
| `Config.Paths`, `Config.Honours`, `Config.Students`, `Config.Scenes`, `Config.Broadcast`, `Config.Archive`, `Config.Recipes` | Data |

## 4. Data changes (all additive, migrated by Sanitize)

| Field | Owner | Shape | Size budget |
|---|---|---|---|
| `Progress.Paths` | Progression | `{Academic=n, Social=n, Combat=n, Athletic=n, Supernatural=n}` | tiny |
| `Progress.Honours` | Progression | `{[id] = day}` (about 60 max) | under 2 KB |
| `Progress.Record` | Progression | the last 40 `{d, k, t}` entries | under 4 KB |
| `Progress.Yearbook` | Progression | one entry per term (tiers, titles, a superlative) | under 0.3 KB per term |
| `Progress.Legacy` | Progression | number | tiny |
| `Social.Relationships` | Reputation | expanded to 64 entries max `{V, Met, Last, Flags}` | under 4 KB |
| `Quests.Decisions` | Quests | `{[decisionId] = choice}` | under 1 KB |
| `Classes[Subject].Bench` | Activities | `{BestScore, Recipes}` | small |
| `Classes.Electives` | Activities | `{Term = n, Pick = id}` | tiny |
| `Lineage` / Beasts | Beasts (new owner `Bestiary`) | `Inventory.Bestiary = {[beast] = {State, Kills}}` | small |
| `Phone.Broadcast` | Phone | the last read item id | tiny |
| `Housing.Decor` | Homes | 12 slots of item ids | small |
| `Inventory.Archive` | Archive | a bitset of 24 pages | tiny |

**The profile limit:** each save slot is its own ProfileService key, so the 4 MB limit applies per slot. *(Corrected in Phase 0: the audit first said one profile held every slot.)* Measured in Phase 0: Testy's whole slot is 20.7 KB. The new fields add about 12 KB per slot at most. A TestBridge check should still warn above 1 MB.

## 5. Performance considerations
- **NPC students:** abstract simulation beyond 160 studs. Brains run at 5 Hz near players and 1 Hz otherwise, as today. At most 3 path plans at once, as today. The target is 40 students at 60 fps server and client.
- **Scenes:** only where a player can see; at most 1 per region per 10 minutes.
- **Rumours:** they spread on a 5-minute hop timer, not every frame.
- **The bench:** a ViewportFrame with fewer than 150 parts and no physics. Interpolation runs on the client; the server validates intents only.
- **Loops:**
  - **Merge** the 1 s / 5 s per-player loops where they share data (Kit, Body).
  - **Do not add** a new per-frame server loop.
- **The clock:** night and phase come from `SchoolClock`, with no extra polling.

## 6. Security
- **Rewards and progression:** every reward, path tier, honour and decision is granted on the server.
- **Client input:** clients send intents only (bench, photography, arcade), each with plausibility checks and rate limits. This follows the Arcade and Regions patterns.
- **Photography checks:** the server re-checks the camera pose against the character position (within 60 studs), the subject's line of sight, and the time.
- **Group cinematics and investigations:** party membership is checked on the server, and shared evidence is granted per player.

## 7. Dependencies (build order matters)
```
SchoolClock helpers ─┬─> Curfew/HallMonitor night duty ─> Crisis
                     ├─> Schedules (PeriodChanged) ─> Teachers ─> Discipline witnesses
                     └─> Terms/Yearbook
Incidents bus ─┬─> Rumours ─> Broadcast (Gazette, Night FM, PA)
               └─> Scene director ─> Rivals (scenes), Crisis
Config.Students roster ─> Relationships (expanded) ─> Rivals, NPC recognition, Ch.2 story
Bench engine ─> 4 subjects ─> Electives ─> Exams ─> Academic path
Paths evaluator ─> Record ─> Honours ─> Yearbook/Archive
Cine framework ─> Prologue, chapter cuts, crisis openers
Quests: Kill/Decision/Cinematic/Enrol objectives ─> Orientation ─> Chapters 2-5
```
