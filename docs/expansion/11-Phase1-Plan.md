# 11. Phase 1 Build Plan: the narrative framework and the prologue

**Target:** NH Combat Test only, version 2.24.0. The Map and production stay untouched.
**Backups:** every script is backed up to `ServerStorage.NH_Backup.Phase1_pre_20261117` before it's edited.
**Mirror:** `tools/phase1-2240/` (`pre/` before, `live/` after).

## What gets built

### 1. The Cine framework (doc 04)
| Piece | Where | What it does |
|---|---|---|
| Cine server | `Services.World.Cine` (new) | `Cine.Play(players, id, opts)`. It freezes and protects the real character, saves the cut as "started" before it plays, collects skip votes (a strict majority; anyone who has seen the cut votes skip automatically), forces Done after the cut's length + 5 s, and replays an unfinished cut once on rejoin, with Skip offered. |
| `NHCine` remote | `ReplicatedStorage.NHCine` | One RemoteEvent: Play (server to client), Done, Skip and Vote (client to server), rate-limited. |
| Cine director | `Controllers.Cine` (new) | Plays a shot list from `ReplicatedStorage.Cinematics.<Id>`. Built on the skill's `Cine.lua`: shot sizes, lenses in mm, moves, DOF, grade, events. It only takes the camera through `CameraLease`, eases in from gameplay, lands behind the player's shoulder and gives control back after a 0.3 s grace. Reduce Motion turns moves into cuts with no shake or Dutch roll. |
| Character director | inside `Controllers.Cine` | Client-side clones on marks: the player's own clone, Hale, and students dressed with `NpcLooks` specs. The real character stays where it is. |
| Cine UI (subtitle UI) | inside `Controllers.Cine` | Letterbox bars, a bottom-third subtitle plate (speaker and line), a chapter card and a large Skip button with a vote count. It follows the kit (Theme colours and fonts), uses the kit's PBR paper and brass images, animates in and out, and keeps text at 20 px or more on phones. |

### 2. Quest objectives (`Quests.Quests`, `Config.Quests`)
- **`Cinematic`** `{ Cut = id }`: plays the cut when the stage is reached, and completes on Done, Skip or the server timeout. On rejoin, an unfinished one plays again.
- **`Decision`** `{ Decision = id, Choices = {...} }`: completes when the player chooses in a dialogue. The choice is saved in `Quests.Decisions[id]`, and dialogue gets `ctx.Decide` and `ctx.Decided`.
- **`Kill`** `{ Kind = "Beast" | "Wolf" | "Student" | "Player" | "Any", Target? , Count }`: counts defeats from `Downed.OnDefeated`.
- **`Enrol`**: already shipped in 2.22.0 (Phase 0). It's reused as it is.

### 3. Orientation, the first-day tutorial (new Main quest, before New Kid)
1. **Cinematic:** the prologue roll call.
2. **Talk:** report to Mr. Hale.
3. **Decision:** answer his question about the roll call. The choice is saved, and nothing is locked by it.
4. **Reach:** find Room 102, the back row.
5. **Kill, optional:** knock down the training dummy.

When it's done, **New Kid** starts as it does today, Enrol step first.
- New Kid gains `Requires = { Orientation }` for new slots only.
- Old saves keep their New Kid exactly as it is.

### 4. Two cuts, staged where the Map is built
The owner's direction: stage things where they'll go in the **Map place**, and leave out what isn't built yet.
- **Built in the Map:** the hallways and classrooms, the garden (about 50%) and the library (about 80%).
- **Left out:** the front yard and the gate (the yard is bare), the bell tower, the staff room and the Records Office (none of them built yet). No cut and no NPC post depends on them.

**Sets, not coordinates.** Each cut frames its shots from named marks in `workspace.NHCineSets.<Set>.<Mark>`, such as `RollCall.TeacherDesk` and `RollCall.BackRowDesk`. Each place has its own marks.
- **NH Combat Test:** the marks sit in the blockout (R102 and the main hallway).
- **The Map, at port time:** the same marks go in the real rooms, so the cut's data ports unchanged.

| Set | In the Map (where it will go) | In NH Combat Test (now) |
|---|---|---|
| **Entrance** | The entrance hall with the grand staircase, inside the front doors (about x -925, z 52), looking down the west hallway | The west end of the main hallway |
| **Room 102** ("Room 102. Back row.") | The first ground-floor classroom west of the entrance hall: chalkboard on the east wall (x -982, z 88), teacher's desk at x -987, a 3 x 4 grid of desks, and the back row at x -1007. The door is on the hallway side (x -1003, z 67). | `School.R102`, with the back-row desk at the existing DeskCarving clue |
| **Hall at night** | The west hallway (chandeliers, the window wall) | The main hallway |

| Cut | Length | Shots |
|---|---|---|
| **Prologue: Roll Call** | about 25 s | Opens from the menu's black "The bell is ringing..." into the entrance hall as the bell rings (a still wide at 22 mm). Students hurry down the hallway (tracking). Then Room 102 from the back row: Mr. Hale reads the register, students answer, and your own student answers to your name. Then "Holt. Mira Holt." Silence. A close-up of the empty back-row desk at 85 mm, with this chapter's one dolly zoom. Hale looks up, frowns, and moves on. It ends behind your shoulder wherever you are. |
| **COLLECTED (Chapter 1 end)** | about 12 s | Added as a final `Cinematic` stage on After Hours. An insert of Mira's file, where "STATUS: COLLECTED" writes itself in red. A wide of the hallway at night: the Night Custodian stands at the far end, his face never seen. The bell rings once. Card: "End of Chapter One: The Empty Desk". |

Each cut must pass `Cine.analyze` with no `[fix]`, and captured key frames are reviewed.

### 5. Mr. Hale and the Night Custodian (existing NPC builder: `Config.Npcs`, `Social.Npcs`, `NpcLooks`)
Today both exist only as stealth watchers, in the staff room and the Records Office. Neither room is built in the Map.
- **Mr. Hale:** a post at the teacher's desk in **Room 102** (his homeroom).
- **The Night Custodian:** a post in the **main hallway** by day, sweeping, with his face kept in shadow. After hours he patrols the Records Office as today (NH Combat Test only).
- **Posts:** each post is an `NpcPost` part. In the Map they go at the Room 102 desk and in the west hallway.
- **Dialogue:** each gets a tree (`ServerStorage.Dialogue.Hale`, `.Custodian`). Hale won't answer about Room 102, as Chapter 1 asks.

## Acceptance (in Play, slot 4 "Testy")
- A new slot gets the prologue once, can skip it on a replay (Journal: "Watch again"), and lands in Orientation, then New Kid.
- A disconnect mid-cut is recovered on rejoin: Play is stopped mid-cut, then started again.
- A two-player group cut vote works.
  - The MCP can only start a one-player Play, so the vote logic is also proven by a TestBridge self-test with a stand-in second viewer.
  - The real two-client run needs Studio's "2 Players" test, started by you. The steps go in the report.
- ENTER SCHOOL and the gate transition are unchanged: `MainMenu` isn't edited, and the cut starts after the menu has finished.
- No console errors from game scripts. The camera returns to Custom, and no `Cine*` leftovers remain.

## What the story bible's [OPEN] items mean for Phase 1
- **Corvin and the bell years:** not needed. Neither cut names the Headmaster or a year.
- **Vesper and Crane:** not touched.
- **Defaults used unless you say otherwise:**
  - Mr. Hale reads the roll.
  - Only new slots get the prologue and Orientation.
  - The Night Custodian's face is never shown.
  - COLLECTED is the file, then the Custodian, then the bell.

## Results (2.24.0, 2026-11-17)

Built as planned in NH Combat Test, with these differences:
- **No training-dummy stage.** Orientation's optional Kill stage was dropped. `Kill` exists and is self-tested, so a
  later quest can use it.
- **Two clocks in a cut:** a cut can set its hour (`Clock`). The roll call plays in morning light and COLLECTED at
  midnight, whatever the server time. `Controllers.World.DayCycle.HoldHour` holds the whole look (light, atmosphere,
  sky) for the cut.
- **Walking reuses the game's clip:** walkers play the Default walk at a rate matched to their speed. Short steps and
  standing up use the pose layer, with the root height following the hips (no pop).
- **Every other body is hidden during a cut:** not only `workspace.Live`. That covers the class in session, the
  substitutes, background students, shopkeepers and dummies.
- **Seats:** the classmates sit where the coverage cameras can see past them. The column beside the back camera stays
  clear, and nobody sits in front of Mira's desk (Hale's eyeline).
- **The bell:** the set's `Bell` mark picks the bell (the nearest part named in `BellPart`). The Map has 61 bells with
  the same full name.

**Checks:** see the 2.24.0 CHANGELOG entry. Each cut analyzes with 0 fixes when the actors are posed where the cut puts
them at each shot.

### Map port table (starting values; check each by screenshot when the Map gets them)

The owner's rule: the Map's builds are not touched until the owner says so. These are where the same marks go in the
Map's real rooms, measured read-only on 2026-11-17.
- **Room 102:** students face +X (east), the board is at x -981.7, the floor is at y 0.
- **The room's walls:** x -981.5 (east, the board wall) to past -1013 (west), z 66.8 (the door) to 103.4.
- **Ceiling:** 16.3.

| Set.Mark | Map position (x, y, z) | Facing | Notes |
|---|---|---|---|
| RollCall.EntranceCam | (-938, 9, 48) | toward EntranceLook | entrance hall, by the grand staircase |
| RollCall.EntranceLook | (-1000, 4, 55) | | down the west hallway to Room 102's door |
| RollCall.HallA1 / A2 / A3 | (-955, 0, 49) / (-960, 0, 52) / (-962, 0, 46) | toward HallB | you start last; the others ahead |
| RollCall.HallB1 / B2 / B3 | (-1003, 0, 63.5) / (-1001.5, 0, 64) / (-1005, 0, 63) | +Z (into the door) | outside the classroom door (-1003, 66.6) |
| RollCall.BackCam / BackLook | (-1016, 9.2, 101) / (-983.8, 4.9, 84.8) | | back corner on the students' right |
| RollCall.HaleMark | (-983.8, 0, 84.8) | -X | behind the teacher's desk, beside his chair |
| RollCall.SeatSelf | (-1010.0, 1.545, 84.5) | +X | Seat = true (StudentChair seat 1.545 above the floor) |
| RollCall.MiraChair | (-1010.0, 1.545, 78.1) | +X | Seat = true |
| RollCall.MiraDesk | (-1007.4, 1.27, 78.1), size 3 x 2.54 x 1.96 | +X | the dolly zoom's subject |
| RollCall.SeatS1 | (-1003.8, 1.545, 84.5) | +X | in front of you |
| RollCall.SeatS2 | (-997.0, 1.545, 90.7) | +X | front column, right |
| RollCall.SeatS3 | (-997.0, 1.545, 78.1) | +X | front column, left |
| RollCall.SeatS4 | (-1010.0, 1.545, 90.7) | +X | back row, right of you |
| RollCall.Aisle / Arrive | (-1010.0, 0, 87.6) / (-1007.0, 0, 87.6) | +X | Arrive needs 8.5 studs clear behind it (12 here) |
| RollCall.Bell / Hall.Bell | (-1003.0, 9.2, 65.3), BellPart = `...SchoolBell_Bell` | | the bell over Room 102's door |
| Strike.You | (-1011.5, 0, 78.1) | +X | (2.26.0) 1.5 behind Mira's chair (test: chair 1.6 behind the desk, Map: 2.6, so the you-side marks are measured from the chair) |
| Strike.Rise / TugIt | (-1005.1, 0, 78.1) | -X | across Mira's desk, the board side. Test: both at z 68.8, overlapping the carved clue top by 0.1 |
| Strike.TugYou | (-1011.1, 0, 78.1) | +X | just behind Mira's chair |
| Strike.DodgeTo | (-1011.9, 0, 74.7) | +X | the dodge goes to your left (-Z in the Map) |
| Strike.ThrownTo | (-1013.0, 0, 80.5) | +X | the aisle between Mira's column and yours. Check the west wall (past -1013) by screenshot |
| Strike.Desk | = RollCall.MiraDesk | +X | the shove's target |
| Strike.File | = Hall.File | | |
| Strike.Wide | (-1013.3, 6.4, 88.1) looking at (-1006.9, 2.9, 78.1) | | the establishing camera, back-right of the room |
| Strike.Bell | = RollCall.Bell | | |
| Hall.File | (-1007.4, 2.56, 78.1) | +X | on Mira's desk top |
| Hall.HallCam / HallLook | (-1008, 5.4, 50) / (-930, 4, 50) | | the west hallway at night, toward the entrance hall |
| Hall.CustodianFar | (-962, 0, 50) | -X | far end, about 46 studs away |
| NpcPost Hale | (-983.8, 3, 84.8) | -X | |
| NpcPost Custodian | (-975, 3, 50) | +Z | the west hallway by day |
| QuestArea MiraDesk | centre (-1008.6, 3, 78.1), size 5 x 6 x 4.5 | | |
