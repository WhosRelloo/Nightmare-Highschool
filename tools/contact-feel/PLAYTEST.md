# Contact feel: play test

- **Date:** 2026-11-12
- **Place:** NH Combat Test (98950102230473), Studio Play solo, six short Play runs (one per build step and fix).
- **Save:** slot 4 "Testy" only, loaded with TestBridge `ChooseSlot 4` then `EnterSchool`.
- **Temporary set-up, restored afterwards:** `SlotCount = 4; -- NH TEMP slot test: set back to 3` in `Config.MainMenu`
  and the `ReplicatedStorage` attribute `NHTestNoMenuKeys`. After the last Stop, Edit shows `SlotCount = 3;`, no
  "NH TEMP" text, the attribute is nil, and no probe instance is left.
- **Nothing was chat-typed.**
- **Time of day:** the school clock was at night (3 to 4 AM) the whole time. I didn't move it, because moving it can mark
  test players absent. Students came from TestBridge `SchedulePlan Break` (hangouts), re-sent every 120 s by a Play-only
  server loop, and from `SchedulePlan Class "Period 4"` for seated students.

## How it was measured

- **Client probe.** This was a Play-only ModuleScript, `ReplicatedStorage.NHContactProbe`, created on the client and
  gone after Stop. It places Testy a set distance from a student, facing them, and drives the humanoid with
  `Humanoid:Move(dir)` from a RenderStep bound after the control script. This works like holding W, and
  `MoveDirection` is set. Every rendered frame near the student it logs:
  - `d`: the flat distance between the roots;
  - `vel`: the root's horizontal velocity;
  - `moved`: the position change divided by the frame time (the real speed after the push-out);
  - `ws`: `Humanoid.WalkSpeed`.

  It also logs which Nudge clip is playing on Testy 0.12 s after contact.
- **Sprint.** Real sprints used the game's own LeftShift (the `user_keyboard_input` key-down) with the probe driving the
  direction. Two controlled runs set the client WalkSpeed to 26 for the run (the old line-matrix test did the same) and
  put it back afterwards.
- **Server log.** A Play-only server listener on `NHContact.Impact` logged each report with the server-side distance.
  The students' Studio-only `NHNudgeWhy` / `NHNudge` attributes and `NHSay` were logged with `os.clock()`. Server and
  client share the Studio process clock, so their times can be compared.
- **Frame rate.** Studio ran at about 15 to 40 fps (the server measured 34 fps), so a frame is 0.025 to 0.07 s.

## Results

| # | Check | Result | Numbers |
|---|---|---|---|
| 1 | Walk into a standing student, dead centre | **PASS** | Walking at 14.4 studs/s, the distance holds at exactly 2.20 (never less). Testy is steered to one side and slides round in 0.35 s, 2.4 studs sideways, at about 11 studs/s, then walks on. |
| 2 | Sprint into a student, dead centre (LeftShift, 25.4 studs/s) | **PASS** | Minimum distance 2.20. Testy steered round them in 0.2 s. |
| 3 | Sprint, slightly off centre (25.4) | **PASS** | Arrived at d 2.54 and slid round in 0.15 s, minimum 2.20. |
| 4 | Brush (walk) slowdown and restore | **PASS** | WalkSpeed 14.4 to 9.36 (x0.65) for 0.25 to 0.27 s, then exactly 14.4 again. Real speed in the slow was 5 to 9 studs/s. Also 12.96 to 8.42 (Wounded) and 11.52 to 7.49 (combat-tagged), both put back exactly. |
| 5 | Hard hit (real LeftShift sprint, 25.4) | **PASS** | WalkSpeed 25.38 to 2.03 (x0.08) for 0.33 s. Real speed 0.4 to 4 studs/s. Testy was rocked back: d 2.37 to 2.98 over 0.24 s (ROCK 8). Afterwards WalkSpeed went to 12.00, the server's own value once Shift was released: nothing of ours was left over. The run before the ROCK change (6 studs/s) gave d 2.33 to 2.68. |
| 6 | The twist on Testy | **PASS** | A brush plays Nudge_Left or Nudge_Right at weight 0.49 to 0.54, on the shoulder that met them. A hard hit plays it at weight 1.00. |
| 7 | Report reaches the server | **PASS** | It arrived 1 to 6 ms after the client's contact, every time. |
| 8 | Student reacts at contact, Senses not flagged (Kind "Contact") | **PASS** | Twist 1 to 7 ms after the client's contact: `Contact: speed 14, ... dist 4.8`, and three more like it. Before the reach fix (row 15) these reports were dropped and MakeWay reacted 0.14 to 0.44 s late. |
| 9 | Report ends a waiting MakeWay | **PASS** | `MakeWay ... dist 4.5` and `dist 7.4`: the server distance was still over CONTACT 3, so the report ended the wait. The reaction came 4 to 10 ms after the report. |
| 10 | Hard hit from behind = shove | **PASS** (carry short) | `MakeWay: speed 26, push.look 1.00, behind true, room 3.7, carry 0.7`, then the Shove clip. Shoved line "Ow! Hey! What did I do?" 1.29 s later, at the look back. Every student I could reach had a wall or the fountain 3 to 4 studs ahead, so the room check held the carry short. The speed scaling (up to 3 x 1.5 = 4.5 studs) never had the room to show: **NOT TESTED** at full carry. |
| 11 | Bump line at contact (brush) | **PASS** | "Eep! My books!" 7 ms after the client's contact (6764.750 to 6764.757). Before, MakeWay said it on the approach. Brushes say it 60% of the time, and a student who spoke in the last 10 s stays quiet (the brain's cooldown), as before. |
| 12 | Sprint line at contact | **PASS** | "No running in the halls!" 4 ms after the contact. Also "Late for something?", "Slow down!" and "Where's the fire?". |
| 13 | Seated student | **PASS** | Solid: minimum distance 2.20. Testy still feels the brush (WalkSpeed 9.36, Nudge_Right 0.54). The report was sent and the student didn't react (no `NHNudgeWhy`): Brain.Contact returns at `S.Seated`. |
| 14 | Group: squeezed between two students | **PASS** | Two students were anchored 3.2 apart for the test (Play-only). Testy was held for 0.27 s under the slow, then 0.5 s stuck, then let through (the 0.4 s stuck rule). They stood at 1.76 from both and passed. A 4.8-stud gap between two students needed no contact at all (minimum 2.35). |
| 15 | Server distance check versus replication lag | **FIXED and PASS** | The server sees the player 3.5 studs behind the client at 13 studs/s, and 7.9 behind at 25. With the first reach (4 + 0.06 x speed), brushes were dropped. Now it's 4 + 0.4 x the server-seen speed, and past 4 the student must be ahead along the reported direction. Accepted at 4.45, 4.83, 5.20 and 7.94. |
| 16 | Near a wall (the Commons fountain rim) | **PASS with a note** | Testy was never trapped. One student was anchored 1.9 studs from the rim and Testy walked into the gap. In the first build, with another student also pushing, Testy was pushed partly up onto the fountain rim (root up to y 6.5, from 4.3) and walked on. The wall rays now start 0.6 studs behind the root and add a shin ray, because a ray that starts inside a rim you already touch doesn't see it. I didn't run this case again after that fix. |
| 17 | Never stuck | **PASS** | No run left Testy held for more than 0.8 s. The two cases that held were the pinned pair (row 14) and an early single-student stall, before the stuck rule; both were let through. |
| 18 | No jitter | **PASS** | While in contact, the logged distance stays at 2.20 to 2.26 frame to frame, and the position moves smoothly along the circle. The only jumps were Studio-wide frame stalls of 0.8 to 1.1 s. I saw them with and without contact (6393 and 6505 had none), so they aren't caused by ContactFeel. |
| 19 | No teleport bumps | **FIXED** | A probe teleport that landed 2.7 studs from a student fired a bump (row 15's run). Now a frame jump of more than 4 studs (or 3 frames of movement) gives the push-out but no impact. This was installed and not seen again, but I didn't test it on purpose. |
| 20 | Console | **PASS** | No `[ContactFeel]` or `[StudentBrain]` warnings in any run. The asset-permission lines in the output were there before this work, and none of them are our sounds (8251487534, 129025918122048). |
| 21 | Camera jolt and sounds | **NOT VERIFIED BY EAR / EYE** | The code calls `EmitManager.ShakeCamera` and plays clones of `Assets.Sounds.Movement.Land` and `SwingSFX.Blunt.Swing`. Neither sound failed to load. I can't hear the sounds, and the night screen captures are too dark to judge the camera bump or the lean. |
| 22 | Screen captures of a brush and a hard hit | **PARTIAL** | Two captures were taken during brushes, one with client exposure raised for the shot. Night lighting makes them nearly unreadable, and the capture call lags the contact by about 1 s. |
| 23 | Transformed player, downed or ragdolled player | **NOT TESTED** | The code skips contact while the player is in Physics, Ragdoll, FallingDown, Seated or PlatformStanding, Downed, carried, gripped, Hidden or on a skateboard. |

## Play-only changes, all gone after Stop

- Students were anchored and moved for rows 14 and 16, and unanchored 25 to 30 s later.
- The client WalkSpeed was set to 26 for two runs and put back.
- Lighting `ExposureCompensation` was raised on the client for one capture and put back.
- The probe ModuleScript, `NHProbeOut`, `NHServerLog`, `NHServerLog2` and the workspace `NHContactTestLoop` attribute.
- Testy's health and status changed: Clique wardens and the night hurt her, so she was Wounded and Chilled. The game did
  that, not the test, and nothing was written to the profile by the test.
