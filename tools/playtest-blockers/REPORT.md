# Playtest blockers: record (2026-11-25)

Branch `playtest-blockers` (off `main` 4de5d56). Place: NH Combat Test (98950102230473), slot 2.
Installed in Edit with `tools/admin-console/install_inplace.py`. Backup: `ServerStorage.NH_Backup.PlaytestBlockers_20261125`
(the pre-change copies of all five scripts). **The place is not saved.**

`orig/` holds the scripts as fetched before the change and `live/` the installed versions. After the last Play round
all five were fetched again and match `live/` byte for byte. `checks/` holds the checks. `tool/` holds private copies of
the admin-console and forms harness tools: another session was running the shared ones in `E:/NH-main` at the same
time, and they write one shared temp file.

| Script | Change |
|---|---|
| `ServerScriptService.Services.Sports.Soccer` | `Local.BallOnlyWalls`: `SportBallWall` collides with `SportBall` only, swept at Setup/OnStart and every 10 s |
| `StarterPlayer...Controllers.Gui.QuestTracker` | `Local.Unclutter`: a needed quest prompt beats the same-key prompts crowding it (client only) |
| `ServerScriptService.Services.Features.LostFound` | adopts the kit-built `LostFoundBox` (tag `NHLostFoundBox`); empty-handed hint |
| `ServerScriptService.Services.Features.Downed` | `Local.Scaled` (carry offset scales with the carrier); every grip welds its victim |
| `ReplicatedStorage.Config.Downed` | `CarryOffset` (-1.3, 2.0, 0.6) -> (-0.5, -0.1, 0.65), comments |

## Findings

1. **Left Alt.** In code, `LeftAlt` appears only in `UI.Settings` (reserved as Shift lock and listed under Fixed Keys),
   `UI.Components` (the key-cap label) and `Controllers.Character.ShiftLockKey`, which sets the PlayerModule's
   `MouseLockController.BoundKeys`. At runtime no ContextActionService action is bound to it. A real Alt press changes only
   the shift-lock reticle, the cursor and `MouseBehavior`, and Shift does not toggle shift lock. **No change.** If the owner saw
   Alt do something else, that needs the exact situation. In Studio itself, Alt also shows the ribbon's key tips.
2. **New Kid note.** Slot 2 was stuck at stage 4 (`Note`). The note prompt (`QuestPrompt`, "Read note") works and is on.
   But `Locker113` also carries the class locker's `NHClassPrompt` ("Change Class"), the lockers 2 studs either side have
   `LockerPrompt` ("Open"), and students stand about the hall with "Talk", all on E. The default `Exclusivity`
   (OnePerButton) shows one of them, and in Play E fired a student's Talk. A first fix (mute only prompts within 3 studs of the
   quest prompt) still lost to that student, so the rule now has two parts:
   - prompts within 3 studs of a needed quest prompt are muted, and
   - while you stand within 4.5 studs of it, every same-key prompt within 10 studs of you is muted too.

   It runs every 0.25 s on the client, and muted prompts come back when the quest prompt goes. Prompts switched off by
   their own systems are left alone.
3. **Lost & Found.** `Workspace.LostFoundBox` (build-kit attribute `NHBuildKit = "LostFound"`) had no `NHLostFoundBox` tag,
   so `Features.LostFound` never put its "Hand in" prompt on it, and the Kit's dorm-key hand-in didn't see it either. The
   lost items (`Lost_*`) carry the same kit attribute, so the adopt rule takes only the model named `LostFoundBox` with no
   `NHLostItem`. A first version tagged items as boxes; it was caught in Play and fixed.
4. **Soccer.** In Edit, `SportBallWall` was non-collidable with Default and Characters. At runtime, character parts are in
   `Entity`, and `Entity`, `NPC`, `Ragdoll`, `Debri`, `NHWalkers` and `TutorialPlayers` all collided with it. So the
   invisible ball walls (`BallWallN/S/E/W`, `BallCeiling`, `PracWall*`) were walls for people too.
5. **Carry and grip** (asked for mid-task). With the carry revamp's clips (IdleCarrier raises the right arm and wraps the
   left across the front), the old offset put the carried torso 3.7 studs up, above the carrier's head and upside down.
   It was screenshotted, then tuned live and checked in a side-view screenshot. A normal grip placed the victim and left it
   free: an NPC told to walk off slid from 3 studs to 0.3 studs, into the gripper.

## Play checks

Each round started with a fresh slot-2 snapshot and recorded cine before and after.

| Round | Checks | Result |
|---|---|---|
| 1 (diagnosis) | probes only | cine before/after `PASS CineState=nil Seen=nil Origin=nil`, slot 2 restored |
| 2 | `pitch_walk.lua` | PASS: pitch gap 2.9 s, centre 6.3 s, practice 3.2 s; groups Entity, Default pass the ball walls |
| 2 | `soccer2/checks/soccer_match_start.lua`, `soccer_match_end.lua` | PASS live (InSport=Pitch), PASS ended |
| 2 | `carry_grip.lua` | PASS: carried torso (1.26, 1.59, 0.45) from the carrier torso, legs y 0.35; grip drift 0.00, weld on, victim finished |
| 2 | first QuestTracker / LostFound versions | failed in Play (E went to a student's Talk; lost items tagged as boxes) -> revised |
| 2 | (stopped from outside before the restore: another session took Studio; nothing on slot 2 had changed) | |
| 3 | `note_setup.lua` + `note_client.lua` + real E + `note_after.lua` | PASS: only "Read note" on (Change Class and 3 Opens muted); E fired `Locker113:Read note`; New Kid completed, EmptyDesk active, LockerNote clue filed. Afterwards all 10 nearby E prompts are back on |
| 3 | `lf_setup.lua` + real E + `lf_after.lua` | PASS: E fired `LostFoundBox:Hand in`; hands empty, 20 Yen paid (put back); only `LostFoundBox` is tagged. Empty-handed E shows "3 things are lying lost around the grounds." |
| 3 | Left Alt, two real presses | PASS: the first changes only the reticle, cursor and MouseBehavior (LockCenter); the second returns to the baseline exactly |
| 3 | cine before/after | `PASS CineState=nil Seen=nil Origin=nil` both; slot 2 restored (EmptyDesk active, New Kid done) |
| Edit | `alt_edit.lua` | PASS: reserved, listed, refused for 8 rebindable actions, no other script names LeftAlt |

**Slot 2 note.** Between rounds 2 and 3 another session's Play round moved slot 2 past New Kid: its snapshot at 13:30 has
New Kid done and the LockerNote clue filed. Round 3 staged New Kid back to stage 4 for the test and restored round 3's own
snapshot afterwards. So slot 2 ends where that session left it, not at the stuck stage-4 state from this morning.

## Not done / follow-ups
- The class locker sits on the quest locker 113 (`NHClassLocker` tag on `Locker113`). The note now wins while it's needed,
  but a class locker on another locker would avoid the clash for good (a place-data change).
- Locker 119's placeholder has two "Open" prompts (two lockers point at it): harmless, but untidy.
- graphify isn't installed here, so the graph wasn't updated.
